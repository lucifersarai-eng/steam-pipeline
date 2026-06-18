"""
gold/gold_comentions.py

Extracts game co-mentions from review texts.

For each review, scans the text for names of other games in our dataset.
Counts how many times each game pair co-occurs across all reviews.

Input:
  silver/games.csv    — game names (used as the search dictionary)
  silver/reviews.csv  — review texts to scan

Output:
  gold/comentions.csv — ranked list of (source_game, mentioned_game, mention_count)
"""

import csv
import os
from collections import defaultdict

SILVER_DIR = "silver"
GOLD_DIR = "gold"

MIN_NAME_LENGTH = 5  # ignore very short names like "War" or "Rust" to reduce false positives


def load_csv(filename: str) -> list[dict]:
    """Load a CSV file from the silver directory into a list of dicts."""
    path = os.path.join(SILVER_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(rows: list[dict], filename: str):
    """Write a list of dicts to a CSV file in the gold directory."""
    os.makedirs(GOLD_DIR, exist_ok=True)
    if not rows:
        print(f"No rows to write for {filename}")
        return
    path = os.path.join(GOLD_DIR, filename)
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Gold table saved: {path} ({len(rows)} rows)")


def build_name_index(games: list[dict]) -> dict[str, dict]:
    """
    Build a lookup of game names to their appid and full name.
    Only includes names longer than MIN_NAME_LENGTH to avoid false positives.

    Returns: {lowercase_name: {"appid": ..., "name": ...}}
    """
    index = {}
    for game in games:
        name = game.get("name", "").strip()
        if len(name) >= MIN_NAME_LENGTH:
            index[name.lower()] = {
                "appid": game["appid"],
                "name": name,
            }
    return index


def find_mentions(review_text: str, name_index: dict, source_appid: str) -> list[str]:
    """
    Scan a review text for game name mentions.
    Returns a list of appids mentioned (excluding the source game itself).
    """
    text_lower = review_text.lower()
    mentioned = []
    for name_lower, game in name_index.items():
        if game["appid"] == source_appid:
            continue  # skip self-mentions
        if name_lower in text_lower:
            mentioned.append(game["appid"])
    return mentioned


def run():
    print("Loading silver tables...")
    games = load_csv("games.csv")
    reviews = load_csv("reviews.csv")
    print(f"  games: {len(games)} | reviews: {len(reviews)}")

    name_index = build_name_index(games)
    print(f"  game names indexed: {len(name_index)}")

    # Count co-mentions: {(source_appid, mentioned_appid): count}
    comention_counts = defaultdict(int)

    for i, review in enumerate(reviews):
        source_appid = review.get("appid")
        text = review.get("review", "")
        if not text:
            continue

        mentioned_appids = find_mentions(text, name_index, source_appid)
        for mentioned_appid in mentioned_appids:
            comention_counts[(source_appid, mentioned_appid)] += 1

    print(f"  unique game pairs with co-mentions: {len(comention_counts)}")

    # Build output rows with game names for readability
    appid_to_name = {g["appid"]: g["name"] for g in games}

    rows = []
    for (source_appid, mentioned_appid), count in comention_counts.items():
        rows.append({
            "source_appid":    source_appid,
            "source_name":     appid_to_name.get(source_appid, ""),
            "mentioned_appid": mentioned_appid,
            "mentioned_name":  appid_to_name.get(mentioned_appid, ""),
            "mention_count":   count,
        })

    rows.sort(key=lambda r: r["mention_count"], reverse=True)
    write_csv(rows, "comentions.csv")

    print("\nTop 10 co-mentions:")
    for r in rows[:10]:
        print(f"  {r['mention_count']}x | '{r['source_name']}' reviews mention '{r['mentioned_name']}'")


if __name__ == "__main__":
    run()
