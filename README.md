# Committee Exercise

A four-seat budget exercise on the estimated model of The Primacy Premium, 2026 to 2035.

Alyssa I. Agard

Play: https://alyssaagard.github.io/primacy-committee-exercise/

## What it is

Up to four committees set real military expenditure for the United States, China, NATO Europe, and the Indo-Pacific allies over five periods to 2035. Commitments are sealed and simultaneous. Expenditure and reserve data publish with their real lags, so each committee decides on a record one to two years old for every seat but its own. Each committee also states 80 percent intervals for two quantities each period and is scored on them.

Any seat without a committee is run by the estimated model of [The Primacy Premium](https://github.com/alyssaagard/primacy-premium), release 1.1.0. The model also runs the hedging middle powers, the rest of the world, and the US dollar and renminbi reserve shares. One person can play any single seat against the model.

The exercise is a conditional forecasting instrument. It reports what the estimated model implies given the commitments made. It does not state that any path will occur.

## Relation to the model

The engine is the model's recursion, run in the browser. With every seat run by the model it reproduces the published 2035 medians of release 1.1.0 for all three pathways. Across 27 medians at 10,000 draws, the largest deviation is 1.02 percent for expenditure levels and 0.15 points for shares, which is sampling error from a different random number generator. The build fails if any median is outside tolerance.

Release 1.0.0 of this exercise used a separate simulation with coefficients set by the designer. Release 2.0.0 keeps its frame (sealed commitment, five periods, publication lags, scored intervals, a sealed record opened at the debrief, no winner) and replaces that engine with the estimated model. See `METHOD.md`, section 2.

## What a session produces

- A resolution after each period: newly published figures, any circular, and interval scores.
- A debrief: the sealed pathway and coefficient draws, every block's path against a reference, each committee's objectives, outlays, and calibration, and each commitment set against the model equation for that seat.
- A downloadable record in JSON, with commitments, realized paths, sealed draws, and scores.

## Estimated and assumed

Coefficients, covariance matrices, residuals, pathway rates, and the 2022 episode quantities come from release 1.1.0 and are used unchanged. The seats, the commitment range, the equal pathway probabilities, the objectives, and the rule that a committed rate is realized exactly are assumptions of the exercise. `METHOD.md`, section 14, lists both.

## Repository

| File | Purpose |
|---|---|
| `index.html` | The built exercise. Self-contained apart from the chart library. |
| `template.html` | Page source: markup, styles, interface. |
| `engine.js` | The simulation engine. Runs in the browser and under Node. |
| `build_data.py` | Reads model outputs into `model_inputs.json`; writes `payload.json`. |
| `reference.js` | Parity check against release 1.1.0; writes `reference.json`. |
| `build_page.py` | Assembles `index.html`. |
| `build_social.py` | Draws the share card from `reference.json`. |
| `tests/playthrough.py` | Plays four seat configurations to the debrief; fails on any page error. |
| `model_inputs.json` | Quantities copied from the model at commit `dc82a6d`. |
| `METHOD.md` | Full method, limitations, and build instructions. |

## Build

```
python build_data.py
node reference.js
python build_social.py
python build_page.py
python tests/playthrough.py
```

To move to a later release of the model, run `python build_data.py --model PATH` against a checkout of that release, then rebuild. The parity check will fail if the engine and the model have diverged.

## Citation and license

Cite as given in `CITATION.cff`. Licensed CC BY-NC 4.0; see `LICENSE.md`. Source data remain subject to their publishers' terms.
