#!/usr/bin/env python3
"""
build_social.py
Renders social-card.png, the Open Graph share image, at 1200 x 630.

The card is drawn in the project's register: near white pink ground, Liberation
Serif (metrically compatible with Times New Roman), small caps set as tracked
capitals, double rules. The fan on the card is not decoration: it is a real
conditional forecast produced by the same simulation as the exercise, run at the
reference stance under seed 20260724, so the share image is an output of the
model rather than an illustration of one.

Rendered at 2x and downsampled with Lanczos for crisp type at small display
sizes, which is where share cards actually get seen.
"""

import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import build_data as M

# Credit line printed on the plate variant. Fill this in with the rights holder
# and the terms under which the image is used before publishing.
PLATE_CREDIT = "PLATE: CREDIT LINE TO BE SUPPLIED, USED BY PERMISSION"
PLATE_SOURCE = "social-plate-source.jpg"

W, H = 1200, 630
S = 2                      # supersample factor
PAGE = (255, 248, 253)     # #fff8fd
INK = (36, 29, 38)         # #241d26
RULE = (156, 111, 134)     # #9c6f86
MUTED = (109, 90, 102)     # #6d5a66
BAND = (238, 216, 229)     # fan fill, flattened from the page rgba
MEDIAN = (138, 90, 114)    # #8a5a72

SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
ITALIC = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"


def font(path, size):
    return ImageFont.truetype(path, size * S)


def text_width(draw, s, f, track=0):
    if not track:
        return draw.textlength(s, font=f)
    return sum(draw.textlength(c, font=f) for c in s) + track * S * (len(s) - 1)


def tracked(draw, xy, s, f, fill, track=0, anchor_center=None):
    """Draw text with letter tracking. anchor_center: x centre in 1x units."""
    x, y = xy[0] * S, xy[1] * S
    if anchor_center is not None:
        x = anchor_center * S - text_width(draw, s, f, track) / 2
    if not track:
        draw.text((x, y), s, font=f, fill=fill)
        return
    for c in s:
        draw.text((x, y), c, font=f, fill=fill)
        x += draw.textlength(c, font=f) + track * S


def double_rule(draw, y, x0, x1, gap=4, w=1):
    for dy in (0, gap):
        draw.rectangle([x0 * S, (y + dy) * S, x1 * S, (y + dy) * S + w * S - 1], fill=RULE)


def reference_fan():
    """Quantiles of the red expenditure index at the reference stance."""
    rng = np.random.default_rng(M.SEED)
    X = M.BASE.copy().reshape(1, -1)
    Y = M.simulate(X, 6000, rng)
    ci = M.CH_KEYS.index("red_milex")
    q = np.quantile(Y[0, ci, :, :], [0.1, 0.5, 0.9], axis=1)
    lo = np.concatenate([[100.0], q[0]])
    md = np.concatenate([[100.0], q[1]])
    hi = np.concatenate([[100.0], q[2]])
    return lo, md, hi


def draw_fan(draw, box):
    """box: (x0, y0, x1, y1) in 1x units."""
    x0, y0, x1, y1 = box
    lo, md, hi = reference_fan()
    n = len(lo)
    ymin, ymax = 92.0, float(hi.max()) * 1.02
    xs = [x0 + (x1 - x0) * i / (n - 1) for i in range(n)]

    def py(v):
        return y1 - (v - ymin) / (ymax - ymin) * (y1 - y0)

    poly = [(xs[i] * S, py(hi[i]) * S) for i in range(n)] + \
           [(xs[i] * S, py(lo[i]) * S) for i in range(n - 1, -1, -1)]
    draw.polygon(poly, fill=BAND)

    # median, dotted in the manner of the page
    for i in range(n - 1):
        ax, ay, bx, by = xs[i], py(md[i]), xs[i + 1], py(md[i + 1])
        steps = 34
        for k in range(steps):
            if k % 2:
                continue
            t0, t1 = k / steps, (k + 0.85) / steps
            draw.line([((ax + (bx - ax) * t0) * S, (ay + (by - ay) * t0) * S),
                       ((ax + (bx - ax) * t1) * S, (ay + (by - ay) * t1) * S)],
                      fill=MEDIAN, width=2 * S)

    # period ticks on the baseline
    for i in range(n):
        draw.line([(xs[i] * S, y1 * S), (xs[i] * S, (y1 + 5) * S)], fill=RULE, width=1 * S)
    draw.line([(x0 * S, y1 * S), (x1 * S, y1 * S)], fill=RULE, width=1 * S)


