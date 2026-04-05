# BACKLOG.md - F1 Analytics

## Current Version: v0.5.3 (Narrative Testing: Safety Car Lottery)

### Scope Decision (2026-03-31)

- **Primary focus**: 2022 Ground Effect Era (2022–2025) vs 2026 Era —
  direct comparison
- **Output**: Jupyter notebooks first; UI tooling decided later based
  on what the analysis needs
- **2026 data**: Matures race by race — completed rounds: Australia,
  China, Japan; next: Miami GP (~May 2026)

---

## Must Have (v0.1.0 — Foundation) ✅ Released 2026-03-31

- [x] FastF1 data loader with caching (`src/data/fastf1_loader.py`)
- [x] OpenF1 client for results and standings (`src/data/openf1_client.py`)
- [x] Core data models: `RaceResult`, `LapSummary`, `DriverStanding`,
  `ConstructorStanding`
- [x] Era helper utility: year → era name + year-within-era
  (`src/utils/era_helper.py`)
- [x] Basic test suite covering models and era helper (21 tests passing)
- [x] Notebook: `notebooks/00_data_validation.ipynb` — confirmed end-to-end

## Must Have (v0.2.0 — 2022 Era Baseline) ✅ Released 2026-04-01

- [x] Constructor points spread across 2022–2025 (Gini coefficient + raw gap)
- [x] P1–P10 lap time delta trend by year within era
- [x] DNF rate by team and year (2022–2025)
- [x] Quali position vs race finishing position consistency
- [x] Notebook: `notebooks/01_2022_era_baseline.ipynb`

## Must Have (v0.3.0 — 2026 Era: First Data) ✅ Released 2026-04-01

- [x] Ingest completed 2026 races: Australia, China, Japan (rounds 1–3)
- [x] Ingest 2026 season results as they arrive (Miami onward) —
  notebook is re-runnable
- [x] Note: Bahrain and Saudi Arabia (Middle East rounds, April 2026)
  cancelled due to regional conflict
- [x] Year 1 convergence: 2026 vs 2022 on same metrics
- [x] Like-for-like team/driver comparison across the regulation reset
- [x] Race control flags (SC, VSC, red flag) per race in both datasets
- [x] Notebook: `notebooks/02_2026_era_year1.ipynb`

## Should Have (v0.4.0 — Deeper Pace Analysis) ✅ Released 2026-04-03

- [x] Sector time breakdown (FastF1, 2022+)
- [x] Tyre compound strategy by team across eras
- [x] Quali-to-race pace delta: who converts, who doesn't
- [x] Intra-team driver comparison: who adapts better to a regulation reset?
  - Same constructor, same car — isolates driver factor from machinery
  - **Primary metric: qualifying gap between teammates** — purest driver
    comparison, eliminates strategy, traffic, and luck as variables
  - Secondary metric: race pace delta — useful but noisier
  - Also track: DNF rate, tyre degradation handling
  - Primary lens: 2026 Year 1 vs 2022 Year 1 (regulation reset comparison)
  - Exclude races with mechanical DNFs to keep the comparison clean
- [x] Field size normalisation for convergence comparisons
  - Cap field comparisons at the lowest classified finisher count across
    the races being compared (e.g. 12 finishers in 2022 Melbourne)
  - Offer fixed P1–P10 as primary view; normalised field as secondary
  - Flag attrition races clearly so gaps aren't misread as pace gaps
- [x] Points boundary and P11 analysis
  - Gap from P10 to P11 per race — how arbitrary is the points cut?
  - P11 gap to P1 as an alternative field spread metric
  - Connects to intra-team analysis: quali P9 but finish P11 is a
    different story to quali P14 and race to P11
- [x] Tail-of-field gap analysis (classified finishers only)
  - For drivers outside the points, track gap to race leader and to P10
    per race — how far behind is the back of the grid?
  - Only include drivers who completed the race distance
  - Useful for measuring whether regulation resets compress or stretch
    the full field, not just the front runners
- [x] Sprint race analysis
  - Load sprint sessions alongside race sessions (`session_type='S'`)
  - Compare sprint vs full race pace for same drivers on same weekend
  - Track position changes: sprint vs full race
  - Note: sprints have no mandatory pit stop — most cars finish on
    original tyres, making them a useful pit-stop-free baseline
  - Flag sprint weekends separately in all convergence metrics
