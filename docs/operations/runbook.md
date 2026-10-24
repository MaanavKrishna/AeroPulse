# Runbook

## A run failed or was partial

Open `/status`. The latest message and the last 10 provider errors are listed there.

| Symptom | Likely cause | Action |
|---|---|---|
| `HTTP 401` / `403` | Key missing, wrong or revoked | Check `AEROPULSE_IGNAV_API_KEY`; rotate if leaked |
| `HTTP 402` | Out of credit | Top up; the run resumes next cycle |
| `HTTP 429` | Provider rate limit | Lower frequency; never add retries that hammer |
| `unexpected ... response shape` | Provider changed its API | Nothing from that answer is used. Update the parser and the fixture, then rebuild |
| `budget_exhausted` | Daily cap reached | Expected if runs were repeated; raise `AEROPULSE_MAX_CALLS_PER_DAY` only deliberately |

Gaps are never back-filled with invented values. A missed day stays missing.

## A number looks wrong

1. Check `/status` exclusions. A spike in `outlier` usually means a feed problem.
2. Look at the product prices for that day in `product_prices.csv`.
3. If stored fares were wrong, fix them in the database, then run
   `aeropulse build --reason "what and why"`. Every changed value is logged in
   `index_revisions`.

## Changing the basket

Add a new version to `basket.yaml` with a future `valid_from`. Never edit an old one. After
the first day under the new version, check that `index_links.csv` has the link.

## Rotating secrets

Change the value in `.env`, then run `docker compose -f deploy/compose.yaml up -d`. No secret
is stored in the database or the repository.
