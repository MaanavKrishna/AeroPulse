# Basket and weights

## The basket

`basket.yaml` lists the routes, in versions:

```yaml
versions:
  - version: b2026.10
    valid_from: 2026-10-24
    routes: [DEL-BOM, BOM-DEL, ...]
```

Version 1 has 40 directed routes: the 20 busiest city pairs in both directions. Before launch,
check the list against the latest DGCA city-pair release.

**Never edit a version that has data.** To change the basket, add a new version with a later
`valid_from`. On that day both versions are priced, which is what chain-linking needs.

## Weights

- **Windows:** equal (¼ each) within a route. There is no public data on how far ahead
  Indian domestic tickets are bought.
- **Routes:** share of DGCA passengers over the latest 12 imported periods, if every basket
  route has traffic data. Otherwise equal. The weights in force, and where they came from,
  are in `basket_weights.csv` and on the method page.

Import DGCA traffic with `aeropulse dgca-import file.csv`. The file format and rules are in
the docstring of `src/aeropulse/official/dgca.py`. Every row carries the URL of the DGCA
release it came from. Never type in a number that is not in the release.

## Chain-linking

When the basket changes, the national and window series are spliced at the first day of
the new version:

$$
\text{factor} = \frac{I_\text{old}(t_\text{link})}{I_\text{new}(t_\text{link})}, \qquad
I(t) = \text{factor} \times I_\text{new}(t) \quad (t > t_\text{link})
$$

Growth inside each version passes through unchanged, and the link adds no movement. Each
product keeps the base price from the first version it appeared in, so **route** series are
unaffected by basket changes and need no link.

Links are published in `index_links.csv`.
