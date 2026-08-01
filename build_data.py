#!/usr/bin/env python3
"""
build_data.py
The Primacy Premium: Committee Exercise, data build stage.

Produces payload.json: the emulator coefficients, simulation constants,
move menus, thresholds, and validation metrics consumed by index.html.

Design notes
------------
1. Every player move maps to a level of a named simulation parameter, not to a
   hardcoded outcome. Moves condition the forecast; they do not cause it.
2. Conditional quantile fans are produced by a fitted emulator (degree two
   polynomial response surface) trained on a Sobol design over the joint
   parameter space, 4096 points, 320 stochastic draws per point, seed 20260724.
3. The in-page resolution path is a single draw of the same generative process,
   replicated exactly in JavaScript from the constants exported here. The
   emulator serves the fans; the recursion serves the realization. Held-out
   emulator error is reported in the payload and displayed on the page.
4. Raw SIPRI and IMF files are excluded from the repository under publisher
   terms. Calibration anchors below were verified against local copies of:
     SIPRIMilexdata19492025_v1.2.xlsx (Constant 2024 USD sheet)
     IMF COFER bulk download of 24 July 2026 (quarterly share series)
     Argus Media explainer on war risk insurance and AWRP (March 2026)
     JWC circular JWLA-033 of 3 March 2026
     Kristensen et al., Nuclear Notebooks 2025 and 2026; DoD CMPR 2025
   This script does not read those files at runtime.

Anchors (verified 2026-08-01)
-----------------------------
US milex 2025:   929.2 bn constant 2024 USD, real change 2024 to 2025 about -7.5 pct
China milex 2025: 335.0 bn constant 2024 USD, real change about +7.4 pct
C&W Europe 2025: 579.8 bn constant 2024 USD, real change about +6.0 pct
USD share of allocated reserves 2025-Q4: 56.42 pct (2021-Q4: 59.40; 2016-Q4: 64.68)
RMB share 2025-Q4: 1.95 pct (peak 2021-Q4: 2.85, declining since)
Mideast Gulf AWRP: 0.15 to 0.20 pct of hull and machinery value at baseline,
  rising to about 1 pct during the 2026 episode (roughly a fivefold move)
China warheads about 600 in 2025; DoD projects over 1000 by 2030 and about
  1500 by 2035. US deployed strategic about 1550 at New START expiry, with
  upload capacity; the treaty lapsed 4 February 2026 with no successor, so the
  denominator is treated as stochastic.
"""

import json
import datetime as _dt
import numpy as np

SEED = 20260724
N_DESIGN = 4096
N_DRAWS = 320
HOLDOUT = 0.2
EPOCHS = ["2026 to 2027", "2028 to 2029", "2030 to 2031", "2032 to 2033", "2034 to 2035"]
T = len(EPOCHS)

# ---------------------------------------------------------------------------
# Parameter space. Order is load bearing: the emulator feature construction in
# JavaScript replicates this order exactly.
# ---------------------------------------------------------------------------
PARAMS = [
    # key, label, side, lo, hi, base
    ("b_force",      "Force structure allocation (strategic forces to shipbuilding)", "blue", -1.0, 1.0, 0.0),
    ("b_alliance",   "Alliance burden sharing pressure",                              "blue",  0.0, 1.0, 0.5),
    ("b_export",     "Transfer policy (tighten controls to expand transfers)",        "blue", -1.0, 1.0, 0.0),
    ("b_posture",    "Forward posture at chokepoints",                                "blue",  0.0, 1.0, 0.5),
    ("b_industrial", "Industrial mobilization",                                       "blue",  0.0, 1.0, 0.5),
    ("r_naval",      "Naval construction tempo",                                      "red",   0.0, 1.0, 0.5),
    ("r_nuclear",    "Nuclear expansion tempo",                                       "red",   0.0, 1.0, 0.5),
    ("r_gray",       "Chokepoint pressure",                                           "red",   0.0, 1.0, 0.5),
    ("r_findiv",     "Reserve diversification drive",                                 "red",   0.0, 1.0, 0.5),
    ("r_export",     "Arms export drive",                                             "red",   0.0, 1.0, 0.5),
    ("g_fiscal",     "Blue fiscal headroom",                                          "world", -1.0, 1.0, 0.0),
    ("g_euro",       "European follow through on the five percent commitment",        "world",  0.0, 1.0, 0.5),
    ("g_shock",      "Global shock propensity",                                       "world",  0.0, 1.0, 0.5),
    ("g_growth",     "Red macroeconomic tailwind",                                    "world", -1.0, 1.0, 0.0),
]
P = len(PARAMS)
KEYS = [p[0] for p in PARAMS]
LO = np.array([p[3] for p in PARAMS])
HI = np.array([p[4] for p in PARAMS])
BASE = np.array([p[5] for p in PARAMS])
IX = {k: i for i, k in enumerate(KEYS)}

