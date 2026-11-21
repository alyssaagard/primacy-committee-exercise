/*
 * engine.js
 * The Primacy Premium, Committee Exercise. Simulation engine.
 *
 * This file is the single implementation of the exercise recursion. The page
 * runs it in the browser and reference.js runs it under Node to check it
 * against the published medians of the model.
 *
 * Expenditure (annual, six blocks). A block run by the model follows the
 * model equation for that block. A block held by a committee grows at the
 * committed rate.
 *   United States   pathway rate + residual
 *   China           ten-year rate + residual
 *   allied tiers    b0 + b_us * US growth(t-1) + b_cn * China growth(t-1)
 *                   + residual + post-event term
 *   rest of world   ten-year mean + residual
 * Residuals for all blocks come from one sample year per simulated year,
 * chosen by stationary bootstrap, so cross-block correlation is kept.
 *
 * Reserves (quarterly). The dollar share moves in percentage points and the
 * renminbi share in log-odds:
 *   change = c0 + c1 * dlog(China / United States expenditure) + residual
 * The regressor is defined as it was estimated: the year-on-year change of
 * the log ratio, with the annual ratio interpolated linearly in logs between
 * year ends. For quarter k of year t this is
 *   (1 - k/4) * d(t-1) + (k/4) * d(t),
 * where d(t) is the annual log change of the simulated ratio. In
 * the two quarters of a demonstration the change equals the 2022-Q1 and
 * 2022-Q2 observations, and drift shifts afterwards by the post-2022 change
 * in mean drift.
 */
