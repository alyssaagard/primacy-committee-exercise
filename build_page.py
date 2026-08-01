#!/usr/bin/env python3
"""
build_page.py
Injects payload.json and the site URL into template.html and writes
index.html at the repository root.

The site URL exists because Open Graph and Twitter card scrapers require
absolute URLs for og:image and og:url. Every other asset reference on the page
is relative, which is what keeps the site working under a GitHub Pages project
path; the share card tags are the one exception the specification forces.

Set the URL once below, or override at build time:

    SITE_URL=https://example.github.io/repo python3 build_page.py
"""

import os
import pathlib

# Edit this one line after creating the repository, or set the SITE_URL
# environment variable. No trailing slash.
SITE_URL = "https://USERNAME.github.io/primacy-committee-exercise"

# Which share card og:image points at. Both are built by build_social.py:
#   social-card-plate.png  the photographic plate
#   social-card.png        the conditional fan
SOCIAL_CARD = "social-card-photo.jpg"

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE / "template.html"
PAYLOAD = HERE / "payload.json"
OUT = HERE / "index.html"
TOKEN = "/*__PAYLOAD__*/null"
URL_TOKEN = "__SITE_URL__"
CARD_TOKEN = "__SOCIAL_CARD__"
TYPE_TOKEN = "__SOCIAL_CARD_TYPE__"


def main():
    site = os.environ.get("SITE_URL", SITE_URL).rstrip("/")
    if "USERNAME" in site:
        print("WARNING: SITE_URL is still a placeholder. Share cards will not")
        print("         resolve until you set it in build_page.py or the")
        print("         SITE_URL environment variable.")

    html = TEMPLATE.read_text(encoding="utf-8")
    payload = PAYLOAD.read_text(encoding="utf-8")
    if TOKEN not in html:
        raise SystemExit("payload token not found in template")
    if URL_TOKEN not in html:
        raise SystemExit("site url token not found in template")
    if CARD_TOKEN not in html:
        raise SystemExit("social card token not found in template")
    card = os.environ.get("SOCIAL_CARD", SOCIAL_CARD)
    if not (HERE / card).exists():
        raise SystemExit(f"share card missing: {card}. Run build_social.py first.")
    if "</script" in payload.lower():
        raise SystemExit("payload contains a script terminator; refuse to inject")

    html = html.replace(TOKEN, payload, 1)
    html = html.replace(URL_TOKEN, site)
    html = html.replace(CARD_TOKEN, card)
    mime = "image/jpeg" if card.lower().endswith((".jpg", ".jpeg")) else "image/png"
    html = html.replace(TYPE_TOKEN, mime)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({os.path.getsize(OUT)/1024:.0f} KB), site {site}, card {card}")


if __name__ == "__main__":
    main()
