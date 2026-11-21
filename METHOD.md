# Method

Committee Exercise, release 2.1.0. Alyssa I. Agard.

## 1. Purpose

The exercise places committees in the seats of the model published as [The Primacy Premium](https://github.com/alyssaagard/primacy-premium), release 1.1.0 (commit `7099dd1`). That model estimates how allied military expenditure and reserve currency shares respond to US and Chinese expenditure, and simulates three pathways to 2035: accretion, retrenchment, and demonstration. In the model the two principals follow assumed rates. In the exercise, committees choose those rates, and may also choose the rates of two allied tiers.

The exercise is a conditional forecasting instrument. Its output is what the estimated model implies given the commitments made. It does not state that any path will occur.

It serves three uses:

1. Teaching. Participants see which outcomes respond to expenditure decisions in the estimated model and which do not.
2. Elicitation. When a committee holds an allied seat, its commitments are recorded beside the value of the estimated allied response equation. The record shows where human judgment departs from the equation.
3. Calibration practice. Each committee states intervals for two quantities each period and is scored on them.

## 2. Relation to release 1.0.0

Release 1.0.0 of the exercise used its own simulation: fourteen stance parameters with coefficients set by the designer, served through a polynomial emulator, and anchored to the July 2026 data. That engine was not the estimated model and could not be reconciled with it.

Release 2.0.0 keeps the frame of the earlier exercise and replaces its engine.

| Kept from 1.0.0 | Replaced in 2.0.0 |
|---|---|
| Sealed simultaneous commitment | Assumed stance coefficients, replaced by the estimates of release 1.1.0 |
| Five periods to 2035 | Polynomial emulator, replaced by the model recursion run directly |
| Publication lags | Two sides, replaced by four seats |
| Interval statements scored by the Winkler rule | Fixed numeric thresholds, replaced by comparison with a reference distribution |
| Sealed parameters opened at the debrief | Stance menus, replaced by one real growth rate per period |
| Pathway record and circulars | |
| Outcomes assessed seat by seat, with no ranking | |

## 3. Seats and blocks

The model has six expenditure blocks. Four can be held by a committee.

| Block | Holder |
|---|---|
| United States | committee or model |
| China | committee or model |
| NATO Europe (30 members) | committee or model |
| Indo-Pacific allies (Japan, South Korea, Taiwan, Australia, Philippines, New Zealand, Thailand) | committee or model |
| Hedging middle powers | model |
| Rest of world, including Russia | model |

Expenditure is in constant 2024 US dollars from the SIPRI Military Expenditure Database. Tier totals are chain-linked over matched members, as in release 1.1.0. The reserve currency shares are run by the model in every configuration.

## 4. Calendar

The last observed expenditure year is 2025 and the last observed reserve quarter is 2026-Q2. The year 2026 is resolved by the model for every seat, because it is in progress at the first decision point.

| Period | Years committed | Decision point | Expenditure published through | Reserves published through |
|---|---|---|---|---|
| I | 2027, 2028 | November 2026 | 2025 | 2026-Q2 |
| II | 2029, 2030 | November 2028 | 2027 | 2028-Q2 |
| III | 2031, 2032 | November 2030 | 2029 | 2030-Q2 |
| IV | 2033, 2034 | November 2032 | 2031 | 2032-Q2 |
| V | 2035 | November 2034 | 2033 | 2034-Q2 |

The lags follow the sources. SIPRI publishes a year's expenditure the following April. The IMF publishes reserve composition about one quarter late. At each decision point a committee therefore sees every other seat's expenditure up to two years back, and its own through the current year. A demonstration is public when it occurs.

## 5. Engine

`engine.js` is the only implementation of the recursion. The page runs it in the browser. `reference.js` runs the same file under Node.

### 5.1 Expenditure

Annual real growth, in percent, for each block *b* in year *t*:

- United States, run by the model: pathway rate plus residual. The rate is the compound rate for 2015 to 2025 (+1.03) under accretion and demonstration, and the 1988 to 1998 rate (−3.76) under retrenchment.
- China, run by the model: the compound rate for 2015 to 2025 (+5.50) plus residual.
- Allied tier, run by the model: `b0 + b_us * g_US(t-1) + b_cn * g_CN(t-1) + residual + post-event term`.
- Rest of world: mean growth over the last ten years (+6.70) plus residual.
- Any seat held by a committee: the committed rate.

Estimated coefficients (standard errors), 1991 to 2025:

| Tier | Response to US growth | Response to China growth | R squared |
|---|---|---|---|
| Indo-Pacific allies | +0.076 (0.072) | −0.041 (0.058) | 0.04 |
| NATO Europe | +0.279 (0.160) | −0.185 (0.130) | 0.12 |
| Hedging middle powers | +0.194 (0.208) | +0.154 (0.124) | 0.09 |

Residuals are the estimation residuals of the six blocks on the common sample 1993 to 2025. One sample year is drawn for each simulated year by stationary bootstrap (Politis and Romano 1994) with a mean run of five years, and its residuals are applied to all blocks together. This keeps correlation across blocks and short-run persistence.

### 5.2 Reserves

Quarterly. The US dollar share moves in percentage points and the renminbi share in log-odds:

`change = c0 + c1 * dlog(China / United States expenditure) + residual`

The regressor is defined as it was estimated in release 1.1.0: the year-on-year change of the log ratio, with the annual ratio placed at year end and interpolated linearly in logs. For quarter *k* of year *t* this equals `(1 - k/4) * d(t-1) + (k/4) * d(t)`, where `d(t)` is the annual log change of the simulated ratio. The 2025 change enters the 2026 quarters through this formula. In the pathway simulation of release 1.1.0 the regressor is a constant per pathway; in the exercise it is computed from the realized path, which is the only link from commitments to reserves. Residuals are resampled from the estimation residuals.

The estimated dollar coefficient is +0.93 points per unit log change (standard error 0.95, R squared 0.012). The response is weak and its sign is uncertain.

### 5.3 Demonstration

A demonstration occurs at most once, in a year from 2028 to 2031. It repeats the one episode on record:

- In the event quarter and the next, the share changes equal those observed in 2022-Q1 and 2022-Q2. Afterwards, drift shifts by the difference between mean quarterly change from 2022-Q1 and before it.
- From the event year, each allied tier run by the model adds its measured post-2022 change in mean growth (Indo-Pacific allies +0.11 points, NATO Europe +7.11, hedging middle powers +5.14), declining linearly to zero over four years.

The event quarter within the year is part of the sealed record.

## 6. Sealed record

At the start, one draw is made from the exercise seed and held until the debrief:

1. A pathway, with probability one third each. A retrenchment draw applies only if the United States is run by the model. A demonstration draw applies only if China is run by the model; its year is uniform on 2028 to 2031.
2. Coefficients for each allied tier, from the joint normal distribution with the estimated covariance.
3. The two reserve coefficients for each currency, drawn the same way.
4. The residual years for 2026 to 2035 and the quarterly reserve residuals.

The same seed and the same commitments reproduce the same exercise.

## 7. Commitments

Each period a committee commits one real growth rate, applied to every year of the period. The range is the 5th to 95th percentile of the seat's own annual real growth from 1993 to 2025, rounded outward to half a point:

| Seat | Range, percent |
|---|---|
| United States | −7.0 to +10.5 |
| China | 0.0 to +20.0 |
| NATO Europe | −3.5 to +11.5 |
| Indo-Pacific allies | −1.0 to +6.0 |

A committed rate is realized exactly. It replaces the model equation and its residual for that seat. A committee holding China may also declare one demonstration in a year of the window that falls in the period.

## 8. Staff estimate

Each seat paper shows a staff estimate: 2,000 draws of the model from the published record, given the committee's own commitment. The staff know what the committee knows: published figures, the committee's own unpublished outlays, and any demonstration already recorded. They do not know the sealed record or another committee's sheet. Every other seat is taken at its model behavior.

Pathway probabilities start at one third each and are revised at each decision point:

- On published US growth. Each published year is treated as an independent normal draw around the pathway rate, with the standard deviation of the US residual sample. Accretion and demonstration share a rate and split their joint probability equally.
- On demonstrations. If none has occurred, draws that place one in a past year are rejected.

## 9. Interval statements

Each period a committee states an 80 percent interval for two quantities:

1. The US dollar reserve share at the last quarter that will be published at the next decision point (2035-Q4 in period V).
2. Combined real growth of NATO Europe and the Indo-Pacific allies in the first year of the period.

Each is scored by the Winkler rule: interval width plus 10 times the distance by which the outcome falls outside. Lower is better. The intervals are prefilled with the staff 10th and 90th percentiles; a committee that leaves them unchanged receives the staff score. The staff score is reported beside each committee score.

## 10. Goals, objectives, and favorable outcomes

`reference.js` simulates the accretion pathway with every seat run by the model, 50,000 draws. This is the reference distribution.

Each seat has one goal, two objectives measured at 2035, and one resource limit. Each objective threshold is the reference median. The resource limit is the 75th percentile of the seat's cumulative outlays, 2026 to 2035, in the reference distribution.

| Seat | Goal | Objective 1 | Objective 2 | Resource limit, USD bn |
|---|---|---|---|---|
| United States | Retain the expenditure margin over China and the reserve position of the dollar. | China to United States expenditure ratio at or below 0.553 | US dollar reserve share, 2035-Q4, at or above 50.36 percent | 10,944.8 |
| China | Close the expenditure gap with the United States and raise the reserve role of the renminbi. | China to United States expenditure ratio at or above 0.553 | Renminbi reserve share, 2035-Q4, at or above 4.59 percent | 5,188.2 |
| NATO Europe | Keep the coalition's expenditure margin over China while the United States continues to carry its share. | Coalition to China expenditure ratio at or above 3.31 | United States share of coalition expenditure at or above 53.1 percent | 6,617.7 |
| Indo-Pacific allies | As NATO Europe. | As NATO Europe. | As NATO Europe. | 2,069.7 |

The coalition is the United States, NATO Europe, and the Indo-Pacific allies.

Outcome for a seat:

- Favorable: every objective met and cumulative outlays within the resource limit.
- Mixed: at least one objective met.
- Unfavorable: no objective met.

Outcomes are assessed seat by seat and are not ranked against each other. The objectives of the two principals on the expenditure ratio are opposed; the allied objectives are not opposed to either. Interval calibration (section 9) is reported separately and does not enter the outcome.

The thresholds are computed from the model. The choice of goals, objectives, and the 75th percentile limit is a design assumption. The second allied objective encodes the incentive to leave the burden with the guarantor, which is the standard burden-sharing result (Olson and Zeckhauser 1966). The debrief also reports each measure's percentile in the reference distribution.

## 11. Commitments against the model

For each year a committee held a seat, the debrief reports the committed rate, the value of the model equation for that seat at the growth rates realized in the prior year (using the published point estimates), the deviation, and the share of the seat's historical residuals that lie below the deviation. For the two principals the equation is the ten-year rate. The table also shows the value the model would have drawn for the seat in the sealed record.

For allied seats this is an elicited record of a reaction function. Release 1.1.0 does not support the allied response hypothesis at the 5 percent level (pooled one-sided p = 0.12). The record of committee play is descriptive and is not evidence on that hypothesis.

## 12. Pathway record

The record is classed as demonstration if a demonstration occurred. Otherwise it is classed as retrenchment if mean US real growth from 2026 is below −1.37 percent per year, the midpoint of the two pathway rates, and as accretion if not.

## 13. Parity with release 1.1.0

With every seat run by the model and the pathway imposed, the engine must reproduce the published 2035 medians of release 1.1.0. `reference.js` checks 27 medians (six blocks, two reserve shares, and the allied share of world expenditure, for three pathways) at 50,000 draws each and stops the build if any is outside tolerance (3 percent for levels, 0.35 points for reserve shares, 0.6 points for the allied share).

Result at this release: the largest deviation is 0.97 percent for expenditure levels and 0.05 points for shares. The two implementations use different random number generators and the published medians rest on 10,000 draws, so the difference is sampling error. The carry-over of the 2025 ratio change into 2026 (section 5.2) is within the same tolerance. The full table is in `reference.json` under `parity`.

## 14. Estimated and assumed

Estimated in release 1.1.0 and used unchanged: the allied response equations and their covariance; the reserve regressions and their covariance; all residual pools; the pathway rates; the 2022 episode quantities; base levels.

Assumed by the exercise:

- A committed rate is realized exactly.
- The pathway probabilities are equal.
- The commitment range is the 5th to 95th percentile of observed growth.
- One rate governs each period.
- The goals, objectives, and resource limits in section 10.
- Committees holding allied seats choose their own response to a demonstration; the measured post-2022 term applies only to tiers run by the model.
- The reserve regressor is computed from the realized path.

## 15. Limitations

- The allied response equations are static, their residuals are serially correlated, and the coefficient signs are uncertain. The sealed draws carry that uncertainty; a single exercise is one draw.
- The demonstration rests on one episode.
- The reserve response is weak. Reserve outcomes in the exercise mostly reflect drift, residuals, and whether a demonstration occurs.
- A committed rate has no execution error, no fiscal constraint, and no within-period adjustment.
- Rest of world includes Russia and is not a strategic actor in the exercise.
- The staff revision of pathway probabilities treats published years as independent, which the residuals are not.
- The exercise has not been run with participants. The scoring axes and objectives have not been validated against play.

## 16. Build

```
python build_data.py --model ../primacy-premium   # refresh model_inputs.json (optional)
python build_data.py                              # payload.json
node reference.js                                 # parity check, reference.json
python build_social.py                            # share image
python build_page.py                              # index.html
python tests/playthrough.py                       # automated play to the debrief
```

`build_data.py` and `build_page.py` need Python 3 only. Refreshing `model_inputs.json` needs pandas and a checkout of the model repository. `reference.js` needs Node. `build_social.py` needs Pillow. The test needs Playwright.

## References

Olson, M., and R. Zeckhauser. 1966. An economic theory of alliances. *Review of Economics and Statistics* 48(3): 266 to 279.

Politis, D. N., and J. P. Romano. 1994. The stationary bootstrap. *Journal of the American Statistical Association* 89(428): 1303 to 1313.

Winkler, R. L. 1972. A decision-theoretic approach to interval estimation. *Journal of the American Statistical Association* 67(337): 187 to 191.

Data sources and their citation requirements are listed in `REFERENCES.md` of the model repository.
