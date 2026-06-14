"""
ingestion/steam_spy.py

Fetches top games from Steam Spy API.
Steam Spy provides estimated player counts, owners, reviews, and playtime.
No API key required — free and public.

Docs: https://steamspy.com/api.php
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.helpers import get_with_retry, save_raw, throttle, logger

STEAMSPY_BASE = "https://steamspy.com/api.php"


def fetch_top_games(request_type: str = "top100in2weeks") -> list[dict]:
    """
    Fetch top games from Steam Spy.

    request_type options:
      - "top100in2weeks"  → top 100 by players in last 2 weeks (most relevant)
      - "top100forever"   → top 100 by all-time players
      - "top100owned"     → top 100 by number of owners
    
    Returns a list of game dicts with appid, name, players, owners, etc.
    """
    logger.info(f"Fetching Steam Spy: {request_type}")

    params = {"request": request_type}
    data = get_with_retry(STEAMSPY_BASE, params=params)

    if not data:
        logger.error("Failed to fetch Steam Spy top games.")
        return []

    # Steam Spy returns a dict keyed by appid — convert to list
    games = []
    for appid, info in data.items():
        games.append({
            "appid": int(appid),
            "name": info.get("name"),
            "developer": info.get("developer"),
            "publisher": info.get("publisher"),
            "owners": info.get("owners"),           # e.g. "2,000,000 .. 5,000,000"
            "players_forever": info.get("players_forever"),
            "players_2weeks": info.get("players_2weeks"),
            "average_forever": info.get("average_forever"),   # avg playtime in minutes
            "average_2weeks": info.get("average_2weeks"),
            "positive": info.get("positive"),
            "negative": info.get("negative"),
            "price": info.get("price"),             # in cents (USD)
            "initialprice": info.get("initialprice"),
        })

    logger.info(f"Fetched {len(games)} games from Steam Spy.")
    return games


def fetch_game_detail(appid: int) -> dict | None:
    """
    Fetch detailed Steam Spy data for a single game by appid.
    Useful for enriching a specific game beyond top-100 lists.
    """
    logger.info(f"Fetching Steam Spy detail for appid {appid}")
    throttle(1.5)  # Steam Spy rate limit: ~1 req/sec

    params = {"request": "appdetails", "appid": appid}
    data = get_with_retry(STEAMSPY_BASE, params=params)

    if not data:
        logger.warning(f"No Steam Spy data for appid {appid}")
        return None

    return {
        "appid": appid,
        "name": data.get("name"),
        "developer": data.get("developer"),
        "publisher": data.get("publisher"),
        "owners": data.get("owners"),
        "players_forever": data.get("players_forever"),
        "players_2weeks": data.get("players_2weeks"),
        "average_forever": data.get("average_forever"),
        "average_2weeks": data.get("average_2weeks"),
        "positive": data.get("positive"),
        "negative": data.get("negative"),
        "price": data.get("price"),
        "tags": data.get("tags", {}),   # dict of {tag: vote_count}
        "genre": data.get("genre"),
        "languages": data.get("languages"),
    }


def run():
    """Main ingestion entry point for Steam Spy."""
    games = fetch_top_games("top100in2weeks")

    if not games:
        logger.error("No games fetched. Aborting.")
        return

    # Save raw
    save_raw(games, name="steamspy_top100")

    # Preview
    logger.info("Sample records:")
    for g in games[:3]:
        logger.info(f"  [{g['appid']}] {g['name']} — players_2w: {g['players_2weeks']}, price: {g['price']}")

    return games


if __name__ == "__main__":
    run()
