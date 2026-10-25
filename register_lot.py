"""Link an existing FunPay listing to an unlinked inventory account."""

import asyncio
import sqlite3

import aiohttp
from aioFunPayAPI.common import exceptions

from database import Database
from i18n import tr
from listing_sync import (
    extract_lot_metadata,
    fetch_funpay_lot,
    normalize_funpay_lot_id,
    sync_listing,
)


async def main():
    db = None
    try:
        db = Database()
        lot_id = normalize_funpay_lot_id(input(tr("cli_lot_id")).strip())
        if db.get_lot(lot_id):
            raise ValueError(tr("cli_lot_already_registered"))
        accounts = db.get_unlinked_accounts()
        if not accounts:
            print(tr("cli_lot_accounts_empty"))
            return

        print(tr("cli_lot_accounts_header"))
        for account in accounts:
            mmr = account["mmr"] if account["mmr"] is not None else "—"
            behavior = (
                account["behavior_score"]
                if account["behavior_score"] is not None
                else "—"
            )
            dota_id = account["dota_account_id"] or "—"
            print(f"{account['account_id']} / {dota_id} / {mmr} / {behavior}")

        account_id = int(input(tr("cli_lot_account_choice")).strip())
        if account_id not in {account["account_id"] for account in accounts}:
            raise ValueError(tr("cli_lot_accounts_empty"))
        selected = next(account for account in accounts if account["account_id"] == account_id)
        if not selected["dota_account_id"]:
            dota_id = input(tr("cli_add_dota_id")).strip()
            if not dota_id:
                raise ValueError(tr("cli_add_dota_required"))
            if not dota_id.isdecimal():
                raise ValueError(tr("cli_add_dota_invalid"))
            db.set_dota_account_id(account_id, dota_id)

        funpay_account, lot_fields = await fetch_funpay_lot(lot_id)
        title_ru, title_en, price = extract_lot_metadata(lot_fields)
        db.register_lot(
            lot_id, title_ru, price, account_id, title_en=title_en
        )
        try:
            await sync_listing(
                db, funpay_account, lot_id, account_id, lot_fields=lot_fields
            )
        except (aiohttp.ClientError, exceptions.RequestFailedError,
                exceptions.UnauthorizedError, exceptions.LotSavingError):
            db.log(
                "listing_sync_failed",
                account_id=account_id,
                details={"lot_id": lot_id},
                severity="error",
            )
            print(tr("listing_sync_failed", lot_id=lot_id))
            return
        print(tr("cli_lot_link_success", lot_id=lot_id, account_id=account_id))
        print(tr("cli_listing_sync_enabled"))
    except (ValueError, sqlite3.Error) as exc:
        print(tr("cli_lot_failed", error=exc))
    except (aiohttp.ClientError, exceptions.AccountNotInitiatedError,
            exceptions.RequestFailedError, exceptions.UnauthorizedError,
            exceptions.LotSavingError):
        print(tr("cli_lot_fetch_failed"))
    finally:
        if db is not None:
            db.close()


if __name__ == "__main__":
    asyncio.run(main())
