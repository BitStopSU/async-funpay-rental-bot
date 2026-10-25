"""Telegram administrator menu for rental status and listing management."""

import asyncio
import logging
import sqlite3
from typing import Any

import aiohttp
import httpx
from aioFunPayAPI.common import exceptions

from config import Config
from database import Database
from i18n import tr

logger = logging.getLogger(__name__)
POLL_TIMEOUT = 25
TELEGRAM_TEXT_LIMIT = 3800


def _main_keyboard() -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [
                {"text": tr("admin_menu_status"), "callback_data": "admin:status"},
                {"text": tr("admin_menu_accounts"), "callback_data": "admin:accounts"},
            ],
            [
                {"text": tr("admin_menu_rentals"), "callback_data": "admin:rentals"},
                {"text": tr("admin_menu_lots"), "callback_data": "admin:lots"},
            ],
            [
                {
                    "text": tr("admin_menu_add_account"),
                    "callback_data": "admin:add_account",
                },
                {
                    "text": tr("admin_menu_settings"),
                    "callback_data": "admin:settings",
                },
            ],
            [
                {
                    "text": tr("admin_menu_listing_text"),
                    "callback_data": "admin:listing_text",
                },
                {
                    "text": tr("admin_menu_link_lot"),
                    "callback_data": "admin:link_lot",
                },
            ],
            [
                {
                    "text": tr("admin_menu_update_behavior"),
                    "callback_data": "admin:update_behavior",
                },
                {
                    "text": tr("admin_menu_sync_listings"),
                    "callback_data": "admin:sync_listings",
                },
            ],
        ]
    }


def _back_keyboard() -> dict[str, Any]:
    return {
        "inline_keyboard": [[
            {"text": tr("admin_menu_back"), "callback_data": "admin:menu"}
        ]]
    }


def _split_lines(text: str) -> list[str]:
    parts: list[str] = []
    current = ""
    for line in text.splitlines():
        if len(line) > TELEGRAM_TEXT_LIMIT:
            if current:
                parts.append(current)
                current = ""
            parts.extend(
                line[index:index + TELEGRAM_TEXT_LIMIT]
                for index in range(0, len(line), TELEGRAM_TEXT_LIMIT)
            )
            continue
        if current and len(current) + len(line) + 1 > TELEGRAM_TEXT_LIMIT:
            parts.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        parts.append(current)
    return parts or [""]


async def _telegram_call(
    client: httpx.AsyncClient, method: str, payload: dict[str, Any]
) -> Any:
    response = await client.post(
        f"https://api.telegram.org/bot{Config.TG_BOT_TOKEN}/{method}",
        json=payload,
    )
    response.raise_for_status()
    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(tr("admin_menu_api_failed", method=method))
    return result.get("result")


async def _send_text(
    client: httpx.AsyncClient,
    text: str,
    keyboard: dict[str, Any] | None = None,
) -> None:
    parts = _split_lines(text)
    for index, part in enumerate(parts):
        payload: dict[str, Any] = {
            "chat_id": Config.TG_ADMIN_ID,
            "text": part,
        }
        if index == len(parts) - 1 and keyboard:
            payload["reply_markup"] = keyboard
        await _telegram_call(client, "sendMessage", payload)


def _account_keyboard(accounts, callback_prefix: str) -> dict[str, Any]:
    buttons = [
        {
            "text": f"#{account['account_id']} · "
            f"{account['mmr'] if account['mmr'] is not None else '—'} MMR",
            "callback_data": f"admin:{callback_prefix}:{account['account_id']}",
        }
        for account in accounts
    ]
    return {
        "inline_keyboard": [
            buttons[index:index + 2] for index in range(0, len(buttons), 2)
        ] + [[{"text": tr("admin_menu_back"), "callback_data": "admin:menu"}]]
    }


def _status_text(db: Database) -> str:
    values = db.get_admin_status()
    return tr("admin_menu_status_text", **values)


