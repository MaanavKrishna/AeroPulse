# Provider trial (go / no-go)

Before AeroPulse publishes a single real number, one provider has to pass this trial. It
gates the launch.

## 1. Terms (a person does this, not code)

Read the provider's current terms of service and API terms. Record the answers below, with
quotes and the date read, in a pull request that flips `terms_reviewed=True` in
`src/aeropulse/providers/policy.py`.

- [ ] May we store API responses indefinitely?
- [ ] May we publish statistics derived from them (medians, indices) under CC BY 4.0?
- [ ] May we republish individual fares? (Sets `raw_redistribution`; default no.)
- [ ] Is attribution required, and in what form?
- [ ] Is commercial or non-commercial use restricted?
- [ ] Rate limits and pricing at our volume (~40 calls per run, 4 runs a day)?

If any of the first two answers is no or unclear, ask the provider in writing before going
further.

## 2. Coverage (a week of real calls)

With `AEROPULSE_ALLOW_UNREVIEWED_TERMS=true` on a **private** instance:

```bash
aeropulse collect --limit 5     # first, a smoke test
aeropulse collect               # then the full basket, 4 times a day for 7 days
```

Go if all of these hold over the week:

- [ ] At least 95% of scheduled runs finish `ok` or `partial` (see `/status`).
- [ ] At least 80% of route × window × day products reach 3 priced dates.
- [ ] Prices come back in INR. If they don't, the `currency` screening rule will exclude
      everything; check the `market` parameter.
- [ ] `observed_at` is within 48 hours of the call for most answers.
- [ ] Spot-check 10 fares by hand against the airline's own site on the same day. They
      should be close, not identical; record the differences.

## 3. Record

Replace `tests/fixtures/*.json` with real recorded responses, which contain no secrets. Note
the trial results in `CHANGELOG.md`.

If Ignav fails, repeat with Travelpayouts. If both fail, the fallback is a paid SerpApi
Google Flights plan; budget and terms need the same review.
