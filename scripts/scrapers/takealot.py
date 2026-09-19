from __future__ import annotations

import logging
import re

import requests

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

# Matches 65", 65”, "65 inch", "65-inch"
_SIZE_RE = re.compile(r'(\d{2,3})\s*(?:"|”|-?\s*inch\b)', re.IGNORECASE)


def parse_size(title: str):
    m = _SIZE_RE.search(title or "")
    return int(m.group(1)) if m else None


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

    out = []
    for item in results:
        try:
            product = _parse(item, sizes, max_price)
        except Exception as exc:
            logger.debug("Skipping Takealot item: %s", exc)
            continue
        if product:
            out.append(product)
    return out


def _parse(item: dict, sizes, max_price: float):
    core = item.get("core") or {}
    title = (core.get("title") or "").strip()
    if not title:
        return None

    size = parse_size(title)
    if size not in sizes:
        return None

    buybox = item.get("buybox_summary") or {}
    price = buybox.get("price")
    if price is None:
        # Multi-variant listings expose a list of prices instead of a scalar.
        prices = buybox.get("prices") or []
        price = min(prices) if prices else None
    if price is None:
        return None

    price = float(price)
    if price > max_price:
        return None

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
    }
