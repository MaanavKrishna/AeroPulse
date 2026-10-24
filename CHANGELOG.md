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
- "Night flight" design: every page opens in a twilight sky and comes down through a
  horizon to the numbers. The home page shows all 40 routes as a live constellation of
  flight arcs between airports at their real positions, coloured by today's fares against
  usual, with planes flying them. Pick a route on the map or in the picker and the answer
  updates in place.
- Route pages open with the route drawn as a single flight, then the fare ribbon, booking
  curve, departure calendar, citation, download and embed tools. Festival, status, method,
  data and about pages share the same sky header.
- Motion: one arrival sequence per page (airports, arcs, planes; fare counts from usual to
  today), view transitions between pages and on route changes. Everything stops under
  reduced motion.
- Server-rendered; works without JavaScript; light and dark grounds.

### Removed from the prototype
- All airline and travel-agency scraping adapters and the robots.txt prober.
- Government review-queue workflow screens.
