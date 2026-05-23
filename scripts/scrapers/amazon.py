from __future__ import annotations
import logging
import random
import time
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_BASE = "https://www.amazon.co.za"
_SEARCH = "https://www.amazon.co.za/s"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-ZA,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def scrape(query: str, max_price: float = 15000) -> list[dict]:
    try:
        session = requests.Session()
        session.get(_BASE, headers=_HEADERS, timeout=12)
        time.sleep(random.uniform(1.5, 3.0))
        resp = session.get(_SEARCH, params={"k": query, "i": "electronics"}, headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            logger.warning("Amazon.co.za returned HTTP %s", resp.status_code)
            return []
        if "captcha" in resp.text.lower() or "robot" in resp.text.lower():
            logger.warning("Amazon.co.za bot-detection triggered — skipping")
            return []
        return _parse_results(resp.text, max_price)
    except Exception as exc:
        logger.error("Amazon.co.za error for %r: %s", query, exc)
        return []


def _parse_results(html: str, max_price: float) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for card in soup.select('[data-component-type="s-search-result"]'):
        try:
            product = _parse_card(card)
        except Exception:
            continue
        if product and product["price"] <= max_price:
            results.append(product)
    return results


def _parse_card(card) -> dict | None:
    title_el = card.select_one("h2 a span") or card.select_one("h2 span")
    if not title_el:
        return None
    title = title_el.get_text(strip=True)
    if not title or not _is_relevant(title):
        return None

    whole_el = card.select_one(".a-price-whole")
    frac_el = card.select_one(".a-price-fraction")
    if not whole_el:
        return None
    whole = whole_el.get_text(strip=True).replace(",", "").replace("\xa0", "").rstrip(".")
    frac = frac_el.get_text(strip=True) if frac_el else "00"
    try:
        price = float(f"{whole}.{frac}")
    except ValueError:
        return None

    link = card.select_one("h2 a")
    href = link["href"] if link and link.get("href") else ""
    url = f"{_BASE}{href}".split("?")[0] if href.startswith("/") else href.split("?")[0]

    return {"store": "Amazon", "title": title, "price": round(price, 2), "currency": "ZAR", "url": url}


def _is_relevant(title: str) -> bool:
    t = title.lower()
    return ("65" in t or '65"' in t) and any(k in t for k in ("tv", "television", "qled", "oled", "qned"))
