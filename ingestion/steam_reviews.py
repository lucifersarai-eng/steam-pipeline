"""
ingestion/steam_reviews.py

Fetches user reviews from the Steam Store Reviews API.
No API key required — free and public.

For each game, fetches a sample of reviews and keeps the most helpful ones,
ranked by votes_up (how many players marked the review as useful).

Docs: https://partner.steamgames.com/doc/store/getreviews
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.helpers import get_with_retry, save_raw, throttle, logger

STEAM_REVIEWS_BASE = "https://store.steampowered.com/appreviews/{appid}"


def fetch_review_summary(appid: int) -> dict | None:
    """
    Fetch the review summary for a single game.

    Returns aggregate stats: total reviews, total positive, total negative,
    and the score description (e.g. "Overwhelmingly Positive").
    """
    url = STEAM_REVIEWS_BASE.format(appid=appid)
    params = {
        "json": 1,
        "num_per_page": 0,  # we only want the summary, not review texts
        "language": "english",
    }

    data = get_with_retry(url, params=params)

    if not data or data.get("success") != 1:
        logger.warning(f"No review summary for appid {appid}")
        return None

    summary = data.get("query_summary", {})

    return {
        "appid": appid,
        "total_reviews": summary.get("total_reviews"),
        "total_positive": summary.get("total_positive"),
        "total_negative": summary.get("total_negative"),
        "review_score": summary.get("review_score"),          # numeric score 0-9
        "review_score_desc": summary.get("review_score_desc"), # e.g. "Overwhelmingly Positive"
    }


def fetch_top_reviews(appid: int, sample_size: int = 100, top_n: int = 20) -> list[dict]:
    """
    Fetch a sample of reviews for a game and return the most helpful ones.

    Strategy:
      1. Fetch `sample_size` reviews from the API (max 100 per request)
      2. Sort by votes_up descending (most helpful first)
      3. Return only the top `top_n`

    We use filter=all so the API returns reviews across all time,
    not just recent ones — giving us a broader sample to rank.
    """
    url = STEAM_REVIEWS_BASE.format(appid=appid)
    params = {
        "json": 1,
        "filter": "all",
        "language": "english",
        "review_type": "all",
        "purchase_type": "all",
        "num_per_page": sample_size,
    }

    data = get_with_retry(url, params=params)

    if not data or data.get("success") != 1:
        logger.warning(f"No reviews for appid {appid}")
        return []

    raw_reviews = data.get("reviews", [])

    reviews = []
    for r in raw_reviews:
        reviews.append({
            "recommendationid": r.get("recommendationid"),
            "voted_up": r.get("voted_up"),                          # True = positive review
            "review": r.get("review", "").strip(),
            "votes_up": r.get("votes_up", 0),                       # helpful votes — our ranking key
            "timestamp_created": r.get("timestamp_created"),
            "author_playtime_forever": r.get("author", {}).get("playtime_forever"),  # in minutes
        })

    # Sort by most helpful and return top N
    reviews.sort(key=lambda r: r["votes_up"], reverse=True)
    return reviews[:top_n]


def fetch_batch(appids: list[int], top_n: int = 20) -> list[dict]:
    """
    Fetch review summary and top reviews for each game in the list.

    Returns a list of dicts, one per game, combining the summary
    and the most helpful reviews.
    """
    results = []
    total = len(appids)

    for i, appid in enumerate(appids, 1):
        logger.info(f"Fetching reviews [{i}/{total}] appid={appid}")
        throttle(1.5)

        summary = fetch_review_summary(appid)
        if not summary:
            continue

        throttle(1.5)
        top_reviews = fetch_top_reviews(appid, top_n=top_n)

        results.append({
            **summary,
            "top_reviews": top_reviews,
        })

    logger.info(f"Fetched reviews for {len(results)}/{total} games.")
    return results


def run(appids: list[int]):
    """Main entry point — fetch and save reviews for a list of appids."""
    if not appids:
        logger.error("No appids provided.")
        return []

    results = fetch_batch(appids)
    save_raw(results, name="steam_reviews")
    return results


if __name__ == "__main__":
    test_appids = [
        730,     # CS2
        570,     # Dota 2
        1091500  # Cyberpunk 2077
    ]
    run(test_appids)
