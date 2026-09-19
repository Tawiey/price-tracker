#!/usr/bin/env python3
"""Temporary diagnostic probe v2 — exact field shapes for the parsers."""
import json

import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)


def probe_takealot():
    print("=" * 70)
    print("TAKEALOT — first result, verbatim")
    print("=" * 70)
    headers = {
        "User-Agent": UA,
        "Accept": "application/json",
        "Accept-Language": "en-ZA,en;q=0.9",
        "Referer": "https://www.takealot.com/",
        "Origin": "https://www.takealot.com",
    }
    for v in ["v-1-9-0", "v-1-11-0", "v-1-13-0"]:
        url = f"https://api.takealot.com/rest/{v}/searches/products"
        try:
            r = requests.get(
                url,
                params={"search": "65 inch tv", "start": 0, "rows": 5,
                        "detail": "mlisting"},
                headers=headers, timeout=20,
            )
        except Exception as e:
            print(f"{v}: EXCEPTION {e}")
            continue
        print(f"\n### version {v} -> HTTP {r.status_code}")
        if r.status_code != 200:
            continue
        data = r.json()
        results = (data.get("sections", {})
                       .get("products", {})
                       .get("results", []))
        print(f"    sections.products.results -> {len(results)} items")
        if not results:
            continue
        print(json.dumps(results[0], indent=1)[:4500])
        return


def probe_amazon():
    print("\n" + "=" * 70)
    print("AMAZON SA — per-card selector check")
    print("=" * 70)
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-ZA,en;q=0.9",
        "Upgrade-Insecure-Requests": "1",
    }
    s = requests.Session()
    s.get("https://www.amazon.co.za", headers=headers, timeout=20)
    r = s.get("https://www.amazon.co.za/s", params={"k": "65 inch tv"},
              headers=headers, timeout=25)
    print(f"HTTP {r.status_code}")
    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.select('[data-component-type="s-search-result"]')
    print(f"cards found: {len(cards)}\n")

    for i, card in enumerate(cards[:4]):
        print(f"--- card {i}  asin={card.get('data-asin')!r}")
        checks = {
            "h2 a span": card.select_one("h2 a span"),
            "h2 span": card.select_one("h2 span"),
            "h2": card.select_one("h2"),
            '[data-cy="title-recipe"] a': card.select_one('[data-cy="title-recipe"] a'),
            "a.a-link-normal[href]": card.select_one("a.a-link-normal[href]"),
        }
        for name, el in checks.items():
            txt = el.get_text(strip=True)[:70] if el else None
            print(f"    {name:32} -> {txt!r}")
        price_off = card.select_one(".a-price .a-offscreen")
        whole = card.select_one(".a-price-whole")
        frac = card.select_one(".a-price-fraction")
        print(f"    {'.a-price .a-offscreen':32} -> "
              f"{price_off.get_text(strip=True)!r if price_off else None}")
        print(f"    {'.a-price-whole':32} -> "
              f"{whole.get_text(strip=True)!r if whole else None}")
        print(f"    {'.a-price-fraction':32} -> "
              f"{frac.get_text(strip=True)!r if frac else None}")
        link = card.select_one("h2 a") or card.select_one("a.a-link-normal[href]")
        print(f"    {'href':32} -> {(link.get('href')[:80] if link else None)!r}")
        print()


if __name__ == "__main__":
    probe_takealot()
    probe_amazon()
    print("Done.")
