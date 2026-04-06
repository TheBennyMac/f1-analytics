# CLAUDE.md - F1 Analytics

## Project Overview

An F1 data analytics project focused on surfacing objective insights from historical race data — particularly around regulation era transitions, how quickly teams converge toward parity, and where public narratives align or conflict with the numbers.

### Core Focus

- **Primary comparison: 2022 Ground Effect Era vs 2026 Era** — like-for-like team and driver comparison across the regulation reset
- **Era Transition Analysis**: How fast does the field converge after a regulation reset?
- **Parity Metrics**: Points spread, lap time gaps, DNF rates, overtaking counts by era year
- **Qualifying vs Race Pace**: Consistency between one-lap pace and race pace by team/driver
- **Reliability**: DNF/retirement rates by era, team, and regulation phase year
- **Narrative vs Data**: Surface where the "received wisdom" holds up and where it doesn't

### Output Philosophy

- **Notebooks first** — all analysis is explored and validated in Jupyter notebooks before any UI is considered
- **Publishing layer: Quarto → GitHub Pages** — decided at v0.6.0. Notebooks are the working environment; `.qmd` pages in `site/` are the published artefact. These are not the same files.
- **Product type: narrative/portfolio artefact** — not an interactive analytics tool. Readers follow authored narratives; they do not query the data themselves.
- **Interactivity: Level 1 only** — hover/zoom via Plotly on scatter plots where race/circuit identity adds value. No filtering, no dynamic querying.
- **2026 season is live and unfolding** — datasets will mature race by race. Design data loaders to be re-runnable as new sessions become available.

### 2026 Season Context (as of 2026-04-04)

- Completed rounds: Australia (R1), China (R2), Japan (R3)
- Bahrain and Saudi Arabia (Middle East rounds, April 2026) cancelled due to regional conflict
- Next upcoming race: Miami GP (~May 2026)
- The convergence narrative for 2026 will be built incrementally across the season

## Regulation Eras (Domain Knowledge)

Use these boundaries for era-based grouping:

| Era                   | Years     | Key Change                                |
|-----------------------|-----------|-------------------------------------------|
| Refuelling Era        | 1994–2009 | Refuelling allowed; V10 -> V8            |
| KERS/DRS Era          | 2010–2013 | No refuelling, KERS, DRS introduced 2011  |
| Hybrid Power Unit Era | 2014–2021 | V6 turbo hybrid; complex PU regulations   |
| Ground Effect Era     | 2022–2025 | Cost cap, ground effect aero, 18" tyres   |
| 2026 Era              | 2026–     | New PU regs, active aero, current season  |

**Within each era, year 1 is the regulation reset year.** Analysis of convergence should track gap metrics relative to "Year N of era" not calendar year.

## Data Sources

- **FastF1** (primary): Python library for session data from ~2018 onward. Lap times, telemetry, tyre compounds, weather, sector times, pit stops. Requires local cache.
- **OpenF1** (secondary REST): Actively maintained open API covering 2023–present. Used for results, standings, and session data where FastF1 is insufficient.
- **Ergast API** (excluded): In maintenance mode and reaches back to 1950, but pre-2022 data is out of scope — the further back, the less technically relevant for era comparison. Revisit only if pre-2022 narrative testing (v0.5.0) requires it.
- **Do NOT use** F1 Live Timing credentials or f1-dash.com until licensing is verified.

### FastF1 Cache

Always enable caching. The cache directory is `data/cache/`. Never commit cache files.

```python
import fastf1
fastf1.Cache.enable_cache('data/cache/')
```

## Project Structure

```text
f1-analytics/
├── CLAUDE.md              # This file
├── BACKLOG.md             # Feature backlog with MoSCoW prioritization
├── CHANGELOG.md           # Version history
├── README.md              # Project overview (GitHub-facing)
├── requirements.txt       # fastf1==3.8.2 pinned — do not unpin without updating CHANGELOG
│
├── src/                   # ANALYSIS LAYER — pure functions, no I/O, no presentation
│   ├── analysis/          # Analysis modules (turn1, pit_window, safety_car, etc.)
│   ├── data/              # FastF1 loader, OpenF1 client
│   ├── models/            # RaceResult, LapSummary, DriverStanding, etc.
│   └── utils/             # era_helper, shared utilities
│
├── notebooks/             # Exploration and validation — numbered, not published directly
│   ├── 00_data_validation.ipynb
│   ├── 01_2022_era_baseline.ipynb
│   ├── 02_2026_era_year1.ipynb
│   ├── 03_pace_and_strategy.ipynb
│   └── 04_narrative_testing.ipynb
│
├── data/
│   ├── cache/             # FastF1 local cache — gitignored
│   └── computed/          # DATA PIPELINE LAYER — pre-exported Parquet files
│       ├── manifest.json  # Committed: records what was exported, when, at which round
│       └── *.parquet      # Gitignored — regenerated locally after each race
│
├── scripts/               # Orchestration only — no analysis logic
│   ├── export_data.py     # Exports DataFrames from notebooks to data/computed/
│   └── update_all.py      # Full post-race rebuild: notebooks → export → render → commit
│
├── site/                  # PRESENTATION LAYER — Quarto project
│   ├── _quarto.yml        # Site config, navbar, theme
│   ├── index.qmd          # Landing page with manifest metadata
│   ├── narratives/        # One .qmd file per narrative (reads from data/computed/ only)
│   │   ├── 01-dnf-categorisation.qmd
│   │   ├── 02-ferrari-trajectory.qmd
│   │   ├── 03-monaco-overtake.qmd
│   │   ├── 04-safety-car.qmd
│   │   ├── 05-drs-active-aero.qmd
│   │   ├── 06-pit-stop-excitement.qmd
│   │   └── 07-turn1-chaos.qmd
│   └── docs/              # Quarto render output — GitHub Pages root (gitignored except on deploy)
│
├── tests/                 # pytest test files — covers all src/analysis/ functions
└── docs/
    ├── decisions.md       # Architectural decision log
    └── data_sources.md    # FastF1, OpenF1 API reference
```

