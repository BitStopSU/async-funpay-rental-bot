import asyncio
import logging

from config import Config
from database import Database
from i18n import tr
from notify import send_tg

logger = logging.getLogger(__name__)


async def password_worker(db: Database):
    """Notify an administrator about manual tasks; never access credentials."""
    while True:
        task = db.get_next_password_task()
        if task:
            message = tr(
                "telegram_password_task",
                account_id=task["account_id"],
                task_id=task["task_id"],
            )
            try:
                await send_tg(message)
            except Exception as exc:
                logger.error(
                    tr("telegram_password_task_failed"),
                    type(exc).__name__,
                )
                db.log(
                    "password_task_notification_failed",
                    account_id=task["account_id"],
                    details={"task_id": task["task_id"]},
                    severity="error",
                )
            else:
                db.mark_password_task_notified(task["task_id"], task["account_id"])
        await asyncio.sleep(Config.PASSWORD_WORKER_INTERVAL)
