# Hosted preview (Vercel)

The repository deploys to Vercel as a **hosted preview**: the website and the API over a
read-only demo snapshot. It is for showing the product, not for publishing real numbers: it
collects nothing, and every page carries the demo notice. For real collection, run the
Docker stack in [Self-hosting](self-hosting.md).

It uses two Vercel projects connected to the same GitHub repository.

| Project | Root directory | Framework | Serves |
|---|---|---|---|
| `aeropulse-api` | `/` (repository root) | Python | `/v1/*`, downloads, CSV, chart images, feeds |
| `aeropulse` | `web` | Next.js | The website |

## The API project

Configured in `pyproject.toml`:

```toml
[tool.vercel]
entrypoint = "deploy.vercel.app:app"

[tool.vercel.scripts]
build = "python deploy/vercel/build.py"
```

1. **Build** (`deploy/vercel/build.py`): generates 120 days of labelled synthetic history
   with the demo provider, strips raw payloads, compacts the database to about 56 MB, and
   writes the open-data export. Takes about a minute.
2. **Serve** (`deploy/vercel/app.py`): opens the snapshot with SQLite's read-only, immutable
   mode, sets `AEROPULSE_ENV=production`, and serves the normal FastAPI app.

| Variable | Meaning |
|---|---|
| `AEROPULSE_SITE_URL` | The website's address, used in feeds and chart images |
| `AEROPULSE_SITE_KEY` | Shared secret; requests from the website that carry it skip the rate limit |
| `AEROPULSE_SNAPSHOT_DAYS` | Days of demo history to generate at build time (default 120) |

## The website project

A standard Next.js project with **Root Directory** set to `web`.

| Variable | Meaning |
|---|---|
| `NEXT_PUBLIC_AEROPULSE_API_URL` | The API project's address, e.g. `https://aeropulse-api.vercel.app` |
| `NEXT_PUBLIC_SITE_URL` | The website's own address |
| `AEROPULSE_SITE_KEY` | The same secret as on the API project. Server-only |

The build prerenders every route, airport and festival page from the API, so deploy the API
first. Pages refresh from the API at most once an hour.

Search engines are told not to index either project while the data is demo data.

## Try it locally

```bash
python deploy/vercel/build.py
uvicorn deploy.vercel.app:app --port 8000
cd web && npm run build && npm start
```
