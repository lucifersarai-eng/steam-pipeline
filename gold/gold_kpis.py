"""
gold/gold_kpis.py

Builds Gold KPI tables from Silver data.

Inputs:
  silver/games.csv            — game metadata
  silver/review_summaries.csv — aggregate review stats per game

Outputs:
  gold/top_games_by_score.csv  — top 20 games by % positive reviews
  gold/top_games_by_volume.csv — top 20 games by total review count
  gold/genre_stats.csv         — avg positive ratio and game count per genre
"""

import csv
import os
from collections import defaultdict

SILVER_DIR = "silver"
GOLD_DIR = "gold"

MIN_REVIEWS = 1000  # ignore games with too few reviews to have a meaningful ratio


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


def join_games_and_summaries(games: list[dict], summaries: list[dict]) -> list[dict]:
    """Join games and review_summaries on appid into a single list."""
    summaries_by_appid = {row["appid"]: row for row in summaries}

    joined = []
    for game in games:
        appid = game.get("appid")
        summary = summaries_by_appid.get(appid, {})
        joined.append({**game, **summary})

    return joined


def build_top_by_score(joined: list[dict]) -> list[dict]:
    """
    Top 20 games ranked by positive_ratio.
    Only includes games with at least MIN_REVIEWS total reviews
    to avoid games with 5/5 stars from only 10 people ranking first.
    """
    eligible = []
    for row in joined:
        try:
            total = int(row.get("total_reviews") or 0)
            ratio = float(row.get("positive_ratio") or 0)
        except (TypeError, ValueError):
            continue
        if total >= MIN_REVIEWS:
            eligible.append({
                "appid":             row["appid"],
                "name":              row["name"],
                "genres":            row["genres"],
                "total_reviews":     total,
                "positive_ratio":    ratio,
                "review_score_desc": row.get("review_score_desc", ""),
                "price_usd":         row.get("price_usd", ""),
                "release_year":      row.get("release_year", ""),
            })

    eligible.sort(key=lambda r: r["positive_ratio"], reverse=True)
    return eligible[:20]


def build_top_by_volume(joined: list[dict]) -> list[dict]:
    """Top 20 games ranked by total number of reviews."""
    rows = []
    for row in joined:
        try:
            total = int(row.get("total_reviews") or 0)
        except (TypeError, ValueError):
            continue
        rows.append({
            "appid":             row["appid"],
            "name":              row["name"],
            "genres":            row["genres"],
            "total_reviews":     total,
            "positive_ratio":    row.get("positive_ratio", ""),
            "review_score_desc": row.get("review_score_desc", ""),
        })

    rows.sort(key=lambda r: r["total_reviews"], reverse=True)
    return rows[:20]


def build_genre_stats(joined: list[dict]) -> list[dict]:
    """
    For each genre, calculate:
      - how many games belong to it
      - average positive_ratio across those games
    Games can belong to multiple genres (pipe-separated in the CSV).
    """
    genre_ratios = defaultdict(list)

    for row in joined:
        genres_raw = row.get("genres", "")
        if not genres_raw:
            continue
        try:
            ratio = float(row.get("positive_ratio") or 0)
        except (TypeError, ValueError):
            continue

        for genre in genres_raw.split(" | "):
            genre = genre.strip()
            if genre:
                genre_ratios[genre].append(ratio)

    stats = []
    for genre, ratios in genre_ratios.items():
        stats.append({
            "genre":              genre,
            "game_count":         len(ratios),
            "avg_positive_ratio": round(sum(ratios) / len(ratios), 1),
        })

    stats.sort(key=lambda r: r["avg_positive_ratio"], reverse=True)
    return stats


def run():
    print("Loading silver tables...")
    games = load_csv("games.csv")
    summaries = load_csv("review_summaries.csv")
    print(f"  games: {len(games)} rows | summaries: {len(summaries)} rows")

    joined = join_games_and_summaries(games, summaries)

    top_by_score = build_top_by_score(joined)
    top_by_volume = build_top_by_volume(joined)
    genre_stats = build_genre_stats(joined)

    write_csv(top_by_score, "top_games_by_score.csv")
    write_csv(top_by_volume, "top_games_by_volume.csv")
    write_csv(genre_stats, "genre_stats.csv")

    print("\nTop 5 by positive ratio:")
    for r in top_by_score[:5]:
        print(f"  {r['positive_ratio']}% | {r['name']} | {r['review_score_desc']}")

    print("\nTop 5 by volume:")
    for r in top_by_volume[:5]:
        print(f"  {r['total_reviews']:,} reviews | {r['name']}")

    print("\nTop 5 genres by avg positive ratio:")
    for r in genre_stats[:5]:
        print(f"  {r['avg_positive_ratio']}% | {r['genre']} ({r['game_count']} games)")


if __name__ == "__main__":
    run()
