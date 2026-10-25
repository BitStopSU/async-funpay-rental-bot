import math

from config import Config
from database import Database
from funpay_session import FunPayAccount
from i18n import tr
from prepare_listing import build_listing_text


def _validated_lot_id(lot_id: str) -> int:
    value = str(lot_id).strip()
    if not value.isdecimal():
        raise ValueError(tr("cli_lot_id_invalid"))
    return int(value)


def extract_lot_metadata(lot_fields):
    title_ru = (lot_fields.title_ru or "").strip()
    title_en = (lot_fields.title_en or "").strip()
    price = lot_fields.price
    if not title_ru and not title_en:
        raise ValueError(tr("cli_lot_fetch_failed"))
    if price is None or not math.isfinite(price) or price <= 0:
        raise ValueError(tr("cli_lot_fetch_failed"))
    return title_ru or title_en, title_en or title_ru, price


async def fetch_funpay_lot(lot_id: str):
    validated_lot_id = _validated_lot_id(lot_id)
    if not Config.GOLDEN_KEY:
        raise ValueError(tr("funpay_key_missing"))
    account = await FunPayAccount(golden_key=Config.GOLDEN_KEY).get(
        update_phpsessid=True
    )
    lot_fields = await account.get_lot_fields(validated_lot_id)
    extract_lot_metadata(lot_fields)
    return account, lot_fields


async def sync_listing(
    db: Database,
    account: FunPayAccount,
    lot_id: str,
    account_id: int,
    lot_fields=None,
) -> bool:
    lot = db.get_lot(lot_id)
    account_data = db.get_account_listing_data(account_id)
    if not lot or not account_data:
        raise ValueError(tr("cli_lot_fetch_failed"))
    if account_data["mmr"] is None:
        db.log(
            "listing_sync_skipped_no_mmr",
            account_id=account_id,
            details={"lot_id": str(lot_id)},
            severity="warning",
        )
        return False

    if lot_fields is None:
        lot_fields = await account.get_lot_fields(_validated_lot_id(lot_id))

    title_ru, description_ru = build_listing_text(
        account_data, lot["price_per_hour"], language="ru"
    )
    title_en, description_en = build_listing_text(
        account_data, lot["price_per_hour"], language="en"
    )
    fields = {
        "fields[summary][ru]": title_ru,
        "fields[summary][en]": title_en,
        "fields[desc][ru]": description_ru,
        "fields[desc][en]": description_en,
    }
    current = lot_fields.fields
    if all(current.get(key, "") == value for key, value in fields.items()):
        if lot["title"] != title_ru or lot["title_en"] != title_en:
            db.update_lot_titles(lot_id, title_ru, title_en)
        return False

    lot_fields.edit_fields(fields)
    await account.save_lot(lot_fields)
    db.update_lot_titles(lot_id, title_ru, title_en)
    db.log(
        "listing_content_updated",
        account_id=account_id,
        details={"lot_id": str(lot_id)},
    )
    return True
