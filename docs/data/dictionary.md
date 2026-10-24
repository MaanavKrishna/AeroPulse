# Data dictionary

`aeropulse export` writes these files and a `manifest.json` with row counts and SHA-256
checksums. Dates are IST collection days (`YYYY-MM-DD`). Every file has an `is_demo` column
or a manifest flag; if it is `true`, the data is synthetic.

## index_values.csv

One row per published point.

| Column | Meaning |
|---|---|
| `date` | Collection day |
| `scope` | `national`, `route` or `window` |
| `route` | Route (`DEL-BOM`) for route scope, else empty |
| `window` | `1-7`, `8-14`, `15-30`, `31-60` for window scope, else empty |
| `kind` | `CHAINED` (published) or `FIXED` (first basket only, for audit) |
| `value` | Index level |
| `ci95_low`, `ci95_high`, `standard_error` | Bootstrap uncertainty ([method](../methodology/uncertainty.md)) |
| `coverage_pct` | Share of basket weight priced |
| `status` | `valid`, `provisional`, `insufficient_data` |
| `fares_used` | Departure-date fares behind the point |
| `products` | Products priced |
| `basket_version`, `methodology_version` | What produced the number |
| `revision` | 0 for first publication, +1 each time it changed |

## product_prices.csv

The index input: one row per route × window × day.

| Column | Meaning |
|---|---|
| `median_cheapest_fare_inr` | Median of the cheapest fares across the window's departure dates |
| `lowest_inr`, `highest_inr` | Cheapest and dearest of those dates |
| `departure_dates_priced` | How many dates had a fare |
| `provider` | Which provider answered |

## basket_products.csv

Each product's `weight`, `base_price_inr`, base days and the basket version's validity. With
`product_prices.csv` this is enough to recompute every point (`aeropulse rebuild`).

## basket_weights.csv

Route weights per basket version and their `source` (`equal` or `dgca:<periods>`).

## index_links.csv

Chain links: `series`, `from_version`, `to_version`, `link_date`, `old_level`, `new_level`,
`factor`.

## index_revisions.csv

Every published value that later changed: the old value, the new value, and the reason.
