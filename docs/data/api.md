# API

Read-only JSON. No key. Default limit 120 requests a minute per client address; responses
carry `X-RateLimit-Limit` and `X-RateLimit-Remaining`. The generated reference is at
`/v1/docs` on any running instance.

Every response includes `data_mode`: `live`, `demo` or `empty`. If it is `demo`, the
numbers are synthetic.

| Path | Returns |
|---|---|
| `GET /v1/meta` | Method version, basket routes, windows, last collection |
| `GET /v1/airports` | Airports used by tracked routes |
| `GET /v1/routes` | Every route with today's verdict |
| `GET /v1/routes/{route}?window=` | Verdict per booking window, booking curve, usual-cheapest stretch |
| `GET /v1/indices/national` | National series |
| `GET /v1/indices/routes/{route}` | Route series |
| `GET /v1/indices/windows/{window}` | Window series |
| `GET /v1/festivals` | Festival calendar |
| `GET /v1/festivals/{slug}` | Festival fares against ordinary weeks |
| `GET /v1/status` | Collection health per provider |

Series endpoints accept `from`, `to` (dates), `kind` (`chained` or `fixed`) and
`format=csv`.

## A verdict

```json
{
  "level": "above",
  "headline": "Higher than usual",
  "value": 5449.0,
  "usual_low": 4669.0,
  "usual_high": 5005.0,
  "usual_median": 4866.0,
  "pct_vs_usual": 12.0,
  "history_days": 90,
  "as_of": "2026-10-24"
}
```

`level` is `above`, `typical`, `below` or `unknown` (not enough history).

## Admin

`POST /v1/admin/rebuild` with `Authorization: Bearer $AEROPULSE_ADMIN_TOKEN`. If the token is
not set, the endpoint does not exist (404).
