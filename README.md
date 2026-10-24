# AeroPulse

**Is your flight fare high today?** AeroPulse is an open, route-level record of Indian
domestic airfares. It tells travellers whether fares are higher or lower than usual, gives
journalists numbers they can cite, and gives researchers a daily dataset with a published
method.

- 40 directed routes between India's busiest airports, priced every day in four booking
  windows (within a week, 1–2 weeks, 2–4 weeks, 1–2 months out)
- A national index, route indices and booking-window indices (chain-linked Jevons, with
  bootstrap 95% ranges)
- "Usual" = the middle half of the last 90 days; no verdict until there are 21 days of history
- Fares only from licensed APIs. No scraping, no personal data, no predictions

> **Status: v0.1, pre-launch.** Real collection starts once a provider passes the trial in
> [docs/operations/provider-spike.md](docs/operations/provider-spike.md). Until then the site
> runs on clearly labelled synthetic data.

## Run it locally

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/aeropulse demo          # 150 days of synthetic, labelled history
.venv/bin/aeropulse serve         # http://127.0.0.1:8000
```

Or with Docker: `docker compose -f deploy/compose.yaml up`.

To collect real fares, put a provider key in `.env` (see [.env.example](.env.example)) and run
`aeropulse collect`, then `aeropulse build`.

## What's where

| Path | What |
|---|---|
| `src/aeropulse/core/` | The method: index, chaining, uncertainty, screening, "usual". Pure functions. |
| `src/aeropulse/providers/` | Fare APIs (Ignav, Travelpayouts) and the demo generator |
| `src/aeropulse/pipeline/` | Collect, build, export, rebuild-from-export |
| `src/aeropulse/official/` | DGCA traffic (weights) and MoSPI CPI (benchmark) importers |
| `src/aeropulse/web/` | Server-rendered site and SVG charts |
| `src/aeropulse/api/v1/` | Public JSON API |
| `src/aeropulse/reference/` | Airports, the basket (which routes are priced, by version) and festivals |
| `docs/` | Documentation site (MkDocs) |
| `deploy/` | Dockerfile, Compose, Caddy, backups |

## Check our numbers

Every published point can be recomputed from the open dataset:

```bash
aeropulse export --out exports
aeropulse rebuild exports      # "All N national index points rebuilt exactly"
```

## Documentation

Method, data dictionary, API, self-hosting and contributing: see [`docs/`](docs/index.md),
or build the site with `pip install mkdocs-material && mkdocs serve`.

## Licences

- Code: [AGPL-3.0](LICENSE). If you run a modified version as a service, publish your changes.
- Data and text: [CC BY 4.0](LICENSE-DATA). Credit "AeroPulse" with a link.
- Fonts: Anek Latin and Source Serif 4, SIL Open Font License (see `src/aeropulse/web/static/fonts/`).
