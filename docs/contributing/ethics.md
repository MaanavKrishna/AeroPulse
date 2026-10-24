# Ethics

These rules are part of the product. Code that breaks them is not merged.

1. **Licensed sources only.** Fares come from APIs we have a key for, used within their
   terms. No scraping of airline or travel-agency sites, no reverse-engineered endpoints,
   no working around rate limits, logins, CAPTCHAs or bot detection.
2. **No personal data.** Nothing about any traveller is collected, stored or inferred. The
   site sets no tracking cookies and loads nothing from third parties.
3. **No invented data in public.** The demo generator exists for development only. Every page
   says so while demo data is present; production refuses to run it; robots are told not to
   index a demo site.
4. **No prediction.** We describe what fares have done. Fare prediction sold as certainty
   pushes people into bad decisions; we don't do it.
5. **Gaps stay gaps.** A missed collection is shown as missing, never filled in.
6. **Every number can be checked.** Method, code and data are open, and
   `aeropulse rebuild` recomputes the published index from the published files.
7. **Secrets stay secret.** Keys live only in environment variables, never in the
   repository, the database or logs.
