"""Shared helpers: size parsing and accessory rejection."""
from __future__ import annotations

import re

# 65", 65”, "65 inch", "65-inch"
_SIZE_RE = re.compile(r'(\d{2,3})\s*(?:"|”|-?\s*inch\b)', re.IGNORECASE)

# "for 32-65 Inch", "45 – 75 inch", "40-85\"" — a size RANGE means the listing
# fits a span of TVs, i.e. it is a mount/cover/stand, not a television.
_RANGE_RE = re.compile(
    r'\d{2}\s*(?:-|–|—|to)\s*\d{2,3}\s*(?:"|”|-?\s*inch)',
    re.IGNORECASE,
)

# Unambiguous accessory phrases. Deliberately multi-word: bare "backlight",
# "control", "stand" or "vesa" all appear in genuine TV titles ("Backlight
# control", "Voice Control", "VESA 400x400"), so matching those would throw
# away real televisions.
_ACCESSORY_PHRASES = (
    "wall mount", "wall-mount", "mount bracket", "tv bracket", "mounting bracket",
    "ceiling mount", "ceiling tv", "tv cover", "cover for", "dust cover",
    "light strip", "led strip", "tv backlight", "user guide", "user manual",
    "instruction manual", "trolley", "tv stand", "floor stand", "rolling stand",
    "screen protector", "remote control", "wall plate",
    "tv mount", "tv trolley", "tv cart",
)

# A real 4K set at these sizes never sells this low; anything cheaper is a
# bracket, cover or cable that happened to mention the size.
MIN_PRICE = {65: 3000, 75: 5000, 85: 7000}


def parse_size(title: str):
    m = _SIZE_RE.search(title or "")
    return int(m.group(1)) if m else None


def is_accessory(title: str) -> bool:
    t = (title or "").lower()
    if _RANGE_RE.search(t):
        return True
    return any(phrase in t for phrase in _ACCESSORY_PHRASES)


def reject_reason(title: str, size, price, max_price: float, sizes) -> str | None:
    """Returns a short reason string, or None if the product should be kept."""
    if not title:
        return "no_title"
    if size is None:
        return "no_size"
    if size not in sizes:
        return f"size_{size}"
    if is_accessory(title):
        return "accessory"
    if price is None:
        return "no_price"
    if price < MIN_PRICE.get(size, 0):
        return "below_floor"
    if price > max_price:
        return "over_budget"
    return None
