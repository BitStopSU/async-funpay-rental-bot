import asyncio
import logging
import math
import sqlite3
from datetime import datetime
from urllib.parse import urlsplit

import aiohttp
import httpx
from aioFunPayAPI import Runner
from aioFunPayAPI.common.enums import EventTypes, OrderStatuses
from aioFunPayAPI.common.exceptions import (
    LotSavingError,
    RequestFailedError,
    UnauthorizedError,
)

from config import Config
from database import Database
from funpay_session import FunPayAccount
from i18n import tr
from listing_sync import normalize_funpay_lot_id, sync_listing
from notify import send_tg_photo
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
        self._ready = asyncio.Event()

    async def start(self):
        if not self.golden_key:
            raise ValueError(tr("funpay_key_missing"))
        self.acc = await FunPayAccount(golden_key=self.golden_key).get(
            update_phpsessid=True
        )
        self.runner = SessionRefreshingRunner(self.acc)
        self._ready.set()
        await self.sync_all_listings()
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

    async def sync_all_listings(self):
        if not self._ready.is_set():
            raise ValueError(tr("admin_menu_funpay_unavailable"))
        updated = 0
        for lot in self.db.get_lots_for_sync():
            updated += await self._sync_listing(lot["lot_id"], lot["account_id"])
        return updated

    async def register_listing(self, lot_id: str, account_id: int):
        if not self._ready.is_set():
            raise ValueError(tr("admin_menu_funpay_unavailable"))
        lot_id = normalize_funpay_lot_id(lot_id)
        if self.db.get_lot(lot_id):
            raise ValueError(tr("cli_lot_already_registered"))
        account = self.db.get_account_listing_data(account_id)
        eligible_ids = {
            row["account_id"] for row in self.db.get_unlinked_accounts()
        }
        if not account or account_id not in eligible_ids:
            raise ValueError(tr("cli_lot_accounts_empty"))

        lot_fields = await self.acc.get_lot_fields(int(lot_id))
        title_ru = (lot_fields.title_ru or "").strip()
        title_en = (lot_fields.title_en or "").strip()
        price = lot_fields.price
        if not title_ru and not title_en or price is None or price <= 0:
            raise ValueError(tr("cli_lot_fetch_failed"))
        self.db.register_lot(
            lot_id,
            title_ru or title_en,
            price,
            account_id,
            title_en=title_en or title_ru,
        )
        await self._sync_listing(lot_id, account_id)
        return lot_id

    async def update_listing_price(self, lot_id: str, price: float):
        if not self._ready.is_set():
            raise ValueError(tr("admin_menu_funpay_unavailable"))
        price = float(price)
        if not math.isfinite(price) or price <= 0:
            raise ValueError(tr("cli_lot_invalid"))
        lot = self.db.get_lot(lot_id)
        if not lot:
            raise ValueError(tr("cli_lot_fetch_failed"))
        fields = await self.acc.get_lot_fields(int(lot_id))
        fields.edit_fields({"price": f"{price:g}"})
        await self.acc.save_lot(fields)
        self.db.update_lot_price(lot_id, price)
        if lot["account_id"] is None or lot["is_extension"]:
            return False
        return await self._sync_listing(lot_id, lot["account_id"])

    async def sync_account_listing(self, account_id: int):
        if not self._ready.is_set():
            return False
        lot = self.db.get_lot_by_account_id(account_id)
        if lot:
            return await self._sync_listing(lot["lot_id"], account_id)
        return False

    async def _sync_listing(self, lot_id: str, account_id: int):
        try:
            return await sync_listing(self.db, self.acc, lot_id, account_id)
        except (
            aiohttp.ClientError,
            RequestFailedError,
            UnauthorizedError,
            LotSavingError,
            ValueError,
        ) as exc:
            logger.error(
                "%s (%s)",
                tr("listing_sync_failed", lot_id=lot_id),
                type(exc).__name__,
            )
            self.db.log(
                "listing_sync_failed",
                account_id=account_id,
                details={"lot_id": str(lot_id), "error_type": type(exc).__name__},
                severity="error",
            )
            self.db.queue_notification(
                tr("listing_sync_failed", lot_id=lot_id),
                severity="warning",
            )
            return False

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
        extension_request = None
        if active and not lot["is_extension"]:
            if str(active["lot_id"]) == str(lot_id):
                extension_request = self.db.get_pending_extension_request(
                    active["order_id"], str(chat_id)
                )
        recent_extension_request = None
        if not lot["is_extension"]:
            recent_extension_request = self.db.get_recent_extension_request(
                str(chat_id), str(lot_id)
            )
        if (
            recent_extension_request
            and not extension_request
            and (
                not active
                or str(active["lot_id"]) == str(lot_id)
            )
        ):
            self.db.log(
                "late_extension_payment_referred",
                user_id=user_id,
                order_id=order_id,
                details={"lot_id": str(lot_id), "chat_id": str(chat_id)},
                severity="warning",
            )
            self.db.queue_notification(
                tr("notify_extension_unmatched", order_id=order_id)
            )
            await self.acc.send_message(chat_id, tr("extension_operator"))
            return
        if lot["is_extension"] or extension_request:
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

        account = self.db.get_free_account_for_lot(str(lot_id))
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
            tr("manual_fulfillment") + "\n\n" + tr("profile_screenshot_request"),
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
        if message.image_link:
            await self.on_profile_screenshot(message)
            return
        text = (message.text or "").strip()
        command_parts = text.split()
        command = (
            command_parts[0].split("@", maxsplit=1)[0].casefold()
            if command_parts else ""
        )
        if command == "/akk":
            await self.on_available_lots_command(
                message.chat_id, command_parts[1:]
            )
            return
        if command == "/dodep":
            if command_parts[1:]:
                await self.acc.send_message(
                    message.chat_id, tr("extension_command_usage")
                )
            else:
                await self.on_extension_command(message.chat_id)
            return
        if text.casefold() not in ("!код", "код", "guard"):
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

    async def on_extension_command(self, chat_id):
        request = self.db.create_extension_request(
            str(chat_id), Config.EXTENSION_PAYMENT_WINDOW_MINUTES
        )
        if not request:
            await self.acc.send_message(
                chat_id, tr("extension_request_unavailable")
            )
            return
        link = f"https://funpay.com/lots/offer?id={request['lot_id']}"
        expires = datetime.fromisoformat(request["expires_at"]).strftime(
            "%H:%M"
        )
        await self.acc.send_message(
            chat_id,
            tr(
                "extension_payment_link",
                link=link,
                expires=expires,
            ),
        )

    async def on_available_lots_command(self, chat_id, arguments):
        lots = self.db.get_available_lots()
        if not lots:
            await self.acc.send_message(chat_id, tr("available_lots_empty"))
            self.db.log(
                "available_lots_requested",
                details={"chat_id": str(chat_id), "count": 0},
            )
            return

        if arguments:
            if len(arguments) != 1 or not arguments[0].isdecimal():
                await self.acc.send_message(chat_id, tr("available_lots_usage"))
                return
            lot_id = arguments[0]
            lot = next((item for item in lots if item["lot_id"] == lot_id), None)
            if not lot:
                await self.acc.send_message(chat_id, tr("available_lots_changed"))
                return
            link = f"https://funpay.com/lots/offer?id={lot_id}"
            await self.acc.send_message(
                chat_id,
                tr(
                    "available_lot_link",
                    lot_id=lot_id,
                    link=link,
                ),
            )
            self.db.log(
                "available_lot_selected",
                details={
                    "chat_id": str(chat_id),
                    "lot_id": str(lot["lot_id"]),
                },
            )
            return

        rows = [
            tr(
                "available_lot_row",
                lot_id=lot["lot_id"],
                title=" ".join(str(lot["title"]).split())[:45],
                mmr=lot["mmr"] if lot["mmr"] is not None else "—",
                price=f"{lot['price_per_hour']:g}",
            )
            for lot in lots
        ]
        chunks = [tr("available_lots_header")]
        for row in rows:
            if len(chunks[-1]) + len(row) + 1 > 3500:
                chunks.append(tr("available_lots_continued"))
            chunks[-1] += f"\n{row}"
        chunks[-1] += f"\n{tr('available_lots_footer')}"
        for chunk in chunks:
            await self.acc.send_message(chat_id, chunk)
        self.db.log(
            "available_lots_requested",
            details={"chat_id": str(chat_id), "count": len(lots)},
        )

    async def on_profile_screenshot(self, message):
        rental = self.db.get_active_rental_by_chat(str(message.chat_id))
        if not rental:
            await self.acc.send_message(
                message.chat_id, tr("profile_screenshot_no_active_rental")
            )
            return
        if not Config.TG_BOT_TOKEN or not Config.TG_ADMIN_ID:
            self.db.log(
                "profile_screenshot_not_stored",
                account_id=rental["account_id"],
                order_id=rental["order_id"],
                details={"reason": "telegram_not_configured"},
                severity="warning",
            )
            await self.acc.send_message(
                message.chat_id, tr("profile_screenshot_admin_unavailable")
            )
            return

        image_url = message.image_link
        try:
            parsed_url = urlsplit(image_url)
            image_port = parsed_url.port
        except ValueError:
            parsed_url = None
            image_port = None
        hostname = (parsed_url.hostname or "").casefold() if parsed_url else ""
        if (
            not parsed_url
            or parsed_url.scheme != "https"
            or image_port not in (None, 443)
            or not hostname
            or not (hostname == "funpay.com" or hostname.endswith(".funpay.com"))
            or parsed_url.username
            or parsed_url.password
        ):
            self.db.log(
                "profile_screenshot_rejected",
                account_id=rental["account_id"],
                order_id=rental["order_id"],
                details={"reason": "unsupported_image_url"},
                severity="warning",
            )
            await self.acc.send_message(
                message.chat_id, tr("profile_screenshot_invalid")
            )
            return

        submission_id = self.db.start_screenshot_submission(
            order_id=rental["order_id"],
            account_id=rental["account_id"],
            buyer_nick=rental["buyer_nick"],
            source_chat_id=str(message.chat_id),
            source_message_id=str(message.id),
        )
        if submission_id is None:
            return

        submitted_at = self.db.conn.execute(
            """SELECT submitted_at FROM screenshot_submissions
               WHERE submission_id = ?""",
            (submission_id,),
        ).fetchone()["submitted_at"]
        caption = tr(
            "profile_screenshot_admin_caption",
            order_id=rental["order_id"],
            buyer=rental["buyer_nick"],
            submitted_at=datetime.fromisoformat(submitted_at).strftime(
                "%d.%m.%Y %H:%M"
            ),
            lot_id=rental["lot_id"],
        )
        try:
            telegram_message = await send_tg_photo(image_url, caption)
        except (httpx.HTTPError, RuntimeError, KeyError, TypeError) as exc:
            self.db.mark_screenshot_submission_failed(submission_id)
            self.db.queue_notification(
                tr(
                    "profile_screenshot_delivery_failed",
                    order_id=rental["order_id"],
                    error=type(exc).__name__,
                )
            )
            await self.acc.send_message(
                message.chat_id, tr("profile_screenshot_delivery_failed_buyer")
            )
            return

        photos = telegram_message.get("photo") or []
        telegram_file_id = photos[-1].get("file_id") if photos else None
        self.db.mark_screenshot_submission_sent(
            submission_id,
            telegram_message["message_id"],
            telegram_file_id,
        )
        await self.acc.send_message(
            message.chat_id, tr("profile_screenshot_received")
        )
