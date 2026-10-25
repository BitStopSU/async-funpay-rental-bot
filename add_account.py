"""Add an account to the encrypted local inventory."""

import getpass
import sqlite3

from database import Database
from i18n import tr


def main():
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
        mmr_text = input(tr("cli_add_mmr")).strip()
        behavior_text = input(tr("cli_add_behavior")).strip()
        if mmr_text and (not mmr_text.isdecimal()):
            raise ValueError(tr("cli_add_mmr_invalid"))
        if behavior_text and (not behavior_text.isdecimal()):
            raise ValueError(tr("cli_add_behavior_invalid"))
        mmr = int(mmr_text) if mmr_text else None
        behavior_score = int(behavior_text) if behavior_text else None

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
        print(tr("cli_add_next"))
    except (ValueError, sqlite3.IntegrityError) as exc:
        print(tr("cli_add_failed", error=exc))
    finally:
        if db is not None:
            db.close()


if __name__ == "__main__":
    main()
