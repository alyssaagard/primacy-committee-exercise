# Method

Design and method documentation for the Committee Exercise.

A two sided conditional forecasting exercise on the pathways question, 2026 to 2035.

Two committees commit stances sealed and simultaneously each period. Stances condition
the forecast rather than script the outcome. Indicators publish on their real
schedules, so each committee reads the world late and partial. Scoring is not zero sum.

---

## Design

### Turn structure

Five periods mapped to the horizon: 2026 to 2027, 2028 to 2029, 2030 to 2031, 2032 to
2033, 2034 to 2035. Each period runs commit, then resolve.

Commitment is simultaneous and sealed. Sequential play would imply reaction functions
the project has not identified and cannot defend, so neither committee sees the
other's stance before resolution.

### Modes

| Mode | Description |
| --- | --- |
| Two committees, one device | Sealed handoff screens between commitments |
| Solo as Blue | Red plays to an archetype prior |
| Solo as Red | Blue plays a balanced program |

Red archetypes are priors over stances, not scripts: patient accretionist,
opportunistic demonstrator, resource constrained consolidator.

### Moves

Five categories per side, three levels each. Each level is a value of a named
parameter of the generative recursion, plus a commitment expenditure tallied at
debrief.

**Blue:** force structure allocation, alliance posture, transfer policy, chokepoint
posture, industrial mobilization.

**Red:** naval construction tempo, nuclear expansion tempo, chokepoint pressure,
reserve diversification, arms export drive.

**World:** blue fiscal headroom and European follow through are chosen at setup.
Shock propensity and the red macroeconomic tailwind are drawn sealed and revealed
only at debrief.

### Channels

| Channel | Unit | Publication lag |
| --- | --- | --- |
| Blue military expenditure | index, 2025 = 100 | provisional in period, final next |
| Red military expenditure | index, 2025 = 100 | provisional in period, final next |
| European expenditure | index, 2025 = 100 | provisional in period, final next |
| USD reserve share | percent of allocated reserves | one period behind |
| RMB reserve share | percent of allocated reserves | one period behind |
| Additional war risk premium | percent of hull and machinery value | fixes in period |
| Red arms export share | percent of world exports | one period behind |
| Warhead ratio, red to blue deployed | ratio | one period behind |

### Scoring

Not zero sum, and no single winner. A zero sum scoreboard would contradict the
project's own thesis, which holds that pathway rather than endpoint drives the
variance: two committees can both attain their conditions along one pathway and both
fail along another.

Each side is scored on three axes:

1. **Objective attainment.** Four fixed, side specific terminal criteria.
2. **Commitment expenditure.** Cumulative cost of the stances taken.
3. **Interval calibration.** A Winkler interval score at eighty percent nominal
   coverage on the war risk premium fixing, stated before each resolution. Width is
   paid always; misses are penalized at ten times the exceedance. Lower is better.

In solo play the scripted committee states its own emulator fan as its interval.

### Pathway posterior

A classifier over conditioning trajectories: softmax over three linear scores on
committed stances and the episode rate. Sealed parameters enter only at debrief. The
posterior updates each period, so a committee that believes it is playing accretion
can discover at period four that its choices have put most of the probability mass on
retrenchment. This is the mechanic that carries the primary proposition.

---

## Method

### Emulator

Two sided play at five moves across five periods is roughly 9.8 million terminal
branches, so an enumerated decision tree is not feasible. Instead a move is a vector of
parameter values, and the precomputed object is a response surface over the parameter
space.

- Design: scrambled Sobol, 4096 points over 14 parameters, scipy preferred, Latin
  hypercube fallback if absent
- Draws: 320 stochastic draws per design point
- Fit: degree two polynomial response surface, least squares, on quantiles of each
  channel at each period
- Validation: reserved fifth of the design

Held out median R squared is 0.997 overall. The weakest channel is the war risk
premium at 0.875 median and 0.630 minimum, which is expected: it is the jump driven
series. The full per channel table renders in the page appendix, so the error is
disclosed to anyone playing rather than buried in the build.

Fitting the premium in log space was tested and validated worse, median R squared
0.812 against 0.875, so the natural space fit was retained with positivity enforced by
a clamp at render.

### Resolution

The realized path is one seeded draw of the same generative recursion, ported to
JavaScript from the exported constants. Fans and realizations therefore share a single
generative process rather than being two unrelated models.

