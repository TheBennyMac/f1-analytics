# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

_v0.1.0 Foundation work in progress on `release/v0.1.0`._

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
