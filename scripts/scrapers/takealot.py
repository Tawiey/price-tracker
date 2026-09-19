from __future__ import annotations

import logging
from collections import Counter

import requests

from .common import parse_size, reject_reason

logger = logging.getLogger(__name__)

_API_URL = "https://api.takealot.com/rest/v-1-9-0/searches/products"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-ZA,en;q=0.9",
    "Referer": "https://www.takealot.com/",
    "Origin": "https://www.takealot.com",
}


def scrape(query: str, sizes, max_price: float = 15000) -> list[dict]:
    """Search Takealot. Raises on transport/HTTP failure so callers can see it."""
    # NOTE: the param is `qsearch`. Passing `search` is silently ignored and
    # Takealot returns an unrelated default product list.
    params = {"qsearch": query, "start": 0, "rows": 50, "detail": "mlisting"}
    resp = requests.get(_API_URL, params=params, headers=_HEADERS, timeout=25)
    resp.raise_for_status()
    data = resp.json()

    # Results are nested under sections.products, not at the top level.
    results = (data.get("sections", {})
                   .get("products", {})
                   .get("results", []))
    if not results:
        logger.warning("Takealot returned no rows for %r", query)
        return []

    out, reasons, samples = [], Counter(), []
    for item in results:
        product, reason, sample = _parse(item, sizes, max_price)
        if product:
            out.append(product)
        else:
            reasons[reason] += 1
            if len(samples) < 3:
                samples.append(sample)

    if not out:
        logger.warning("Takealot %r: %d rows, none kept. reasons=%s samples=%s",
                       query, len(results), dict(reasons), samples)
    return out


def _parse(item: dict, sizes, max_price: float):
    """Returns (product | None, reject_reason, sample_tuple)."""
    core = item.get("core") or {}
    title = (core.get("title") or "").strip()
    size = parse_size(title)

    buybox = item.get("buybox_summary") or {}
    price = buybox.get("price")
    if price is None:
        # Multi-variant listings expose a list of prices instead of a scalar.
        prices = buybox.get("prices") or []
        price = min(prices) if prices else None
    price = float(price) if price is not None else None

    sample = (title[:48], size, price)
    reason = reject_reason(title, size, price, max_price, sizes)
    if reason:
        return None, reason, sample

    slug = core.get("slug") or ""
    plid = core.get("id")
    url = f"https://www.takealot.com/{slug}/PLID{plid}" if slug and plid else ""

    return {
        "store": "Takealot",
        "title": title,
        "size": size,
        "price": round(price, 2),
        "currency": "ZAR",
        "url": url,
    }, None, sample
