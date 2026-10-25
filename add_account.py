"""Add an account to the encrypted local inventory."""

import asyncio
import getpass
import sqlite3

import aiohttp
from aioFunPayAPI.common import exceptions

from database import Database
from i18n import tr
from listing_sync import extract_lot_metadata, fetch_funpay_lot, sync_listing


async def main():
    db = None
    try:
        db = Database()
        confirmation = input(tr("cli_add_verified_prompt")).strip().casefold()
        if confirmation not in {"да", "yes"}:
            print(tr("cli_add_verification_required"))
            return
        login = input(tr("cli_add_login")).strip()
        password = getpass.getpass(tr("cli_add_password"))
        shared_secret = getpass.getpass(tr("cli_add_shared_secret"))
        steamid64 = input(tr("cli_add_steamid")).strip() or None
        dota_account_id = input(tr("cli_add_dota_id")).strip() or None
        if dota_account_id and not dota_account_id.isdecimal():
            raise ValueError(tr("cli_add_dota_invalid"))
        mmr_text = input(tr("cli_add_mmr")).strip()
        behavior_text = input(tr("cli_add_behavior")).strip()
        if mmr_text and (not mmr_text.isdecimal()):
            raise ValueError(tr("cli_add_mmr_invalid"))
        if behavior_text and (not behavior_text.isdecimal()):
            raise ValueError(tr("cli_add_behavior_invalid"))
        mmr = int(mmr_text) if mmr_text else None
        behavior_score = int(behavior_text) if behavior_text else None
        lot_id = input(tr("cli_add_lot_id")).strip()
        lot_context = None
        lot_metadata = None
        if lot_id:
            if db.get_lot(lot_id):
                raise ValueError(tr("cli_lot_already_registered"))
            if not dota_account_id:
                raise ValueError(tr("cli_add_dota_required"))
            lot_context = await fetch_funpay_lot(lot_id)
            lot_metadata = extract_lot_metadata(lot_context[1])

        account_id = db.add_account(
            login=login,
            password=password,
            shared_secret=shared_secret,
            steamid64=steamid64,
            dota_account_id=dota_account_id,
            mmr=mmr,
            behavior_score=behavior_score,
        )
        print(tr("cli_add_success", account_id=account_id))
        if lot_context and lot_metadata:
            lot_account, lot_fields = lot_context
            title_ru, title_en, price = lot_metadata
            db.register_lot(
                lot_id, title_ru, price, account_id, title_en=title_en
            )
            try:
                await sync_listing(
                    db, lot_account, lot_id, account_id, lot_fields=lot_fields
                )
                print(tr("cli_listing_sync_enabled"))
            except (aiohttp.ClientError, exceptions.RequestFailedError,
                    exceptions.UnauthorizedError, exceptions.LotSavingError):
                db.log(
                    "listing_sync_failed",
                    account_id=account_id,
                    details={"lot_id": lot_id},
                    severity="error",
                )
                print(tr("listing_sync_failed", lot_id=lot_id))
        else:
            print(tr("cli_add_next"))
    except (ValueError, sqlite3.IntegrityError) as exc:
        print(tr("cli_add_failed", error=exc))
    except (aiohttp.ClientError, exceptions.AccountNotInitiatedError,
            exceptions.RequestFailedError, exceptions.UnauthorizedError,
            exceptions.LotSavingError):
        print(tr("cli_lot_fetch_failed"))
    finally:
        if db is not None:
            db.close()


if __name__ == "__main__":
    asyncio.run(main())
