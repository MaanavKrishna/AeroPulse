"""Where fares come from and what we are allowed to do with them.

Every provider is a licensed API used with our own key. We do not scrape airline or travel
sites, call unofficial endpoints, get around rate limits or bot checks, or collect anything
about travellers.

`terms_reviewed` stays False until a person has read the provider's current terms and
confirmed that (a) storing responses and (b) publishing indices derived from them are
allowed. Production collection refuses to run for a provider whose terms are unreviewed,
unless AEROPULSE_ALLOW_UNREVIEWED_TERMS is set for a private trial.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderPolicy:
    name: str
    display_name: str
    homepage: str
    terms_url: str
    kind: str
    #: May raw fares (per departure date) be republished? Default no: we publish only
    #: aggregates and indices until the terms clearly allow more.
    raw_redistribution: bool
    terms_reviewed: bool
    attribution: str
    notes: str


POLICIES: dict[str, ProviderPolicy] = {
    "ignav": ProviderPolicy(
        name="ignav", display_name="Ignav", homepage="https://ignav.com",
        terms_url="https://ignav.com/terms", kind="Licensed fare API (pay per request)",
        raw_redistribution=False, terms_reviewed=False,
        attribution="Fare data from Ignav.",
        notes="Cheapest fare per departure date via POST /api/fares/cheapest-dates. "
              "Pricing at time of writing: first 1,000 requests free, then $2 per 1,000."),
    "travelpayouts": ProviderPolicy(
        name="travelpayouts", display_name="Travelpayouts (Aviasales Data API)",
        homepage="https://www.travelpayouts.com",
        terms_url="https://www.travelpayouts.com/terms", kind="Cached fare API (free, token)",
        raw_redistribution=False, terms_reviewed=False,
        attribution="Fare data from Aviasales via Travelpayouts.",
        notes="Prices are cached from searches by Aviasales users in the previous 48 hours, "
              "so thin routes can have gaps. Used as a cross-check."),
    "demo": ProviderPolicy(
        name="demo", display_name="Demo generator", homepage="",
        terms_url="", kind="Synthetic data for development",
        raw_redistribution=True, terms_reviewed=True,
        attribution="Synthetic demo data. Not real fares.",
        notes="Deterministic generator used for development and tests. Refused in "
              "production."),
}


NEVER_COLLECTED = (
    "Names, emails, phone numbers or any other traveller details",
    "Booking references or payment information",
    "Anything behind a login, a paywall or a bot check",
    "Pages or endpoints that a site's robots.txt or terms disallow",
)
