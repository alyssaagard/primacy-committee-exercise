#!/usr/bin/env python3
"""
build_page.py
Stage 3. Assembles index.html.

Inlines engine.js, payload.json, and reference.json into template.html, and
sets the absolute site address that share card tags require. All other
asset references on the page are relative.

    python build_page.py
    SITE_URL=https://example.org/exercise python build_page.py

Writes: index.html
"""

import os
from pathlib import Path

SITE_URL = "https://alyssaagard.github.io/primacy-committee-exercise"
SOCIAL_CARD = "social-card.png"

HERE = Path(__file__).resolve().parent
TOKENS = {
    "/*__ENGINE__*/": "engine.js",
    "/*__PAYLOAD__*/null": "payload.json",
    "/*__REFERENCE__*/null": "reference.json",
}


def main() -> None:
    html = (HERE / "template.html").read_text(encoding="utf-8")
    for token, name in TOKENS.items():
        if html.count(token) != 1:
            raise SystemExit(f"token for {name} not found exactly once")
        text = (HERE / name).read_text(encoding="utf-8").strip()
        if "</script" in text.lower():
            raise SystemExit(f"{name} contains a script terminator")
        html = html.replace(token, text)
    site = os.environ.get("SITE_URL", SITE_URL).rstrip("/")
    card = os.environ.get("SOCIAL_CARD", SOCIAL_CARD)
    if not (HERE / card).exists():
        raise SystemExit(f"share card missing: {card}. Run build_social.py.")
    mime = "image/jpeg" if card.lower().endswith((".jpg", ".jpeg")) else "image/png"
    html = (html.replace("__SITE_URL__", site)
                .replace("__SOCIAL_CARD_TYPE__", mime)
                .replace("__SOCIAL_CARD__", card))
    out = HERE / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"index.html written, {out.stat().st_size / 1024:.0f} KB; "
          f"site {site}; card {card}")


if __name__ == "__main__":
    main()
