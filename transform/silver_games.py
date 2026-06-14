"""
transform/silver_games.py

Reads raw Steam Store JSON and transforms into a clean Silver table.

Raw  → messy JSON, lists, nulls, inconsistent types
Silver → one row per game, clean types, flat structure, ready for analysis

Output: silver/games.csv
"""

import json
import csv
import os
import glob
from datetime import datetime

RAW_DIR = "raw"
SILVER_DIR = "silver"


def load_latest_raw(prefix: str) -> list[dict]:
    """Load the most recent raw JSON file matching a prefix."""
    pattern = os.path.join(RAW_DIR, f"{prefix}_*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No raw files found matching: {pattern}")
    latest = files[-1]
    print(f"Loading: {latest}")
    with open(latest, "r", encoding="utf-8") as f:
        return json.load(f)


def clean_age(value) -> int | None:
    """required_age comes as int or string — normalize to int."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def cents_to_dollars(value) -> float | None:
    """Convert price from cents (2999) to dollars (29.99)."""
    if value is None:
        return None
    try:
        return round(int(value) / 100, 2)
    except (TypeError, ValueError):
        return None


def flatten_list(values: list, separator: str = " | ") -> str:
    """Turn ['Action', 'RPG'] into 'Action | RPG'."""
    if not values:
        return ""
    return separator.join(str(v) for v in values)


def parse_release_year(date_str: str | None) -> int | None:
    """Extract year from date strings like 'Aug 21, 2012' or 'Nov 4, 2020'."""
    if not date_str:
        return None
    for fmt in ("%b %d, %Y", "%b %Y"):
        try:
            return datetime.strptime(date_str, fmt).year
        except ValueError:
            continue
    return None


def transform_game(raw: dict) -> dict:
    """Transform one raw game record into a clean Silver row."""
    price_initial = cents_to_dollars(raw.get("price_initial"))
    price_final = cents_to_dollars(raw.get("price_final"))

    return {
        "appid":             raw.get("appid"),
        "name":              raw.get("name", "").strip(),
        "type":              raw.get("type", ""),
        "is_free":           1 if raw.get("is_free") else 0,
        "developer":         flatten_list(raw.get("developers", [])),
        "publisher":         flatten_list(raw.get("publishers", [])),
        "genres":            flatten_list(raw.get("genres", [])),
        "on_windows":        1 if raw.get("platforms", {}).get("windows") else 0,
        "on_mac":            1 if raw.get("platforms", {}).get("mac") else 0,
        "on_linux":          1 if raw.get("platforms", {}).get("linux") else 0,
        "release_date":      raw.get("release_date"),
        "release_year":      parse_release_year(raw.get("release_date")),
        "metacritic_score":  raw.get("metacritic_score"),
        "price_usd":         price_final if price_final is not None else price_initial,
        "price_original_usd": price_initial,
        "discount_percent":  raw.get("discount_percent"),
        "required_age":      clean_age(raw.get("required_age")),
        "short_description": raw.get("short_description", "").strip(),
    }


def run():
    os.makedirs(SILVER_DIR, exist_ok=True)

    # Load raw data
    raw_games = load_latest_raw("steam_store_metadata")
    print(f"Raw records loaded: {len(raw_games)}")

    # Transform
    silver_games = [transform_game(g) for g in raw_games if g.get("name")]
    print(f"Silver records after cleaning: {len(silver_games)}")

    # Write CSV
    output_path = os.path.join(SILVER_DIR, "games.csv")
    if silver_games:
        fieldnames = list(silver_games[0].keys())
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(silver_games)

    print(f"Silver table saved: {output_path}")
    print(f"Columns: {fieldnames}")

    # Quick preview
    print("\nSample rows:")
    for g in silver_games[:3]:
        print(f"  [{g['appid']}] {g['name']} | {g['genres']} | free={g['is_free']} | price=${g['price_usd']} | year={g['release_year']}")

    return silver_games


if __name__ == "__main__":
    run()
