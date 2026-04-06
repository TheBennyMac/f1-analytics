# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

---

## [v0.6.0] — 2026-04-06

### Added

- `scripts/export_data.py` — data pipeline layer:
  - `export(**dataframes)` — validates schema, coerces dtypes, atomic Parquet
    write (`.tmp` staging → rename), updates `manifest.json`
  - `read(name)` — reads a single Parquet from `data/computed/`
  - `manifest_summary()` — prints row counts and export timestamps
  - SCHEMAS dict covering all 7 exported files
- `data/computed/` — pre-computed Parquet pipeline directory; `.gitkeep` tracked,
  `.parquet` files gitignored
- `scripts/update_all.py` — post-race rebuild orchestrator:
  - Executes notebooks 02 and 04 headlessly via `jupyter nbconvert`
  - Runs `quarto render site/`
  - Stages `site/docs/` and `manifest.json` for commit
  - Usage: `python scripts/update_all.py --season YYYY --round N`
- `site/` — Quarto website project:
  - `_quarto.yml` — website config, darkly theme, navbar, `docs/` output dir
  - `index.qmd` — landing page reading from `manifest.json`; data coverage table
  - `narratives/01-dnf-categorisation.qmd` — DNF cause categorisation
  - `narratives/02-ferrari-trajectory.qmd` — Ferrari championship trajectory
    (Plotly line chart)
  - `narratives/03-monaco-overtake.qmd` — Monaco overtake index (Plotly bar)
  - `narratives/04-safety-car.qmd` — safety car lottery (Plotly subplots)
  - `narratives/05-drs-active-aero.qmd` — DRS vs active aero (Plotly scatter)
  - `narratives/06-pit-stop-excitement.qmd` — pit stop excitement (Plotly scatter)
  - `narratives/07-turn1-chaos.qmd` — Turn 1 chaos (Matplotlib bar)
- Export cells added to `notebooks/02_2026_era_year1.ipynb` and
  `notebooks/04_narrative_testing.ipynb`
- `pyarrow` added to `requirements.txt`
- First export run: 7 Parquet files, `manifest.json` verified

### Infrastructure

- `.gitignore` updated: `data/computed/*.parquet` and `site/docs/*` gitignored;
  `.gitkeep` files tracked to preserve directory structure
- `QUARTO_PYTHON` environment variable set to `C:\Python313\python.exe` to
  direct Quarto to the correct Python installation on Windows

### Analysis

- All 7 narrative verdicts confirmed on first site render:
  - DNF categorisation: Inconclusive (data source insufficient)
  - Ferrari trajectory: Not supported (2 seasons only)
  - Monaco overtake index: Partially supported
  - Safety car lottery: Supported
  - DRS vs active aero: Not supported (3 rounds — directional only)
  - Pit stop excitement: Partially supported — era-specific
  - Turn 1 chaos: Supported

---

## [v0.5.6] — 2026-04-06

### Added

- `src/analysis/turn1.py` — Turn 1 chaos analysis:
  - `first_lap_retirements()` — first-lap DNF rate per race, grouped by
    era year; accepts optional `season_laps` dict to detect early retirements
    by lap count (FastF1 assigns positions 1–20 to all drivers, so
    `finish_position` alone cannot identify lap 1 retirements)
  - `lap1_position_changes()` — positions gained on lap 1 vs grid position
  - `turn1_summary_by_era_year()` — aggregates DNF metrics by year-within-era
- `tests/test_turn1.py` — 25 tests (287 total passing)
- `src/analysis/__init__.py` — turn1 module exported
- `notebooks/04_narrative_testing.ipynb` — Section 7: Turn 1 chaos
  - First-lap retirement rate by era year (bar chart)
  - DNS count by era year (bar chart — shows opposite pattern to DNFs)
  - Findings and verdict documented

### Fixed

- `first_lap_retirements()` — initial implementation used `finish_position.isna()`
  which never fires with real FastF1 data; replaced with lap count threshold
  (≤ 2 laps completed) when `season_laps` is provided

### Analysis

- Year 1 (2022): 9 first-lap DNFs across 22 races — mean rate 2.1%
- Years 2–4: 3–4 DNFs per season — mean rate 0.6–0.9%
- Rate falls monotonically; stabilises by Year 3
- DNS events could not be measured — FastF1 excludes non-starters from
  session results entirely
- **Narrative verdict: supported** — first-lap chaos is measurably higher
  in the regulation reset year; converges rapidly as the era matures

### Milestone

- **v0.5.0 Narrative Testing milestone complete** — all seven narratives
  tested and documented in `notebooks/04_narrative_testing.ipynb`

---

## [v0.5.5] — 2026-04-06

### Added

