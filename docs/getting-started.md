# Getting started

You need Python 3.12 or newer and Node 20 or newer.

```bash
git clone https://github.com/MaanavKrishna/AeroPulse aeropulse && cd aeropulse
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/aeropulse demo
.venv/bin/aeropulse serve --port 8000
```

That starts the API; its interactive reference is at <http://127.0.0.1:8000/v1/docs>.
Then start the website in a second terminal:

```bash
cd web
cp .env.example .env.local
npm install
npm run dev
```

Open <http://localhost:3000>. Every page carries a "Demo data" notice: `aeropulse demo`
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
    aeropulse serve --port 8000
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
| `aeropulse serve` | Run the API |

## Tests

```bash
.venv/bin/pytest
.venv/bin/ruff check src tests
cd web && npm run lint && npm run typecheck
```

Python tests mirror the package (`tests/core`, `tests/providers`, `tests/pipeline`, `tests/api`) and
never call a real provider. Provider contract tests use fixtures built from each provider's
published schema.
