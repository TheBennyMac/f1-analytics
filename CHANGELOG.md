# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

---

## [v0.4.0] — 2026-04-03

### Added

- `src/analysis/intra_team.py` — intra-team qualifying gap analysis:
  - `prepare_quali_results()` — normalises FastF1 qualifying session results
  - `teammate_quali_gaps()` — gap (seconds + %) per constructor per race
  - `season_teammate_gaps()` — aggregates across multiple races
  - `mean_gap_by_constructor()` — season-level mean gap, sorted closest first
  - `driver_dominance()` — how often each driver outqualified their teammate;
    `min_races` filter to exclude replacement/one-off drivers
- `src/analysis/__init__.py` — intra_team module exported to public API
- `tests/test_intra_team.py` — 23 tests covering all functions (87 total, all passing)
- `notebooks/03_pace_and_strategy.ipynb` — intra-team driver comparison notebook:
  - 2022 Y1 mean qualifying gap by constructor (22 rounds)
  - 2026 Y1 mean qualifying gap by constructor (3 rounds: Australia, China, Japan)
  - Driver dominance: who outqualified their teammate more often (2022 Y1)
  - Field-wide mean and median gap comparison: 2022 Y1 vs 2026 Y1
  - Gap distribution boxplot across both eras
  - Like-for-like constructor comparison across the regulation reset
  - Auto-populated summary table (re-runs update automatically)

### Analysis

- Field-wide mean intra-team qualifying gap: 0.816s (2022 Y1) vs 0.349s (2026 Y1)
- Field-wide median gap: 0.350s (2022 Y1) vs 0.276s (2026 Y1)
- 2026 figures directional only — 3 rounds; will mature across the season
- Every like-for-like constructor showed a tighter teammate gap in
  2026 Y1 vs 2022 Y1
- 2022 standouts: ALB (Williams, 95%), NOR (McLaren, 90.9%), VER (Red Bull, 81.8%)

---

## [v0.3.0] — 2026-04-01

### Added

- `notebooks/02_2026_era_year1.ipynb` — 2026 Year 1 analysis notebook:
  - Dynamically loads all available 2026 rounds via FastF1 with OpenF1 fallback
    (re-runnable as Miami and later races land)
  - Cancelled rounds (Bahrain, Saudi Arabia) skipped gracefully
  - Same four metrics as baseline: constructor Gini, P1–P10 lap gap,
    DNF rate, quali→race conversion
  - Like-for-like Year 1 comparison: 2026 R1–N vs 2022 R1–N (round-matched)
  - Driver continuity section: who crossed the era boundary and with which team
- `src/data/fastf1_loader.py` — `get_race_control_flags(session)` function:
  - Returns `had_sc`, `had_vsc`, `had_red_flag` booleans per race
  - Uses structured `Flag` column from `race_control_messages` (not free-text)
- Race control flags (`had_sc`, `had_vsc`, `had_red_flag`) added to both
  notebook datasets and annotated on lap time charts

### Fixed

- `src/analysis/reliability.py` — `is_dnf()` now correctly treats `'Lapped'`
  (FastF1 2026+ format) and `'+N Lap(s)'` as classified finishes, not DNFs
  (previously miscounted 297 lapped finishers as DNFs in the 2022–2025 dataset)
- `src/analysis/quali_race_delta.py` — same `'Lapped'` fix applied to DNF flag
- Both notebook loading cells: sprint weekend format filter updated from
  hardcoded allowlist to `!= 'testing'`, catching `sprint_shootout` (2023)
  and `sprint_qualifying` (2024+) formats — previously missing 18 races
- OpenF1 fallback date-based session matching: sprint weekends have two OpenF1
  sessions labelled `'Race'`; now picks the Sunday GP by taking the latest
  session within 1 day of the FastF1 `EventDate`
- DNS statuses (`'Did not start'`, `'Did not qualify'`, `'Withdrew'`) now set
  `finish_position=None` rather than inheriting a classified position
- `is_sprint_weekend` flag added to all result rows in both notebooks

### Data

