import asyncio
import logging

from admin_menu import admin_menu_loop
from config import Config
from daily_checks import daily_checks
from database import Database
from funpay_bot import RentalBot
from notify import digest_loop
from password_worker import password_worker


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    db = Database()
    bot = RentalBot(Config.GOLDEN_KEY, db)
    workers = [
        asyncio.create_task(daily_checks(db), name="daily-account-checks"),
        asyncio.create_task(password_worker(db), name="manual-password-tasks"),
        asyncio.create_task(digest_loop(db), name="notification-digest"),
        asyncio.create_task(admin_menu_loop(db), name="telegram-admin-menu"),
    ]
    try:
        await bot.start()
    finally:
        for worker in workers:
            worker.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
