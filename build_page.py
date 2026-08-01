#!/usr/bin/env python3
"""
build_page.py
Injects payload.json into template.html and writes
index.html at the repository root.

"""

import json
import os
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE / "template.html"
PAYLOAD = HERE / "payload.json"
OUT = HERE / "index.html"
TOKEN = "/*__PAYLOAD__*/null"


def main():
    html = TEMPLATE.read_text(encoding="utf-8")
    payload = PAYLOAD.read_text(encoding="utf-8")
    if TOKEN not in html:
        raise SystemExit("payload token not found in template")
    if "</script" in payload.lower():
        raise SystemExit("payload contains a script terminator; refuse to inject")
    html = html.replace(TOKEN, payload, 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({os.path.getsize(OUT)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
