import asyncio
import logging

import httpx

from config import Config
from database import Database
from i18n import tr

logger = logging.getLogger(__name__)
STEAM_BANS_URL = "https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/"
OPENDOTA_PLAYER_URL = "https://api.opendota.com/api/players/{}"


async def run_daily_checks(db: Database, client: httpx.AsyncClient | None = None):
    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=20)
    try:
        accounts = db.conn.execute(
            """SELECT account_id, steamid64, dota_account_id
               FROM accounts WHERE vac_banned = 0"""
        ).fetchall()
        await _check_vac_bans(db, client, accounts)
        await _check_mmr(db, client, accounts)
    finally:
        if owns_client:
            await client.aclose()


async def _check_vac_bans(db: Database, client: httpx.AsyncClient, accounts):
    steamids = [row["steamid64"] for row in accounts if row["steamid64"]]
    if not steamids:
        return
    if not Config.STEAM_API_KEY:
        db.log("vac_check_skipped", details={"reason": "STEAM_API_KEY is unset"},
               severity="warning")
        db.queue_notification(tr("notify_vac_disabled"))
        return

    for offset in range(0, len(steamids), 100):
        try:
            response = await client.get(
                STEAM_BANS_URL,
                params={
                    "key": Config.STEAM_API_KEY,
                    "steamids": ",".join(steamids[offset:offset + 100]),
                },
            )
            response.raise_for_status()
            players = response.json().get("players")
            if not isinstance(players, list):
                raise ValueError(tr("steam_response_invalid"))
            for player in players:
                if player.get("VACBanned") and player.get("SteamId"):
                    count = db.mark_vac_banned(player["SteamId"])
                    if count:
                        db.queue_notification(
                            tr("notify_vac_banned", steam_id=player["SteamId"]),
                            severity="critical",
                        )
        except (httpx.HTTPError, ValueError, TypeError, AttributeError) as exc:
            logger.error(tr("daily_vac_failed"), type(exc).__name__)
            db.log("vac_check_failed", severity="warning")
            db.queue_notification(tr("notify_vac_failed"))


async def _check_mmr(db: Database, client: httpx.AsyncClient, accounts):
    for account in accounts:
        account_id = account["account_id"]
        dota_id = account["dota_account_id"]
        if not dota_id:
            continue
        try:
            response = await client.get(OPENDOTA_PLAYER_URL.format(dota_id))
            response.raise_for_status()
            payload = response.json()
            estimate = payload.get("mmr_estimate") or {}
            mmr = estimate.get("estimate")
            db.update_mmr(account_id, int(mmr) if mmr is not None else None)
        except (httpx.HTTPError, ValueError, TypeError, AttributeError) as exc:
            logger.error(
                tr("daily_mmr_failed"), account_id, type(exc).__name__,
            )
            db.log(
                "mmr_check_failed", account_id=account_id,
                details={"provider": "OpenDota"}, severity="warning",
            )
            db.queue_notification(
                tr("notify_mmr_failed", account_id=account_id)
            )
        await asyncio.sleep(max(0, Config.OPENDOTA_REQUEST_DELAY))


async def daily_checks(db: Database):
    while True:
        try:
            await run_daily_checks(db)
        except Exception as exc:
            logger.error(tr("daily_checks_failed"), type(exc).__name__)
            db.log("daily_checks_failed", severity="error")
        await asyncio.sleep(Config.DAILY_CHECK_INTERVAL)
