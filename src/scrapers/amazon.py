"""
Amazon.com scraper (prices in USD).

Note: Amazon has aggressive bot-detection. This works for occasional/monthly
runs but may intermittently fail with a CAPTCHA response. If that happens,
the scraper logs a warning and returns an empty list — Takealot data is
unaffected.
"""
import logging
import random
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://www.amazon.com/s"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}


def scrape(query: str, max_price: float = 850) -> list[dict]:
    params = {
        "k": query,
        "i": "electronics",
        "rh": "n:172659",  # TVs & Video category
    }
    try:
        session = requests.Session()
        # Warm up session with a visit to the homepage first
        session.get("https://www.amazon.com", headers=_HEADERS, timeout=12)
        time.sleep(random.uniform(1.5, 3.0))

        resp = session.get(_SEARCH_URL, params=params, headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            logger.warning("Amazon returned HTTP %s", resp.status_code)
            return []
        if "captcha" in resp.text.lower() or "robot" in resp.text.lower():
            logger.warning(
                "Amazon showed a bot-detection page — skipping Amazon results this run"
            )
            return []

        return _parse_results(resp.text, query, max_price)
    except Exception as exc:
        logger.error("Amazon scrape error for %r: %s", query, exc)
        return []


def _parse_results(html: str, query: str, max_price: float) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    results = []
    for card in soup.select('[data-component-type="s-search-result"]'):
        try:
            product = _parse_card(card, query)
        except Exception as exc:
            logger.debug("Skipping Amazon card: %s", exc)
            continue
        if product and product["price"] <= max_price:
            results.append(product)
    return results


def _parse_card(card, query: str) -> dict | None:
    title_el = card.select_one("h2 a span") or card.select_one("h2 span")
    if not title_el:
        return None
    title = title_el.get_text(strip=True)
    if not title or not _is_relevant(title):
        return None

    # Price: whole + fraction, e.g. "1,299." + "00"
    whole_el = card.select_one(".a-price-whole")
    frac_el = card.select_one(".a-price-fraction")
    if not whole_el:
        return None

    whole = whole_el.get_text(strip=True).replace(",", "").rstrip(".")
    frac = frac_el.get_text(strip=True) if frac_el else "00"
    try:
        price = float(f"{whole}.{frac}")
    except ValueError:
        return None

    link = card.select_one("h2 a")
    href = link["href"] if link and link.get("href") else ""
    url = f"https://www.amazon.com{href}" if href.startswith("/") else href
    # Strip tracking params to keep URL clean
    url = url.split("?")[0] if url else ""

    return {
        "store": "Amazon",
        "title": title,
        "price": price,
        "currency": "USD",
        "url": url,
        "scraped_at": datetime.now().isoformat(),
        "search_query": query,
    }


def _is_relevant(title: str) -> bool:
    t = title.lower()
    has_size = "65" in t or '65"' in t
    has_tv = any(kw in t for kw in ("tv", "television", "qled", "oled", "qned"))
    return has_size and has_tv
