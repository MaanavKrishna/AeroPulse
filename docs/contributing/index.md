# How to contribute

The short version lives in
[CONTRIBUTING.md](https://github.com/MaanavKrishna/aeropulse/blob/main/CONTRIBUTING.md).

## Where help is most useful

- **Data checks.** Compare our route verdicts with what you see when booking, and open an
  issue with the route, date and what differed.
- **DGCA imports.** Prepare the city-pair CSV from a DGCA release (format in
  `src/aeropulse/official/dgca.py`).
- **Accessibility.** Screen-reader and keyboard testing of the charts.
- **Hindi.** The fonts and airport data already include Devanagari; the copy does not yet.

## Layout of the code

See [Architecture](../architecture.md) for the full map. In short: `core` is pure method code,
`reference` holds the basket and airports, `providers` talk to fare APIs, `pipeline`
orchestrates, and `web` and `api` only read through `queries.py`.

Before changing anything visual, read [Design](design.md).
