#!/usr/bin/env python3
"""
Monthly price scraper — writes results to data/prices.json.

Exits non-zero if it collects nothing, so a broken scraper fails the workflow
instead of quietly committing a date bump (which is what happened from June to
September 2026).
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrapers import amazon, takealot  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRICES_JSON = os.path.join(ROOT, "data", "prices.json")

SIZES = [65, 75, 85]
MAX_PRICE_ZAR = 15000
QUERY_TEMPLATES = ["{size} inch 4K TV", "{size} inch OLED TV"]

STORES = [("Takealot", takealot), ("Amazon SA", amazon)]


def load() -> dict:
    if os.path.exists(PRICES_JSON):
        with open(PRICES_JSON) as f:
            return json.load(f)
    return {"last_updated": None, "scrape_count": 0, "products": []}


def save(data: dict) -> None:
    os.makedirs(os.path.dirname(PRICES_JSON), exist_ok=True)
    with open(PRICES_JSON, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def collect() -> tuple[list[dict], int]:
    """Returns (unique products, number of failed queries)."""
    found, failures = [], 0
    size_set = set(SIZES)

    for label, module in STORES:
        logger.info("--- %s ---", label)
        for size in SIZES:
            for template in QUERY_TEMPLATES:
                query = template.format(size=size)
                try:
                    results = module.scrape(query, size_set,
                                            max_price=MAX_PRICE_ZAR)
                except Exception as exc:
                    failures += 1
                    logger.error("  %-22r FAILED: %s", query, exc)
                    continue
                logger.info("  %-22r -> %d", query, len(results))
                found.extend(results)

    seen, unique = set(), []
    for p in found:
        key = (p["store"], p["title"])
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique, failures


def merge(existing: list, fresh: list, today: str) -> list:
    index = {(p["store"], p["title"]): p for p in existing}
    for p in fresh:
        key = (p["store"], p["title"])
        if key in index:
            entry = index[key]
            entry["url"] = p["url"] or entry.get("url", "")
            entry["size"] = p.get("size") or entry.get("size")
            if today not in {h["date"] for h in entry["history"]}:
                entry["history"].append({"date": today, "price": p["price"]})
        else:
            index[key] = {
                "store": p["store"],
                "title": p["title"],
                "size": p.get("size"),
                "currency": "ZAR",
                "url": p["url"],
                "history": [{"date": today, "price": p["price"]}],
            }
    return list(index.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="scrape and report, but do not write prices.json")
    args = ap.parse_args()

    today = datetime.now().strftime("%Y-%m-%d")
    logger.info("Scraping for %s (sizes %s, cap R%s)",
                today, SIZES, MAX_PRICE_ZAR)

    unique, failures = collect()

    by_size = {s: sum(1 for p in unique if p.get("size") == s) for s in SIZES}
    logger.info("Found %d unique products  %s  (%d failed queries)",
                len(unique), by_size, failures)

    for store in ("Takealot", "Amazon"):
        sample = next((p for p in unique if p["store"] == store), None)
        if sample:
            logger.info("  sample %s: %r R%s -> %s",
                        store, sample["title"][:55], sample["price"], sample["url"])

    if not unique:
        logger.error("Collected nothing from either store — failing the run so "
                     "this does not silently commit a date bump.")
        return 1

    if args.dry_run:
        logger.info("Dry run — prices.json not written.")
        return 0

    data = load()
    data["products"] = merge(data.get("products", []), unique, today)
    data["last_updated"] = today
    data["scrape_count"] = data.get("scrape_count", 0) + 1
    save(data)
    logger.info("Saved %d products to %s", len(data["products"]), PRICES_JSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