- `src/analysis/pit_window.py`:
  - `position_changes_by_phase()` — positions gained per lap pre/post
    median pit lap split; excludes pit laps from both phases
  - `pit_excitement_summary()` — aggregates across multiple races
- `tests/test_pit_window.py` — 10 new tests (24 total, 262 total passing)
- `src/analysis/__init__.py` — new functions exported
- `notebooks/04_narrative_testing.ipynb` — Section 6: pit stop excitement
  - Lap data loader for 2022 and 2026 non-sprint races
  - Grouped bar: mean pre vs post positions gained per lap by era
  - Scatter: pre vs post per race with diagonal reference line
  - Findings and verdict documented

### Analysis

- 2022 Ground Effect Era: pre 2.592 vs post 2.556 positions/lap (17 races)
  — negligible difference; narrative does not hold for this era
- 2026 Era: pre 4.052 vs post 1.144 positions/lap (2 races, directional)
  — 3.5\u00d7 drop post-stop; likely reflects Hard tyre characteristics
- **Narrative verdict: partially supported, era-specific** — effect is
  dramatic in 2026 but absent in 2022. Revisit as 2026 season matures.

---

## [v0.5.4] — 2026-04-06

### Added

- `src/analysis/overtake_index.py` — `overtake_index_by_era()`: groups
  race-level overtake index by regulation era using EraHelper
- `tests/test_overtake_index.py` — 7 new tests for `overtake_index_by_era()`
  (33 total in file, 252 total passing)
- `src/analysis/__init__.py` — `overtake_index_by_era` exported
- `notebooks/04_narrative_testing.ipynb` — Section 5: DRS vs active aero
  - Lightweight 2026 results loader (FastF1 + OpenF1 fallback; future
    rounds skipped gracefully)
  - Era comparison bar chart: Ground Effect Era vs 2026 Era
  - Per-race scatter coloured by era
  - Findings and verdict documented

### Analysis

- Ground Effect Era (DRS, 2022–2025): mean overtake index 1.688 (92 races)
- 2026 Era (active aero, 3 rounds): mean overtake index 1.874
- **Narrative verdict: not supported** — position changes are higher in
  2026 without DRS, not lower. 3 rounds is directional only; early 2026
  circuits may be inherently higher-overtaking. Revisit as season matures.

---

## [v0.5.3] — 2026-04-05

### Added

- `src/data/fastf1_loader.py` — `get_race_control_flags()` extended to
  return `sc_count`, `vsc_count`, `red_flag_count` (distinct deployment
  events) alongside existing boolean flags
- `src/analysis/safety_car.py` — safety car lottery analysis:
  - `sc_counts_per_race()` — one row per race with deployment counts
    and `any_intervention` flag
  - `sc_position_impact()` — joins SC counts with overtake index per race
  - `sc_lottery_summary()` — mean overtake index grouped by SC count
    (0 SCs / 1 SC / 2+ SCs)
  - `intervention_frequency()` — SC/VSC/red flag rates by season
- `tests/test_safety_car.py` — 25 tests (245 total passing)
- `src/analysis/__init__.py` — safety_car module exported
- `notebooks/04_narrative_testing.ipynb` — Section 4: SC lottery
  - Intervention frequency table by season
  - Bar chart: mean overtake index by SC count group
  - Scatter: SC deployments vs overtake index per race
  - Findings and verdict documented
- Title cell updated to reflect all four completed narratives

### Analysis

- SC deployment rate: 73% in 2022, declining to 33% in 2024, 50% in 2025
- Overtake index: 1.487 (0 SCs) → 1.767 (1 SC) → 2.131 (2+ SCs)
- **Narrative verdict: supported** — each SC deployment correlates with
  materially more position changes; effect compounds with multiple
  deployments

---

## [v0.5.2] — 2026-04-05

### Added

- `src/analysis/overtake_index.py` — overtake index analysis:
  - `position_changes_per_race()` — net position delta per driver per race;
    excludes DNFs and pit-lane starters (grid == 0)
  - `overtake_index_per_race()` — positions gained / starters per race
    (normalised for field size and attrition)
  - `overtake_index_by_circuit()` — mean index per circuit across seasons,
    sorted ascending (most processional first)
  - `monaco_vs_field()` — circuit rankings with target circuit flagged
- `tests/test_overtake_index.py` — 26 tests (220 total passing)
- `src/analysis/__init__.py` — overtake_index module exported
- `notebooks/04_narrative_testing.ipynb` — Section 3: Monaco overtake index
  - Bar chart of all circuits ranked by mean overtake index (2022–2025)
  - Monaco highlighted; field mean reference line
  - Findings table and narrative verdict

### Analysis

- Monaco mean overtake index: 2nd lowest on the calendar, behind Japan
- Both considerably below the field mean
- **Narrative verdict: partially supported** — Monaco is genuinely
  low-overtaking but not uniquely so; Japan is comparably processional
