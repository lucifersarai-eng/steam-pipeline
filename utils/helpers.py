import time
import logging
import requests
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def get_with_retry(url: str, params: dict = None, retries: int = 3, backoff: float = 2.0) -> dict | None:
    """
    GET request with retry + exponential backoff.
    Steam APIs are rate-limited — this handles transient failures gracefully.
    """
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 429:
                wait = backoff ** attempt
                logger.warning(f"Rate limited. Waiting {wait}s before retry {attempt}/{retries}...")
                time.sleep(wait)
                continue

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(backoff ** attempt)

    logger.error(f"All {retries} attempts failed for URL: {url}")
    return None


def save_raw(data: dict | list, name: str, raw_dir: str = "raw") -> str:
    """
    Save raw API response as timestamped JSON.
    Keeps a full audit trail of what was ingested and when.
    """
    import json, os
    os.makedirs(raw_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = f"{raw_dir}/{name}_{timestamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved raw data to {path}")
    return path


def throttle(seconds: float = 1.5):
    """Simple sleep to respect API rate limits between calls."""
    time.sleep(seconds)
