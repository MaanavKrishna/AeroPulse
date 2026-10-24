# How to contribute

The short version lives in
[CONTRIBUTING.md](https://github.com/MaanavKrishna/aeropulse/blob/main/CONTRIBUTING.md).

## Where help is most useful

- **Data checks.** Compare our route verdicts with what you see when booking, and open an
  issue with the route, date and what differed.
- **DGCA imports.** Prepare the city-pair CSV from a DGCA release (format in
  `src/aeropulse/official/dgca.py`).
- **Accessibility.** Screen-reader and keyboard testing of the charts.
- **Hindi.** The fonts and airport data already include Devanagari; the copy does not yet.

## Layout of the code

| Package | Rule |
|---|---|
| `core` | Pure functions, no I/O. Every method change happens here, with tests. |
| `providers` | One module per licensed API; must satisfy `Provider` |
| `pipeline` | Orchestration: collect, build, export, rebuild |
| `web`, `api` | Read-only views over `queries.py` |
