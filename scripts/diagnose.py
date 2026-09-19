#!/usr/bin/env python3
"""Temporary diagnostic probe v3 — confirm qsearch param + lxml parsing."""
import json

import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)


def probe_takealot():
    print("=" * 70)
    print("TAKEALOT — qsearch param + head of first result")
    print("=" * 70)
    headers = {
        "User-Agent": UA,
        "Accept": "application/json",
        "Accept-Language": "en-ZA,en;q=0.9",
        "Referer": "https://www.takealot.com/",
        "Origin": "https://www.takealot.com",
    }
    url = "https://api.takealot.com/rest/v-1-9-0/searches/products"
    r = requests.get(
        url,
        params={"qsearch": "65 inch tv", "start": 0, "rows": 5, "detail": "mlisting"},
        headers=headers, timeout=20,
    )
    print(f"HTTP {r.status_code}")
    data = r.json()
    print("search_request.qsearch =",
          repr(data.get("search_request", {}).get("qsearch")))
    results = data.get("sections", {}).get("products", {}).get("results", [])
    print(f"results: {len(results)}")
    if not results:
        return
    print("\nTOP-LEVEL KEYS of results[0]:")
    print(" ", list(results[0].keys()))
    print("\nHEAD of results[0]:")
    print(json.dumps(results[0], indent=1)[:1800])
    print("\n--- titles returned ---")
    for res in results:
        ecom = (res.get("enhanced_ecommerce_click", {})
                   .get("ecommerce", {}).get("click", {}).get("products", [{}]))
        name = ecom[0].get("name") if ecom else None
        bb = res.get("buybox_summary", {})
        print(f"  {name!r}  prices={bb.get('prices')}")


def probe_amazon():
    print("\n" + "=" * 70)
    print("AMAZON SA — html.parser vs lxml")
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
    html = r.text
    marker = 'data-component-type="s-search-result"'
    print(f"HTTP {r.status_code}  raw marker count: {html.count(marker)}")

    for parser in ("html.parser", "lxml"):
        try:
            soup = BeautifulSoup(html, parser)
            cards = soup.select('[data-component-type="s-search-result"]')
            print(f"  {parser:12} -> {len(cards)} cards")
        except Exception as e:
            print(f"  {parser:12} -> ERROR {e}")
            continue
        if not cards:
            continue
        for i, card in enumerate(cards[:3]):
            def txt(sel):
                el = card.select_one(sel)
                return el.get_text(strip=True)[:65] if el else None
            link = card.select_one("h2 a") or card.select_one("a.a-link-normal[href]")
            print(f"    card{i} asin={card.get('data-asin')!r}")
            print(f"      h2 a span          : {txt('h2 a span')!r}")
            print(f"      h2 span            : {txt('h2 span')!r}")
            print(f"      h2                 : {txt('h2')!r}")
            print(f"      .a-price .a-offscreen: {txt('.a-price .a-offscreen')!r}")
            print(f"      .a-price-whole     : {txt('.a-price-whole')!r}")
            print(f"      href               : "
                  f"{(link.get('href')[:70] if link else None)!r}")


if __name__ == "__main__":
    probe_takealot()
    probe_amazon()
    print("\nDone.")
