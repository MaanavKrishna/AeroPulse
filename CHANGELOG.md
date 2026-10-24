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
- New consumer-first design ("fare weather"): route picker, fare ribbon, booking curve,
  departure calendar, festival pages, status page, embeds, feeds.
- Server-rendered; works without JavaScript; light and dark themes.

### Removed from the prototype
- All airline and travel-agency scraping adapters and the robots.txt prober.
- Government review-queue workflow screens.
