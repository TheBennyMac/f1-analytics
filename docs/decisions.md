# Architectural Decision Log

Decisions that shaped this project — recorded so future sessions understand the *why*, not just the *what*. Each entry follows a lightweight ADR (Architectural Decision Record) format.

---

## ADR-001: OpenF1 over Ergast for historical data

**Date:** 2026-03-31
**Status:** Accepted

### Context

The project needs historical F1 results and standings data. Two candidate REST APIs were evaluated: Ergast (data back to 1950) and OpenF1 (data from 2023 onward).

### Decision

Use OpenF1 only. Ergast is excluded from scope.

### Rationale

- Ergast is in maintenance mode and at risk of deprecation
- The primary analysis focus is 2022 Ground Effect Era vs 2026 Era — OpenF1 covers this window alongside FastF1
- The further back the data, the less technically comparable it is to modern F1 (different engines, tyres, regulations, car concepts)
- FastF1 covers ~2018 onward for session-level data; OpenF1 fills the gaps for results and standings from 2023+

### Consequences

- Pre-2022 narrative testing (v0.5.0) may need to revisit this if Ergast data is required
- If Ergast is eventually needed, it should be added as a thin, optional client — not a core dependency
- See `docs/data_sources.md` for full API reference

---

## ADR-002: Notebooks-first output philosophy

**Date:** 2026-03-31
**Status:** Accepted

### Context

The project produces analytical insights from F1 data. A decision was needed on whether to build a UI (dashboard, web app) alongside the analysis, or defer it.

### Decision

All analysis is explored and validated in Jupyter notebooks. No UI framework is adopted before v0.6.0.

### Rationale

- Notebooks allow fast iteration and visual exploration without framework lock-in
- Choosing a UI framework before the analysis matures risks building the wrong thing
- The right output medium (Streamlit, Dash, Observable, static site) can only be judged once the analysis exists

### Consequences

- All analysis logic in `src/analysis/` must remain completely decoupled from any rendering layer
- UI evaluation happens at v0.6.0, informed by what the notebooks actually produce

---

## ADR-003: FastF1 as primary data source

**Date:** 2026-03-31
**Status:** Accepted

### Context

Multiple data sources are available for F1 session data. FastF1 is a Python library with a local cache; OpenF1 is a REST API. Both cover overlapping data from 2023 onward.

### Decision

FastF1 is the primary source for all session-level data (lap times, telemetry, tyre compounds, sector times). OpenF1 is secondary, used for results and standings where FastF1 is insufficient.

### Rationale

- FastF1 provides richer session data (telemetry, sector times, pit stops) than REST APIs
- FastF1's local cache means data is available offline and loads fast after the first run
- Coverage from ~2018 onward is sufficient for the Ground Effect Era analysis

### Consequences

- FastF1 cache must always be enabled (`data/cache/` directory, gitignored)
- First-run data loads will be slow as the cache populates
- FastF1 coverage starts ~2018 — pre-2018 session data is not available through this source

---

## ADR-004: 2022 Ground Effect Era as analysis baseline

**Date:** 2026-03-31
**Status:** Accepted

### Context

The 2026 season introduces a major regulation reset (new power units, active aero). The project needs a historical baseline to compare convergence, parity, and reliability against.

### Decision

The 2022–2025 Ground Effect Era is the primary baseline. Earlier eras are out of scope for now.

### Rationale

- 2022 was the last major regulation reset before 2026 — the most like-for-like comparison available
- Same cost cap framework, same tyre spec (18"), same teams and most of the same drivers
- Pre-2022 eras differ too significantly in technical regulations to be a meaningful comparator

### Consequences

- Analysis modules should parameterise by era year (Year 1, Year 2…) not calendar year
- The `EraHelper` utility must correctly map 2022→Year 1, 2023→Year 2, etc.
- If pre-2022 context is ever needed, it should be clearly labelled as supplementary
