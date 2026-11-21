#!/usr/bin/env node
/*
 * reference.js
 * Stage 2. Parity check and reference distributions.
 *
 * Runs engine.js with every seat held by the model, once per pathway, and
 * compares the 2035 medians with the medians published by The Primacy
 * Premium at the vendored commit. The two implementations use different
 * random number generators, so agreement is within sampling tolerance, not
 * exact. The script exits with an error if any median is outside tolerance.
 *
 * It then writes reference.json: the distribution of each scored measure
 * under the accretion pathway with every seat held by the model. The
 * exercise reports outcomes against these distributions.
 *
 * Run: node reference.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const E = require("./engine.js").Engine;

const payload = JSON.parse(fs.readFileSync(path.join(__dirname, "payload.json")));
const P = E.prepare(payload);
const m = payload.model, d = payload.design;
const N = d.reference_draws;
const PATHWAYS = ["accretion", "retrenchment", "demonstration"];
const TOL = { level: 0.03, usd: 0.35, cny: 0.35, allied_share: 0.6 };
const PROBS = [];
for (let p = 5; p <= 95; p += 5) PROBS.push(p / 100);

function run(force, seed) {
  const rng = E.Rng(seed), out = { final: [], years: {}, quarters: {} };
  for (let i = 0; i < N; i++) {
    const W = E.drawWorld(P, rng, { force: force });
    let s = E.initialState(P);
    const cum = {};
    d.seat_order.forEach((b) => { cum[b] = 0; });
    while (s.year < d.horizon) {
      const res = E.step(P, W, s, {});
      s = res.state;
      d.seat_order.forEach((b) => { cum[b] += s.lvl[b]; });
      (out.years[s.year] = out.years[s.year] || []).push(Object.assign({}, s.lvl));
      res.rec.quarters.forEach((k) => {
        (out.quarters[k.qi] = out.quarters[k.qi] || []).push(k.usd);
      });
    }
    out.final.push({ lvl: s.lvl, meas: E.measures(P, s, cum) });
  }
  return out;
}

const med = (a) => E.quantile(E.sortNum(a), 0.5);
const rows = [];
let failed = false;
const runs = {};
PATHWAYS.forEach((p, pi) => {
  const r = runs[p] = run(p, m.seed + pi + 1);
  m.blocks.forEach((b) => {
    const got = med(r.final.map((f) => f.lvl[b]));
    const want = m.published.endpoints_musd[p][b];
    const dev = got / want - 1;
    const ok = Math.abs(dev) <= TOL.level;
    failed = failed || !ok;
    rows.push({ pathway: p, quantity: b + ", 2035, USD m", engine: Math.round(got),
                published: want, deviation: (100 * dev).toFixed(2) + " %", ok });
  });
  [["usd", "US dollar reserve share, 2035-Q4, percent"],
   ["cny", "Renminbi reserve share, 2035-Q4, percent"],
   ["allied_share", "Allied share of world expenditure, 2035, percent"]]
    .forEach(([k, label]) => {
      const got = med(r.final.map((f) => f.meas[k]));
      const want = k === "allied_share" ? m.published.allied_share[p]
                                        : m.published[k][p];
      const ok = Math.abs(got - want) <= TOL[k];
      failed = failed || !ok;
      rows.push({ pathway: p, quantity: label, engine: +got.toFixed(2),
                  published: want, deviation: (got - want).toFixed(2) + " pp", ok });
    });
});

const acc = runs.accretion;
const keys = Object.keys(acc.final[0].meas);
const dist = {};
keys.forEach((k) => {
  const v = E.sortNum(acc.final.map((f) => f.meas[k]));
  dist[k] = PROBS.map((p) => +E.quantile(v, p).toPrecision(7));
});
const yearMedians = {};
Object.keys(acc.years).forEach((y) => {
  yearMedians[y] = {};
  m.blocks.forEach((b) => {
    yearMedians[y][b] = Math.round(med(acc.years[y].map((l) => l[b])));
  });
});
const usdFan = Object.keys(acc.quarters).map(Number).sort((a, b) => a - b)
  .map((qi) => {
    const v = E.sortNum(acc.quarters[qi]);
    return { qi, p10: +E.quantile(v, 0.1).toFixed(3),
             p50: +E.quantile(v, 0.5).toFixed(3),
             p90: +E.quantile(v, 0.9).toFixed(3) };
  });

const reference = {
  note: "Accretion pathway, every seat held by the model.",
  draws: N, seed: m.seed + 1, probs: PROBS, dist, year_medians: yearMedians,
  usd_fan: usdFan,
  parity: { tolerance: TOL, passed: !failed, rows },
};
fs.writeFileSync(path.join(__dirname, "reference.json"),
                 JSON.stringify(reference) + "\n");

const worst = (unit) => rows.filter((r) => r.deviation.endsWith(unit))
  .reduce((a, r) => Math.max(a, Math.abs(parseFloat(r.deviation))), 0);
console.log(`parity: ${rows.length} medians, ${N} draws per pathway; ` +
            `largest level deviation ${worst("%").toFixed(2)} percent, ` +
            `largest share deviation ${worst("pp").toFixed(2)} points`);
if (failed) {
  rows.filter((r) => !r.ok).forEach((r) => console.error("OUTSIDE TOLERANCE", r));
  process.exit(1);
}
console.log("reference.json written");
