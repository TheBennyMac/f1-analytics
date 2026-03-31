# BACKLOG.md - F1 Analytics

## Current Version: v0.1.0 (Scaffolding)

---

## Must Have (v0.1.0 — Foundation)
- [ ] FastF1 data loader with caching
- [ ] Ergast API client for historical results
- [ ] Core data models: RaceResult, LapSummary, DriverStanding
- [ ] Era helper utility (year → era name + year-within-era)
- [ ] Basic test suite structure

## Must Have (v0.2.0 — Era Convergence)
- [ ] Constructor points spread by era year (entropy/Gini metric)
- [ ] P1–P10 lap time gap trend across era years
- [ ] Convergence rate comparison: how fast did 2022 era converge vs 2014 era?
- [ ] Visualisation: convergence chart with era overlay

## Should Have (v0.3.0 — Reliability & DNFs)
- [ ] DNF rate by team, year, era
- [ ] DNF cause breakdown (mechanical vs accident vs other) where available
- [ ] Reliability trend: Year 1 vs Year 3 of each era
- [ ] Visualisation: reliability heatmap by team × era year

## Should Have (v0.4.0 — Pace & Consistency)
- [ ] Qualifying vs race pace delta by driver/team
- [ ] Quali position vs race finishing position consistency metric
- [ ] Sector time breakdown where available (FastF1, 2018+)
- [ ] Visualisation: scatter of quali rank vs race rank coloured by era

## Could Have (v0.5.0 — Narrative Testing)
- [ ] "Ferrari always bottles it" — championship lead conversion rate
- [ ] "Monaco produces processional races" — overtake index by circuit
- [ ] "Safety car lottery" — SC frequency and position change correlation
- [ ] "DRS made overtaking artificial" — overtake index pre/post DRS

## Could Have (v0.6.0 — 2026 Era Monitoring)
- [ ] 2026 season data integration (once FastF1 support is available)
- [ ] Live comparison: 2026 Year 1 vs previous regulation reset years
- [ ] Dashboard for tracking 2026 narrative in real time

## Won't Have (this phase)
- Real-time telemetry streaming
- Driver fitness/biometric data
- Commercial/sponsorship analysis

---

## Completed
- [x] Project scaffolding, CLAUDE.md, BACKLOG.md, hooks, skills (v0.1.0)
