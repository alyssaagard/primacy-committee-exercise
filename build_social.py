#!/usr/bin/env python3
"""
build_social.py
Renders the share image from social-plate-source.jpg.

    social-card-photo.jpg    1200 x 630, the image the share tags point at
    social-card-github.png   1280 x 640, for the repository social preview

The source is scaled to the card height and centered on a ground sampled
from its own background, so the whole image is kept. The JPEG is saved
under 290 KB because some scrapers drop larger images.

Run: python build_social.py
"""

from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "social-plate-source.jpg"


def card(w: int, h: int) -> Image.Image:
    src = Image.open(SOURCE).convert("RGB")
    im = src.resize((round(src.width * h / src.height), h), Image.LANCZOS)
    bg = Image.new("RGB", (w, h), src.getpixel((20, 20)))
    bg.paste(im, ((w - im.width) // 2, 0))
    return bg


def main() -> None:
    jpg = HERE / "social-card-photo.jpg"
    img = card(1200, 630)
    for q in (88, 82, 76, 70, 64):
        img.save(jpg, quality=q, optimize=True, progressive=True)
        if jpg.stat().st_size < 290_000:
            break
    print(f"{jpg.name} written, {jpg.stat().st_size // 1024} KB, quality {q}")
    png = HERE / "social-card-github.png"
    card(1280, 640).save(png, optimize=True)
    print(f"{png.name} written, {png.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
