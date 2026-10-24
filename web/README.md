# AeroPulse website

The public site for AeroPulse, built with Next.js (App Router), TypeScript and Motion. It reads
everything from the AeroPulse API in the repository root; it has no database of its own.

## Run it

Start the API first (from the repository root):

```bash
aeropulse demo seed && aeropulse serve --port 8000
```

Then, in this folder:

```bash
cp .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000.

## Checks

```bash
npm run lint
npm run typecheck
npm run build
```

`npm run build` prerenders every route, airport and festival page, so the API must be running.
Set `AEROPULSE_SITE_KEY` on both sides so the build is not rate limited.

## Layout

| Path | What lives there |
| --- | --- |
| `src/app/(site)/` | Pages with the header and footer: home, routes, airports, trends, festivals, compare, guide, methodology, data, status, about |
| `src/app/embed/` | Bare chart pages for `<iframe>` embeds |
| `src/components/charts/` | Fare ribbon, route map, booking curve, weekday bars, multi-line, festival track |
| `src/components/ui/` | Pictograms, section heads, verdict chips, FAQ, copy buttons |
| `src/lib/` | API client (`api.ts`, cached for an hour), types, formatting, copy and chart maths |
| `src/styles/` | Design tokens and shared classes |

Design rules are in [`docs/contributing/design.md`](../docs/contributing/design.md).
