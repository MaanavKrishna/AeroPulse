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

## Run it locally

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/aeropulse demo          # 150 days of synthetic, labelled history
.venv/bin/aeropulse serve         # http://127.0.0.1:8000
```

To collect real fares, put a provider key in `.env` (see [.env.example](.env.example)), then
run `aeropulse collect` and `aeropulse build`.

## Deploy

| Target | What you get | Guide |
|---|---|---|
| Docker Compose on a server | Site, API, collector every 6 hours, Postgres, HTTPS | [Self-hosting](docs/operations/self-hosting.md) |
| Vercel | Hosted preview of the site over a read-only demo snapshot | [Hosted preview](docs/operations/vercel.md) |

## What's where

```
src/aeropulse/
  core/        the method: index, chaining, uncertainty, screening, "usual" (pure functions)
  reference/   airports, the basket (basket.yaml) and festivals (festivals.yaml)
  providers/   licensed fare APIs (Ignav, Travelpayouts), demo generator, terms policy
  official/    DGCA traffic and MoSPI CPI importers
  pipeline/    collect, build, export, rebuild-from-export
  db/          models, sessions, Alembic migrations
  queries.py   every read the site and API make
  web/         server-rendered site: views, text, charts, templates, static
  api/v1/      public JSON API
deploy/        Dockerfile, Compose, Caddy, backups, Vercel preview
docs/          documentation site (MkDocs)
tests/         mirrors src: core, providers, pipeline, web
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
.venv/bin/pytest                  # 76 tests, no network
.venv/bin/ruff check src tests
mkdocs serve                      # docs site (pip install mkdocs-material)
```

Read [CONTRIBUTING.md](CONTRIBUTING.md) first, and
[docs/contributing/design.md](docs/contributing/design.md) before changing anything visual.

## Licences

- Code: [AGPL-3.0](LICENSE). If you run a modified version as a service, publish your changes.
- Data and text: [CC BY 4.0](LICENSE-DATA). Credit "AeroPulse" with a link.
- Fonts: Anek Latin and Source Serif 4, SIL Open Font License (see `src/aeropulse/web/static/fonts/`).