(function (root) {
  "use strict";

  var Y0 = 2026;                     // first simulated year
  var US = "United States", CN = "China", ROW = "Rest of world";

  /* ------------------------------------------------------------ random */
  function mulberry32(a) {
    a = a >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function Rng(seed) {
    var u = mulberry32(seed), spare = null;
    return {
      u: u,
      int: function (n) { return Math.floor(u() * n); },
      n: function () {               // standard normal, Box-Muller
        if (spare !== null) { var s = spare; spare = null; return s; }
        var a = 0, b = u();
        while (a < 1e-12) a = u();
        var m = Math.sqrt(-2 * Math.log(a));
        spare = m * Math.sin(2 * Math.PI * b);
        return m * Math.cos(2 * Math.PI * b);
      }
    };
  }

  function chol(A) {
    var n = A.length, L = [], i, j, k, s;
    for (i = 0; i < n; i++) {
      L.push(new Array(n).fill(0));
      for (j = 0; j <= i; j++) {
        s = A[i][j];
        for (k = 0; k < j; k++) s -= L[i][k] * L[j][k];
        L[i][j] = i === j ? Math.sqrt(Math.max(s, 0)) : s / L[j][j];
      }
    }
    return L;
  }

  function mvn(rng, mean, L) {
    var n = mean.length, z = [], out = [], i, j, s;
    for (i = 0; i < n; i++) z.push(rng.n());
    for (i = 0; i < n; i++) {
      s = mean[i];
      for (j = 0; j <= i; j++) s += L[i][j] * z[j];
      out.push(s);
    }
    return out;
  }

  /* ------------------------------------------------------------- dates */
  function qIndex(year, q) { return (year - Y0) * 4 + (q - 3); }   // 2026-Q3 = 0
  function qLabel(i) {
    var k = i + 2;
    return (Y0 + Math.floor(k / 4)) + "-Q" + (k % 4 + 1);
  }
  var logit = function (p) { return Math.log(p / (100 - p)); };
  var expit = function (z) { return 100 / (1 + Math.exp(-z)); };

  /* ------------------------------------------------------- preparation */
  function prepare(payload) {
    var m = payload.model, P = {
      m: m, d: payload.design, blocks: m.blocks, allied: m.allied,
      col: {}, L: {}, nq: qIndex(payload.design.horizon, 4) + 1,
      ny: payload.design.horizon - Y0 + 1
    };
    m.blocks.forEach(function (b, i) { P.col[b] = i; });
    m.allied.forEach(function (t) { P.L[t] = chol(m.feedback[t].cov); });
    P.Lusd = chol(m.reserve.usd.cov);
    P.Lcny = chol(m.reserve.cny.cov);
    return P;
  }

  function initialState(P) {
    var m = P.m, lvl = {};
    m.blocks.forEach(function (b) { lvl[b] = m.base[b]; });
    return { year: m.base_year, lvl: lvl, usPrev: m.rates.us_last,
             cnPrev: m.rates.cn_last, zU: m.reserve.usd0,
             zC: logit(m.reserve.cny0), q: -1, eventYear: 0, eventQ: 0,
             xPrev: Math.log((1 + m.rates.cn_last / 100)
                             / (1 + m.rates.us_last / 100)) };
  }

  function copyState(s) {
    var c = {}, k;
    for (k in s) c[k] = s[k];
    c.lvl = {};
    for (k in s.lvl) c.lvl[k] = s.lvl[k];
    return c;
  }

  /* ------------------------------------------------------- sealed draw */
  /*
   * opt.usModel, opt.cnModel   the seat is run by the model
   * opt.force                  impose a pathway (reference runs)
   * opt.noEventThrough         condition on no demonstration through a year
   * opt.eventKnown             a demonstration has already occurred
   * opt.prior                  probabilities of accretion and retrenchment
   *                            (the remainder is demonstration); default
   *                            one third each
   */
  function drawWorld(P, rng, opt) {
    opt = opt || {};
    var m = P.m, W = { coef: {}, idx: [], usdEps: [], cnyEps: [] }, i, t;
    var e0 = m.event_years[0], e1 = m.event_years[1];
    for (;;) {
      var u = rng.u();
      var pa = opt.prior ? opt.prior[0] : 1 / 3;
      var pr = opt.prior ? opt.prior[1] : 1 / 3;
      W.path = opt.force || (u < pa ? "accretion"
                             : u < pa + pr ? "retrenchment" : "demonstration");
      W.eventYear = e0 + rng.int(e1 - e0 + 1);
      W.eventQuarter = 1 + rng.int(4);
      if (W.path !== "demonstration" || opt.cnModel === false || opt.eventKnown) {
        W.eventYear = 0;
      }
      if (!W.eventYear || !opt.noEventThrough ||
          W.eventYear > opt.noEventThrough) break;
    }
    W.usPath = (W.path === "retrenchment" && opt.usModel !== false)
      ? "retrenchment" : "accretion";
    for (i = 0; i < m.allied.length; i++) {
      t = m.allied[i];
      W.coef[t] = mvn(rng, m.feedback[t].mean, P.L[t]);
    }
    W.usd = mvn(rng, m.reserve.usd.mean, P.Lusd);
    W.cny = mvn(rng, m.reserve.cny.mean, P.Lcny);
    var n = m.resid.rows.length, p = 1 / m.mean_run_years;
    for (i = 0; i < P.ny; i++) {      // stationary bootstrap of sample years
      var restart = rng.u() < p, start = rng.int(n);
      W.idx.push(i === 0 || restart ? start : (W.idx[i - 1] + 1) % n);
    }
    var ru = m.reserve.usd_resid, rc = m.reserve.cny_resid;
    for (i = 0; i < P.nq; i++) {
      W.usdEps.push(ru[rng.int(ru.length)]);
      W.cnyEps.push(rc[rng.int(rc.length)]);
    }
    return W;
  }

  /* --------------------------------------------------------- one year */
  /*
   * Advances the state by one year. commit maps a block to a committed real
   * growth rate in percent; blocks absent from commit follow the model.
   * commit.event true declares a demonstration in this year.
   */
  function step(P, W, s0, commit) {
    commit = commit || {};
    var m = P.m, s = copyState(s0), y = s.year + 1, j = y - Y0;
    var eps = m.resid.rows[W.idx[j]], g = {}, model = {}, i, t;
    if (!s.eventYear && (commit.event || W.eventYear === y)) {
      s.eventYear = y;
      s.eventQ = qIndex(y, W.eventQuarter);
    }
    var usRate = W.usPath === "retrenchment" ? m.rates.us_contraction
                                             : m.rates.us_trend;
    model[US] = { fitted: m.rates.us_trend, sealed: usRate + eps[P.col[US]] };
    model[CN] = { fitted: m.rates.cn_trend,
                  sealed: m.rates.cn_trend + eps[P.col[CN]] };
    for (i = 0; i < m.allied.length; i++) {
      t = m.allied[i];
      var c = W.coef[t], f = m.feedback[t].mean, since = y - s.eventYear;
      var bump = (s.eventYear && since >= 0 && since < m.decay_years)
        ? m.mobilization[t] * (1 - since / m.decay_years) : 0;
      model[t] = {
        fitted: f[0] + f[1] * s.usPrev + f[2] * s.cnPrev + bump,
        sealed: c[0] + c[1] * s.usPrev + c[2] * s.cnPrev + eps[P.col[t]] + bump
      };
    }
    model[ROW] = { fitted: m.rates.row_mean,
                   sealed: m.rates.row_mean + eps[P.col[ROW]] };
    m.blocks.forEach(function (b) {
      g[b] = commit[b] != null ? commit[b] : model[b].sealed;
      s.lvl[b] = s.lvl[b] * (1 + g[b] / 100);
    });

    var x = Math.log((1 + g[CN] / 100) / (1 + g[US] / 100));
    var r = m.reserve, quarters = [];
    for (var q = 1; q <= 4; q++) {
      var qi = qIndex(y, q);
      if (qi < 0 || qi <= s.q) continue;
      var xq = (1 - q / 4) * s.xPrev + (q / 4) * x;
      var dU = W.usd[0] + W.usd[1] * xq, dC = W.cny[0] + W.cny[1] * xq;
      if (s.eventYear) {
        var k = qi - s.eventQ;
        if (k >= 0 && k < r.usd_jumps.length) {
          dU = r.usd_jumps[k]; dC = r.cny_jumps[k];
        } else if (k >= r.usd_jumps.length) {
          dU += r.usd_shift; dC += r.cny_shift;
        }
      }
      s.zU = Math.min(100, Math.max(0, s.zU + dU + W.usdEps[qi]));
      s.zC = s.zC + dC + W.cnyEps[qi];
      s.q = qi;
      quarters.push({ qi: qi, usd: s.zU, cny: expit(s.zC) });
    }
    s.year = y; s.usPrev = g[US]; s.cnPrev = g[CN]; s.xPrev = x;
    return { state: s, rec: { year: y, g: g, model: model, lagUS: s0.usPrev,
                              lagCN: s0.cnPrev, quarters: quarters, x: x } };
  }

  /* ----------------------------------------------------------- measures */
  function measures(P, s, cum) {
    var l = s.lvl, co = P.d.coalition, c = 0, w = 0, out;
    co.forEach(function (b) { c += l[b]; });
    P.blocks.forEach(function (b) { w += l[b]; });
    out = {
      cn_us: l[CN] / l[US],
      coalition_cn: c / l[CN],
      us_share_coalition: 100 * l[US] / c,
      allied_share: 100 * (l["Indo-Pacific allies"] + l["NATO Europe"]) / w,
      usd: s.zU, cny: expit(s.zC)
    };
    if (cum) P.d.seat_order.forEach(function (b) { out["cum:" + b] = cum[b]; });
    return out;
  }

  function quantile(sorted, p) {
    var h = (sorted.length - 1) * p, lo = Math.floor(h), hi = Math.ceil(h);
    return sorted[lo] + (sorted[hi] - sorted[lo]) * (h - lo);
  }
  function sortNum(a) { return a.slice().sort(function (x, y) { return x - y; }); }

  /* Percentile of a value within a distribution given on a quantile grid. */
  function percentileOf(grid, probs, v) {
    if (v <= grid[0]) return probs[0] * 100;
    for (var i = 1; i < grid.length; i++) {
      if (v <= grid[i]) {
        var f = grid[i] === grid[i - 1] ? 0
          : (v - grid[i - 1]) / (grid[i] - grid[i - 1]);
        return 100 * (probs[i - 1] + f * (probs[i] - probs[i - 1]));
      }
    }
    return probs[probs.length - 1] * 100;
  }

  /* Share of a block's historical residuals below a deviation. */
  function residualPercentile(P, block, dev) {
    var c = P.col[block], rows = P.m.resid.rows, n = 0;
    for (var i = 0; i < rows.length; i++) if (rows[i][c] < dev) n++;
    return 100 * n / rows.length;
  }

  /* ------------------------------------------------------ staff estimate */
  /*
   * Distribution of the stated quantities given what a committee can know.
   * o.start     state at the last published expenditure year, with reserves
   *             at the last published quarter
   * o.fixed     { year: { block: growth, event: bool } } known to the seat
   * o.endYear   last year to simulate
   * o.usdQ      target quarter index for the dollar share
   * o.growthYear target year for combined allied real growth
   */
  function estimate(P, o) {
    var rng = Rng(o.seed), usd = [], grow = [], ratio = [], path = {};
    var qi, n = o.n, i;
    for (qi = o.start.q + 1; qi <= o.usdQ; qi++) path[qi] = [];
    for (i = 0; i < n; i++) {
      var W = drawWorld(P, rng, { usModel: o.usModel, cnModel: o.cnModel,
                                  prior: o.prior,
                                  noEventThrough: o.noEventThrough,
                                  eventKnown: !!o.start.eventYear });
      var s = copyState(o.start);
      while (s.year < o.endYear) {
        var a = s.lvl["NATO Europe"] + s.lvl["Indo-Pacific allies"];
        var res = step(P, W, s, o.fixed[s.year + 1] || {});
        s = res.state;
        res.rec.quarters.forEach(function (k) {
          if (path[k.qi]) path[k.qi].push(k.usd);
          if (k.qi === o.usdQ) usd.push(k.usd);
        });
        if (s.year === o.growthYear) {
          grow.push(100 * ((s.lvl["NATO Europe"]
                            + s.lvl["Indo-Pacific allies"]) / a - 1));
        }
      }
      ratio.push(s.lvl[CN] / s.lvl[US]);
    }
    var fan = [];
    for (qi = o.start.q + 1; qi <= o.usdQ; qi++) {
      var v = sortNum(path[qi]);
      fan.push({ qi: qi, p10: quantile(v, 0.1), p50: quantile(v, 0.5),
                 p90: quantile(v, 0.9) });
    }
    var su = sortNum(usd), sg = sortNum(grow), sr = sortNum(ratio);
    var q3 = function (v) {
      return v.length ? [quantile(v, 0.1), quantile(v, 0.5), quantile(v, 0.9)]
                      : null;
    };
    return { fan: fan, usd: q3(su), growth: q3(sg), ratio: q3(sr), n: n };
  }

  /*
   * Staff probabilities of the US pathway rate given published US growth.
   * Each published year is treated as an independent normal draw around the
   * pathway rate with the standard deviation of the US residual sample.
   * Returns [P(accretion), P(retrenchment)]; the remainder is demonstration,
   * which shares the accretion rate.
   */
  function pathwayPosterior(P, growth) {
    var m = P.m, c = P.col[US], rows = m.resid.rows, ss = 0, i;
    for (i = 0; i < rows.length; i++) ss += rows[i][c] * rows[i][c];
    var sd = Math.sqrt(ss / (rows.length - 1)), la = 0, lr = 0;
    for (i = 0; i < growth.length; i++) {
      la -= Math.pow((growth[i] - m.rates.us_trend) / sd, 2) / 2;
      lr -= Math.pow((growth[i] - m.rates.us_contraction) / sd, 2) / 2;
    }
    var mx = Math.max(la, lr), wa = 2 * Math.exp(la - mx), wr = Math.exp(lr - mx);
    return [wa / (wa + wr) / 2, wr / (wa + wr)];
  }

  /* ------------------------------------------------------------ scoring */
  /* Winkler interval score: width plus (2 / alpha) times any exceedance. */
  function winkler(lo, hi, x, coverage) {
    var a = 1 - coverage, miss = x < lo ? lo - x : x > hi ? x - hi : 0;
    return { width: hi - lo, miss: miss, score: (hi - lo) + (2 / a) * miss,
             hit: miss === 0 };
  }

  function classify(P, records, eventYear) {
    if (eventYear) return "demonstration";
    var s = 0;
    records.forEach(function (r) { s += r.g[US]; });
    return s / records.length < P.d.us_midpoint ? "retrenchment" : "accretion";
  }

  root.Engine = {
    Y0: Y0, Rng: Rng, prepare: prepare, initialState: initialState,
    copyState: copyState, drawWorld: drawWorld, step: step,
    measures: measures, estimate: estimate, winkler: winkler,
    classify: classify, pathwayPosterior: pathwayPosterior, quantile: quantile, sortNum: sortNum,
    percentileOf: percentileOf, residualPercentile: residualPercentile,
    qIndex: qIndex, qLabel: qLabel, expit: expit, logit: logit
  };
})(typeof module !== "undefined" && module.exports ? module.exports : this);
