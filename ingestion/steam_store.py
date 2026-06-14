"""
ingestion/steam_store.py

Fetches game metadata from the Steam Store API.
No API key required — free and public.

Docs: https://store.steampowered.com/api/appdetails
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.helpers import get_with_retry, save_raw, throttle, logger

STEAM_STORE_BASE = "https://store.steampowered.com/api/appdetails"


def fetch_game_metadata(appid: int) -> dict | None:
    """
    Fetch full metadata for a single game from the Steam Store API.

    Returns structured metadata including:
    - name, type, description
    - genres, categories, tags
    - release date
    - platforms (win/mac/linux)
    - price (current + original)
    - metacritic score
    - developers, publishers
    """
    throttle(1.5)  # Steam Store rate limit: ~200 req/5min

    params = {"appids": appid, "cc": "us", "l": "en"}
    data = get_with_retry(STEAM_STORE_BASE, params=params)

    if not data:
        logger.warning(f"No response for appid {appid}")
        return None

    app_data = data.get(str(appid), {})
    if not app_data.get("success"):
        logger.warning(f"Steam Store returned success=false for appid {appid}")
        return None

    info = app_data.get("data", {})

    return {
        "appid": appid,
        "name": info.get("name"),
        "type": info.get("type"),                       # "game", "dlc", "demo", etc.
        "is_free": info.get("is_free"),
        "short_description": info.get("short_description"),
        "developers": info.get("developers", []),
        "publishers": info.get("publishers", []),
        "platforms": info.get("platforms", {}),         # {windows: bool, mac: bool, linux: bool}
        "genres": [g["description"] for g in info.get("genres", [])],
        "categories": [c["description"] for c in info.get("categories", [])],
        "release_date": info.get("release_date", {}).get("date"),
        "coming_soon": info.get("release_date", {}).get("coming_soon"),
        "metacritic_score": info.get("metacritic", {}).get("score"),
        "price_currency": info.get("price_overview", {}).get("currency"),
        "price_initial": info.get("price_overview", {}).get("initial"),     # in cents
        "price_final": info.get("price_overview", {}).get("final"),
        "discount_percent": info.get("price_overview", {}).get("discount_percent"),
        "required_age": info.get("required_age"),
        "header_image": info.get("header_image"),
    }


def fetch_batch(appids: list[int]) -> list[dict]:
    """
    Fetch metadata for a list of appids.
    Throttles between each call to respect rate limits.
    """
    results = []
    total = len(appids)

    for i, appid in enumerate(appids, 1):
        logger.info(f"Fetching metadata [{i}/{total}] appid={appid}")
        metadata = fetch_game_metadata(appid)
        if metadata:
            results.append(metadata)
        else:
            logger.warning(f"Skipping appid {appid} — no data returned")

    logger.info(f"Fetched metadata for {len(results)}/{total} games.")
    return results


def run(appids: list[int]):
    """Main entry point — fetch and save metadata for a list of appids."""
    if not appids:
        logger.error("No appids provided.")
        return []

    results = fetch_batch(appids)
    save_raw(results, name="steam_store_metadata")
    return results


if __name__ == "__main__":
    # Quick test with a few well-known games
    test_appids = [
        730,    # CS2
        570,    # Dota 2
        1091500 # Cyberpunk 2077
    ]
    run(test_appids)