## Development Guidelines

### Code Style

- snake_case for Python throughout
- Small, single-responsibility functions
- Comments only where logic is non-obvious
- Type hints on all public functions

### Working with Claude

- Always read existing code before modifying
- Start new chat windows at major phase boundaries — CLAUDE.md is the handoff document
- Run retrospective after each release to update this file
- Use `/update-backlog` skill to keep BACKLOG.md current

### Testing Requirements

- Unit tests for all analysis logic
- New modules get dedicated test files (`tests/test_<module>.py`)
- Run before every commit: `python -m pytest tests/ -v`
- Edge cases: missing sessions, cancelled races, DNFs mid-lap, incomplete seasons

### Git Workflow

- Branch naming: `release/X.Y.Z`
- Commit messages: descriptive + version tag, e.g. `feat: add era convergence chart (v0.1.0)`
- PR to `main` when release is complete
- No `gh` CLI — PRs via GitHub web UI

### Security

- API keys and credentials in `.env` (gitignored)
- Never hardcode credentials
- FastF1 data is free to use for non-commercial analysis

## Architecture Patterns

### Layer Separation (enforced from v0.6.0)

Three layers with strict boundaries:

| Layer | Location | Reads from | Must not |
|---|---|---|---|
| Analysis | `src/` | Nothing (pure functions) | Touch files, call FastF1, render charts |
| Pipeline | `data/computed/` + `scripts/` | FastF1 cache via `src/data/` | Contain analysis logic |
| Presentation | `site/` | `data/computed/` + `src/analysis/` | Call FastF1 or notebook state |

### Data Flow

```text
FastF1 cache → src/data/ loaders → notebooks (exploration)
                                 → scripts/export_data.py → data/computed/*.parquet
                                                          → site/*.qmd (published)
```

### Era Helper Pattern

All analysis that groups by era uses `src/utils/era_helper.get_year_within_era(season)`,
which maps a calendar year to year-within-era (1, 2, 3…). This is built and in use.

### Data Pipeline Pattern

After each race, `scripts/update_all.py` orchestrates:
1. Execute notebooks headlessly via `nbconvert`
2. Validate and export DataFrames to `data/computed/` (atomic — staging then promote)
3. Update `data/computed/manifest.json` with export date, FastF1 version, row counts
4. Run `quarto render site/`
5. Commit `site/docs/` and `manifest.json`

`manifest.json` is always committed. Parquet files are always gitignored.

### Chart Strategy (v0.6.0 decision — do not revisit without cause)

- **Plotly**: scatter plots where hovering reveals race or circuit identity
- **Matplotlib**: bar charts with ≤ 8 bars, or any chart where the findings table carries the values
- Converted charts (Plotly): Ferrari trajectory line, Monaco circuit bar, SC scatter, DRS scatter, pit excitement scatter
- Do not convert additional charts without applying the decision rule: "does hover reveal information not in the axis or findings table?"

### Visualization Standards

- Quarto site uses Plotly for Level 1 interactivity (hover/zoom) — no filtering or dynamic querying
- Notebooks continue to use Matplotlib or Plotly as convenient for exploration
- All analysis logic stays in `src/analysis/` — `.qmd` pages are thin composition layers only

## Key Metrics Glossary

- **Lap delta**: Gap to fastest lap, expressed in seconds or %
- **Convergence rate**: How the P1–P10 gap changes across years within an era
- **Quali-race delta**: Difference between qualifying position and race finishing position (consistency proxy)
- **DNF rate**: Retirements as % of race starts, by era/team/year
- **Points entropy**: Statistical spread of constructor points — high entropy = competitive field
- **Overtake index**: Estimated overtakes per race (from position change data)

## Getting Started

1. `python -m pip install -r requirements.txt`
2. Run tests: `python -m pytest tests/ -v`
3. Launch notebooks: `python -m jupyterlab`
4. Check BACKLOG.md for current work
5. FastF1 first-run will populate the cache — expect slow initial loads

### Windows note

Packages are installed to the user AppData location, so pip-installed scripts
are not on PATH. Always use `python -m <tool>` — never bare commands:

- `python -m jupyterlab` — NOT `jupyter lab`
- `python -m pytest tests/ -v` — NOT `pytest tests/ -v`
- `python -m pip install ...` — NOT `pip install ...`