- [x] Pre vs post pit window excitement in full-length Grand Prix
  - **2026 observation to test:** first half to two-thirds of the full
    race (before the main pit window) appears more competitive than
    the post-stop phase, where fresh tyres spread the field
  - Measure lap time deltas and position changes before and after the
    median pit lap for each race
  - Compare sprint (no stops) vs full race post-stop phase — does
    removing pit strategy produce closer racing?
  - Test whether this pattern is consistent across eras or specific
    to 2026 tyre characteristics
- [x] Notebook: `notebooks/03_pace_and_strategy.ipynb`

## Should Have (v0.5.0 — Narrative Testing)

- [x] "Ferrari always bottles it" — within-season points trajectory analysis
  - Original hypothesis (championship lead conversion rate) requires
    historical data beyond our 2022–2026 scope; deferred — see v0.7.0
  - Reframed for available data: in seasons where Ferrari was competitive
    (2022, 2024), track cumulative points gap to the eventual champion
    round by round — when does the gap open up and why?
  - Identify the inflection point where Ferrari's title challenge falters
  - Compare trajectory to other competitive constructors in the same seasons
  - **Verdict: not supported** — Ferrari led 2022 before Red Bull dominance;
    were second-best for most of 2024. Two seasons directional only.
- [x] "Monaco produces processional races" — overtake index by circuit
  - **Verdict: partially supported** — Monaco ranks 2nd lowest by overtake
    index (behind Japan); not uniquely processional. Both circuits are
    qualifying spectacles where grid position is structurally decisive.
- [x] "Safety car lottery" — SC frequency and position change correlation
  - Extend `had_sc`/`had_vsc`/`had_red_flag` booleans to deployment counts
    per race (a race with two SCs is materially different to one with one)
  - Count distinct deployment events from `race_control_messages` per session
  - **Verdict: supported** — overtake index rises with each SC deployment:
    1.487 (0 SCs) → 1.767 (1 SC) → 2.131 (2+). SC rate peaked at 73%
    in 2022, declining to 33% in 2024.
- [ ] "DRS made overtaking artificial" — overtake index pre/post DRS
- [ ] "Races are more exciting before the pit stop" — in full Grand Prix
    races, the pre-pit-stop phase (cars on original tyres, natural
    degradation) appears more competitive than the post-stop phase
    (field reset, fresh Hard tyres, gaps re-open)
  - Use `pit_window.py` phase split as foundation; extend with
    position change counts pre vs post median pit lap
  - Examine tyre compound angle: Medium pre-stop vs Hard post-stop —
    does compound choice correlate with processional post-stop racing?
  - Test whether this pattern is specific to 2026 or present across
    the Ground Effect Era
  - 2026 hypothesis: Hard tyres are not allowing effective racing
    compared to Mediums; other causes (track position, DRS, fuel
    load) should also be surfaced
- [ ] "Turn 1 chaos is worse in regulation reset years" — compare
    first-lap incidents and retirements in Year 1 vs Year 2+ of each era
- [x] DNF cause categorisation — module built, narrative tested
  - **Verdict: inconclusive — data source insufficient**
  - FastF1 status strings degrade significantly from 2023 onward;
    2024 and 2025 have zero attributed (Mechanical/Collision) DNFs —
    everything records as generic "Retired"
  - 2022 data is credible (52% Mechanical / 48% Collision) but
    year-on-year comparison is not possible from this source
  - `src/analysis/dnf_categorisation.py` remains as infrastructure
    for any future dataset with richer status recording
  - To test the narrative properly: requires a manually curated
    source (e.g. motorsport-reference.com race reports)
- [x] Notebook: `notebooks/04_narrative_testing.ipynb` — created,
  DNF section complete with findings documented

## Could Have (v0.7.0 — Historical Era Analysis)

- [ ] "Ferrari always bottles it" — championship lead conversion rate
  - Requires historical data beyond 2022 (2012, 2017, 2018 are key seasons)
  - Revisit once a pre-2022 data source is integrated (Ergast or equivalent)
  - Measure: of seasons where Ferrari led the championship at any point,
    what % did they convert to a title?
  - Compare against other constructors for the same metric

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

- [x] v0.3.0 2026 Year 1: 3 rounds ingested, four metrics, like-for-like 2022
  comparison, race control flags
- [x] v0.2.0 Baseline: points spread, lap time delta, DNF rates,
  quali->race conversion, 92 races 1838 entries
- [x] v0.1.0 Foundation: FastF1 loader, OpenF1 client, data models,
  era helper, tests, validation notebook
- [x] Project scaffolding, CLAUDE.md, BACKLOG.md, hooks, skills,
  docs, PR template, CHANGELOG
