from __future__ import annotations
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

_API_URL = "https://api.takealot.com/rest/v-1-9-0/searches/products"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-ZA,en;q=0.9",
    "Referer": "https://www.takealot.com/",
    "Origin": "https://www.takealot.com",
}


def scrape(query: str, max_price: float = 15000) -> list[dict]:
    params = {"userinit": "false", "search": query, "newsearch": "true",
              "sort": "BestMatch", "filters": "", "start": 0, "plp": "true"}
    try:
        resp = requests.get(_API_URL, params=params, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.error("Takealot error for %r: %s", query, exc)
        return []

    results = []
    for item in data.get("results", []):
        try:
            product = _parse(item, query)
        except Exception:
            continue
        if product and product["price"] <= max_price:
            results.append(product)
    return results


def _parse(item: dict, query: str) -> dict | None:
    title = (
        item.get("title") or
        item.get("product_views", {}).get("title") or
        item.get("name", "")
    ).strip()
    if not title or not _is_relevant(title):
        return None

    buybox = item.get("buybox_summary", {})
    price = buybox.get("price") or buybox.get("listing_price") or item.get("price")
    if price is None:
        return None
    price = float(price)
    if price > 500_000:
        price /= 100

    slug = item.get("core", {}).get("slug", "")
    return {
        "store": "Takealot",
        "title": title,
        "price": round(price, 2),
        "currency": "ZAR",
        "url": f"https://www.takealot.com/{slug}" if slug else "",
    }


def _is_relevant(title: str) -> bool:
    t = title.lower()
    return "65" in t and any(k in t for k in ("tv", "television", "qled", "oled", "qned", "led"))
