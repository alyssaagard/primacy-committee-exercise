# Committee Exercise

**The Primacy Premium · two sided conditional play on the pathways question, 2026 to 2035**

A wargame in the analytic tradition rather than the hex and counter one. Two committees
commit stances sealed and simultaneously across five periods. Stances condition the
forecast, they do not script the outcome: every fan on screen is a conditional forecast
served by an emulator fitted to a documented generative process, and the realized path
is one seeded draw of that same process. Indicators publish on their real schedules, so
each committee reads the world late and partial, which is the condition the underlying
research project is about. Scoring is not zero sum.

**Play:** `index.html`, served by GitHub Pages at the repository root, or opened
directly in a browser. No build step, no server; the only external dependency is the
Plotly CDN.

## The game

- **Five periods**, 2026 to 2027 through 2034 to 2035, tracked on a persistent period
  rail with episode markers.
- **Three modes**: two committees on one device with sealed handoffs, solo as Blue
  against a Red archetype prior (patient accretionist, opportunistic demonstrator,
  resource constrained consolidator), or solo as Red against a balanced Blue program.
- **Five stance categories per side**, three levels each, every level a value of a
  named simulation parameter. The committee estimate redraws live as stances change:
  the morphing fan is the conditioning, made visible.
- **Publication lag as fog.** The war risk premium fixes in period; expenditure
  publishes provisional then final; reserve composition, export shares, and warhead
  estimates arrive a period behind. Unpublished cells render hatched until the record
  catches up.
- **Episodes as circulars.** Chokepoint disruption episodes stamp in as resolution
  circulars in the Joint War Committee register, with premium fixings calibrated to
  the 2026 Gulf case.
- **Scoring on three axes per side**: objective attainment against fixed criteria,
  commitment expenditure, and a Winkler interval score at eighty percent nominal
  coverage on premium forecasts stated before each resolution.
- **A pathway posterior** that updates every period. A committee that believes it is
  playing accretion can discover at period four that its choices have put the
  probability mass on retrenchment. That mechanic carries the project's central
  proposition: the pathway, not the endpoint, carries the variance.

## Honesty constraints

The exercise makes no causal claim it cannot support. Fans run in three conditioning
tiers so that no screen leaks a sealed stance: a committee's own sheet conditions on
its stance with the counterpart at reference values, the shared resolution screen
shows a reference fan, and only the debrief recomputes at the true joint record with
the sealed world parameters revealed. The divergence between tiers is the measured
cost of the fog.

Emulator error is disclosed in the page appendix rather than buried in the build:
held out median R squared 0.997 overall, 0.875 on the war risk premium, which is the
jump driven channel. Process parity between the Python build and the JavaScript
resolution recursion is verified at under 1 percent on every channel except the
premium, at 2.3 percent, attributable to draw counts. Full method in
[METHOD.md](METHOD.md).

## Reproduce

```bash
python3 build_data.py    # design, simulation, emulator fit, validation; writes payload.json
python3 build_page.py    # injects the payload into template.html; writes index.html
```

numpy required, scipy preferred for the Sobol design. Seed 20260724 throughout, so the
same seed reproduces the same design, coefficients, sealed draws, and resolution path.
The included GitHub Actions workflow rebuilds on every push and fails if the committed
`index.html` does not match a fresh rebuild, so reproducibility is checked rather than
asserted.

Raw SIPRI and IMF files are excluded under publisher terms. Calibration anchors, among
them the 2025 US real expenditure decline, the renminbi reserve share peaking in 2021
and declining since, and the fivefold Gulf premium move under circular JWLA-033, are
hardcoded with provenance in the `build_data.py` header.

## Repository layout

| File | Role |
| --- | --- |
| `index.html` | The built game, self contained apart from the Plotly CDN |
| `build_data.py` | Parameter space, generative recursion, Sobol design, emulator fit, validation |
| `build_page.py` | Payload injection into the template |
| `template.html` | Page template with the engine, payload token unfilled |
| `payload.json` | Generated: emulator coefficients, constants, move menus, thresholds, validation |
| `METHOD.md` | Full design and method documentation |
| `.github/workflows/build.yml` | Reproducibility check on every push |

## Publish

Create the repository, push, then Settings, Pages, deploy from `main` at `/ (root)`.
The game is live at `https://USERNAME.github.io/REPOSITORY/` within a minute. The
`.nojekyll` file is included so Pages serves the site without a Jekyll pass.

## Relation to the main project

This exercise is the interactive layer of The Primacy Premium, a quantitative research
project producing conditional forecasts of defense and commercial markets under
Chinese military primacy by 2035. The generative constants here are a transparent
placeholder layer: when the main project's calibration module exposes its transfer
coefficients as addressable parameters, they swap into one block of `build_data.py`
and everything downstream regenerates.

## Accessibility

Motion is deliberate and bounded: number fixings tick, circulars stamp, rules draw,
reveals stagger. All of it respects `prefers-reduced-motion`, every sequence is
skippable from the proceed control, and the exercise is fully playable by keyboard.

## License and citation

CC BY-NC 4.0. See [LICENSE.md](LICENSE.md). A `CITATION.cff` is included; GitHub
renders it as a citation block on the repository page.

Alyssa Agard.
