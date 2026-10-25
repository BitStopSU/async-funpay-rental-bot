"""Generate a truthful listing preview without publishing or accessing accounts."""

import math
import sqlite3

from database import Database
from i18n import tr


def build_listing_text(account, hourly_price: float) -> tuple[str, str]:
    if account["mmr"] is None:
        raise ValueError(tr("cli_preview_mmr_required"))
    mmr = str(account["mmr"])
    behavior = (
        str(account["behavior_score"])
        if account["behavior_score"] is not None
        else tr("listing_behavior_unknown")
    )
    title = tr("listing_title_template", mmr=mmr, behavior=behavior)
    description = tr(
        "listing_description_template",
        mmr=mmr,
        behavior=behavior,
        price=f"{hourly_price:g}",
    )
    return title, description


def main():
    db = None
    try:
        db = Database()
        account_id = int(input(tr("cli_preview_account")).strip())
        price = float(input(tr("cli_preview_price")).strip().replace(",", "."))
        if not math.isfinite(price) or price <= 0:
            raise ValueError(tr("cli_lot_invalid"))
        account = db.get_account_listing_data(account_id)
        if (
            not account
            or account["status"] != "free"
            or account["vac_banned"]
        ):
            raise ValueError(tr("cli_preview_missing"))

        title, description = build_listing_text(account, price)
        print(f"\n{tr('cli_preview_title')}\n{title}\n")
        print(f"{tr('cli_preview_description')}\n{description}")
        print(f"\n{tr('cli_preview_publish_warning')}")
        db.log(
            "listing_preview_generated",
            account_id=account_id,
            details={
                "mmr": account["mmr"],
                "behavior_score": account["behavior_score"],
                "hourly_price": price,
            },
        )
    except (ValueError, sqlite3.Error) as exc:
        print(tr("cli_preview_failed", error=exc))
    finally:
        if db is not None:
            db.close()


if __name__ == "__main__":
    main()
