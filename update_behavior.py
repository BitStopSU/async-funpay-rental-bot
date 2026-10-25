"""Update a manually verified behavior score and synchronize its listing."""

import asyncio
import sqlite3

import aiohttp
from aioFunPayAPI.common import exceptions

from database import Database
from i18n import tr
from listing_sync import fetch_funpay_lot, sync_listing


async def main():
    db = None
    lot = None
    try:
        db = Database()
        accounts = db.conn.execute(
            """SELECT account_id, mmr, behavior_score
               FROM accounts ORDER BY account_id"""
        ).fetchall()
        for account in accounts:
            mmr = account["mmr"] if account["mmr"] is not None else "—"
            behavior = (
                account["behavior_score"]
                if account["behavior_score"] is not None
                else "—"
            )
            print(f"{account['account_id']} / {mmr} / {behavior}")

        account_id = int(input(tr("cli_behavior_account")).strip())
        score_text = input(tr("cli_behavior_value")).strip()
        if not score_text.isdecimal():
            raise ValueError(tr("cli_behavior_invalid"))
        db.update_behavior_score(account_id, int(score_text))

        lot = db.get_lot_by_account_id(account_id)
        if lot:
            account_data = db.get_account_listing_data(account_id)
            if account_data["mmr"] is None:
                print(tr("cli_behavior_updated"))
                print(tr("cli_behavior_waiting_mmr"))
                return
            if not account_data["vac_banned"]:
                account, lot_fields = await fetch_funpay_lot(lot["lot_id"])
                await sync_listing(
                    db,
                    account,
                    lot["lot_id"],
                    account_id,
                    lot_fields=lot_fields,
                )
                print(tr("cli_behavior_listing_updated"))
        print(tr("cli_behavior_updated"))
    except (ValueError, sqlite3.Error) as exc:
        print(tr("cli_listing_sync_failed", error=exc))
    except (
        aiohttp.ClientError,
        exceptions.AccountNotInitiatedError,
        exceptions.RequestFailedError,
        exceptions.UnauthorizedError,
        exceptions.LotSavingError,
    ):
        lot_id = lot["lot_id"] if lot else "—"
        print(tr("cli_behavior_update_failed", lot_id=lot_id))
    finally:
        if db is not None:
            db.close()


if __name__ == "__main__":
    asyncio.run(main())
