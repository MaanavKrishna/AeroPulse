# Hosted preview (Vercel)

The repository can be deployed to Vercel as a **hosted preview**: the full site and API over
a read-only demo snapshot. It is for showing the product, not for publishing real numbers:
it collects nothing, and every page carries the demo banner. For real collection, run the
Docker stack in [Self-hosting](self-hosting.md).

## How it works

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
   mode, sets `AEROPULSE_ENV=production`, and serves the normal FastAPI app. The public site
   URL comes from Vercel's `VERCEL_PROJECT_PRODUCTION_URL` unless `AEROPULSE_SITE_URL` is set.

Search engines are told not to index it (`robots.txt` disallows everything while the data
is demo data).

## Deploy

Connect the GitHub repository in Vercel (framework preset: FastAPI); every push to `main`
deploys. Optional environment variables:

| Variable | Default | Meaning |
|---|---|---|
| `AEROPULSE_SITE_URL` | `https://<production domain>` | Used in citations, feeds and the sitemap |
| `AEROPULSE_SNAPSHOT_DAYS` | `120` | Days of demo history to generate at build time |

To try the same thing locally:

```bash
python deploy/vercel/build.py
uvicorn deploy.vercel.app:app --port 8000
```