def draw_plate(img, d, box):
    """Set the photograph as a framed plate, the way a typographic page carries
    a photographic figure: ruled frame, its own ground, a caption beneath."""
    x0, y0, x1, y1 = box
    side = min(x1 - x0, y1 - y0)
    src = Image.open(PLATE_SOURCE).convert("RGB")
    n = min(src.size)
    src = src.crop(((src.width - n) // 2, (src.height - n) // 2,
                    (src.width + n) // 2, (src.height + n) // 2))
    src = src.resize((side * S, side * S), Image.LANCZOS)
    img.paste(src, (x0 * S, y0 * S))
    d.rectangle([x0 * S, y0 * S, (x0 + side) * S - 1, (y0 + side) * S - 1],
                outline=RULE, width=1 * S)
    return x0 + side, y0 + side


def render_plate(w=W, h=H, out="social-card-plate.png"):
    if "TO BE SUPPLIED" in PLATE_CREDIT:
        print("WARNING: PLATE_CREDIT is still a placeholder. Set the rights holder")
        print("         and terms of use before publishing this variant.")
    img = Image.new("RGB", (w * S, h * S), PAGE)
    d = ImageDraw.Draw(img)

    ml, mr = 76, w - 76
    double_rule(d, 52, ml, mr)
    double_rule(d, 536, ml, mr)

    px1, py1 = draw_plate(img, d, (ml, 96, ml + 400, 496))

    f_credit = font(SERIF, 12)
    tracked(d, (ml, py1 + 10), PLATE_CREDIT, f_credit, MUTED, track=2)

    tx = px1 + 54
    f_eyebrow = font(SERIF, 18)
    f_title = font(SERIF, 62)
    f_sub = font(ITALIC, 23)
    f_rail = font(SERIF, 17)

    tracked(d, (tx, 128), "THE PRIMACY PREMIUM", f_eyebrow, MUTED, track=7)
    tracked(d, (tx, 166), "Committee", f_title, INK, track=1)
    tracked(d, (tx, 242), "Exercise", f_title, INK, track=1)
    tracked(d, (tx, 336), "Two sided conditional play on the", f_sub, MUTED)
    tracked(d, (tx, 368), "pathways question, 2026 to 2035", f_sub, MUTED)

    d.rectangle([tx * S, 420 * S, (tx + 120) * S, 420 * S + 1 * S - 1], fill=RULE)
    tracked(d, (tx, 438), "CONDITIONAL FORECASTING", f_rail, MUTED, track=5)
    tracked(d, (tx, 464), "UNDER SEALED SIMULTANEOUS PLAY", f_rail, MUTED, track=5)

    byline = "ALYSSA AGARD"
    bw = text_width(d, byline, f_rail, 6)
    tracked(d, (mr - bw / S, 560), byline, f_rail, MUTED, track=6)
    rail = "  ".join(["I", "II", "III", "IV", "V"])
    tracked(d, (ml, 560), rail, f_rail, RULE, track=6)

    img = img.resize((w, h), Image.LANCZOS)
    img.save(out, optimize=True)
    print(f"wrote {out} ({w}x{h})")


def render_photo(w=W, h=H, out="social-card-photo.png"):
    """The source photograph alone at share card dimensions, letterboxed onto its
    own ground so the full figure survives; scrapers crop, they do not letterbox."""
    src = Image.open(PLATE_SOURCE).convert("RGB")
    scale = h / src.height
    im = src.resize((int(src.width * scale), h), Image.LANCZOS)
    bg = Image.new("RGB", (w, h), src.getpixel((20, 20)))
    bg.paste(im, ((w - im.width) // 2, 0))
    bg.save(out, optimize=True)
    print(f"wrote {out} ({w}x{h})")


def render(w=W, h=H, out="social-card.png"):
    img = Image.new("RGB", (w * S, h * S), PAGE)
    d = ImageDraw.Draw(img)

    ml, mr = 76, w - 76
    f_eyebrow = font(SERIF, 19)
    f_title = font(SERIF, 82)
    f_sub = font(ITALIC, 27)
    f_small = font(SERIF, 17)
    f_rail = font(SERIF, 18)

    double_rule(d, 52, ml, mr)

    tracked(d, (0, 84), "THE PRIMACY PREMIUM", f_eyebrow, MUTED, track=7,
            anchor_center=w / 2)
    tracked(d, (0, 122), "Committee Exercise", f_title, INK, track=1,
            anchor_center=w / 2)
    tracked(d, (0, 232), "Two sided conditional play on the pathways question, 2026 to 2035",
            f_sub, MUTED, anchor_center=w / 2)

    draw_fan(d, (ml, 300, mr, 470))

    f_year = font(SERIF, 16)
    tracked(d, (ml, 480), "2025", f_year, MUTED, track=3)
    yw = text_width(d, "2035", f_year, 3)
    tracked(d, (mr - yw / S, 480), "2035", f_year, MUTED, track=3)

    tracked(d, (0, 486), "CONDITIONAL FORECAST AT THE REFERENCE STANCE", f_small, MUTED,
            track=5, anchor_center=w / 2)

    double_rule(d, 536, ml, mr)

    # period rail, left; byline, right
    rail = "  ".join(["I", "II", "III", "IV", "V"])
    tracked(d, (ml, 560), rail, f_rail, RULE, track=6)
    byline = "ALYSSA AGARD"
    bw = text_width(d, byline, f_rail, 6)
    tracked(d, (mr - bw / S, 560), byline, f_rail, MUTED, track=6)

    img = img.resize((w, h), Image.LANCZOS)
    img.save(out, optimize=True)
    print(f"wrote {out} ({w}x{h})")


if __name__ == "__main__":
    variant = sys.argv[1] if len(sys.argv) > 1 else "both"
    if variant in ("fan", "both"):
        render(1200, 630, "social-card.png")
    if variant in ("plate", "both"):
        render_plate(1200, 630, "social-card-plate.png")
    if variant in ("photo", "both"):
        render_photo(1200, 630, "social-card-photo.png")
