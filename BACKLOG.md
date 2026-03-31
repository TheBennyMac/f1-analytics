# BACKLOG.md - F1 Analytics

## Current Version: v0.1.0 (Scaffolding)

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

## Must Have (v0.2.0 — 2022 Era Baseline)

- [ ] Constructor points spread across 2022–2025 (Gini coefficient + raw gap)
- [ ] P1–P10 lap time delta trend by year within era
- [ ] DNF rate by team and year (2022–2025)
- [ ] Quali position vs race finishing position consistency
- [ ] Notebook: `notebooks/01_2022_era_baseline.ipynb`

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
  - **Primary metric: qualifying gap between teammates** — purest driver comparison,
    eliminates strategy, traffic, and luck as variables
  - Secondary metric: race pace delta — useful but noisier
  - Also track: DNF rate, tyre degradation handling
  - Primary lens: 2026 Year 1 vs 2022 Year 1 (regulation reset comparison)
  - Exclude races with mechanical DNFs to keep the comparison clean
- [ ] Notebook: `notebooks/03_pace_and_strategy.ipynb`

## Should Have (v0.5.0 — Narrative Testing)

- [ ] "Ferrari always bottles it" — championship lead conversion rate
- [ ] "Monaco produces processional races" — overtake index by circuit
- [ ] "Safety car lottery" — SC frequency and position change correlation
- [ ] "DRS made overtaking artificial" — overtake index pre/post DRS
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

- [x] v0.1.0 Foundation: FastF1 loader, OpenF1 client, data models, era helper, tests, validation notebook
- [x] Project scaffolding, CLAUDE.md, BACKLOG.md, hooks, skills, docs, PR template, CHANGELOG
