# Uncertainty

Each product price is a median of a handful of departure dates. A different handful would
give a different median, and the index inherits that noise. We estimate it with a
**nonparametric bootstrap over departure dates**:

1. For every product-day, resample its departure-date fares with replacement and take the
   median.
2. Re-estimate each product's base price from the same resample.
3. Recompute every series. Where the basket changed, recompute the chain link too: the link
   factor is estimated from the data and is uncertain as well.
4. Repeat 200 times with a fixed seed (20261024).

The standard error is the standard deviation across replications. The published 95% range
is centre ± 1.96 × SE. On route pages, the rupee chart's range is the 2.5th–97.5th
percentile of the same kind of resample of that product's median.

Because the seed is fixed, the same data always gives the same ranges.

## What the range does not cover

It does **not** cover whether these 40 routes represent all Indian domestic flying. The
basket is chosen by traffic, not sampled at random, so that uncertainty cannot be estimated
from this data. A narrow range means "given this basket, the choice of dates hardly matters",
nothing more.

## Changes between two days

Two points share no fares, so the SE of a change is the square root of the sum of the two
variances (`core.variance.change_standard_error`).
