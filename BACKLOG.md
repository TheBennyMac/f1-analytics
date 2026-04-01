# BACKLOG.md - F1 Analytics

## Current Version: v0.2.0 (2022 Era Baseline)

### Scope Decision (2026-03-31)

- **Primary focus**: 2022 Ground Effect Era (2022–2025) vs 2026 Era — direct comparison
- **Output**: Jupyter notebooks first; UI tooling decided later based on what the analysis needs
- **2026 data**: Matures race by race — completed rounds: Australia, China, Japan; next: Miami GP (~May 2026)

---

## Must Have (v0.1.0 — Foundation) ✅ Released 2026-03-31

- [x] FastF1 data loader with caching (`src/data/fastf1_loader.py`)
- [x] OpenF1 client for results and standings (`src/data/openf1_client.py`)
- [x] Core data models: `RaceResult`, `LapSummary`, `DriverStanding`, `ConstructorStanding`
- [x] Era helper utility: year → era name + year-within-era (`src/utils/era_helper.py`)
- [x] Basic test suite covering models and era helper (21 tests passing)
- [x] Notebook: `notebooks/00_data_validation.ipynb` — confirmed end-to-end

## Must Have (v0.2.0 — 2022 Era Baseline) ✅ Released 2026-04-01

- [x] Constructor points spread across 2022–2025 (Gini coefficient + raw gap)
- [x] P1–P10 lap time delta trend by year within era
- [x] DNF rate by team and year (2022–2025)
- [x] Quali position vs race finishing position consistency
- [x] Notebook: `notebooks/01_2022_era_baseline.ipynb`

## Must Have (v0.3.0 — 2026 Era: First Data)

- [ ] Ingest completed 2026 races: Australia, China, Japan (rounds 1–3)
- [ ] Ingest 2026 season results as they arrive (Miami onward)
- [ ] Note: Bahrain and Saudi Arabia (Middle East rounds, April 2026) cancelled due to regional conflict
- [ ] Year 1 convergence: 2026 vs 2022 on same metrics
- [ ] Like-for-like team/driver comparison across the regulation reset
- [ ] Notebook: `notebooks/02_2026_era_year1.ipynb`

## Should Have (v0.4.0 — Deeper Pace Analysis)

- [ ] Sector time breakdown (FastF1, 2022+)
- [ ] Tyre compound strategy by team across eras
- [ ] Quali-to-race pace delta: who converts, who doesn't
- [ ] Intra-team driver comparison: who adapts better to a regulation reset?
  - Same constructor, same car — isolates driver factor from machinery
  - **Primary metric: qualifying gap between teammates** — purest driver
    comparison, eliminates strategy, traffic, and luck as variables
  - Secondary metric: race pace delta — useful but noisier
  - Also track: DNF rate, tyre degradation handling
  - Primary lens: 2026 Year 1 vs 2022 Year 1 (regulation reset comparison)
  - Exclude races with mechanical DNFs to keep the comparison clean
- [ ] Field size normalisation for convergence comparisons
  - Cap field comparisons at the lowest classified finisher count across
    the races being compared (e.g. 12 finishers in 2022 Melbourne)
  - Offer fixed P1–P10 as primary view; normalised field as secondary
  - Flag attrition races clearly so gaps aren't misread as pace gaps
- [ ] Points boundary and P11 analysis
  - Gap from P10 to P11 per race — how arbitrary is the points cut?
  - P11 gap to P1 as an alternative field spread metric
  - "Near-miss points" frequency: how often does P11 finish within 5s
    of P10 across an era?
  - Connects to intra-team analysis: quali P9 but finish P11 is a
    different story to quali P14 and race to P11
- [ ] Tail-of-field gap analysis (classified finishers only)
  - For drivers outside the points, track gap to race leader and to P10
    per race — how far behind is the back of the grid?
  - Only include drivers who completed the race distance
  - Useful for measuring whether regulation resets compress or stretch
    the full field, not just the front runners
- [ ] Sprint race analysis
  - Load sprint sessions alongside race sessions (`session_type='S'`)
  - Compare sprint vs full race pace for same drivers on same weekend
  - Track position changes: sprint vs full race
  - Note: sprints have no mandatory pit stop — most cars finish on
    original tyres, making them a useful pit-stop-free baseline
  - Flag sprint weekends separately in all convergence metrics
- [ ] Pre vs post pit window excitement in full-length Grand Prix
  - **2026 observation to test:** first half to two-thirds of the full
    race (before the main pit window) appears more competitive than
    the post-stop phase, where fresh tyres spread the field
  - Measure lap time deltas and position changes before and after the
    median pit lap for each race
  - Compare sprint (no stops) vs full race post-stop phase — does
    removing pit strategy produce closer racing?
  - Test whether this pattern is consistent across eras or specific
    to 2026 tyre characteristics
- [ ] Notebook: `notebooks/03_pace_and_strategy.ipynb`

## Should Have (v0.5.0 — Narrative Testing)

- [ ] "Ferrari always bottles it" — championship lead conversion rate
- [ ] "Monaco produces processional races" — overtake index by circuit
- [ ] "Safety car lottery" — SC frequency and position change correlation
- [ ] "DRS made overtaking artificial" — overtake index pre/post DRS
- [ ] "Sprints are only exciting before the tyre stops" — compare lap
    time deltas and position changes in first vs second half of sprint
    races; test whether 2026 observation holds across the era
- [ ] "Turn 1 chaos is worse in regulation reset years" — compare
    first-lap incidents and retirements in Year 1 vs Year 2+ of each era
- [ ] Notebook: `notebooks/04_narrative_testing.ipynb`

## Could Have (v0.6.0 — UI / Publishing)

- [ ] Evaluate output medium: Streamlit, Dash, Observable, static site, or other
- [ ] Decision based on what the analysis actually needs — not assumed upfront
- [ ] Consider making repo public at this point

## Won't Have (this phase)

- Real-time telemetry streaming
- Driver fitness/biometric data
- Commercial/sponsorship analysis
- Any UI framework before v0.6.0

---

## Completed

- [x] v0.2.0 Baseline: points spread, lap time delta, DNF rates,
  quali->race conversion, 74 races 1478 entries
- [x] v0.1.0 Foundation: FastF1 loader, OpenF1 client, data models, era helper, tests, validation notebook
- [x] Project scaffolding, CLAUDE.md, BACKLOG.md, hooks, skills, docs, PR template, CHANGELOG
