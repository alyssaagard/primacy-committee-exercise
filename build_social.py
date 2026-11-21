#!/usr/bin/env python3
"""
build_social.py
Renders the share card: social-card.png (1200 x 630) and
social-card-github.png (1280 x 640).

The fan on the card is model output. It is the 10th to 90th percentile
band and median of the US dollar reserve share under the accretion pathway
with every seat run by the model, read from reference.json.

Type is Liberation Serif, which is metrically compatible with Times New
Roman. Small caps are set as tracked capitals. The card is drawn at twice
size and reduced.

Run: python build_social.py   (after reference.js)
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
S = 2
PAGE, INK = (255, 248, 253), (36, 29, 38)
RULE, MUTED = (156, 111, 134), (109, 90, 102)
BAND, MEDIAN = (238, 216, 229), (138, 90, 114)
FONTS = "/usr/share/fonts/truetype/liberation/"
SERIF = FONTS + "LiberationSerif-Regular.ttf"
ITALIC = FONTS + "LiberationSerif-Italic.ttf"


def font(path, size):
    return ImageFont.truetype(path, size * S)


def width(d, s, f, track):
    return sum(d.textlength(c, font=f) for c in s) + track * S * (len(s) - 1)


def text(d, y, s, f, fill, track=0, x=None, center=None, right=None):
    w = width(d, s, f, track)
    px = (x * S if x is not None else
          center * S - w / 2 if center is not None else right * S - w)
    for c in s:
        d.text((px, y * S), c, font=f, fill=fill)
        px += d.textlength(c, font=f) + track * S


def double_rule(d, y, x0, x1):
    for dy in (0, 4):
        d.rectangle([x0 * S, (y + dy) * S, x1 * S, (y + dy) * S + S - 1],
                    fill=RULE)


def fan(d, box):
    ref = json.loads((HERE / "reference.json").read_text())
    start = json.loads((HERE / "payload.json").read_text())[
        "model"]["reserve"]["usd0"]
    lo = [start] + [k["p10"] for k in ref["usd_fan"]]
    md = [start] + [k["p50"] for k in ref["usd_fan"]]
    hi = [start] + [k["p90"] for k in ref["usd_fan"]]
    x0, y0, x1, y1 = box
    n, vmin, vmax = len(lo), min(lo) - 0.5, max(hi) + 0.5
    xs = [x0 + (x1 - x0) * i / (n - 1) for i in range(n)]

    def py(v):
        return y1 - (v - vmin) / (vmax - vmin) * (y1 - y0)

    d.polygon([(xs[i] * S, py(hi[i]) * S) for i in range(n)]
              + [(xs[i] * S, py(lo[i]) * S) for i in range(n - 1, -1, -1)],
              fill=BAND)
    for i in range(n - 1):            # dotted median
        ax, ay, bx, by = xs[i], py(md[i]), xs[i + 1], py(md[i + 1])
        for k in range(0, 6, 2):
            t0, t1 = k / 6, (k + 1) / 6
            d.line([((ax + (bx - ax) * t0) * S, (ay + (by - ay) * t0) * S),
                    ((ax + (bx - ax) * t1) * S, (ay + (by - ay) * t1) * S)],
                   fill=MEDIAN, width=2 * S)
    d.line([(x0 * S, y1 * S), (x1 * S, y1 * S)], fill=RULE, width=S)
    return md[0], md[-1]


def render(w, h, out):
    img = Image.new("RGB", (w * S, h * S), PAGE)
    d = ImageDraw.Draw(img)
    ml, mr, top = 76, w - 76, (h - 630) // 2
    double_rule(d, top + 52, ml, mr)
    text(d, top + 84, "THE PRIMACY PREMIUM", font(SERIF, 19), MUTED, 7,
         center=w / 2)
    text(d, top + 122, "Committee Exercise", font(SERIF, 82), INK, 1,
         center=w / 2)
    text(d, top + 232,
         "A four-seat budget exercise on the estimated model, 2026 to 2035",
         font(ITALIC, 27), MUTED, center=w / 2)
    first, last = fan(d, (ml, top + 300, mr, top + 470))
    f_small = font(SERIF, 16)
    text(d, top + 480, "2026", f_small, MUTED, 3, x=ml)
    text(d, top + 480, "2035", f_small, MUTED, 3, right=mr)
    text(d, top + 486,
         f"US DOLLAR RESERVE SHARE, REFERENCE MEDIAN {first:.1f} TO {last:.1f} PERCENT",
         f_small, MUTED, 4, center=w / 2)
    double_rule(d, top + 536, ml, mr)
    f_rail = font(SERIF, 18)
    text(d, top + 560, "I  II  III  IV  V", f_rail, RULE, 6, x=ml)
    text(d, top + 560, "ALYSSA I. AGARD", f_rail, MUTED, 6, right=mr)
    img.resize((w, h), Image.LANCZOS).save(HERE / out, optimize=True)
    print(f"{out} written ({w} x {h})")


if __name__ == "__main__":
    render(1200, 630, "social-card.png")
    render(1280, 640, "social-card-github.png")
