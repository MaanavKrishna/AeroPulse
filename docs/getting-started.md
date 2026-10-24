# Getting started

You need Python 3.12 or newer.

```bash
git clone https://github.com/MaanavKrishna/aeropulse && cd aeropulse
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/aeropulse demo
.venv/bin/aeropulse serve
```

Open <http://127.0.0.1:8000>. Every page carries a "Demo data" banner: `aeropulse demo`
fills the database with 150 days of synthetic fares, made by a deterministic generator so
the site has something realistic to show. They are not real prices.

## Collect real fares

1. Get an API key from a supported provider (see [Sources](data/sources.md)).
2. `cp .env.example .env` and set `AEROPULSE_PROVIDERS=ignav` and `AEROPULSE_IGNAV_API_KEY`.
3. Try a handful of routes first:

    ```bash
    aeropulse collect --limit 3
    ```

4. Build the series and look at the site:

    ```bash
    aeropulse build
    aeropulse serve
    ```

Use a fresh database for real data (`AEROPULSE_DATABASE_URL`). Real and demo data are never
meant to share one database.

## Commands

| Command | What it does |
|---|---|
| `aeropulse collect` | One collection run for every basket route |
| `aeropulse build` | Rebuild every series from stored fares (safe to repeat) |
| `aeropulse export` | Write the open dataset and its manifest |
| `aeropulse rebuild DIR` | Recompute the index from an export and compare |
| `aeropulse dgca-import FILE` | Import DGCA traffic for route weights |
| `aeropulse cpi-import FILE` | Import the MoSPI CPI airfare series |
| `aeropulse demo` | Synthetic history for development |
| `aeropulse db upgrade` | Apply database migrations |
| `aeropulse serve` | Run the site and API |

## Tests

```bash
.venv/bin/pytest
.venv/bin/ruff check src tests
```

Tests never call a real provider. Provider contract tests use fixtures built from each
provider's published schema.
