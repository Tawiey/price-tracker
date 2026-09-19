#!/usr/bin/env python3
"""
Temporary diagnostic probe.

The scrapers have been returning 0 products with no errors, which means the
HTTP calls succeed but the response shape no longer matches our parsers.
This prints the actual structure of what Takealot and Amazon SA return so the
parsers can be rewritten against reality. Delete once the scrapers work.
"""
import json
import re

import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)


def shape(obj, depth=0, max_depth=3):
    """Compact structural summary of a JSON blob."""
    pad = "  " * depth
    if depth > max_depth:
        return f"{pad}..."
    if isinstance(obj, dict):
        lines = []
        for k, v in list(obj.items())[:12]:
            if isinstance(v, (dict, list)):
                lines.append(f"{pad}{k}:")
                lines.append(shape(v, depth + 1, max_depth))
            else:
                val = repr(v)[:70]
                lines.append(f"{pad}{k} = {val}")
        return "\n".join(lines)
    if isinstance(obj, list):
        if not obj:
            return f"{pad}[] (empty)"
        return f"{pad}[{len(obj)} items], first:\n" + shape(obj[0], depth + 1, max_depth)
    return f"{pad}{repr(obj)[:70]}"


def probe_takealot_api():
    print("\n" + "=" * 70)
    print("TAKEALOT API")
    print("=" * 70)
    versions = ["v-1-9-0", "v-1-10-0", "v-1-11-0", "v-1-12-0", "v-1-13-0"]
    headers = {
        "User-Agent": UA,
        "Accept": "application/json",
        "Accept-Language": "en-ZA,en;q=0.9",
        "Referer": "https://www.takealot.com/",
        "Origin": "https://www.takealot.com",
    }
    for v in versions:
        url = f"https://api.takealot.com/rest/{v}/searches/products"
        params = {"search": "65 inch tv", "start": 0, "rows": 6, "detail": "mlisting"}
        try:
            r = requests.get(url, params=params, headers=headers, timeout=20)
            print(f"\n--- {v}: HTTP {r.status_code}  {len(r.content)} bytes  "
                  f"{r.headers.get('content-type','?')}")
            if r.status_code != 200:
                print("   body:", r.text[:200])
                continue
            data = r.json()
            print("   TOP-LEVEL KEYS:", list(data.keys())[:15])
            print(shape(data, depth=1, max_depth=3))
            return  # first working version is enough
        except Exception as e:
            print(f"\n--- {v}: EXCEPTION {type(e).__name__}: {e}")


def probe_takealot_html():
    print("\n" + "=" * 70)
    print("TAKEALOT SEARCH PAGE (HTML)")
    print("=" * 70)
    url = "https://www.takealot.com/all"
    try:
        r = requests.get(
            url,
            params={"qsearch": "65 inch tv"},
            headers={"User-Agent": UA, "Accept-Language": "en-ZA,en;q=0.9"},
            timeout=25,
        )
        print(f"HTTP {r.status_code}  {len(r.content)} bytes")
        html = r.text
        for marker in ("__INITIAL_STATE__", "__NEXT_DATA__", "application/ld+json",
                       "data-ref=\"product-card", "productCard"):
            print(f"  contains {marker!r}: {marker in html}")
        m = re.search(r'R\s?\d[\d\s,]{2,}', html)
        print("  first price-like string:", m.group(0) if m else "none")
    except Exception as e:
        print(f"EXCEPTION {type(e).__name__}: {e}")


def probe_amazon():
    print("\n" + "=" * 70)
    print("AMAZON SOUTH AFRICA")
    print("=" * 70)
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-ZA,en;q=0.9",
        "Upgrade-Insecure-Requests": "1",
    }
    try:
        s = requests.Session()
        home = s.get("https://www.amazon.co.za", headers=headers, timeout=20)
        print(f"homepage: HTTP {home.status_code}  {len(home.content)} bytes")
        r = s.get("https://www.amazon.co.za/s", params={"k": "65 inch tv"},
                  headers=headers, timeout=25)
        print(f"search:   HTTP {r.status_code}  {len(r.content)} bytes")
        html = r.text
        low = html.lower()
        print("  captcha marker:", "captcha" in low)
        print("  'enter the characters':", "enter the characters" in low)
        for sel in ('data-component-type="s-search-result"', "s-result-item",
                    "a-price-whole", "a-price"):
            print(f"  occurrences of {sel!r}: {html.count(sel)}")
        m = re.search(r'<title>(.*?)</title>', html, re.S)
        print("  <title>:", (m.group(1).strip()[:90] if m else "none"))
    except Exception as e:
        print(f"EXCEPTION {type(e).__name__}: {e}")


if __name__ == "__main__":
    probe_takealot_api()
    probe_takealot_html()
    probe_amazon()
    print("\nDone.")
