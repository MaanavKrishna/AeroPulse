# Sources and licences

## Fares

| Provider | Role | How | Terms reviewed |
|---|---|---|---|
| [Ignav](https://ignav.com) | Primary: feeds the index | `POST /api/fares/cheapest-dates`, one call per route per run | Not yet |
| [Travelpayouts](https://www.travelpayouts.com) (Aviasales Data API) | Cross-check | `GET /aviasales/v3/prices_for_dates`, one call per route per month | Not yet |

Only one provider feeds the index at a time. Mixing providers would make movements partly
about which provider answered.

"Terms reviewed" stays "Not yet" until a person has read the provider's current terms and
confirmed both points:

- storing responses is allowed;
- publishing indices derived from them is allowed.

Until then production refuses to collect, except in an explicitly flagged private trial. See
[Provider trial](../operations/provider-spike.md).

We do not republish individual departure-date fares unless a provider's terms allow it. We
publish medians, ranges and indices.

**What we never do:** scrape airline or travel-agency sites; call unofficial endpoints, such as
reverse-engineered Google Flights clients; work around rate limits, logins or bot checks;
collect anything about travellers.

## Official data

| Source | Used for | Licence |
|---|---|---|
| DGCA domestic traffic, city-pair tables | Route weights, route selection | Government Open Data License – India |
| MoSPI CPI (base 2024), airfare item | Outside benchmark only | Government Open Data License – India |

Both are imported from CSV files prepared from the official releases, with the release URL
on every row. We do not scrape government sites either.

## Our licences

- Data and text: CC BY 4.0. Credit "AeroPulse" with a link.
- Code: AGPL-3.0.
