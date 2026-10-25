import os
from dotenv import load_dotenv

load_dotenv()


def _optional_int(name: str, default: int = 0) -> int:
    value = os.getenv(name)
    return int(value) if value else default


class Config:
    # FunPay
    GOLDEN_KEY = os.getenv("FUNPAY_GOLDEN_KEY")

    # Telegram для алертов
    TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
    TG_ADMIN_ID = _optional_int("TG_ADMIN_ID")

    # База
    DB_PATH = os.getenv("DB_PATH", "rental.db")

    # Публичные проверки
    STEAM_API_KEY = os.getenv("STEAM_API_KEY")
    OPENDOTA_REQUEST_DELAY = float(os.getenv("OPENDOTA_REQUEST_DELAY", "1"))
    # Язык сообщений покупателям и администратору: ru или en.
    BOT_LANGUAGE = os.getenv("BOT_LANGUAGE", "ru").strip().lower()

    # Бизнес-логика
    BUFFER_MINUTES = 30
    TICKER_INTERVAL = 30
    DAILY_CHECK_INTERVAL = 24 * 60 * 60
    NOTIFICATION_DIGEST_INTERVAL = 60 * 60
    PASSWORD_WORKER_INTERVAL = 5