# ---------------------------------------------------------------------------
# Simulation constants. Exported verbatim to the payload; the JavaScript
# resolution recursion reads these same numbers.
# ---------------------------------------------------------------------------
C = {
    # Initial state, end 2025
    "y0": {
        "blue_milex": 100.0,   # index, 2025 = 100 (929.2 bn constant 2024 USD)
        "red_milex": 100.0,    # index, 2025 = 100 (335.0 bn)
        "euro_milex": 100.0,   # index, 2025 = 100 (C&W Europe 579.8 bn)
        "usd_share": 56.42,    # pct of allocated reserves, 2025-Q4
        "rmb_share": 1.95,     # pct, 2025-Q4
        "awrp": 0.175,         # pct of hull and machinery value, pre-episode midpoint
        "red_export": 5.5,     # pct of world major arms exports, trend basis
        "red_wh": 600.0,       # red warheads, 2025
        "blue_dep": 1550.0,    # blue deployed strategic, treaty-era counting
    },
    # Blue expenditure, annual real growth
    "bx_a": -0.020, "bx_fiscal": 0.016, "bx_ind": 0.014, "bx_post": 0.006, "bx_sd": 0.016,
    # Red expenditure, annual real growth
    "rx_a": 0.050, "rx_naval": 0.022, "rx_nuc": 0.012, "rx_growth": 0.018, "rx_sd": 0.020,
    # European expenditure, annual real growth
    "ex_a": 0.018, "ex_euro": 0.052, "ex_all": 0.014, "ex_sd": 0.020,
    # Episode hazard per epoch (chokepoint disruption with premium spike)
    "hz_a": 0.05, "hz_gray": 0.40, "hz_shock": 0.20, "hz_post": -0.14, "hz_int": 0.12,
    "hz_lo": 0.02, "hz_hi": 0.92,
    # War risk premium, log AR(1) around baseline with episode jumps
    "aw_phi": 0.35, "aw_sd": 0.12, "aw_jump_a": 0.85, "aw_jump_gray": 0.55, "aw_jump_sd": 0.15,
    "aw_lo": 0.05, "aw_hi": 3.0,
    # USD share of allocated reserves, per-epoch drift in points
    "us_a": -0.40, "us_findiv": -0.75, "us_ep": -0.45, "us_sd": 0.30, "us_lo": 45.0, "us_hi": 62.0,
    # RMB share, per-epoch drift in points
    "rm_a": -0.05, "rm_findiv": 0.42, "rm_ep": 0.18, "rm_sd": 0.10, "rm_lo": 1.2, "rm_hi": 6.5,
    # Red arms export share, per-epoch drift in points
    "re_a": 0.15, "re_drive": 1.05, "re_bexp": -0.40, "re_btight": 0.15, "re_ep": -0.55,
    "re_sd": 0.30, "re_lo": 2.0, "re_hi": 14.0,
    # Red warheads, annual growth
    "nw_a": 0.055, "nw_tempo": 0.065, "nw_sd": 0.006,
    # Blue deployed strategic per epoch: upload plus post-treaty drift
    "nd_upload": 95.0, "nd_sd": 45.0, "nd_lo": 1400.0, "nd_hi": 2600.0,
}

