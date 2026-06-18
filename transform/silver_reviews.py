"""
transform/silver_reviews.py

Reads raw Steam Reviews JSON and transforms into two clean Silver tables:

  silver/review_summaries.csv  — one row per game, aggregate review stats
  silver/reviews.csv           — one row per review, individual texts

Both tables use appid as foreign key to silver/games.csv.

Raw  → nested JSON with summary + list of review texts
Silver → flat CSVs, clean types, ready for analysis
"""

import json
import csv
import os
import glob
from datetime import datetime, timezone

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


def timestamp_to_date(ts) -> str | None:
    """Convert Unix timestamp (seconds since 1970) to readable date string."""
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def minutes_to_hours(minutes) -> float | None:
    """Convert playtime from minutes to hours, rounded to 1 decimal."""
    if minutes is None:
        return None
    try:
        return round(int(minutes) / 60, 1)
    except (TypeError, ValueError):
        return None


def positive_ratio(total_positive, total_reviews) -> float | None:
    """Calculate percentage of positive reviews."""
    try:
        return round(int(total_positive) / int(total_reviews) * 100, 1)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def transform_summary(raw: dict) -> dict:
    """Transform the aggregate review stats for one game."""
    return {
        "appid":             raw.get("appid"),
        "total_reviews":     raw.get("total_reviews"),
        "total_positive":    raw.get("total_positive"),
        "total_negative":    raw.get("total_negative"),
        "positive_ratio":    positive_ratio(raw.get("total_positive"), raw.get("total_reviews")),
        "review_score":      raw.get("review_score"),        # numeric 0-9
        "review_score_desc": raw.get("review_score_desc"),   # e.g. "Overwhelmingly Positive"
    }


def transform_review(appid: int, raw: dict) -> dict:
    """Transform one individual review into a clean Silver row."""
    return {
        "appid":            appid,
        "recommendationid": raw.get("recommendationid"),
        "voted_up":         1 if raw.get("voted_up") else 0,
        "votes_up":         raw.get("votes_up", 0),
        "review_date":      timestamp_to_date(raw.get("timestamp_created")),
        "playtime_hours":   minutes_to_hours(raw.get("author_playtime_forever")),
        "review":           raw.get("review", "").strip(),
    }


def write_csv(rows: list[dict], path: str):
    """Write a list of dicts to a CSV file."""
    if not rows:
        print(f"No rows to write for {path}")
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Silver table saved: {path} ({len(rows)} rows, {len(fieldnames)} columns)")


def run():
    os.makedirs(SILVER_DIR, exist_ok=True)

    raw_data = load_latest_raw("steam_reviews")
    print(f"Raw game records loaded: {len(raw_data)}")

    summaries = []
    reviews = []

    for game in raw_data:
        appid = game.get("appid")
        if not appid:
            continue

        summaries.append(transform_summary(game))

        for raw_review in game.get("top_reviews", []):
            reviews.append(transform_review(appid, raw_review))

    write_csv(summaries, os.path.join(SILVER_DIR, "review_summaries.csv"))
    write_csv(reviews, os.path.join(SILVER_DIR, "reviews.csv"))

    print("\nSample summaries:")
    for s in summaries[:3]:
        print(f"  [{s['appid']}] {s['review_score_desc']} | {s['positive_ratio']}% positive | {s['total_reviews']:,} total")

    print("\nSample reviews:")
    for r in reviews[:3]:
        print(f"  [{r['appid']}] votes_up={r['votes_up']} | {r['playtime_hours']}h | {r['review'][:80]}...")

    return summaries, reviews


if __name__ == "__main__":
    run()
