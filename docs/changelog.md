# Changelog

## 0.1.0 (unreleased)

First open-source version. A rewrite of the SIH 2025 prototype (problem statement SIH26056)
as a public product for everyone.

### Method (v3.0)
- Product = route × booking window; price = median of the cheapest economy fares across the
  departure dates in the window.
- Jevons index, chain-linked across basket versions; route indices keep their own base.
- Bootstrap 95% ranges over departure dates, chain rebuilt in every replication.
- "Usual" = 25th–75th percentile of the previous 90 days; no verdict before 21 days.
- Screening: currency, plausible range, booking horizon, robust z > 6.

### Data
- Providers: Ignav (primary) and Travelpayouts (cross-check), both licensed APIs.
  Terms review is a manual gate before production.
- DGCA traffic and MoSPI CPI importers (CSV, with source URL per row).
- Open dataset export with SHA-256 manifest; `aeropulse rebuild` recomputes the index from
  the export alone.

### Website
- A Next.js (App Router) and TypeScript app in `web/`, separate from the Python API. Pages
  are prerendered from the API and refresh at most once an hour.
- Pages: home, routes, route detail, airports, airport detail, trends, festivals, festival
  detail, compare, guide, methodology, data, status, about, plus chart embeds, a sitemap and
  a 404 page.
- Design language taken from airport wayfinding: dark sign panels, signal yellow,
  pictograms, cards; blue and orange kept for fares cheaper and dearer than usual
  (see docs/contributing/design.md).
- Home page answers the question in words first ("Yes, higher than usual."), with a route
  picker, booking-window tabs, the fare ribbon and a map of all 40 routes.
- Route pages: booking-window tabs, fare ribbon with 1, 3 and 6-month ranges, when it is
  usually cheapest, weekday effect, next departures, related routes, citation, CSV, image,
  embed and feed.
- New: a ⌘K search for routes, cities and pages; a compare tool for up to four routes; a
  guide with an annotated chart, FAQ and glossary; a collection status page.
- Animation with Motion: chart wipe-ins, sliding tab backgrounds, answers that cross-fade,
  airways that draw in. All of it respects reduced motion. Light and dark themes.

### API
- Pure JSON API under `/v1` with routes, airports, insights, festivals, methodology,
  sources, downloads and status; per-route CSV, SVG chart images and Atom feeds.
- Per-IP rate limit; the website's server skips it with a shared `AEROPULSE_SITE_KEY`.

### Code layout
- Reference data (airports with ICAO codes, basket, festivals) in one `reference` package
  that ships with the install. API routes in `api/v1/routes.py`, files in `api/files.py`.
  Server-side chart images and feed text in `render/`. Tests mirror the source tree.

### Deployment
- Docker Compose stack for real collection: API, website, collector, Postgres, Caddy
  (`deploy/compose.yaml`).
- Vercel hosted preview in two projects: the API over a labelled demo snapshot built at
  deploy time (`deploy/vercel/`), and the website (`web/`).

### Removed from the prototype
- All airline and travel-agency scraping adapters and the robots.txt prober.
- Government review-queue workflow screens.
