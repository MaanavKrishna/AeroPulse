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

### Site
- Design language taken from aeronautical en-route charts: chart paper, ink, hairlines,
  a latitude/longitude grid. No shadows, gradients, blur or card grids
  (see docs/contributing/design.md).
- Home page answers the question in words first ("Yes, higher than usual."), with a ruled
  facts strip and the fare ribbon. The route chart shows all 40 routes as airways between
  airport chart symbols (IATA, city, ICAO), coloured by fares against usual, with a km scale
  bar; the selected route carries its great-circle distance and the only moving plane.
  No country outline is drawn.
- Route pages: the leg between two airport symbols with its distance, booking-window tabs,
  fare ribbon, booking curve, departure calendar, citation, CSV, image, embed and feed.
- Motion is one draw-in per page plus responses to the reader; it all stops under reduced
  motion. Server-rendered; works without JavaScript; light and dark themes.

### Code layout
- Reference data (airports with ICAO codes, basket, festivals) in one `reference` package
  that ships with the install. API routes in `api/v1/routes.py`. Charts split into
  `ribbon`, `curves`, `network` and shared `base`; formatting in `web/format.py`.
  Templates in `layouts/`, `partials/`, `pages/`. Tests mirror the source tree.

### Deployment
- Docker Compose stack for real collection (`deploy/compose.yaml`).
- Vercel hosted preview: builds a labelled demo snapshot at deploy time and serves it
  read-only (`deploy/vercel/`).

### Removed from the prototype
- All airline and travel-agency scraping adapters and the robots.txt prober.
- Government review-queue workflow screens.
