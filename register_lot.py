"""Bind an already-created FunPay listing to one inventory account."""

import sqlite3

from database import Database
from i18n import tr


def main():
    db = None
    try:
        db = Database()
        lot_id = input(tr("cli_lot_id")).strip()
        title = input(tr("cli_lot_title")).strip()
        price_text = input(tr("cli_lot_price")).strip()
        account_text = input(tr("cli_lot_account")).strip()

        try:
            price = float(price_text)
            account_id = int(account_text)
        except ValueError as exc:
            raise ValueError(tr("cli_lot_invalid")) from exc

        db.register_lot(lot_id, title, price, account_id)
        print(tr("cli_lot_success"))
    except (ValueError, sqlite3.IntegrityError) as exc:
        print(tr("cli_lot_failed", error=exc))
    finally:
        if db is not None:
            db.close()


if __name__ == "__main__":
    main()
