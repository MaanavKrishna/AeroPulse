# Configuration

All settings are environment variables (or a `.env` file). Secrets are never read from
anywhere else.

| Variable | Default | Meaning |
|---|---|---|
| `AEROPULSE_ENV` | `development` | `development`, `production` or `test`. Production refuses the demo provider and unreviewed provider terms. |
| `AEROPULSE_DATABASE_URL` | `sqlite:///./aeropulse.db` | SQLAlchemy URL. Postgres: `postgresql+psycopg://user:pass@host/db` |
| `AEROPULSE_SITE_URL` | `http://localhost:8000` | Public URL for citations, feeds, sitemap |
| `AEROPULSE_PROVIDERS` | `ignav` | Comma-separated, priority order. The first feeds the index. |
| `AEROPULSE_IGNAV_API_KEY` | | Ignav key (secret) |
| `AEROPULSE_TRAVELPAYOUTS_TOKEN` | | Travelpayouts token (secret) |
| `AEROPULSE_MAX_CALLS_PER_DAY` | `200` | Hard cap per provider per IST day |
| `AEROPULSE_HTTP_TIMEOUT` | `30` | Seconds per provider request |
| `AEROPULSE_ALLOW_UNREVIEWED_TERMS` | `false` | Private trial only; shows a notice on every page |
| `AEROPULSE_ADMIN_TOKEN` | | Enables `/v1/admin/*` (secret) |
| `AEROPULSE_RATE_LIMIT` | `120` | API requests per minute per client |
| `AEROPULSE_BASKET_PATH` | `./basket.yaml` | Basket definition |
| `AEROPULSE_FESTIVALS_PATH` | `./data/festivals.yaml` | Festival calendar |
| `AEROPULSE_EXPORT_DIR` | `./exports` | Where `aeropulse export` writes |
| `AEROPULSE_COLLECT_EVERY` | `21600` | Collector loop interval in seconds (Docker only) |
