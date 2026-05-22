#!/usr/bin/env python3
"""
Entry point for the TV Price Tracker.

Usage:
  python main.py scrape   # Fetch latest prices and store them
  python main.py serve    # Start the web dashboard (default)
  python main.py          # Alias for 'serve'
"""
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_scraper() -> int:
    from config import (
        AMAZON_SEARCHES,
        MAX_PRICE_USD,
        MAX_PRICE_ZAR,
        TAKEALOT_SEARCHES,
    )
    from src import database
    from src.scrapers import amazon, takealot

    database.init_db()
    all_products: list[dict] = []

    logger.info("Scraping Takealot…")
    for query in TAKEALOT_SEARCHES:
        found = takealot.scrape(query, max_price=MAX_PRICE_ZAR)
        logger.info("  %r → %d products", query, len(found))
        all_products.extend(found)

    logger.info("Scraping Amazon…")
    for query in AMAZON_SEARCHES:
        found = amazon.scrape(query, max_price=MAX_PRICE_USD)
        logger.info("  %r → %d products", query, len(found))
        all_products.extend(found)

    # Deduplicate by (store, title), keeping first occurrence
    seen: set[tuple] = set()
    unique = []
    for p in all_products:
        key = (p["store"], p["title"])
        if key not in seen:
            seen.add(key)
            unique.append(p)

    if unique:
        database.save_prices(unique)
        logger.info("Saved %d unique products to database.", len(unique))
    else:
        logger.warning("No products found — nothing saved.")

    return len(unique)


def run_server():
    from src.app import app
    logger.info("Starting dashboard at http://localhost:5000")
    app.run(debug=False, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "serve"

    if command == "scrape":
        count = run_scraper()
        sys.exit(0 if count >= 0 else 1)
    elif command == "serve":
        run_server()
    else:
        print(f"Unknown command: {command!r}")
        print("Usage: python main.py [scrape|serve]")
        sys.exit(1)
