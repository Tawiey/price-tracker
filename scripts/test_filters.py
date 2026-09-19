#!/usr/bin/env python3
"""
Filter tests built from titles the scraper actually returned on 2026-09-19.

The accessory rules are the only thing standing between the dashboard and a
list of TV brackets, so they get pinned down here. Run: python scripts/test_filters.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrapers.common import parse_size, reject_reason  # noqa: E402

SIZES = {65, 75, 85}
MAX = 15000

# (title, price) pairs that are NOT televisions and must be rejected.
ACCESSORIES = [
    ("Universal LED/LCD/OLED Flat & Curved TV, Mount With Vesa mostly", 109),
    ("Heavy-Duty Flat Panel TV Wall Mount Bracket for 40-85 Inch LED", 149),
    ("Volkano Universal TV Wall Mount for Up to 85 Inch TVs", 263),
    ('Full Motion TV Wall Mount for 32-85" TVs, Heavy-Duty Bracket', 549),
    ("Perfect Dealz Swivel TV Wall Mount Support for 32 - 65 inch Screens", 599),
    ("Ceiling Mount TV Bracket with Dual-Pole Support for 40-85 Inch", 850),
    ("Ceiling TV Bracket for 32-65 Inch Flat Panel, LCD, LED, Plasma", 879),
    ("DJ-07 Heavy Duty Ceiling/Wall TV Mount Bracket for 40-85 Inch", 949),
    ("GIPOYENT TV Light Strip, 5M TV Backlight, for 45-75 Inch TV", 978),
    ("Samsung Crystal UHD U8000F 4K Smart TV User Guide: Quick Start", 1170),
    ("Fanfanwin 65 Inch Black TV Cover for Moving, Scratch Resistant", 1259),
    ("Rolling TV Stand with Shelves, 40-75 Inch, Height Adjustable", 1400),
    ("Barkan TV Wall Mount, 19-65 inch Fixed, Flat/Curved", 1551),
    ("IC ICLOVER Outdoor TV Cover 60-65 inch, 600D Heavy Duty", 1755),
    ("IC ICLOVER Outdoor TV Cover 70-75inch, with Waterproof", 3095),
    ("Heavy-Duty Mobile TV Floor Stand Trolley for 32-75 Inch", 1499),
]

# Real televisions that must survive the filters.
TELEVISIONS = [
    ('Hisense 65" Q7Q 144Hz 4K UHD QLED Gaming VIDAA SMART TV with Dolby '
     'Vision, Game Mode PRO, QLED Colour, Hi-Concerto, Filmmaker Mode', 7999),
    ('Toshiba 65" M450RP 4K QLED Smart TV with Dolby Atmos & Colourful '
     'Quantum Dot, REGZA Engine ZR, AI Motion Enhancer, Backlight control, '
     'MEMC', 6999),
    ("TCL 65 Inch 4K QLED Smart TV, Google TV, Dolby Vision", 8729.03),
    ("Samsung 65-Inch QLED Q60D 4K Tizen OS Smart TV", 11000),
    ("LG UA80 HDR10 webOS25 2025 UHD 4K AI 65-Inch Smart TV", 9308),
    ('Hisense 65" 4K UHD E7Q QLED Smart TV with AI Upscaler & Dolby Atmos, '
     'AI Smooth Motion, QLED Colour, Game Mode PLUS, Voice Control, '
     'AI Light Sensor', 7856.13),
    ('Skyworth 65" X6600H 4K QD-MiniLED Google Smart TV, Eye Care 5.0 '
     'Display, Dolby Vision & Dolby Atmos, HDR10+, 120Hz Turbo Motion, '
     'Local Dimming, MEMC, Game Mode', 9999),
    ("Samsung UA65U8000FUXXA U8000F Crystal 4K UHD 65-Inch Smart TV", 9999),
    ('Hisense 75" U7Q Pro 165Hz 4K MiniLED Smart TV', 14999),
    ('TCL 85" P7K 4K QLED Google TV', 14500),
]


def main():
    failures = []

    for title, price in ACCESSORIES:
        reason = reject_reason(title, parse_size(title), price, MAX, SIZES)
        if reason is None:
            failures.append(f"ACCESSORY NOT REJECTED: {title[:60]!r} @ R{price}")

    for title, price in TELEVISIONS:
        reason = reject_reason(title, parse_size(title), price, MAX, SIZES)
        if reason is not None:
            failures.append(
                f"TV WRONGLY REJECTED ({reason}): {title[:60]!r} @ R{price}")

    if failures:
        print(f"{len(failures)} failure(s):")
        for f in failures:
            print("  -", f)
        return 1

    print(f"OK: {len(ACCESSORIES)} accessories rejected, "
          f"{len(TELEVISIONS)} televisions kept.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
