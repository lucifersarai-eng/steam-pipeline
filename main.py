"""
main.py

Orchestrates the full Steam ingestion pipeline:
  1. Fetch top 100 games from Steam Spy
  2. Extract appids
  3. Fetch metadata for each game from Steam Store API
  4. Save all raw data for downstream transformation

Run:
    python main.py
"""

from ingestion.steam_spy import fetch_top_games, save_raw
from ingestion.steam_store import fetch_batch
from utils.helpers import logger


def run():
    logger.info("=== Steam Pipeline Starting ===")

    # Step 1: Get top games from Steam Spy
    logger.info("Step 1: Fetching top games from Steam Spy...")
    games = fetch_top_games("top100in2weeks")
    if not games:
        logger.error("No games fetched from Steam Spy. Aborting.")
        return
    save_raw(games, name="steamspy_top100")

    # Step 2: Extract appids
    appids = [g["appid"] for g in games]
    logger.info(f"Step 2: Extracted {len(appids)} appids.")

    # Step 3: Fetch Steam Store metadata for each game
    logger.info("Step 3: Fetching Steam Store metadata...")
    metadata = fetch_batch(appids)
    save_raw(metadata, name="steam_store_metadata")

    logger.info(f"=== Pipeline complete. {len(metadata)} games ingested. ===")


if __name__ == "__main__":
    run()
