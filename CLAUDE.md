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
- **UI tooling is undecided** — do not assume Streamlit or any specific framework. When visualisation is needed, evaluate the most appropriate tool at that point. Keep all analysis code completely decoupled from any presentation layer.
- **2026 season is live and unfolding** — datasets will mature race by race. Design data loaders to be re-runnable as new sessions become available.

### 2026 Season Context (as of 2026-03-31)

- First two races (Middle East) cancelled — next race is Miami GP (~May 2026)
- This gives time to build and validate the 2022 era foundation before 2026 data accumulates
- The convergence narrative for 2026 will be built incrementally across the season

## Regulation Eras (Domain Knowledge)

Use these boundaries for era-based grouping:

| Era                    | Years     | Key Change                              |
|------------------------|-----------|------------------------------------------|
| Refuelling Era         | 1994–2009 | Refuelling allowed; V10 → V8            |
| KERS/DRS Era           | 2010–2013 | No refuelling, KERS, DRS introduced 2011 |
| Hybrid Power Unit Era  | 2014–2021 | V6 turbo hybrid; complex PU regulations  |
| Ground Effect Era      | 2022–2025 | Cost cap, ground effect aero, 18" tyres  |
| 2026 Era               | 2026–     | New PU regs, active aero, current season |

**Within each era, year 1 is the regulation reset year.** Analysis of convergence should track gap metrics relative to "Year N of era" not calendar year.

## Data Sources

- **FastF1** (primary): Python library for session data from ~2018 onward. Lap times, telemetry, tyre compounds, weather, sector times, pit stops. Requires local cache.
- **Ergast API** (historical breadth): REST API for results, standings, lap times back to 1950. Use for era-level statistics. Note: Ergast is in maintenance mode — verify availability.
- **OpenF1** (alternative REST): Newer open API, good for recent seasons.
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
├── notebooks/             # Jupyter notebooks — primary analysis output (numbered)
│   ├── 00_data_validation.ipynb
│   ├── 01_2022_era_baseline.ipynb
│   ├── 02_2026_era_year1.ipynb
│   └── ...
├── src/
│   ├── data/              # Data loaders (FastF1, Ergast/OpenF1 clients)
│   ├── models/            # Data models (RaceResult, LapSummary, DriverStanding, etc.)
│   ├── analysis/          # Analysis modules (era_convergence, reliability, pace, etc.)
│   ├── visualizations/    # Placeholder — no framework chosen yet
│   └── utils/             # Helpers (era_helper, formatters, validators)
├── tests/                 # pytest test files
├── data/
│   └── cache/             # FastF1 local cache (gitignored)
└── docs/                  # Era analysis specs, data source notes
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

### Data Flow

```text
FastF1 / Ergast API → Loaders (src/data/) → Models → Analysis modules → Visualizations
                                                     → Era metrics    → Convergence charts
                                                     → Reliability    → DNF charts
                                                     → Pace delta     → Quali vs Race charts
```

### Era Helper Pattern

All analysis that groups by era must use the `EraHelper` utility (to be built), which maps a calendar year to:

- Era name
- Year-within-era (1, 2, 3…)

This ensures consistent grouping across all analyses.

### Visualization Standards

- **No UI framework is decided yet.** Do not build Streamlit components or lock to any charting library until v0.4.0+.
- All notebook visualisations use whatever is most convenient for exploration (matplotlib, plotly, seaborn)
- When a UI layer is eventually added, analyse the options (Streamlit, Dash, Observable, static site) and choose based on what the analysis actually needs
- Keep all analysis logic in `src/analysis/` completely independent of any rendering layer

## Key Metrics Glossary

- **Lap delta**: Gap to fastest lap, expressed in seconds or %
- **Convergence rate**: How the P1–P10 gap changes across years within an era
- **Quali-race delta**: Difference between qualifying position and race finishing position (consistency proxy)
- **DNF rate**: Retirements as % of race starts, by era/team/year
- **Points entropy**: Statistical spread of constructor points — high entropy = competitive field
- **Overtake index**: Estimated overtakes per race (from position change data)

## Getting Started

1. `pip install -r requirements.txt`
2. Run tests: `python -m pytest tests/ -v`
3. Check BACKLOG.md for current work
4. FastF1 first-run will populate the cache — expect slow initial loads
