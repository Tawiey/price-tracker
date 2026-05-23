#!/usr/bin/env python3
"""Monthly price scraper — writes results to data/prices.json."""
import json
import logging
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrapers import takealot, amazon

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PRICES_JSON = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "prices.json")

MAX_PRICE_ZAR = 15000

TAKEALOT_SEARCHES = [
    "65 inch Neo QLED 4K TV",
    "65 inch OLED 4K TV",
    "65 inch 4K QLED smart TV",
]
AMAZON_SEARCHES = [
    "65 inch Neo QLED 4K TV",
    "65 inch OLED 4K smart TV",
]


def load() -> dict:
    if os.path.exists(PRICES_JSON):
        with open(PRICES_JSON) as f:
            return json.load(f)
    return {"last_updated": None, "scrape_count": 0, "products": []}


def save(data: dict) -> None:
    os.makedirs(os.path.dirname(PRICES_JSON), exist_ok=True)
    with open(PRICES_JSON, "w") as f:
        json.dump(data, f, indent=2)


def merge(existing: list, fresh: list, today: str) -> list:
    index = {(p["store"], p["title"]): p for p in existing}
    for p in fresh:
        key = (p["store"], p["title"])
        if key in index:
            index[key]["url"] = p["url"] or index[key]["url"]
            if today not in {h["date"] for h in index[key]["history"]}:
                index[key]["history"].append({"date": today, "price": p["price"]})
        else:
            index[key] = {
                "store": p["store"],
                "title": p["title"],
                "currency": "ZAR",
                "url": p["url"],
                "history": [{"date": today, "price": p["price"]}],
            }
    return list(index.values())


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    logger.info("Scraping for %s", today)

    data = load()
    fresh = []

    logger.info("Scraping Takealot...")
    for q in TAKEALOT_SEARCHES:
        results = takealot.scrape(q, max_price=MAX_PRICE_ZAR)
        logger.info("  %r → %d", q, len(results))
        fresh.extend(results)

    logger.info("Scraping Amazon SA...")
    for q in AMAZON_SEARCHES:
        results = amazon.scrape(q, max_price=MAX_PRICE_ZAR)
        logger.info("  %r → %d", q, len(results))
        fresh.extend(results)

    # Deduplicate
    seen, unique = set(), []
    for p in fresh:
        key = (p["store"], p["title"])
        if key not in seen:
            seen.add(key)
            unique.append(p)

    logger.info("Found %d unique products", len(unique))

    data["products"] = merge(data.get("products", []), unique, today)
    data["last_updated"] = today
    data["scrape_count"] = data.get("scrape_count", 0) + 1

    save(data)
    logger.info("Saved %d products to %s", len(data["products"]), PRICES_JSON)


if __name__ == "__main__":
    main()
