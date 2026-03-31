# Data Sources

Reference for all external data sources used in this project. See `docs/decisions.md` for the reasoning behind source selection.

---

## FastF1 (Primary)

**Type:** Python library
**Coverage:** ~2018 to present (session-level data)
**Auth:** None required
**Docs:** https://docs.fastf1.dev

### What it provides

- Lap times (all drivers, all laps)
- Telemetry (speed, throttle, brake, gear, DRS — sampled per ~3–4Hz)
- Sector times
- Tyre compounds and pit stop data
- Weather data per session
- Car and driver numbers, team mappings

### Usage pattern

```python
import fastf1

fastf1.Cache.enable_cache('data/cache/')
session = fastf1.get_session(2022, 'Bahrain', 'R')
session.load()
laps = session.laps
```

### Cache behaviour

- Cache is stored at `data/cache/` (gitignored — never commit)
- First load of a session downloads and caches the full dataset — can take 1–2 minutes
- Subsequent loads are near-instant
- Re-run loaders freely as new sessions become available; the cache handles deduplication

### Known limitations

- Coverage starts ~2018 — older sessions may be incomplete or unavailable
- Telemetry availability varies by session and year (older seasons have gaps)
- Session names must match FastF1's naming convention (e.g. `'R'` for race, `'Q'` for qualifying)

---

## OpenF1 (Secondary)

**Type:** REST API
**Coverage:** 2023 to present
**Auth:** None required (public endpoints)
**Base URL:** `https://api.openf1.org/v1`
**Docs:** https://openf1.org

### What it provides

- Session metadata (race, qualifying, practice)
- Driver and constructor standings
- Race results
- Pit stop records
- Car data (speed, throttle, brake — similar to FastF1 telemetry)
- Race control events (flags, safety car, VSC)
- Weather per session

### Key endpoints

| Endpoint | Description |
|---|---|
| `/sessions` | All sessions with metadata |
| `/drivers` | Driver info per session |
| `/laps` | Lap-by-lap data |
| `/pit` | Pit stop records |
| `/race_control` | Flags, safety car, VSC events |
| `/position` | Driver positions throughout a session |
| `/car_data` | Telemetry (speed, throttle, brake, gear) |

### Usage pattern

```python
import requests

BASE_URL = "https://api.openf1.org/v1"

response = requests.get(f"{BASE_URL}/sessions", params={"year": 2024, "session_type": "Race"})
sessions = response.json()
```

### Known limitations

- Coverage starts 2023 — cannot use for 2022 season data via this API
- For 2022 results and standings, FastF1 is the fallback
- No official rate limit documented — use reasonable request spacing in loaders
- Responses can be large for telemetry endpoints; filter by session key where possible

---

## Ergast API (Excluded)

**Status:** Out of scope

Ergast provides race results, standings, and lap times back to 1950. It was evaluated and excluded:

- In maintenance mode — no active development, at risk of deprecation
- Pre-2022 data is less technically comparable to modern F1
- OpenF1 and FastF1 together cover the target window (2022–present)

**Revisit at v0.5.0** if pre-2022 narrative testing (DRS era, refuelling era comparisons) requires historical depth beyond FastF1's ~2018 coverage.