Process parity was verified by comparing terminal quantiles from 20000 Python draws
against 2000 JavaScript paths at the reference stance. Worst relative gap is 2.3
percent, on the premium channel, attributable to draw counts. Every other channel is
under 1 percent.

### Conditioning tiers

Showing a fan conditioned on the true joint stance would leak the counterpart's sealed
move, so fans run in three tiers:

| Screen | Conditions on |
| --- | --- |
| Committee move sheet | own stance held forward, counterpart and sealed at reference |
| Shared resolution | all stances at reference, disclosing neither committee's choices |
| Debrief | true joint record, sealed parameters revealed |

The divergence between the in period estimates and the debrief fan is the measured
cost of the fog, which is the epistemic point of the exercise.

### Calibration anchors

Verified against local copies; the build script does not read raw files at runtime.

| Anchor | Value |
| --- | --- |
| US military expenditure 2025 | 929.2 bn constant 2024 USD, about 7.5 percent real decline |
| China 2025 | 335.0 bn constant 2024 USD, about 7.4 percent real increase |
| Central and Western Europe 2025 | 579.8 bn constant 2024 USD, about 6.0 percent real increase |
| USD share of allocated reserves, 2025 Q4 | 56.42 percent, against 59.40 at 2021 Q4 |
| RMB share, 2025 Q4 | 1.95 percent, off a 2.85 peak at 2021 Q4 |
| Mideast Gulf additional war risk premium | 0.15 to 0.20 percent of hull value at baseline, about 1 percent during the 2026 episode |
| China warheads 2025 | about 600, DoD projecting about 1500 by 2035 |

Episode severity is calibrated to the 2026 Gulf case, in which the premium moved
roughly fivefold under circular JWLA-033 of 3 March 2026. Episode declarations render
in the page as resolution circulars in the JWC register.

New START lapsed 4 February 2026 with no successor, so the blue deployed strategic
denominator is stochastic rather than fixed, consistent with the design amendment
already carried elsewhere in the project.

---

## Reproduce

```bash
python3 build_data.py    # writes payload.json
python3 build_page.py    # writes index.html
```

Dependencies: numpy required, scipy preferred. Build seed 20260724 throughout, so the
same seed reproduces the same design, emulator coefficients, and sealed draws.

Raw SIPRI and IMF files are excluded from the repository under publisher terms. The
build scripts do not read them; anchors are hardcoded with provenance in the
`build_data.py` header.

---

## Presentation and motion

Motion is spent where the game state actually changes, and nowhere else. The
resolution sequence is the payoff moment of each period, so it is staged: the period
rail fills, a circular stamps in when an episode is declared, indicator fixings tick
from their previous published values to the new ones, the reference fan redraws, the
interval scores reveal and count, and the pathway posterior updates, with a marginal
note when the leading pathway changes. On the commit sheet the committee estimate
animates between stances, so the act of conditioning is visible as the fan morphs
under the player's hand.

Three disciplines keep this honest and in register. Every sequence is skippable: the
proceed control is live from the first frame and completes the resolution instantly,
so the animation is texture rather than gate. Everything respects
prefers-reduced-motion, under which values appear at their final states with no
transforms. And nothing animated is decorative in the pejorative sense: each moving
element is a state change in the record, in the learned society register the project
already uses, double rules, small caps, tabular numerals, and the circular stamp.

## Limitations and next steps

**Horizon constant conditioning.** The emulator conditions on a single stance vector
per playthrough. A stance path is aggregated by averaging commitments to date with the
current stance held forward. A time varying emulator is the natural extension and would
let a mid game reversal register properly in the fan.

**Placeholder constants.** The generative constants are a transparent placeholder
layer. When the calibration module exposes its transfer coefficients as addressable
parameters, they swap into the constants block of `build_data.py` and
everything downstream regenerates unchanged.

**Archetypes are priors, not reaction functions.** A scripted committee does not read
the indicator board. Indicator conditioned reaction functions are the next mechanic,
and a set of Blue archetypes would complete solo play from the Red seat.

**Tripwire scoring against live data.** The terminal criteria are checked against
simulated outcomes. Because they are drawn from the project's falsification tripwires,
they can also be re-scored annually as SIPRI and COFER actually publish, which would
turn a past playthrough into a dated, falsifiable forecast record.
