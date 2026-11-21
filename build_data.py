#!/usr/bin/env python3
"""
build_data.py
Stage 1. Model inputs and exercise constants.

The exercise runs the estimated model of The Primacy Premium, release
1.1.0. This script copies the quantities the engine needs from a checkout
of that repository into model_inputs.json, then combines them with the
exercise design constants into payload.json.

    python build_data.py --model ../primacy-premium   refresh model_inputs.json
    python build_data.py                              rebuild payload.json only

Nothing is estimated here. Every coefficient, covariance matrix, residual
pool, and base level is read from the model outputs. The design constants
defined in this file (seats, periods, commitment bounds, priors, interval
coverage, objectives) are choices of the exercise, and METHOD.md lists
them as such.

Writes: model_inputs.json (with --model), payload.json
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

BLOCKS = ["United States", "China", "Indo-Pacific allies", "NATO Europe",
          "Hedging middle powers", "Rest of world"]
ALLIED = ["Indo-Pacific allies", "NATO Europe", "Hedging middle powers"]
SEATS = ["United States", "China", "NATO Europe", "Indo-Pacific allies"]
PATHWAYS = ["accretion", "retrenchment", "demonstration"]

# ---------------------------------------------------------------- design
START_YEAR = 2026          # first simulated year; run by the model for all
PERIODS = [                # years each commitment governs
    {"roman": "I", "years": [2027, 2028]},
    {"roman": "II", "years": [2029, 2030]},
    {"roman": "III", "years": [2031, 2032]},
    {"roman": "IV", "years": [2033, 2034]},
    {"roman": "V", "years": [2035]},
]
BOUND_QUANTILES = (0.05, 0.95)   # commitment range, own observed growth
BOUND_SAMPLE = (1993, 2025)
STEP = 0.5                       # commitment increment, percentage points
COVERAGE = 0.80                  # nominal coverage of stated intervals
STAFF_DRAWS = 2_000              # draws behind each staff estimate
REFERENCE_DRAWS = 50_000
RESOURCE_QUANTILE = 0.75         # resource limit, reference distribution
HISTORY_FROM = 2010


def r(x, n=6):
    return round(float(x), n)


def vendor(model: Path) -> dict:
    """Read the model outputs. Requires pandas and the model's own modules."""
    import pandas as pd
    sys.path.insert(0, str(model / "src"))
    from tiers import growth_table, level_table  # noqa: E402

    out = model / "outputs"
    cal1 = json.loads((out / "calibration.json").read_text())
    cal2 = json.loads((out / "calibration_layer2.json").read_text())
    sim1 = json.loads((out / "simulation_summary.json").read_text())
    sim2 = json.loads((out / "layer2_summary.json").read_text())
    commit = subprocess.run(["git", "-C", str(model), "rev-parse", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    version = "1.1.0"
    for line in (model / "CITATION.cff").read_text().splitlines():
        if line.startswith("version:"):
            version = line.split(":", 1)[1].strip().strip('"')

    levels = level_table()
    growth = growth_table()
    base_year = int(levels[BLOCKS].dropna().index.max())
    hist = levels.loc[HISTORY_FROM:base_year, BLOCKS]
    g_hist = growth.loc[HISTORY_FROM:base_year, BLOCKS]

    lo, hi = BOUND_SAMPLE
    bounds = {}
    for s in SEATS:
        q = growth.loc[lo:hi, s].quantile(list(BOUND_QUANTILES))
        bounds[s] = [r(q.iloc[0], 3), r(q.iloc[1], 3)]

    pools = pd.read_csv(out / "layer2_residual_pools.csv")
    wide = pools.pivot_table("resid", "year", "block")[BLOCKS].sort_index()

    def tier(t):
        f = cal2["feedback"][t]
        order = [f["cov_names"].index(k) for k in ["const", "us_lag", "cn_lag"]]
        cov = [[r(f["cov"][i][j], 10) for j in order] for i in order]
        return {"mean": [f["b0"], f["b_us"], f["b_cn"]], "cov": cov,
                "se": [r(cov[i][i] ** 0.5, 3) for i in range(3)],
                "r2": f["r2"], "nobs": f["nobs"], "sample": f["sample"],
                "breusch_godfrey_p": f["breusch_godfrey_p"]}

    def reg(key):
        g = cal1[key]
        idx = [g["cov_names"].index(k) for k in ["const", "x_ratio"]]
        cov = [[r(g["cov"][i][j], 12) for j in idx] for i in idx]
        return {"mean": [r(g["params"]["const"], 8),
                         r(g["params"]["x_ratio"], 8)],
                "cov": cov, "se": [r(g["bse"]["const"], 4),
                                   r(g["bse"]["x_ratio"], 4)],
                "r2": r(g["r2"], 4), "nobs": g["nobs"]}

    inn = pd.read_csv(out / "innovation_pools.csv")
    cases, regimes = cal1["cases"], cal1["cases"]["drift_regimes"]
    shares = pd.read_csv(model / "data" / "processed" / "cofer_shares_wide.csv")
    shares = shares[shares.quarter >= f"{HISTORY_FROM}-Q1"]
    h2 = cal2["h2"]["primary"]

    return {
        "source": {"repository": "https://github.com/alyssaagard/primacy-premium",
                   "version": version, "commit": commit,
                   "built": cal1["meta"]["built"]},
        "seed": sim2["seed"],
        "blocks": BLOCKS, "allied": ALLIED,
        "base_year": base_year,
        "base": {b: r(levels.loc[base_year, b], 1) for b in BLOCKS},
        "history": {"years": [int(y) for y in hist.index],
                    "levels": {b: [r(v, 1) for v in hist[b]] for b in BLOCKS},
                    "growth": {b: [r(v, 3) for v in g_hist[b]] for b in BLOCKS}},
        "bounds_observed": bounds,
        "rates": {
            "us_trend": r(cases["accretion_decade"]["usa"], 4),
            "cn_trend": r(cases["accretion_decade"]["china"], 4),
            "trend_window": [cases["accretion_decade"]["start_year"],
                             cases["accretion_decade"]["end_year"]],
            "us_contraction": r(cases["peace_dividend"]["annual_rate_pct"], 4),
            "row_mean": cal2["principal_blocks"]["Rest of world"]["mean_last10"],
            "us_last": cal2["principal_blocks"]["United States"]["last_year_growth"],
            "cn_last": cal2["principal_blocks"]["China"]["last_year_growth"],
        },
        "feedback": {t: tier(t) for t in ALLIED},
        "mobilization": {t: cal2["demonstration_mobilization_2022"][t]["delta_pp"]
                         for t in ALLIED},
        "decay_years": 4,
        "event_years": [2028, 2031],
        "mean_run_years": sim2["mean_block_length_years"],
        "resid": {"years": [int(y) for y in wide.index],
                  "rows": [[r(v, 4) for v in row] for row in wide.to_numpy()]},
        "reserve": {
            "last_quarter": cal1["latest_state"]["quarter"],
            "usd0": r(cal1["latest_state"]["usd_share"], 4),
            "cny0": r(cal1["latest_state"]["cny_share"], 4),
            "usd": reg("usd_regression"), "cny": reg("cny_regression"),
            "usd_resid": [r(v, 5) for v in inn.usd_resid.dropna()],
            "cny_resid": [r(v, 6) for v in inn.cny_resid_logit.dropna()],
            "usd_jumps": cases["sanctions_2022"]["d_usd"],
            "cny_jumps": cases["sanctions_2022"]["d_cny_logit"],
            "usd_shift": r(regimes["usd_post"] - regimes["usd_pre"], 6),
            "cny_shift": r(regimes["cny_post_logit"]
                           - regimes["cny_pre_logit"], 6),
            "history": {"quarters": shares.quarter.tolist(),
                        "usd": [r(v, 3) for v in shares.USD],
                        "cny": [None if v != v else r(v, 3)
                                for v in shares.CNY]},
        },
        "war_risk_multiple": sim2["war_risk_event_multiplier"],
        "h2": {"b_us": h2["b_us"], "b_cn": h2["b_cn"],
               "p_one_sided": h2["p_one_sided"],
               "verdict": cal2["h2"]["verdict"]},
        "published": {
            "draws": sim2["draws"],
            "endpoints_musd": {p: {b: sim2["endpoints_musd"][p][b]["median"]
                                   for b in BLOCKS} for p in PATHWAYS},
            "allied_share": {p: sim2["allied_share"][p]["median"]
                             for p in PATHWAYS},
            "usd": {p: r(sim1["usd"][p]["median"], 3) for p in PATHWAYS},
            "cny": {p: r(sim1["cny"][p]["median"], 3) for p in PATHWAYS},
        },
    }


def round_out(lo: float, hi: float) -> list:
    """Round a range outward to the commitment increment."""
    import math
    return [math.floor(lo / STEP) * STEP, math.ceil(hi / STEP) * STEP]


def design(m: dict) -> dict:
    rates = m["rates"]
    us_mid = (rates["us_trend"] + rates["us_contraction"]) / 2
    ratio = {"measure": "cn_us", "dp": 3,
             "label": "China to United States expenditure ratio, 2035"}
    coal = {"measure": "coalition_cn", "op": ">=", "dp": 2,
            "label": "Coalition to China expenditure ratio, 2035"}
    burden = {"measure": "us_share_coalition", "op": ">=", "dp": 1,
              "label": "United States share of coalition expenditure, "
                       "2035, percent"}
    allied_goal = ("{} to keep the coalition's expenditure margin over "
                   "China while the United States continues to carry its "
                   "share.")
    seats = {
        "United States": {
            "code": "us",
            "goal": "The United States seeks to retain its expenditure "
                    "margin over China and the reserve position of the "
                    "dollar.",
            "refs": [["Ten-year rate", rates["us_trend"]],
                     ["1988 to 1998 rate", rates["us_contraction"]],
                     ["No real change", 0.0]],
            "objectives": [
                dict(ratio, op="<="),
                {"measure": "usd", "op": ">=", "dp": 2,
                 "label": "US dollar reserve share, 2035-Q4, percent"}]},
        "China": {
            "code": "cn",
            "goal": "China seeks to close the expenditure gap with the "
                    "United States and to raise the reserve role of the "
                    "renminbi.",
            "refs": [["Ten-year rate", rates["cn_trend"]],
                     ["2025 rate", rates["cn_last"]],
                     ["No real change", 0.0]],
            "objectives": [
                dict(ratio, op=">="),
                {"measure": "cny", "op": ">=", "dp": 2,
                 "label": "Renminbi reserve share, 2035-Q4, percent"}]},
        "NATO Europe": {"code": "eu", "refs": [],
                        "goal": allied_goal.format("NATO Europe seeks"),
                        "objectives": [coal, burden]},
        "Indo-Pacific allies": {"code": "ip", "refs": [],
                                "goal": allied_goal.format(
                                    "The Indo-Pacific allies seek"),
                                "objectives": [coal, burden]},
    }
    hist = m["history"]
    for s, d in seats.items():
        d["bounds"] = round_out(*m["bounds_observed"][s])
        y = hist["years"]
        i0, i1 = y.index(rates["trend_window"][0]), y.index(rates["trend_window"][1])
        lv = hist["levels"][s]
        trend = 100 * ((lv[i1] / lv[i0]) ** (1 / (i1 - i0)) - 1)
        if s in ("NATO Europe", "Indo-Pacific allies"):
            d["refs"] = [["Ten-year rate", round(trend, 2)],
                         ["2025 rate", hist["growth"][s][-1]],
                         ["No real change", 0.0]]
        d["refs"] = [[k, round(v, 2)] for k, v in d["refs"]
                     if d["bounds"][0] <= v <= d["bounds"][1]]
    return {
        "seats": seats, "seat_order": SEATS,
        "start_year": START_YEAR, "horizon": PERIODS[-1]["years"][-1],
        "periods": PERIODS, "step": STEP,
        "coverage": COVERAGE, "resource_quantile": RESOURCE_QUANTILE,
        "staff_draws": STAFF_DRAWS, "reference_draws": REFERENCE_DRAWS,
        "pathway_prior": {p: round(1 / 3, 6) for p in PATHWAYS},
        "us_midpoint": round(us_mid, 4),
        "bound_rule": {"quantiles": list(BOUND_QUANTILES),
                       "sample": list(BOUND_SAMPLE)},
        "coalition": ["United States", "NATO Europe", "Indo-Pacific allies"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path,
                    help="path to a primacy-premium checkout")
    args = ap.parse_args()
    inputs = HERE / "model_inputs.json"
    if args.model:
        inputs.write_text(json.dumps(vendor(args.model.resolve()), indent=1)
                          + "\n")
        print(f"model_inputs.json refreshed from {args.model}")
    m = json.loads(inputs.read_text())
    payload = {
        "meta": {"title": "Committee Exercise", "series": "The Primacy Premium",
                 "author": "Alyssa I. Agard", "license": "CC BY-NC 4.0",
                 "seed": m["seed"], "built": m["source"]["built"]},
        "model": m, "design": design(m),
    }
    (HERE / "payload.json").write_text(
        json.dumps(payload, separators=(",", ":")) + "\n")
    print(f"payload.json written, "
          f"{(HERE / 'payload.json').stat().st_size / 1024:.0f} KB; "
          f"model {m['source']['version']} at {m['source']['commit'][:7]}")


if __name__ == "__main__":
    main()
