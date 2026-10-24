# Test fixtures

These are **constructed** responses, not recorded ones. They follow each provider's
published schema:

- `ignav_cheapest_dates.json`: `CheapestDatesResponseModel` from https://ignav.com/api/openapi.json
- `travelpayouts_prices_for_dates.json`: `prices_for_dates` as documented at
  https://support.travelpayouts.com/hc/en-us/articles/203956163

The prices are invented. When the provider spike records real responses, replace these
with recorded ones (strip nothing but the API key, which is never in a response anyway).
