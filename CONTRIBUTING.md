# Contributing

Thanks for helping. AeroPulse publishes numbers people cite, so the bar is: every change is
tested, and no change makes the site say something it cannot back up.

## Setup

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/aeropulse demo
.venv/bin/pytest
.venv/bin/ruff check src tests
```

## Ground rules

- **No scraping.** Fares come only from licensed APIs used within their terms. Pull requests
  that fetch airline or travel-agency pages, call unofficial endpoints, or work around rate
  limits or bot checks will be closed.
- **No personal data.** Nothing about travellers is collected or stored.
- **No predictions.** Copy describes what fares have done. Avoid "will", "book now",
  "expected to". The tests check for some of these phrases.
- **Method changes are versioned.** Anything in `src/aeropulse/core/methodology.py` changes
  what published numbers mean: bump `METHODOLOGY_VERSION`, explain why in `CHANGELOG.md`, and
  update `docs/methodology/`.
- **Demo data stays labelled.** Never remove the demo banner logic or the production guard.

## Common changes

**Add a route:** add a new version to `src/aeropulse/reference/basket.yaml` (copy the latest, add the route, set
`valid_from` to a future date). Do not edit an existing version. Add any new airport to
`src/aeropulse/reference/airports.json`.

**Add a provider:** implement the `Provider` protocol in `src/aeropulse/providers/base.py`,
add a policy entry in `providers/policy.py` with `terms_reviewed=False`, register it in
`providers/__init__.py`, and add contract tests with a fixture that follows the provider's
published schema.

**Change copy:** generated sentences live in `src/aeropulse/web/text.py`. Follow
`docs/contributing/voice.md`.

**Change the look:** read `docs/contributing/design.md` first. Tokens live in
`src/aeropulse/web/static/css/tokens.css`; charts in `src/aeropulse/web/charts/`; templates
are grouped into `layouts/`, `partials/` and `pages/`.

Where everything lives: `docs/architecture.md`.

## Commits and pull requests

Small, focused commits with a clear message. A pull request should say what changed, why,
and how you checked it (tests, screenshots for visual changes at 390px and 1440px, light and
dark).
