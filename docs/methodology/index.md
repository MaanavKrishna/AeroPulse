# Method (v3.0)

!!! summary "In plain words"
    Every day we ask a licensed provider for the cheapest economy one-way fare on every
    departure date over the next two months, for 40 busy routes. We summarise those fares by how
    far ahead you are booking, compare them with what is usual for that route, and combine the
    routes into one national number.

The authoritative values for every constant below are in
[`src/aeropulse/core/methodology.py`](https://github.com/MaanavKrishna/aeropulse/blob/main/src/aeropulse/core/methodology.py).

## What is priced

A **route** is a directed airport pair (DEL to BOM is not BOM to DEL). Each route is priced in
four **booking windows**:

| Window | Days before departure |
|---|---|
| Within a week | 1–7 |
| 1–2 weeks out | 8–14 |
| 2–4 weeks out | 15–30 |
| 1–2 months out | 31–60 |

A route × window pair is a **product**. On collection day *t*, its price is

$$
P_i(t) = \operatorname{median}\{\, c(d) : d \in \text{departure dates in the window} \,\}
$$

where *c(d)* is the cheapest economy one-way fare for departure date *d*, as returned by the
provider that day. A product needs at least 3 priced dates, or it is skipped that day.

Same-day departures are excluded.

## The index

$$
I(t) = 100 \times \exp\!\left( \frac{\sum_i w_i \ln\big(P_i(t) / P_i^{\text{base}}\big)}{\sum_i w_i} \right)
$$

This is a weighted geometric mean of price relatives (Jevons). The arithmetic version (Carli)
fails the time-reversal test and drifts upward on volatile prices. It is advised against by
the international CPI Manual and prohibited in the European HICP.

The sum runs over products priced that day. **Coverage** is the priced share of total weight:

- 80% or more: `valid`
- 60–80%: `provisional`
- below 60%: `insufficient_data`, which is not used for verdicts

Three families of series are published:

- **national**: all products;
- **route**: the four windows of one route;
- **window**: one window across all routes.

## Base

Each product's base price is its mean over the first **7** days it was priced. Series start
near 100.

## "Usual"

The usual band is the **25th–75th percentile of the previous 90 days**, excluding today.

- Above the band: "higher than usual".
- Below it: "lower than usual".
- Inside it: "about usual".

The percentage shown compares today with the median of those days.

With fewer than **21** days of history there is no verdict. For the first 90 days the series
is labelled "early series".

## What this is not

This is a **cheapest-available-fare** index. It follows the lowest fare on sale, not what the
average passenger paid. The CPI airfare item is closer to the second. The two usually move
together but can diverge, for example when cheap seats sell out early.

## Known limits

- One provider's view of the market. Fares sold only on an airline's own site may be missing.
- Economy, one-way, one adult only.
- Goa is measured at Dabolim (GOI), not Mopa (GOX).
- History begins when collection began. Nothing earlier is reconstructed.

See also [Uncertainty](uncertainty.md) and [Basket and weights](basket.md).
