import asyncio
import logging
import sqlite3

from aioFunPayAPI import Account, Runner
from aioFunPayAPI.common.enums import EventTypes, OrderStatuses
from aioFunPayAPI.common.exceptions import RequestFailedError

from database import Database
from i18n import tr
from ticker import expiry_ticker

logger = logging.getLogger(__name__)
SESSION_REFRESH_COOLDOWN = 60


class SessionRefreshingRunner(Runner):
    """Refresh FunPay session data once after a stale-cookie response."""

    def __init__(self, account):
        super().__init__(account)
        self._last_session_refresh = 0.0

    async def get_updates(self):
        try:
            return await super().get_updates()
        except RequestFailedError as exc:
            now = asyncio.get_running_loop().time()
            if (
                not _is_stale_cookie_error(exc)
                or now - self._last_session_refresh < SESSION_REFRESH_COOLDOWN
            ):
                raise

            self._last_session_refresh = now
            logger.warning(tr("funpay_cookie_refresh"))
            await self.account.get(update_phpsessid=True)
            return await super().get_updates()


def _is_stale_cookie_error(error: RequestFailedError) -> bool:
    if error.status_code != 400:
        return False
    try:
        message = error.response.json().get("msg", "").casefold()
    except (AttributeError, TypeError, ValueError):
        return False
    return "cookie" in message and (
        "устарел" in message or "отсутствует" in message
    )


class RentalBot:
    def __init__(self, golden_key: str, db: Database):
        self.acc = None
        self.runner = None
        self.golden_key = golden_key
        self.db = db

    async def start(self):
        if not self.golden_key:
            raise ValueError(tr("funpay_key_missing"))
        self.acc = await Account(golden_key=self.golden_key).get(
            update_phpsessid=True
        )
        self.runner = SessionRefreshingRunner(self.acc)
        logger.info(tr("funpay_started"))
        ticker = asyncio.create_task(expiry_ticker(self.db), name="rental-expiry-ticker")
        try:
            async for event in self.runner.listen(requests_delay=6.0):
                try:
                    await self.handle_event(event)
                except Exception as exc:
                    logger.error(
                        tr("funpay_handler_failed"), type(exc).__name__
                    )
                    self.db.log(
                        "handler_error",
                        details={"error_type": type(exc).__name__,
                                 "event_type": str(event.type)},
                        severity="error",
                    )
        finally:
            ticker.cancel()
            await asyncio.gather(ticker, return_exceptions=True)

    async def handle_event(self, event):
        if event.type == EventTypes.NEW_ORDER:
            await self.on_new_order(event)
        elif event.type == EventTypes.NEW_MESSAGE:
            await self.on_message(event)

    async def on_new_order(self, event):
        order = event.order
        if order.status != OrderStatuses.PAID:
            return

        order_id = str(order.id).replace("#", "")
        order_info = await self.acc.get_order(order_id)
        if self.db.is_order_processed(order_id):
            chat_id = getattr(order, "buyer_id", None)
            await self.acc.send_message(
                chat_id, tr("order_already_registered")
            )
            return
        buyer = order.buyer_username
        quantity = int(getattr(order, "amount", None) or 1)
        buyer_id = getattr(order, "buyer_id", None)
        chat_id = getattr(order, "chat_id", None) or buyer_id
        lot_id = getattr(order, "lot_id", None)
        lot = self.db.get_lot(str(lot_id)) if lot_id is not None else None
        if not lot:
            lot_title = getattr(order_info, "short_description", None)
            if lot_title:
                lot = self.db.get_lot_by_title(lot_title)
            if lot:
                lot_id = lot["lot_id"]
        if not buyer or buyer_id is None or not lot or quantity <= 0:
            self.db.log(
                "order_rejected_invalid", order_id=order_id,
                details={
                    "has_buyer": bool(buyer),
                    "has_buyer_id": buyer_id is not None,
                    "has_configured_lot": bool(lot),
                },
                severity="warning",
            )
            self.db.queue_notification(
                tr("notify_lot_unmatched", order_id=order_id)
            )
            await self.acc.send_message(
                chat_id, tr("paid_order_operator")
            )
            return

        user_id = self.db.get_or_create_user(buyer)

        active = self.db.get_active_rental_by_buyer(buyer)
        if lot["is_extension"]:
            if not active:
                self.db.log(
                    "extension_without_active_rental", user_id=user_id,
                    order_id=order_id, details={"lot_id": lot_id},
                    severity="warning",
                )
                self.db.queue_notification(
                    tr("notify_extension_unmatched", order_id=order_id)
                )
                await self.acc.send_message(
                    chat_id,
                    tr("extension_operator"),
                )
                return
            ends = self.db.extend_rental(
                active["order_id"], quantity, extension_order_id=order_id
            )
            if not ends:
                await self.acc.send_message(
                    chat_id,
                    tr("extension_operator"),
                )
                return
            await self.acc.send_message(
                chat_id,
                tr(
                    "extension_confirmed", hours=quantity,
                    ends=ends.strftime("%Y-%m-%d %H:%M"),
                ),
            )
            return

        if active:
            self.db.log(
                "buyer_already_renting", user_id=user_id, order_id=order_id,
                details={"active_order_id": active["order_id"]},
                severity="warning",
            )
            self.db.queue_notification(
                tr("notify_buyer_already_renting", order_id=order_id)
            )
            await self.acc.send_message(
                chat_id,
                tr("already_renting"),
            )
            return

        account = self.db.get_free_account()
        if not account:
            self.db.log(
                "no_free_account", user_id=user_id, order_id=order_id,
                severity="warning",
            )
            self.db.queue_notification(
                tr("notify_no_accounts", order_id=order_id)
            )
            await self.acc.send_message(
                chat_id,
                tr("no_accounts"),
            )
            return

        try:
            ends = self.db.create_rental(
                order_id, user_id, account["account_id"], lot_id, quantity,
                buyer, chat_id=chat_id,
            )
        except (ValueError, sqlite3.Error) as exc:
            self.db.log(
                "rental_creation_failed", user_id=user_id,
                account_id=account["account_id"], order_id=order_id,
                details={"error_type": type(exc).__name__}, severity="error",
            )
            self.db.queue_notification(
                tr("notify_order_failed", order_id=order_id)
            )
            await self.acc.send_message(
                chat_id, tr("paid_order_operator")
            )
            return

        self.db.queue_notification(
            tr(
                "notify_manual_fulfillment",
                order_id=order_id,
                account_id=account["account_id"],
            )
        )
        await self.acc.send_message(
            chat_id,
            tr("manual_fulfillment"),
        )
        self.db.log(
            "rental_requires_manual_fulfillment", user_id=user_id,
            account_id=account["account_id"], order_id=order_id,
            details={"ends": ends.isoformat()},
        )

    async def on_message(self, event):
        message = event.message
        if str(message.author_id) == str(self.acc.id):
            return
        text = (message.text or "").lower().strip()
        if text not in ("!код", "код", "guard"):
            return
        rental = self.db.get_active_rental_by_chat(str(message.chat_id))
        if rental:
            response = tr("credential_request_active")
        else:
            response = tr("credential_request_inactive")
        await self.acc.send_message(message.chat_id, response)
        self.db.log(
            "credential_request_referred_to_operator",
            account_id=rental["account_id"] if rental else None,
            order_id=rental["order_id"] if rental else None,
            details={"chat_id": str(message.chat_id)},
        )
