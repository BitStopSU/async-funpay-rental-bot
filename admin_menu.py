"""Telegram administrator menu for read-only rental management."""

import asyncio
import logging
import sqlite3
from typing import Any

import httpx

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
    client: httpx.AsyncClient, db: Database, section: str
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
    elif section == "settings":
        text = _settings_text()
    else:
        await _show_menu(client)
        return
    await _send_text(client, text, _back_keyboard())


async def _show_menu(client: httpx.AsyncClient) -> None:
    await _send_text(
        client,
        f"{tr('admin_menu_title')}\n{tr('admin_menu_open')}",
        _main_keyboard(),
    )


async def _handle_update(
    client: httpx.AsyncClient, db: Database, update: dict[str, Any]
) -> None:
    message = update.get("message")
    if message:
        sender = message.get("from", {})
        chat = message.get("chat", {})
        command = (message.get("text") or "").split(maxsplit=1)
        command = command[0].split("@", maxsplit=1)[0] if command else ""
        if (
            sender.get("id") == Config.TG_ADMIN_ID
            and chat.get("id") == Config.TG_ADMIN_ID
            and command in {"/start", "/menu"}
        ):
            await _show_menu(client)
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
        await _show_menu(client)
    else:
        await _show_section(client, db, section)


async def admin_menu_loop(db: Database) -> None:
    """Poll Telegram updates and respond only to the configured admin in private chat."""
    if not Config.TG_BOT_TOKEN or not Config.TG_ADMIN_ID:
        logger.info(tr("admin_menu_not_configured"))
        return

    offset = None
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
                        await _handle_update(client, db, update)
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