def _accounts_text(db: Database) -> str:
    accounts = db.get_admin_accounts()
    if not accounts:
        return tr("admin_menu_accounts_empty")
    lines = []
    for account in accounts:
        lines.append(
            tr(
                "admin_menu_account_row",
                account_id=account["account_id"],
                status=tr(f"admin_status_{account['status']}"),
                mmr=account["mmr"] if account["mmr"] is not None else "—",
                vac=(
                    tr("admin_menu_vac_yes")
                    if account["vac_banned"]
                    else tr("admin_menu_vac_no")
                ),
                lot=account["lot_id"] or tr("admin_menu_no_lot"),
            )
        )
    return "\n".join(lines)


def _rentals_text(db: Database) -> str:
    rentals = db.get_admin_active_rentals()
    if not rentals:
        return tr("admin_menu_rentals_empty")
    return "\n".join(
        tr(
            "admin_menu_rental_row",
            order_id=rental["order_id"],
            buyer=rental["buyer_nick"],
            account_id=rental["account_id"],
            lot_id=rental["lot_id"],
            ends_at=rental["ends_at"],
        )
        for rental in rentals
    )


def _lots_text(db: Database) -> str:
    lots = db.get_admin_lots()
    if not lots:
        return tr("admin_menu_lots_empty")
    return "\n".join(
        tr(
            "admin_menu_lot_row",
            lot_id=lot["lot_id"],
            title=lot["title"],
            price=lot["price_per_hour"],
            account=(
                lot["account_id"]
                if lot["account_id"] is not None
                else tr("admin_menu_no_lot")
            ),
        )
        for lot in lots
    )


def _settings_text() -> str:
    configured = tr("admin_menu_configured")
    missing = tr("admin_menu_missing")
    return tr(
        "admin_menu_settings_text",
        funpay=configured if Config.GOLDEN_KEY else missing,
        telegram=(
            configured
            if Config.TG_BOT_TOKEN and Config.TG_ADMIN_ID
            else missing
        ),
        encryption=configured if Config.SECRET_KEY else missing,
        steam_api=configured if Config.STEAM_API_KEY else missing,
        db_path=Config.DB_PATH,
        language=Config.BOT_LANGUAGE,
    )


async def _show_section(
    client: httpx.AsyncClient, db: Database, section: str, pending: dict
) -> None:
    if section == "status":
        text = _status_text(db)
    elif section == "accounts":
        text = _accounts_text(db)
    elif section == "rentals":
        text = _rentals_text(db)
    elif section == "lots":
        text = _lots_text(db)
    elif section == "add_account":
        text = tr("admin_menu_add_account_text")
    elif section == "listing_text":
        text = _listing_text(db)
    elif section == "settings":
        text = _settings_text()
    elif section == "link_lot":
        accounts = db.get_unlinked_accounts()
        if not accounts:
            await _send_text(
                client, tr("admin_menu_link_no_accounts"), _back_keyboard()
            )
            return
        pending["action"] = "lot_id"
        await _send_text(client, tr("admin_menu_link_enter_lot"))
        return
    elif section == "update_behavior":
        accounts = db.conn.execute(
            """SELECT account_id, mmr FROM accounts
               WHERE vac_banned = 0 ORDER BY account_id"""
        ).fetchall()
        if not accounts:
            await _send_text(
                client, tr("admin_menu_accounts_empty"), _back_keyboard()
            )
            return
        await _send_text(
            client,
            tr("admin_menu_behavior_choose"),
            _account_keyboard(accounts, "behavior_account"),
        )
        return
    elif section == "sync_listings":
        return
    else:
        await _show_menu(client)
        return
    await _send_text(client, text, _back_keyboard())


def _listing_text(db: Database) -> str:
    lots = db.get_lots_for_sync()
    if not lots:
        return tr("admin_menu_lots_empty")
    return "\n".join(
        tr(
            "admin_menu_listing_stats",
            lot_id=lot["lot_id"],
            account_id=lot["account_id"],
            mmr=lot["mmr"] if lot["mmr"] is not None else "—",
            behavior=(
                lot["behavior_score"]
                if lot["behavior_score"] is not None
                else "—"
            ),
        )
        for lot in lots
    )


async def _show_menu(client: httpx.AsyncClient) -> None:
    await _send_text(
        client,
        f"{tr('admin_menu_title')}\n{tr('admin_menu_open')}",
        _main_keyboard(),
    )


