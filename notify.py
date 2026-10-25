import asyncio
import logging

import httpx

from config import Config
from database import Database
from i18n import tr, severity_label

logger = logging.getLogger(__name__)


async def send_tg(text: str):
    if not Config.TG_BOT_TOKEN or not Config.TG_ADMIN_ID:
        raise RuntimeError(tr("telegram_credentials_missing"))
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            f"https://api.telegram.org/bot{Config.TG_BOT_TOKEN}/sendMessage",
            json={"chat_id": Config.TG_ADMIN_ID, "text": text[:4000]},
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            raise RuntimeError(tr("telegram_rejected"))


async def critical(text: str):
    await send_tg(f"🚨 {text}")


async def digest_loop(db: Database):
    while True:
        await asyncio.sleep(Config.NOTIFICATION_DIGEST_INTERVAL)
        rows = db.get_pending_notifications()
        if not rows:
            continue
        title_key = (
            "digest_critical_title"
            if any(row["severity"] == "critical" for row in rows)
            else "digest_warning_title"
        )
        summary = tr(title_key) + "\n" + "\n".join(
            f"[{severity_label(row['severity'])}] {row['text']}" for row in rows
        )
        try:
            await send_tg(summary)
        except Exception as exc:
            logger.error(tr("telegram_digest_failed"), type(exc).__name__)
            db.log("notification_digest_failed", severity="error")
            continue
        db.mark_notifications_sent([row["notification_id"] for row in rows])
        db.log(
            "notification_digest_sent",
            details={"notification_ids": [row["notification_id"] for row in rows]},
        )