# Architecture

AeroPulse has two parts: a Python package (`src/aeropulse`) that collects fares, builds the
index and serves it as an API, and a Next.js website (`web/`) that reads that API. Data flows
one way: providers write fares, the pipeline turns fares into published series, and the API
and website only read.

```
providers ──► pipeline/collect ──► fares (silver) ──► pipeline/build ──► index_values (gold)
                                                                            │
                         reference/ (airports, basket, festivals)           ▼
                                                     queries.py ──► api/ (JSON, CSV, SVG, feeds)
                                                                            │
                                                                            ▼
                                                                  web/ (Next.js website)
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
| `queries.py` | Every read the API makes | One implementation, so a page and its JSON never disagree. |
| `api/v1/` | Public read-only JSON API (`routes.py`) | Mirrors `queries.py`; every response carries `data_mode`. |
| `api/files.py` | Downloads, per-route CSV, chart images (SVG) and Atom feeds | |
| `render/` | Server-side SVG charts and generated sentences for images and feeds | |
| `app.py` | FastAPI app factory, security headers, CORS, rate limit | The website's server skips the rate limit with `AEROPULSE_SITE_KEY`. |
| `cli.py` | The `aeropulse` command | |
| `config.py` | Settings from environment variables | The only place secrets are read. |

### The website (`web/`)

Next.js 16 with the App Router, TypeScript and [Motion](https://motion.dev) for animation.

| Path | What |
|---|---|
| `src/app/(site)/` | Every page with the header and footer. Dynamic pages (`routes/[route]`, `airports/[iata]`, `festivals/[slug]`) are prerendered for every known value with `generateStaticParams` |
| `src/app/embed/` | Chart-only pages for `<iframe>` embeds |
| `src/app/sitemap.ts`, `robots.ts` | Search engines are kept out while the data is demo data |
| `src/lib/api.ts` | The only place that calls the API. Each response is cached for an hour (`'use cache'` with `cacheLife('hours')`) |
| `src/lib/types.ts` | Types for every API response |
| `src/lib/copy.ts`, `insight.ts` | Sentences generated from data |
| `src/lib/chart.ts` | Scales, ribbon geometry, map projection |
| `src/components/charts/` | Fare ribbon, route map, booking curve, weekday bars, multi-line, festival track |
| `src/components/home/`, `routes/`, `compare/` | The interactive explorers |
| `src/components/site/` | Header, nav, search (⌘K), theme toggle, footer, demo notice |
| `src/components/ui/` | Pictograms, section heads, verdict chips, FAQ, copy buttons |
| `src/styles/` | `tokens.css` (design tokens, light and dark), `base.css` (shared classes) |

Pages render on the server and arrive as HTML. Interactive pieces (the route picker, map,
chart hover, window tabs, compare tool, search) are client components. The HTML already
carries each page's answer and numbers, so search engines and slow phones get them first.

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
| Your machine | `aeropulse demo` + `aeropulse serve`, SQLite; `npm run dev` in `web/` | — |
| A server | API, website, collector loop, Postgres, Caddy | `deploy/compose.yaml`, `deploy/Dockerfile`, `deploy/web.Dockerfile` |
| Vercel (hosted preview) | Two projects: the API over a read-only demo snapshot built at deploy time, and the website | `deploy/vercel/`, `[tool.vercel]` in `pyproject.toml`, `web/` |

## Tests

`tests/` mirrors the package: `core/`, `providers/`, `pipeline/`, `api/`. The website is
checked by ESLint, the TypeScript compiler and a full `next build`. Tests never call a
real provider; provider contract tests use fixtures built from each provider's published
schema (`tests/fixtures/`).
