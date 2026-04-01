# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

_v0.3.0 2026 Era: First Data — work begins on `release/v0.3.0`._

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
