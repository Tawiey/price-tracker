"""Amazon South Africa (amazon.co.za) scraper — prices in ZAR."""
from __future__ import annotations

import logging
import random
import time

import requests
from bs4 import BeautifulSoup

from .common import parse_size, reject_reason

logger = logging.getLogger(__name__)

_BASE = "https://www.amazon.co.za"
_SEARCH = "https://www.amazon.co.za/s"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-ZA,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
}

_CARD_SEL = '[data-component-type="s-search-result"]'


def scrape(query: str, sizes, max_price: float = 15000) -> list[dict]:
    """Search Amazon SA. Raises on transport/HTTP failure or bot challenge."""
    session = requests.Session()
    session.get(_BASE, headers=_HEADERS, timeout=20)
    time.sleep(random.uniform(1.0, 2.0))

    resp = session.get(_SEARCH, params={"k": query}, headers=_HEADERS, timeout=25)
    resp.raise_for_status()
    html = resp.text

    if "enter the characters" in html.lower() or "/errors/validateCaptcha" in html:
        raise RuntimeError("Amazon served a bot challenge")

    soup = BeautifulSoup(html, "lxml")
    cards = soup.select(_CARD_SEL)
    if not cards:
        # Amazon intermittently serves a stripped page with no result markup.
        logger.warning("Amazon returned no result cards for %r", query)
        return []

    out = []
    for card in cards:
        try:
            product = _parse_card(card, sizes, max_price)
        except Exception as exc:
            logger.debug("Skipping Amazon card: %s", exc)
            continue
        if product:
            out.append(product)
    return out


def _price_of(card):
    # The full formatted price lives in .a-offscreen, e.g. 'R\xa08\xa0729.03'
    off = card.select_one(".a-price .a-offscreen")
    if off:
        txt = (off.get_text(strip=True)
                  .replace("R", "").replace("\xa0", "")
                  .replace(" ", "").replace(",", ""))
        try:
            return float(txt)
        except ValueError:
            pass

    whole_el = card.select_one(".a-price-whole")
    if whole_el:
        whole = (whole_el.get_text(strip=True)
                         .replace("\xa0", "").replace(" ", "")
                         .replace(",", "").rstrip("."))
        frac_el = card.select_one(".a-price-fraction")
        frac = frac_el.get_text(strip=True) if frac_el else "00"
        try:
            return float(f"{whole}.{frac}")
        except ValueError:
            pass
    return None


def _parse_card(card, sizes, max_price: float):
    # The title sits in `h2 span`; `h2 a span` no longer matches.
    title_el = card.select_one("h2 span") or card.select_one("h2")
    title = title_el.get_text(strip=True) if title_el else ""
    size = parse_size(title)
    price = _price_of(card)

    if reject_reason(title, size, price, max_price, sizes):
        return None

    asin = card.get("data-asin")
    url = f"{_BASE}/dp/{asin}" if asin else ""

    return {
        "store": "Amazon",
        "title": title,
        "size": size,
        "price": round(price, 2),
        "currency": "ZAR",
        "url": url,
    }