- 2022–2025 baseline corrected: 92 races, 1838 entries (up from 74/1478)
- 2026: 3 rounds loaded (Australia, China, Japan); sprint weekend flagged (China)
- Race control summary printed at load time for both datasets

---

## [v0.2.0] — 2026-04-01

### Added

- `src/analysis/points_spread.py` — Gini coefficient, cumulative points gap,
  season-end Gini by round
- `src/analysis/reliability.py` — DNF rate by constructor/driver/year,
  DNF cause frequency
- `src/analysis/lap_time_delta.py` — fastest lap per driver, P1–Pn gap,
  season mean gap
- `src/analysis/quali_race_delta.py` — position delta, quali->race conversion
  by driver and constructor
- `src/analysis/__init__.py` — unified public API across all analysis modules
- `tests/test_points_spread.py`, `tests/test_reliability.py`,
  `tests/test_lap_time_delta.py`, `tests/test_quali_race_delta.py`
- `notebooks/01_2022_era_baseline.ipynb` — full 2022–2025 baseline:
  74 races, 1478 entries

### Analysis

- Constructor points Gini: 2022 anomaly; subsequent years trend toward
  convergence
- Lap time field spread: downward trend across era; 2024 anomaly flagged
  for further investigation
- DNF rates: 2024 showed elevated failure rates across most constructors
- Quali->race conversion: Red Bull pattern requires year-on-year breakdown
  for meaningful interpretation

### Decisions

- Same circuit as primary comparison basis for 2026 vs 2022 (not round
  number) — ADR-006
- FastF1 primary for 2026 data; OpenF1 as cross-check — ADR-005

---

## [v0.1.0] — 2026-03-31

### Added

- `src/data/fastf1_loader.py` — FastF1 session loader with automatic cache initialisation
- `src/data/openf1_client.py` — OpenF1 REST client (sessions, drivers, laps, pit stops, race control)
- `src/models/` — `RaceResult`, `LapSummary`, `DriverStanding`, `ConstructorStanding`
- `src/utils/era_helper.py` — maps calendar year → era name + year-within-era (1-indexed)
- `tests/test_models.py`, `tests/test_era_helper.py` — 21 tests, all passing
- `notebooks/00_data_validation.ipynb` — end-to-end validation of all data sources and models

---

## [v0.1.0-scaffold] — 2026-03-31

Initial project scaffolding. No analysis code yet — establishes structure, tooling, and governance before implementation begins.

### Added

- `CLAUDE.md` — domain knowledge, architecture patterns, development guidelines
- `BACKLOG.md` — MoSCoW-prioritised roadmap across v0.1.0–v0.6.0
- `README.md` — public-facing project summary
- `CHANGELOG.md` — this file
- Python package structure: `src/`, `tests/`, `notebooks/`, `data/cache/`, `docs/`
- `requirements.txt` — FastF1, OpenF1, pandas, numpy, jupyterlab, matplotlib, seaborn, plotly, pytest
- `.gitignore` — Python, venv, FastF1 cache, Jupyter checkpoints, secrets, IDE artefacts
- `.env.example` — environment variable template
- `pytest.ini` — test runner configuration
- `docs/decisions.md` — architectural decision log (ADR-001 through ADR-004)
- `docs/data_sources.md` — FastF1 and OpenF1 API reference
- `.github/PULL_REQUEST_TEMPLATE.md` — standardised PR descriptions
- Claude Code skills: `/new-session`, `/update-backlog`, `/analyse-era`
- Pre-commit hook: runs pytest before every commit

### Decisions

- OpenF1 selected as historical data source; Ergast excluded (maintenance mode, pre-2022 out of scope) — ADR-001
- Notebooks-first output; no UI framework before v0.6.0 — ADR-002
- FastF1 as primary session data source; OpenF1 secondary for results/standings — ADR-003
- 2022 Ground Effect Era as analysis baseline for 2026 comparison — ADR-004

### 2026 Season Context

- Completed rounds: Australia (R1), China (R2), Japan (R3)
- Cancelled: Bahrain, Saudi Arabia (April 2026) — regional conflict
- Next race: Miami GP (~May 2026)
