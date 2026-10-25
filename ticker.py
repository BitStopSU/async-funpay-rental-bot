import asyncio
import logging

from config import Config
from database import Database
from i18n import tr

logger = logging.getLogger(__name__)


async def expiry_ticker(db: Database):
    while True:
        try:
            for rental in db.get_expired_rentals():
                released = db.release_expired_rental(rental["order_id"])
                if not released:
                    continue
                account_id = released["account_id"]
                db.log(
                    "account_released", account_id=account_id,
                    order_id=rental["order_id"],
                )
                if released["auto_change_password"]:
                    db.queue_notification(
                        tr("notify_password_manual", account_id=account_id),
                        severity="warning",
                    )
        except Exception as exc:
            logger.error(tr("ticker_failed"), type(exc).__name__)
            db.log("expiry_ticker_failed", severity="error")
        await asyncio.sleep(Config.TICKER_INTERVAL)