async def _handle_update(
    client: httpx.AsyncClient,
    db: Database,
    update: dict[str, Any],
    bot=None,
    pending: dict | None = None,
) -> None:
    pending = pending if pending is not None else {}
    message = update.get("message")
    if message:
        sender = message.get("from", {})
        chat = message.get("chat", {})
        if (
            sender.get("id") != Config.TG_ADMIN_ID
            or chat.get("id") != Config.TG_ADMIN_ID
        ):
            return
        text = (message.get("text") or "").strip()
        command = text.split(maxsplit=1)
        command = command[0].split("@", maxsplit=1)[0] if command else ""
        if command in {"/start", "/menu"}:
            pending.clear()
            await _show_menu(client)
        elif command == "/cancel":
            pending.clear()
            await _send_text(client, tr("admin_menu_cancelled"), _back_keyboard())
        elif pending.get("action") == "lot_id":
            if not text.isdecimal():
                await _send_text(client, tr("cli_lot_id_invalid"))
                return
            accounts = db.get_unlinked_accounts()
            if not accounts:
                pending.clear()
                await _send_text(
                    client, tr("admin_menu_link_no_accounts"), _back_keyboard()
                )
                return
            pending["action"] = "link_account"
            pending["lot_id"] = text
            await _send_text(
                client,
                tr("admin_menu_link_choose_account"),
                _account_keyboard(accounts, "link_account"),
            )
        elif pending.get("action") == "behavior_value":
            if not text.isdecimal() or int(text) > 12000:
                await _send_text(client, tr("admin_menu_behavior_invalid"))
                return
            account_id = pending["account_id"]
            pending.clear()
            try:
                db.update_behavior_score(account_id, int(text))
                synced = False
                if bot:
                    synced = await bot.sync_account_listing(account_id)
                await _send_text(
                    client,
                    tr(
                        "admin_menu_behavior_saved"
                        if synced
                        else "admin_menu_behavior_saved_pending"
                    ),
                    _back_keyboard(),
                )
            except (aiohttp.ClientError, exceptions.RequestFailedError,
                    exceptions.UnauthorizedError, exceptions.LotSavingError,
                    ValueError, sqlite3.Error) as exc:
                logger.error(
                    tr("admin_menu_operation_failed"), type(exc).__name__
                )
                await _send_text(
                    client, tr("admin_menu_operation_failed_text"), _back_keyboard()
                )
        elif pending.get("action") == "dota_id":
            if not text.isdecimal():
                await _send_text(client, tr("cli_add_dota_invalid"))
                return
            account_id = pending["account_id"]
            lot_id = pending["lot_id"]
            pending.clear()
            try:
                db.set_dota_account_id(account_id, text)
                linked_lot = await bot.register_listing(lot_id, account_id)
                await _send_text(
                    client,
                    tr(
                        "admin_menu_linked",
                        lot_id=linked_lot,
                        account_id=account_id,
                    ),
                    _back_keyboard(),
                )
            except (aiohttp.ClientError, exceptions.AccountNotInitiatedError,
                    exceptions.RequestFailedError, exceptions.UnauthorizedError,
                    exceptions.LotSavingError, ValueError, sqlite3.Error) as exc:
                logger.error(
                    tr("admin_menu_operation_failed"), type(exc).__name__
                )
                await _send_text(
                    client, tr("admin_menu_operation_failed_text"), _back_keyboard()
                )
        return

    callback = update.get("callback_query")
    if not callback:
        return
    sender = callback.get("from", {})
    message = callback.get("message", {})
    chat = message.get("chat", {})
    if (
        sender.get("id") != Config.TG_ADMIN_ID
        or chat.get("id") != Config.TG_ADMIN_ID
    ):
        return

    await _telegram_call(
        client,
        "answerCallbackQuery",
        {"callback_query_id": callback["id"]},
    )
    callback_data = callback.get("data", "")
    if not callback_data.startswith("admin:"):
        return
    section = callback_data.removeprefix("admin:")
    if section == "menu":
        pending.clear()
        await _show_menu(client)
    elif section.startswith("link_account:"):
        if pending.get("action") != "link_account" or not bot:
            await _send_text(client, tr("admin_menu_action_expired"), _back_keyboard())
            return
        try:
            account_id = int(section.split(":", maxsplit=1)[1])
            account = db.get_account_listing_data(account_id)
            if not account:
                raise ValueError("Account does not exist")
            if not account["dota_account_id"]:
                pending["action"] = "dota_id"
                pending["account_id"] = account_id
                await _send_text(
                    client,
                    tr("admin_menu_dota_enter", account_id=account_id),
                    _back_keyboard(),
                )
            else:
                lot_id = await bot.register_listing(pending["lot_id"], account_id)
                pending.clear()
                await _send_text(
                    client,
                    tr("admin_menu_linked", lot_id=lot_id, account_id=account_id),
                    _back_keyboard(),
                )
        except (aiohttp.ClientError, exceptions.AccountNotInitiatedError,
                exceptions.RequestFailedError, exceptions.UnauthorizedError,
                exceptions.LotSavingError, ValueError, sqlite3.Error) as exc:
            logger.error(tr("admin_menu_operation_failed"), type(exc).__name__)
            pending.clear()
            await _send_text(
                client, tr("admin_menu_operation_failed_text"), _back_keyboard()
            )
    elif section.startswith("behavior_account:"):
        try:
            account_id = int(section.split(":", maxsplit=1)[1])
            if not db.get_account_listing_data(account_id):
                raise ValueError("Account does not exist")
            pending["action"] = "behavior_value"
            pending["account_id"] = account_id
            await _send_text(
                client,
                tr("admin_menu_behavior_enter", account_id=account_id),
                _back_keyboard(),
            )
        except (ValueError, sqlite3.Error):
            await _send_text(
                client, tr("admin_menu_operation_failed_text"), _back_keyboard()
            )
    elif section == "sync_listings":
        if not bot:
            await _send_text(
                client, tr("admin_menu_funpay_unavailable"), _back_keyboard()
            )
            return
        try:
            updated = await bot.sync_all_listings()
            await _send_text(
                client, tr("admin_menu_sync_done", updated=updated), _back_keyboard()
            )
        except ValueError:
            await _send_text(
                client, tr("admin_menu_funpay_unavailable"), _back_keyboard()
            )
    else:
        await _show_section(client, db, section, pending)


