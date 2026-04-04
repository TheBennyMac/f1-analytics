# F1 Analytics

An F1 data analytics project focused on surfacing objective insights from historical race data — particularly around regulation era transitions, how quickly teams converge toward parity, and where public narratives align or conflict with the numbers.

## Primary Focus

**2022 Ground Effect Era vs 2026 Era** — like-for-like comparison across the regulation reset, tracking convergence, reliability, and pace metrics across both eras.

## Getting Started

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

FastF1 will populate its local cache on first run — expect slower initial loads.

## Project Structure

```
notebooks/    # Primary analysis output — start here
src/data/     # Data loaders (FastF1, historical API clients)
src/models/   # Core data models
src/analysis/ # Analysis modules (convergence, reliability, pace)
src/utils/    # Helpers (era grouping, formatters)
tests/        # pytest test suite
data/cache/   # FastF1 local cache (gitignored)
```

## Data Sources

- **FastF1** — session data from ~2018 onward (lap times, telemetry,
  tyre compounds, sector times)
- **OpenF1** — results and standings from 2023 onward (cross-check
  and supplementary data)

## Development

See [CLAUDE.md](CLAUDE.md) for full architecture, domain knowledge, and working guidelines.
See [BACKLOG.md](BACKLOG.md) for current priorities.
