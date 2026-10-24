# AeroPulse

**Is your flight fare high today?** AeroPulse is an open, route-level record of Indian
domestic airfares. It tells travellers whether fares are higher or lower than usual, gives
journalists numbers they can cite, and gives researchers a daily dataset with a published
method.

- 40 directed routes between 13 of India's busiest airports, priced every day in four
  booking windows (within a week, 1–2 weeks, 2–4 weeks, 1–2 months out)
- A national index, route indices and booking-window indices (chain-linked Jevons, with
  bootstrap 95% ranges)
- "Usual" = the middle half of the last 90 days; no verdict until there are 21 days of history
- Fares only from licensed APIs. No scraping, no personal data, no predictions

> **Status: v0.1, pre-launch.** Real collection starts once a provider passes the trial in
> [docs/operations/provider-spike.md](docs/operations/provider-spike.md). Until then the site
> runs on clearly labelled synthetic data.

## Two parts

| Part | Stack | Folder |
|---|---|---|
| **API and pipeline**: collects fares, builds the index, serves JSON, CSV, chart images and feeds | Python, FastAPI, SQLAlchemy | `src/aeropulse/` |
| **Website**: routes, airports, trends, festivals, compare, guide, method, open data | Next.js (App Router), TypeScript, Motion | `web/` |

The website has no database. It reads the API and caches each response for an hour.

## Run it locally

You need Python 3.12+ and Node 20+.

```bash
# 1. The API, with 150 days of synthetic, labelled history
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/aeropulse demo
.venv/bin/aeropulse serve --port 8000        # http://127.0.0.1:8000/v1/docs

# 2. The website, in a second terminal
cd web && cp .env.example .env.local && npm install && npm run dev   # http://localhost:3000
```

To collect real fares, put a provider key in `.env` (see [.env.example](.env.example)), then
run `aeropulse collect` and `aeropulse build`.

## Pages

| Page | What it answers |
|---|---|
| `/` | Is my fare high today? Pick a route and a booking window |
| `/routes`, `/routes/del-bom` | Every route; one route's fares, when it is cheapest, which weekday, next departures |
| `/airports`, `/airports/del` | Every route from one city |
| `/trends` | The national index, booking curve and weekday effect |
| `/festivals` | How fares behave around Diwali, Chhath and other peaks |
| `/compare` | Up to four routes on one chart |
| `/guide` | How to read the charts, FAQ and glossary |
| `/methodology`, `/data`, `/status`, `/about` | The method, downloads and API, collection health, sources and ethics |

## Deploy

| Target | What you get | Guide |
|---|---|---|
| Docker Compose on a server | Website, API, collector every 6 hours, Postgres, HTTPS | [Self-hosting](docs/operations/self-hosting.md) |
| Vercel | Hosted preview: the website plus the API over a read-only demo snapshot | [Hosted preview](docs/operations/vercel.md) |

## What's where

```
src/aeropulse/
  core/        the method: index, chaining, uncertainty, screening, "usual" (pure functions)
  reference/   airports, the basket (basket.yaml) and festivals (festivals.yaml)
  providers/   licensed fare APIs (Ignav, Travelpayouts), demo generator, terms policy
  official/    DGCA traffic and MoSPI CPI importers
  pipeline/    collect, build, export, rebuild-from-export
  db/          models, sessions, Alembic migrations
  queries.py   every read the API makes
  api/         JSON API (v1/) and files: CSV, chart images, feeds, downloads
  render/      server-side SVG charts and text for images and feeds
web/
  src/app/         pages (App Router)
  src/components/  charts, explorers, UI pieces
  src/lib/         API client, types, formatting, copy, chart maths
deploy/        Dockerfiles, Compose, Caddy, backups, Vercel API preview
docs/          documentation site (MkDocs)
tests/         mirrors src: core, providers, pipeline, api
```

More detail in [docs/architecture.md](docs/architecture.md).

## Check our numbers

Every published point can be recomputed from the open dataset:

```bash
aeropulse export --out exports
aeropulse rebuild exports      # "All N national index points rebuilt exactly"
```

## Development

```bash
.venv/bin/pytest                  # 81 tests, no network
.venv/bin/ruff check src tests
cd web && npm run lint && npm run typecheck && npm run build   # build needs the API running
mkdocs serve                      # docs site (pip install mkdocs-material)
```

Read [CONTRIBUTING.md](CONTRIBUTING.md) first, and
[docs/contributing/design.md](docs/contributing/design.md) before changing anything visual.

## Licences

- Code: [AGPL-3.0](LICENSE). If you run a modified version as a service, publish your changes.
- Data and text: [CC BY 4.0](LICENSE-DATA). Credit "AeroPulse" with a link.
- Fonts: Anek Latin and Source Serif 4, SIL Open Font License (see `web/src/app/fonts/`).
