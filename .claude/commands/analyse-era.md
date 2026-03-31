# /analyse-era

Run a structured era analysis for a given regulation period.

## Usage
`/analyse-era [era-name]` — e.g. `/analyse-era Ground Effect Era`

## What this does
1. **Identify the era boundaries** from the regulation eras table in CLAUDE.md
2. **List the available metrics** for that era (some metrics require FastF1 and are only available from 2018+)
3. **Summarise the key narrative questions** that apply to this era:
   - How quickly did the field converge?
   - Which team dominated Year 1 and did that hold?
   - DNF/reliability story in Year 1 vs later years
   - Any well-known public narratives to test?
4. **Recommend the analysis modules** to build or run first
5. **Flag any data gaps** (e.g. Ergast-only for pre-2018, missing sessions, cancelled races)

Output a structured markdown summary suitable for saving to `docs/era-<name>.md`.
