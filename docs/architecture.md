# Architecture

AeroPulse is one Python package (`src/aeropulse`) with four layers. Data flows one way:
providers write fares, the pipeline turns fares into published series, and the site and API
only read.

```
providers ──► pipeline/collect ──► fares (silver) ──► pipeline/build ──► index_values (gold)
                                                                            │
                         reference/ (airports, basket, festivals)           ▼
                                                     queries.py ──► web/ (site)   api/v1/ (JSON)
```

## Package layout

| Path | Responsibility | Rule |
|---|---|---|
| `core/` | The method: index, chaining, bootstrap uncertainty, fare screening, the "usual" verdict, method constants | Pure functions. No database, no network. Every method change happens here, with tests. |
| `reference/` | Airports (IATA, ICAO, coordinates), the basket (`basket.yaml`), festivals (`festivals.yaml`) | Data lives in version control and ships inside the package. Never stored in the database. |
| `providers/` | One module per licensed fare API, the demo generator, and the provider policy registry | Must satisfy the `Provider` protocol in `base.py`. Terms review gates production. |
| `official/` | DGCA traffic and MoSPI CPI importers | CSV in, with a source URL on every row. |
| `pipeline/` | `collect`, `build`, `export`, `rebuild` | Orchestration only; the maths is in `core/`. |
| `db/` | SQLAlchemy models, sessions, Alembic migrations | Bronze (raw responses), silver (fares), gold (published series). |
| `queries.py` | Every read the site and API make | One implementation, so a page and its JSON never disagree. |
| `web/` | Server-rendered site | See below. |
| `api/v1/` | Public read-only JSON API (`routes.py`) | Mirrors `queries.py`; every response carries `data_mode`. |
| `app.py` | FastAPI app factory, security headers, rate limit | |
| `cli.py` | The `aeropulse` command | |
| `config.py` | Settings from environment variables | The only place secrets are read. |

### The web layer

| Path | What |
|---|---|
| `web/views.py` | Page routes |
| `web/text.py` | Every sentence generated from data (verdicts, answers, context lines) |
| `web/format.py` | Rupee grouping, dates, escaping |
| `web/charts/` | Server-rendered SVG: `ribbon.py` (fare ribbon), `curves.py` (booking curve, festival track), `network.py` (route chart and the route-page leg), `base.py` (shared geometry and colour) |
| `web/templates/layouts/` | `base.html`, the page shell |
| `web/templates/partials/` | Reusable pieces: hero, macros |
| `web/templates/pages/` | One template per page |
| `web/templates/embed/`, `feeds/` | Embeddable chart, Atom feed |
| `web/static/` | `css/tokens.css` (design tokens), `css/app.css`, `js/app.js` (progressive enhancement), self-hosted fonts |

Charts render on the server, so every page works with JavaScript switched off. `app.js`
only adds the in-place route picker, chart hover and scrubbing, and copy buttons.

## Storage

Three layers in one database (SQLite in development, Postgres in production):

- **bronze** `raw_responses`: exactly what a provider returned, with a SHA-256 hash;
- **silver** `fares`: one cheapest fare per route, departure date and run, screened, with
  an exclusion reason when not eligible;
- **gold** `product_prices`, `index_values`, `index_links`, `index_revisions`,
  `basket_weights`, `basket_products`: what is published.

Gold is always rebuildable from silver, and silver from bronze. `aeropulse rebuild`
recomputes the published index from the open export alone.

## Deployments

| Where | What it runs | Files |
|---|---|---|
| Your machine | `aeropulse demo` + `aeropulse serve`, SQLite | — |
| A server | App, collector loop, Postgres, Caddy | `deploy/compose.yaml`, `deploy/Dockerfile` |
| Vercel (hosted preview) | The site over a read-only demo snapshot built at deploy time; collects nothing | `deploy/vercel/`, `[tool.vercel]` in `pyproject.toml` |

## Tests

`tests/` mirrors the package: `core/`, `providers/`, `pipeline/`, `web/`. Tests never call a
real provider; provider contract tests use fixtures built from each provider's published
schema (`tests/fixtures/`).