- Insight: both circuits are qualifying spectacles where grid position
  is structurally decisive — low overtaking and high qualifying interest
  appear to be two sides of the same coin

---

## [v0.5.1] — 2026-04-04

### Added

- `notebooks/04_narrative_testing.ipynb` — Section 2 executed and findings documented:
  - Ferrari championship trajectory charts for 2022 and 2024
  - Inflection point annotations on cumulative points gap charts
  - Multi-constructor comparison overlaid per season

### Analysis

- 2022: Ferrari gap widened at Round 5 — but Red Bull had early engine failures;
  Ferrari were leading the championship to that point
- 2024: Gap widened at Round 3, then again Round 7–8;
  Ferrari closed from Round 18
- Rate of decline in 2022 similar to Mercedes — Red Bull simply dominated the field
- 2024: Ferrari second-best for most of the season behind Red Bull, then McLaren
- **Narrative verdict: not supported** — no consistent "bottling it" pattern across
  these two seasons; two data points are directional only, not statistically conclusive

### Deferred

- Full championship lead conversion rate requires pre-2022 data — see v0.7.0

---

## [v0.5.0] — 2026-04-04

### Added

- `src/analysis/dnf_categorisation.py` — DNF cause classification:
  - `categorise_dnf()` — classifies status strings as Mechanical,
    Collision, or Unknown
  - `dnf_category_counts()` — grouped counts by season/era year/constructor
  - `mechanical_share_by_era_year()` — mechanical DNF share per year-within-era
- `src/analysis/championship_trajectory.py` — constructor points trajectory:
  - `cumulative_constructor_points()` — running points total by round
  - `points_gap_to_leader()` — gap to championship leader per round
  - `constructor_trajectory()` — filtered trajectory for named constructors
  - `gap_inflection_round()` — round where gap starts widening
    (first sustained increase)
- `src/analysis/__init__.py` — both modules exported to public API
- `tests/test_dnf_categorisation.py` — coverage for categorisation logic
- `tests/test_championship_trajectory.py` — 15 tests (194 total passing)
- `notebooks/04_narrative_testing.ipynb` — narrative testing notebook:
  - Section 1: DNF cause categorisation across 2022–2025
  - Section 2: Ferrari championship trajectory (2022, 2024)

### Analysis

- DNF categorisation verdict: **inconclusive** — FastF1 status strings degrade
  from 2023 onward; 2024–2025 show zero attributed DNFs (all "Retired")
- 2022 data credible (52% Mechanical / 48% Collision) but year-on-year comparison
  not possible from this source alone
- `dnf_categorisation.py` retained as infrastructure for richer future datasets

---

## [v0.4.0] — 2026-04-03

### Added

- `src/analysis/sector_times.py` — sector time breakdown:
  - `best_sector_times()` — best S1/S2/S3 per driver per session
    (pit laps excluded)
  - `sector_gap()` — P1-Pn gap per sector for a single race
  - `sector_gap_summary()` — aggregate sector gaps across multiple races
  - `mean_sector_gap_by_season()` — season-level mean sector gap
- `src/analysis/tyre_strategy.py` — tyre compound strategy:
  - `stints_from_laps()` — stint-level data (driver, team, compound,
    laps) from FastF1 laps
  - `strategy_summary()` — compounds used and number of stops per
    driver per race
  - `mean_stint_length()` — mean stint length per compound across a race
  - `compound_usage_by_constructor()` — compound usage aggregated
    across multiple races
- `src/analysis/field_spread.py` — field normalisation, P11, tail-of-field:
  - `p1_to_pn_gap_normalised()` — P1-Pn gap with attrition races flagged
    (emits a row for every race; `sufficient=False` where field < n)
  - `p11_gap_per_race()` — P10-P11 and P1-P11 lap time gaps per race
  - `tail_gap_analysis()` — last-classified-driver gap to P1 and P10
    per race
- `src/analysis/sprint_analysis.py` — sprint race analysis:
  - `sprint_position_changes()` — positions gained/lost per driver
    in a sprint
  - `sprint_vs_race_pace()` — median sprint vs full race lap pace
    per driver
  - `flag_sprint_weekends()` — deduplicated sprint weekend flags
    from results data
- `src/analysis/pit_window.py` — pre/post pit window analysis:
  - `median_pit_lap()` — median first pit stop lap across all drivers
  - `lap_time_deltas_by_phase()` — mean P1-P5 per-lap gap
    before/after split lap
  - `pit_window_summary()` — pre/post pit window phase metrics
    across multiple races
