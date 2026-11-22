#!/usr/bin/env python3
"""
tests/playthrough.py
Plays the built page from the opening screen to the debrief in several seat
configurations and fails on any console or page error.

Checks
1. Each configuration reaches the debrief.
2. The same seed and the same commitments give the same record.
3. A committee's commitment is realized exactly.
4. A declared demonstration is recorded in the declared year.

Requires playwright for Python and a Chromium or Chrome binary.

    python tests/playthrough.py [--shots DIR]

Environment: CHROME (browser path), PLOTLY_JS (local copy of plotly.min.js,
used when the content delivery network is unreachable).
"""

import argparse
import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright

PAGE = Path(__file__).resolve().parents[1] / "index.html"
SEATS = ["United States", "China", "NATO Europe", "Indo-Pacific allies"]
CONFIGS = {
    "us_alone": {"seats": [0], "rates": {0: 3.0}},
    "china_demonstration": {"seats": [1], "rates": {1: 6.0}, "event": 2029},
    "alliance_table": {"seats": [0, 2, 3], "rates": {0: -3.5, 2: 8.0, 3: 5.0}},
    "all_four": {"seats": [0, 1, 2, 3],
                 "rates": {0: 1.0, 1: 5.5, 2: 4.0, 3: 3.0}},
}


async def shot(pg, path, full=True):
    """Screenshot, then reset scroll: a full-page capture can leave the
    layout offset, which misplaces the next click."""
    await pg.screenshot(path=path, full_page=full)
    await pg.evaluate("window.scrollTo(0, 0)")


async def play(pg, name, cfg, shots, seed=20260724):
    await pg.goto(PAGE.as_uri())
    await pg.wait_for_selector("#convene")
    for i in range(4):
        want = "true" if i in cfg["seats"] else "false"
        card = pg.locator(f'.placard[data-seat="{i}"]')
        if await card.get_attribute("aria-pressed") != want:
            await card.click()
    await pg.fill("#seed", str(seed))
    if shots:
        await shot(pg, f"{shots}/{name}_0_front.png")
    await pg.click("#convene")
    for k in range(5):
        for n, seat in enumerate(cfg["seats"]):
            await pg.wait_for_selector("#commit")
            rate = cfg["rates"][seat]
            await pg.evaluate(
                "v => { const e = document.getElementById('g'); e.value = v;"
                " e.dispatchEvent(new Event('input')); }", rate)
            if cfg.get("event") and await pg.query_selector("#event"):
                opts = await pg.eval_on_selector_all(
                    "#event option", "o => o.map(x => x.value)")
                if str(cfg["event"]) in opts:
                    await pg.select_option("#event", str(cfg["event"]))
            if shots and k in (0, 1) and n == 0:
                await pg.wait_for_timeout(400)
                await shot(pg, f"{shots}/{name}_{k + 1}_seat.png")
            await pg.click("#commit")
            if len(cfg["seats"]) > 1:
                await pg.wait_for_selector("#handoff.active")
                if shots and k == 0 and n == 0:
                    await shot(pg, f"{shots}/{name}_handoff.png", False)
                await pg.click("#handoff-btn")
        if k < 4:
            await pg.wait_for_selector("#next")
            if shots and k == 1:
                await pg.wait_for_timeout(1300)
                await shot(pg, f"{shots}/{name}_resolution.png")
            await pg.click("#next")
            if len(cfg["seats"]) > 1:
                await pg.click("#handoff-btn")
    await pg.click("#unseal")
    await pg.wait_for_selector("#save")
    if shots:
        await pg.wait_for_timeout(900)
        await shot(pg, f"{shots}/{name}_debrief.png")
    return await pg.evaluate(
        "() => { const g = CX.game; return JSON.stringify({"
        " growth: Object.fromEntries(Object.keys(g.recs).map(y => [y, g.recs[y].g])),"
        " usd: g.q[37].usd, event: g.states[2035].eventYear, scores: g.scores }); }")


async def main(shots):
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(
            executable_path=os.environ.get("CHROME") or None,
            args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 1280, "height": 900})
        pg.on("console", lambda m: errors.append(m.text)
              if m.type == "error" else None)
        pg.on("pageerror", lambda e: errors.append(f"page error: {e}"))
        local = os.environ.get("PLOTLY_JS")
        if local:
            async def route(r):
                if "plotly" in r.request.url:
                    await r.fulfill(path=local,
                                    content_type="application/javascript")
                else:
                    await r.abort()
            await pg.route("https://**", route)
        for name, cfg in CONFIGS.items():
            first = json.loads(await play(pg, name, cfg, shots))
            again = json.loads(await play(pg, name, cfg, None))
            assert first == again, f"{name}: record not reproducible"
            for seat, rate in cfg["rates"].items():
                for y in range(2027, 2036):
                    got = first["growth"][str(y)][SEATS[seat]]
                    assert got == rate, f"{name}: {SEATS[seat]} {y} {got}"
            if cfg.get("event"):
                assert first["event"] == cfg["event"], f"{name}: event year"
            other = json.loads(await play(pg, name, cfg, None, seed=7))
            assert other["usd"] != first["usd"], f"{name}: seed has no effect"
            print(f"{name}: debrief reached; reproducible; "
                  f"USD share 2035-Q4 {first['usd']:.2f}")
        if shots:      # narrow viewport
            await pg.set_viewport_size({"width": 390, "height": 800})
            await play(pg, "narrow", CONFIGS["us_alone"], shots)
        await b.close()
    if errors:
        raise SystemExit("console errors:\n" + "\n".join(errors[:20]))
    print("no console errors")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots")
    a = ap.parse_args()
    if a.shots:
        Path(a.shots).mkdir(parents=True, exist_ok=True)
    asyncio.run(main(a.shots))
