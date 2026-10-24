# Self-hosting

This is the full deployment with live collection. For a quick hosted preview over demo
data, see [Hosted preview (Vercel)](vercel.md).

One small VPS is enough: 2 vCPU, 2 GB RAM. The stack in `deploy/compose.yaml` runs:

| Service | Role |
|---|---|
| `db` | Postgres 16 |
| `app` | API, downloads, chart images and feeds (uvicorn, 2 workers); runs migrations on start |
| `web` | The Next.js website; builds on start once the API is healthy, then serves |
| `collector` | Collects, builds and exports every 6 hours (`deploy/collector.sh`) |
| `caddy` | HTTPS with automatic certificates. Sends `/v1/*`, `/downloads/*`, `/csv/*`, `/img/*`, `/feeds/*` to `app` and everything else to `web` |

## Steps

```bash
git clone https://github.com/MaanavKrishna/AeroPulse /opt/aeropulse && cd /opt/aeropulse
cp .env.example .env
```

Edit `.env`:

```bash
AEROPULSE_ENV=production
AEROPULSE_SITE_URL=https://fares.example.org
AEROPULSE_PROVIDERS=ignav
AEROPULSE_IGNAV_API_KEY=...
AEROPULSE_SITE_KEY=<long random string>
POSTGRES_PASSWORD=<long random string>
SITE_DOMAIN=fares.example.org
```

Then point the domain's DNS at the server and start:

```bash
docker compose --env-file .env -f deploy/compose.yaml up -d
docker compose --env-file .env -f deploy/compose.yaml logs -f collector
```

## Backups

`deploy/backup.sh /var/backups/aeropulse` writes a gzipped `pg_dump` and keeps 30 days. Run
it nightly from the host's cron, and copy the directory off the machine.

## Caching

The website's static files are content-hashed and cached for a year, and its pages refresh
from the API at most once an hour. API responses allow 5 minutes of shared caching. Put a CDN
in front if traffic grows.

## Updating

```bash
git pull && docker compose --env-file .env -f deploy/compose.yaml up -d --build
```

Migrations run automatically when the app starts, and the website rebuilds when its
container restarts.