CHANNELS = [
    ("blue_milex", "Blue military expenditure",  "index, 2025 = 100", 1, "flash"),
    ("red_milex",  "Red military expenditure",   "index, 2025 = 100", 1, "flash"),
    ("euro_milex", "European expenditure",       "index, 2025 = 100", 1, "flash"),
    ("usd_share",  "USD reserve share",          "pct of allocated reserves", 1, "slow"),
    ("rmb_share",  "RMB reserve share",          "pct of allocated reserves", 2, "slow"),
    ("awrp",       "Additional war risk premium","pct of hull and machinery value", 2, "fast"),
    ("red_export", "Red arms export share",      "pct of world exports", 1, "slow"),
    ("nuc_ratio",  "Warhead ratio, red to blue deployed", "ratio", 2, "slow"),
]
CH_KEYS = [c[0] for c in CHANNELS]
NC = len(CHANNELS)
QUANTS = [0.1, 0.5, 0.9]


def simulate(X, n_draws, rng):
    """Vectorized simulation. X: (n, P) parameter matrix, horizon-constant.
    Returns Y: (n, NC, T, n_draws)."""
    n = X.shape[0]
    g = {k: X[:, IX[k]][:, None] for k in KEYS}  # (n,1) broadcast against draws
    N = lambda sd: rng.normal(0.0, sd, size=(n, n_draws))
    U = lambda: rng.random(size=(n, n_draws))

    blue = np.full((n, n_draws), C["y0"]["blue_milex"])
    red = np.full((n, n_draws), C["y0"]["red_milex"])
    euro = np.full((n, n_draws), C["y0"]["euro_milex"])
    usd = np.full((n, n_draws), C["y0"]["usd_share"])
    rmb = np.full((n, n_draws), C["y0"]["rmb_share"])
    law = np.full((n, n_draws), np.log(C["y0"]["awrp"]))
    rex = np.full((n, n_draws), C["y0"]["red_export"])
    wh = np.full((n, n_draws), C["y0"]["red_wh"])
    dep = np.full((n, n_draws), C["y0"]["blue_dep"])

    out = np.empty((n, NC, T, n_draws))
    base_law = np.log(C["y0"]["awrp"])

    for t in range(T):
        # Episode draw for this epoch
        hz = np.clip(C["hz_a"] + C["hz_gray"] * g["r_gray"] + C["hz_shock"] * g["g_shock"]
                     + C["hz_post"] * g["b_posture"]
                     + C["hz_int"] * g["r_gray"] * (1.0 - g["b_posture"]),
                     C["hz_lo"], C["hz_hi"])
        ep = (U() < hz).astype(float)

        gb = (C["bx_a"] + C["bx_fiscal"] * g["g_fiscal"] + C["bx_ind"] * g["b_industrial"]
              + C["bx_post"] * g["b_posture"])
        blue = blue * (1.0 + gb) ** 2 * np.exp(N(C["bx_sd"]))

        gr = (C["rx_a"] + C["rx_naval"] * g["r_naval"] + C["rx_nuc"] * g["r_nuclear"]
              + C["rx_growth"] * g["g_growth"])
        red = red * (1.0 + gr) ** 2 * np.exp(N(C["rx_sd"]))

        ge = C["ex_a"] + C["ex_euro"] * g["g_euro"] + C["ex_all"] * g["b_alliance"]
        euro = euro * (1.0 + ge) ** 2 * np.exp(N(C["ex_sd"]))

        usd = np.clip(usd + C["us_a"] + C["us_findiv"] * g["r_findiv"] + C["us_ep"] * ep
                      + N(C["us_sd"]), C["us_lo"], C["us_hi"])
        rmb = np.clip(rmb + C["rm_a"] + C["rm_findiv"] * g["r_findiv"] + C["rm_ep"] * ep
                      + N(C["rm_sd"]), C["rm_lo"], C["rm_hi"])

        law = base_law + C["aw_phi"] * (law - base_law) + N(C["aw_sd"])
        jump = np.log(C["aw_jump_a"] + C["aw_jump_gray"] * g["r_gray"]) + N(C["aw_jump_sd"])
        law = np.where(ep > 0.5, np.maximum(law, jump), law)
        awrp = np.clip(np.exp(law), C["aw_lo"], C["aw_hi"])
        law = np.log(awrp)

        rex = np.clip(rex + C["re_a"] + C["re_drive"] * g["r_export"]
                      + C["re_bexp"] * np.maximum(g["b_export"], 0.0)
                      + C["re_btight"] * np.maximum(-g["b_export"], 0.0)
                      + C["re_ep"] * ep + N(C["re_sd"]), C["re_lo"], C["re_hi"])

        gn = C["nw_a"] + C["nw_tempo"] * g["r_nuclear"] + N(C["nw_sd"])
        wh = wh * (1.0 + gn) ** 2
        dep = np.clip(dep + C["nd_upload"] * np.maximum(-g["b_force"], 0.0)
                      + N(C["nd_sd"]), C["nd_lo"], C["nd_hi"])

        out[:, 0, t, :] = blue
        out[:, 1, t, :] = red
        out[:, 2, t, :] = euro
        out[:, 3, t, :] = usd
        out[:, 4, t, :] = rmb
        out[:, 5, t, :] = awrp
        out[:, 6, t, :] = rex
        out[:, 7, t, :] = wh / dep
    return out