- `src/analysis/__init__.py` — all new modules exported to public API
- `tests/test_sector_times.py` — 13 tests
- `tests/test_tyre_strategy.py` — 13 tests
- `tests/test_field_spread.py` — 14 tests
- `tests/test_sprint_analysis.py` — 13 tests
- `tests/test_pit_window.py` — 12 tests
- `notebooks/03_pace_and_strategy.ipynb` — 14 new sections added
  (sections 8–14):
  - Race results loading cell (lightweight; used for quali-race delta)
  - Race laps loading cell (heavy; used for all lap-level analyses)
  - Sections 8–14 covering all remaining v0.4.0 analyses

- `src/analysis/intra_team.py` — intra-team qualifying gap analysis:
  - `prepare_quali_results()` — normalises FastF1 qualifying session results
  - `teammate_quali_gaps()` — gap (seconds + %) per constructor per race
  - `season_teammate_gaps()` — aggregates across multiple races
  - `mean_gap_by_constructor()` — season-level mean gap, sorted closest first
  - `driver_dominance()` — how often each driver outqualified their teammate;
    `min_races` filter to exclude replacement/one-off drivers
- `src/analysis/__init__.py` — intra_team module exported to public API
- `tests/test_intra_team.py` — 23 tests covering all functions
  (87 total, all passing)
- `notebooks/03_pace_and_strategy.ipynb` — intra-team driver
  comparison notebook:
  - 2022 Y1 mean qualifying gap by constructor (22 rounds)
  - 2026 Y1 mean qualifying gap by constructor
    (3 rounds: Australia, China, Japan)
  - Driver dominance: who outqualified their teammate more often (2022 Y1)
  - Field-wide mean and median gap comparison: 2022 Y1 vs 2026 Y1
  - Gap distribution boxplot across both eras
  - Like-for-like constructor comparison across the regulation reset
  - Auto-populated summary table (re-runs update automatically)

### Analysis

- Field-wide mean intra-team qualifying gap: 0.816s (2022 Y1)
  vs 0.349s (2026 Y1)
- Field-wide median gap: 0.350s (2022 Y1) vs 0.276s (2026 Y1)
- 2026 figures directional only — 3 rounds; will mature across the season
- Every like-for-like constructor showed a tighter teammate gap in
  2026 Y1 vs 2022 Y1
- 2022 standouts: ALB (Williams, 95%), NOR (McLaren, 90.9%),
  VER (Red Bull, 81.8%)

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
- 2026: 3 rounds loaded (Australia, China, Japan); sprint weekend
  flagged (China)
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

- `src/data/fastf1_loader.py` — FastF1 session loader with automatic
  cache initialisation
- `src/data/openf1_client.py` — OpenF1 REST client (sessions, drivers,
  laps, pit stops, race control)
- `src/models/` — `RaceResult`, `LapSummary`, `DriverStanding`,
  `ConstructorStanding`
- `src/utils/era_helper.py` — maps calendar year → era name +
  year-within-era (1-indexed)
- `tests/test_models.py`, `tests/test_era_helper.py` — 21 tests, all passing
- `notebooks/00_data_validation.ipynb` — end-to-end validation of
  all data sources and models

---

## [v0.1.0-scaffold] — 2026-03-31

Initial project scaffolding. No analysis code yet — establishes
structure, tooling, and governance before implementation begins.

### Added

- `CLAUDE.md` — domain knowledge, architecture patterns, development guidelines
- `BACKLOG.md` — MoSCoW-prioritised roadmap across v0.1.0–v0.6.0
- `README.md` — public-facing project summary
- `CHANGELOG.md` — this file
- Python package structure: `src/`, `tests/`, `notebooks/`,
  `data/cache/`, `docs/`
- `requirements.txt` — FastF1, OpenF1, pandas, numpy, jupyterlab,
  matplotlib, seaborn, plotly, pytest
- `.gitignore` — Python, venv, FastF1 cache, Jupyter checkpoints,
  secrets, IDE artefacts
- `.env.example` — environment variable template
- `pytest.ini` — test runner configuration
- `docs/decisions.md` — architectural decision log (ADR-001 through ADR-004)
- `docs/data_sources.md` — FastF1 and OpenF1 API reference
- `.github/PULL_REQUEST_TEMPLATE.md` — standardised PR descriptions
- Claude Code skills: `/new-session`, `/update-backlog`, `/analyse-era`
- Pre-commit hook: runs pytest before every commit

### Decisions

- OpenF1 selected as historical data source; Ergast excluded
  (maintenance mode, pre-2022 out of scope) — ADR-001
- Notebooks-first output; no UI framework before v0.6.0 — ADR-002
- FastF1 as primary session data source; OpenF1 secondary for
  results/standings — ADR-003
- 2022 Ground Effect Era as analysis baseline for 2026 comparison — ADR-004

### 2026 Season Context

- Completed rounds: Australia (R1), China (R2), Japan (R3)
- Cancelled: Bahrain, Saudi Arabia (April 2026) — regional conflict
- Next race: Miami GP (~May 2026)
