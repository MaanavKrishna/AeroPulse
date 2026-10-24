# Self-hosting

This is the full deployment with live collection. For a quick hosted preview over demo
data, see [Hosted preview (Vercel)](vercel.md).

One small VPS is enough: 2 vCPU, 2 GB RAM. The stack in `deploy/compose.yaml` runs:

| Service | Role |
|---|---|
| `db` | Postgres 16 |
| `app` | Site and API (uvicorn, 2 workers); runs migrations on start |
| `collector` | Collects, builds and exports every 6 hours (`deploy/collector.sh`) |
| `caddy` | HTTPS with automatic certificates |

## Steps

```bash
git clone https://github.com/MaanavKrishna/aeropulse /opt/aeropulse && cd /opt/aeropulse
cp .env.example .env
```

Edit `.env`:

```bash
AEROPULSE_ENV=production
AEROPULSE_SITE_URL=https://fares.example.org
AEROPULSE_PROVIDERS=ignav
AEROPULSE_IGNAV_API_KEY=...
POSTGRES_PASSWORD=<long random string>
SITE_DOMAIN=fares.example.org
```

Then point the domain's DNS at the server and start:

```bash
docker compose -f deploy/compose.yaml up -d
docker compose -f deploy/compose.yaml logs -f collector
```

## Backups

`deploy/backup.sh /var/backups/aeropulse` writes a gzipped `pg_dump` and keeps 30 days. Run
it nightly from the host's cron, and copy the directory off the machine.

## Caching

Static files are content-hashed and cached for a year. API and embed responses allow 5
minutes of shared caching. Put a CDN in front if traffic grows.

## Updating

```bash
git pull && docker compose -f deploy/compose.yaml up -d --build
```

Migrations run automatically when the app starts.
