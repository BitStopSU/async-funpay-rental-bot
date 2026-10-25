"""Best-effort public Dota profile verification."""

import asyncio
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from config import Config

OPENDOTA_PROFILE_URL = "https://api.opendota.com/api/players/{}"
DOTABUFF_PROFILE_URL = "https://www.dotabuff.com/players/{}"
STEAM_SUMMARIES_URL = (
    "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
)
STEAM_ID_BASE = 76561197960265728
FOUND = "found"
NOT_FOUND = "not_found"
UNKNOWN = "unknown"
NOT_CONFIGURED = "not_configured"


@dataclass(frozen=True)
class DotaProfileVerification:
    opendota: str
    dotabuff: str
    steamid64: str | None = None
    steam_visibility: str = NOT_CONFIGURED
    persona_name: str | None = None
    mmr_estimate: int | None = None
    rank_tier: int | None = None

    @property
    def verified_by(self) -> list[str]:
        return [
            source
            for source, result in (
                ("OpenDota", self.opendota),
                ("Dotabuff", self.dotabuff),
            )
            if result == FOUND
        ]


async def _check_opendota(client: httpx.AsyncClient, dota_id: str) -> str:
    try:
        response = await client.get(OPENDOTA_PROFILE_URL.format(dota_id))
        if response.status_code in {404, 410}:
            return NOT_FOUND
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            return UNKNOWN
        profile = payload.get("profile")
        if not isinstance(profile, dict):
            return NOT_FOUND
        profile_id = profile.get("account_id")
        if profile_id is None:
            return UNKNOWN
        return FOUND if str(profile_id) == dota_id else UNKNOWN
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        return UNKNOWN


async def _check_dotabuff(client: httpx.AsyncClient, dota_id: str) -> str:
    try:
        response = await client.get(DOTABUFF_PROFILE_URL.format(dota_id))
        if response.status_code in {404, 410}:
            return NOT_FOUND
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        canonical = soup.find("link", rel="canonical")
        open_graph = soup.find("meta", property="og:url")
        profile_url = (
            canonical.get("href")
            if canonical and canonical.get("href")
            else open_graph.get("content")
            if open_graph and open_graph.get("content")
            else ""
        )
        parsed = urlparse(profile_url)
        if (
            parsed.scheme == "https"
            and parsed.hostname in {"dotabuff.com", "www.dotabuff.com"}
            and parsed.path.rstrip("/") == f"/players/{dota_id}"
        ):
            return FOUND
        title = soup.title.get_text(" ", strip=True).casefold() if soup.title else ""
        if "player not found" in title or "not found" in title:
            return NOT_FOUND
        return UNKNOWN
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        return UNKNOWN


async def _check_steam_visibility(
    client: httpx.AsyncClient, steamid64: str, api_key: str | None
) -> tuple[str, str | None]:
    if not api_key:
        return NOT_CONFIGURED, None
    try:
        response = await client.get(
            STEAM_SUMMARIES_URL,
            params={"key": api_key, "steamids": steamid64},
        )
        response.raise_for_status()
        payload = response.json()
        players = payload.get("response", {}).get("players")
        if not isinstance(players, list):
            return UNKNOWN, None
        player = next(
            (
                item for item in players
                if isinstance(item, dict)
                and str(item.get("steamid")) == steamid64
            ),
            None,
        )
        if player is None:
            return UNKNOWN, None
        visibility = player.get("communityvisibilitystate")
        if (
            isinstance(visibility, str)
            and visibility.isdecimal()
        ):
            visibility = int(visibility)
        visibility_status = {
            1: "private",
            2: "friends_only",
            3: "public",
        }.get(visibility, UNKNOWN)
        return visibility_status, player.get("personaname")
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        return UNKNOWN, None


async def verify_dota_profile(
    dota_id: str, client: httpx.AsyncClient | None = None
) -> DotaProfileVerification:
    if not dota_id.isdecimal() or not 1 <= int(dota_id) <= 0xFFFFFFFF:
        raise ValueError("Dota account ID must be a positive 32-bit integer")

    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(
            timeout=8,
            follow_redirects=True,
            headers={"User-Agent": "async-funpay-rental-bot profile check"},
        )
    try:
        opendota_task = client.get(OPENDOTA_PROFILE_URL.format(dota_id))
        opendota_response, dotabuff_status = await asyncio.gather(
            opendota_task,
            _check_dotabuff(client, dota_id),
        )
        if opendota_response.status_code in {404, 410}:
            return DotaProfileVerification(NOT_FOUND, dotabuff_status)
        opendota_response.raise_for_status()
        payload = opendota_response.json()
        if not isinstance(payload, dict):
            return DotaProfileVerification(UNKNOWN, dotabuff_status)
        profile = payload.get("profile")
        if not isinstance(profile, dict):
            return DotaProfileVerification(NOT_FOUND, dotabuff_status)
        profile_id = profile.get("account_id")
        if profile_id is None or str(profile_id) != dota_id:
            return DotaProfileVerification(UNKNOWN, dotabuff_status)

        steamid64 = str(STEAM_ID_BASE + int(dota_id))
        opendota_steamid = profile.get("steamid")
        if opendota_steamid:
            normalized_steamid = str(opendota_steamid)
            if (
                not normalized_steamid.isdecimal()
                or len(normalized_steamid) != 17
                or normalized_steamid != steamid64
            ):
                return DotaProfileVerification(UNKNOWN, dotabuff_status)

        steam_visibility, persona_name = await _check_steam_visibility(
            client, steamid64, Config.STEAM_API_KEY
        )
        estimate = (payload.get("mmr_estimate") or {}).get("estimate")
        rank_tier = payload.get("rank_tier")
        if (
            isinstance(estimate, bool)
            or not isinstance(estimate, int)
            or not 0 <= estimate <= 15000
        ):
            estimate = None
        return DotaProfileVerification(
            FOUND,
            dotabuff_status,
            steamid64=steamid64,
            steam_visibility=steam_visibility,
            persona_name=persona_name,
            mmr_estimate=estimate if isinstance(estimate, int) else None,
            rank_tier=rank_tier if isinstance(rank_tier, int) else None,
        )
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        return DotaProfileVerification(UNKNOWN, UNKNOWN)
    finally:
        if owns_client:
            await client.aclose()
