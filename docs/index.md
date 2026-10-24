# AeroPulse

AeroPulse is an open, route-level record of Indian domestic airfares. Every day it asks a
licensed fare provider for the cheapest economy fare on each departure date over the next two
months, for 40 busy routes, and publishes:

- whether fares on each route are **higher or lower than usual**, by how far ahead you book;
- a **national index** and indices per route and booking window, with 95% ranges;
- the **open dataset** behind every number, under CC BY 4.0.

It is built for three groups:

| Who | Question | Where |
|---|---|---|
| Travellers | Is this fare high right now? When is this route usually cheapest? | Route pages |
| Journalists and analysts | Did festival fares really jump, and by how much? | Festival pages, embeds, citations |
| Researchers and developers | Is there a daily Indian airfare series I can use? | Downloads, API |

## Principles

1. **Describe, never predict.** The site says what fares have done. It does not say what they
   will do.
2. **Licensed data only.** No scraping, no unofficial endpoints, nothing behind a login or a
   bot check.
3. **No personal data.** Nothing about travellers is collected.
4. **Reproducible.** Every published point can be rebuilt from the published files with
   `aeropulse rebuild`.
5. **Honest gaps.** Missing days stay missing. Demo data is always labelled.

## Where to start

- Try it locally: [Getting started](getting-started.md)
- Understand the numbers: [Method](methodology/index.md)
- Use the data: [Data dictionary](data/dictionary.md) and [API](data/api.md)
- Run your own copy: [Self-hosting](operations/self-hosting.md)