def poly2_features(X01):
    """Degree two polynomial features on parameters scaled to [0,1].
    Order: bias, linear, squares, pairwise products (i < j). Mirrored in JS."""
    n, p = X01.shape
    cols = [np.ones((n, 1)), X01, X01 ** 2]
    for i in range(p):
        for j in range(i + 1, p):
            cols.append((X01[:, i] * X01[:, j])[:, None])
    return np.hstack(cols)


def main():
    rng = np.random.default_rng(SEED)
    try:
        from scipy.stats import qmc
        X01 = qmc.Sobol(d=P, scramble=True, seed=SEED).random(N_DESIGN)
        design_kind = "Sobol, scrambled"
    except Exception:
        X01 = rng.random((N_DESIGN, P))
        perm = np.argsort(rng.random((N_DESIGN, P)), axis=0)
        X01 = (perm + X01) / N_DESIGN
        design_kind = "Latin hypercube"
    X = LO + X01 * (HI - LO)

    print(f"design: {design_kind}, {N_DESIGN} points, {N_DRAWS} draws, seed {SEED}")
    Y = simulate(X, N_DRAWS, rng)                       # (n, NC, T, draws)
    Q = np.quantile(Y, QUANTS, axis=3)                  # (3, n, NC, T)
    n_targets = NC * T * len(QUANTS)
    target_index = []
    Ymat = np.empty((N_DESIGN, n_targets))
    k = 0
    for ci in range(NC):
        for t in range(T):
            for qi, q in enumerate(QUANTS):
                Ymat[:, k] = Q[qi, :, ci, t]
                target_index.append({"c": CH_KEYS[ci], "e": t, "q": q})
                k += 1

    Phi = poly2_features(X01)
    n_tr = int(N_DESIGN * (1 - HOLDOUT))
    order = rng.permutation(N_DESIGN)
    tr, te = order[:n_tr], order[n_tr:]
    B, *_ = np.linalg.lstsq(Phi[tr], Ymat[tr], rcond=None)   # (features, targets)
    pred = Phi[te] @ B
    resid = pred - Ymat[te]

    val = {}
    for ci, ck in enumerate(CH_KEYS):
        cols = [i for i, ti in enumerate(target_index) if ti["c"] == ck]
        y = Ymat[np.ix_(te, cols)]
        r = resid[:, cols]
        ss_res = (r ** 2).sum(axis=0)
        ss_tot = ((y - y.mean(axis=0)) ** 2).sum(axis=0)
        r2 = 1 - ss_res / ss_tot
        rmse = np.sqrt((r ** 2).mean(axis=0))
        val[ck] = {"r2_median": round(float(np.median(r2)), 4),
                   "r2_min": round(float(r2.min()), 4),
                   "rmse_median": round(float(np.median(rmse)), 4),
                   "rmse_max": round(float(rmse.max()), 4)}
        print(f"  {ck:11s} R2 med {val[ck]['r2_median']:.3f} min {val[ck]['r2_min']:.3f} "
              f"RMSE med {val[ck]['rmse_median']:.3f}")
    overall_r2 = round(float(np.median([v["r2_median"] for v in val.values()])), 4)

    # Move menus. Each level is a stance value of the named parameter; cost is
    # the commitment expenditure tallied in the debrief.
    def menu(key, levels):
        return {"param": key, "levels": [
            {"label": lab, "value": v, "cost": c, "brief": b} for lab, v, c, b in levels]}

    moves = {
        "blue": [
            {"key": "b_force", "label": "Force structure allocation", **menu("b_force", [
                ("Strategic forces priority", -0.7, 2, "Upload toward higher deployed counts; shipbuilding holds."),
                ("Balanced program",           0.0, 1, "Programmed force, no reallocation."),
                ("Shipbuilding surge",         0.7, 2, "Hull production prioritized over strategic upload."),
            ])},
            {"key": "b_alliance", "label": "Alliance posture", **menu("b_alliance", [
                ("Status quo consultation", 0.15, 0, "Existing burden sharing language."),
                ("Press commitments",       0.50, 1, "Sustained pressure on the five percent pledge."),
                ("Full court press",        0.85, 2, "Summit-level demands with conditionality."),
            ])},
            {"key": "b_export", "label": "Transfer policy", **menu("b_export", [
                ("Tighten controls",  -0.7, 1, "Export denial widens; partner backlog slows."),
                ("Current framework",  0.0, 0, "Present control and transfer regime."),
                ("Expand transfers",   0.7, 1, "Loosened releasability; crowd rival suppliers."),
            ])},
            {"key": "b_posture", "label": "Chokepoint posture", **menu("b_posture", [
                ("Drawdown",        0.15, 0, "Reduced presence at listed-area chokepoints."),
                ("Sustained patrol",0.50, 1, "Present rotational coverage."),
                ("Forward surge",   0.85, 2, "Continuous presence; deterrent effect on episode hazard."),
            ])},
            {"key": "b_industrial", "label": "Industrial mobilization", **menu("b_industrial", [
                ("Baseline appropriations", 0.15, 0, "No supplemental industrial investment."),
                ("Targeted expansion",      0.50, 1, "Munitions and yard capacity supplements."),
                ("Mobilization footing",    0.85, 2, "Sustained multiyear industrial ramp."),
            ])},
        ],
        "red": [
            {"key": "r_naval", "label": "Naval construction tempo", **menu("r_naval", [
                ("Consolidate",   0.15, 0, "Absorb current classes; slow new keels."),
                ("Program tempo", 0.50, 1, "Present shipbuilding trajectory."),
                ("Accelerate",    0.85, 2, "Additional yards to series production."),
            ])},
            {"key": "r_nuclear", "label": "Nuclear expansion tempo", **menu("r_nuclear", [
                ("Pause",          0.15, 0, "Hold near current stockpile growth."),
                ("Program tempo",  0.50, 1, "Silo fill and warhead production continue."),
                ("Sprint",         0.85, 2, "Maximum sustainable expansion."),
            ])},
            {"key": "r_gray", "label": "Chokepoint pressure", **menu("r_gray", [
                ("Restraint",      0.15, 0, "No gray zone activity at chokepoints."),
                ("Calibrated",     0.50, 1, "Intermittent pressure below the episode threshold."),
                ("Coercive",       0.85, 2, "Sustained pressure; episode hazard rises."),
            ])},
            {"key": "r_findiv", "label": "Reserve diversification", **menu("r_findiv", [
                ("Passive",        0.15, 0, "No active de-dollarization push."),
                ("Steady drive",   0.50, 1, "Bilateral settlement and swap-line expansion."),
                ("Full drive",     0.85, 2, "Coordinated diversification with partners."),
            ])},
            {"key": "r_export", "label": "Arms export drive", **menu("r_export", [
                ("Selective",      0.15, 0, "Existing client base only."),
                ("Expand",         0.50, 1, "Financing-backed offers in contested markets."),
                ("Aggressive",     0.85, 2, "Loss-leader pricing to displace incumbents."),
            ])},
        ],
        "world": [
            {"key": "g_fiscal", "label": "Blue fiscal headroom", **menu("g_fiscal", [
                ("Constrained", -0.6, 0, "Deficit pressure binds topline."),
                ("Neutral",      0.0, 0, "Present fiscal trajectory."),
                ("Permissive",   0.6, 0, "Supplementals pass without offset."),
            ])},
            {"key": "g_euro", "label": "European follow through", **menu("g_euro", [
                ("Slippage",     0.2, 0, "Commitments restated, outlays lag."),
                ("Partial",      0.5, 0, "Uneven national implementation."),
                ("Delivered",    0.8, 0, "The Hague trajectory holds."),
            ])},
        ],
    }
    sealed = ["g_shock", "g_growth"]

    pathway_weights = {
        "accretion":     {"r_naval": 1.2, "r_export": 1.0, "r_findiv": 0.6, "r_gray": -0.8, "episodes": -0.5},
        "retrenchment":  {"g_fiscal": -0.55, "b_industrial_inv": 0.9, "b_posture_inv": 0.7, "r_naval": 0.5, "episodes": -0.4},
        "demonstration": {"r_gray": 1.5, "episodes": 1.1, "r_nuclear": 0.8, "g_shock": 0.4},
        "tau": 0.8,
    }

    thresholds = {
        "blue": [
            {"channel": "usd_share", "op": ">=", "value": 53.0, "label": "USD share of allocated reserves holds at or above 53 percent"},
            {"channel": "awrp",      "op": "<=", "value": 0.30, "label": "War risk premium closes at or below 0.30 percent of hull value"},
            {"channel": "nuc_ratio", "op": "<=", "value": 0.78, "label": "Warhead ratio held at or below 0.78"},
            {"channel": "euro_milex","op": ">=", "value": 135.0,"label": "European expenditure at least 35 percent above 2025 in real terms"},
        ],
        "red": [
            {"channel": "rmb_share", "op": ">=", "value": 3.2,  "label": "RMB share of allocated reserves reaches 3.2 percent"},
            {"channel": "red_export","op": ">=", "value": 8.0,  "label": "Red share of world arms exports reaches 8 percent"},
            {"channel": "nuc_ratio", "op": ">=", "value": 0.90, "label": "Warhead ratio reaches 0.90"},
            {"channel": "usd_share", "op": "<=", "value": 54.5, "label": "USD share of allocated reserves erodes to 54.5 percent or below"},
        ],
    }

    payload = {
        "meta": {
            "title": "The Primacy Premium: Committee Exercise",
            "seed": SEED,
            "built": _dt.date.today().isoformat(),
            "design": design_kind, "n_design": N_DESIGN, "n_draws": N_DRAWS,
            "holdout": HOLDOUT, "license": "CC BY-NC 4.0",
        },
        "epochs": EPOCHS,
        "params": [{"key": k, "label": l, "side": s, "lo": lo, "hi": hi, "base": b}
                   for (k, l, s, lo, hi, b) in PARAMS],
        "channels": [{"key": k, "label": l, "unit": u, "dp": dp, "lag": lag,
                      "y0": C["y0"].get(k, C["y0"]["red_wh"] / C["y0"]["blue_dep"] if k == "nuc_ratio" else None)}
                     for (k, l, u, dp, lag) in CHANNELS],
        "consts": C,
        "emulator": {
            "kind": "degree two polynomial response surface, least squares",
            "param_order": KEYS,
            "feature_order": "bias, linear, squares, pairwise products i<j",
            "target_index": target_index,
            "coef": [[round(float(x), 6) for x in B[:, j]] for j in range(n_targets)],
        },
        "validation": {"per_channel": val, "overall_r2_median": overall_r2,
                       "note": "Held-out fifth of the design; R squared and RMSE per channel across epochs and quantiles."},
        "moves": moves,
        "sealed": sealed,
        "pathways": pathway_weights,
        "thresholds": thresholds,
        "scoring": {"alpha": 0.2, "interval_channel": "awrp",
                    "note": "Winkler interval score at eighty percent nominal coverage, lower is better."},
        "lags": {"fast": "resolves in period", "flash": "provisional in period, final next period",
                 "slow": "publishes next period"},
    }
    with open("payload.json", "w") as f:
        json.dump(payload, f, separators=(",", ":"))
    import os
    print(f"payload written: {os.path.getsize('payload.json')/1024:.0f} KB, "
          f"overall holdout R2 median {overall_r2}")


if __name__ == "__main__":
    main()