async def admin_menu_loop(db: Database, bot=None) -> None:
    """Poll Telegram updates and respond only to the configured admin in private chat."""
    if not Config.TG_BOT_TOKEN or not Config.TG_ADMIN_ID:
        logger.info(tr("admin_menu_not_configured"))
        return

    offset = None
    pending: dict[str, Any] = {}
    async with httpx.AsyncClient(timeout=POLL_TIMEOUT + 10) as client:
        while True:
            try:
                payload: dict[str, Any] = {
                    "timeout": POLL_TIMEOUT,
                    "allowed_updates": ["message", "callback_query"],
                }
                if offset is not None:
                    payload["offset"] = offset
                updates = await _telegram_call(client, "getUpdates", payload)
                for update in updates:
                    offset = update["update_id"] + 1
                    try:
                        await _handle_update(client, db, update, bot, pending)
                    except (
                        httpx.HTTPError, RuntimeError, KeyError, TypeError,
                        sqlite3.Error,
                    ) as exc:
                        logger.error(
                            tr("admin_menu_poll_failed"), type(exc).__name__
                        )
                        db.log(
                            "admin_menu_update_failed",
                            details={"error_type": type(exc).__name__},
                            severity="error",
                        )
            except asyncio.CancelledError:
                raise
            except (
                httpx.HTTPError, RuntimeError, KeyError, TypeError, ValueError,
                sqlite3.Error,
            ) as exc:
                if isinstance(exc, RuntimeError):
                    logger.error(tr("admin_menu_poll_conflict"))
                logger.error(tr("admin_menu_poll_failed"), type(exc).__name__)
                db.log(
                    "admin_menu_poll_failed",
                    details={"error_type": type(exc).__name__},
                    severity="error",
                )
                await asyncio.sleep(5)
