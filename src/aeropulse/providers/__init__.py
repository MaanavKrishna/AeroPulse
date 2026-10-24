from __future__ import annotations

import datetime as dt

from ..config import Settings
from .base import DateFare, Provider, ProviderError, ProviderResponse, SchemaChangeError
from .policy import POLICIES

__all__ = ["DateFare", "Provider", "ProviderError", "ProviderResponse", "SchemaChangeError",
           "POLICIES", "make_provider"]


def make_provider(name: str, settings: Settings, collection_date: dt.date) -> Provider:
    """Build a configured provider, refusing anything that would publish something untrue
    or that we have not confirmed we may use."""
    if name not in POLICIES:
        raise ProviderError(f"unknown provider {name!r}; known: {', '.join(POLICIES)}")
    policy = POLICIES[name]
    if name == "demo":
        if settings.is_production:
            raise ProviderError("the demo provider cannot run in production")
        from .demo import DemoProvider
        return DemoProvider(collection_date)
    if settings.is_production and not policy.terms_reviewed \
            and not settings.allow_unreviewed_terms:
        raise ProviderError(
            f"{policy.display_name}: terms not yet reviewed (see providers/policy.py). "
            "Review them, or set AEROPULSE_ALLOW_UNREVIEWED_TERMS=true for a private trial.")
    if name == "ignav":
        from .ignav import IgnavProvider
        key = settings.ignav_api_key.get_secret_value() if settings.ignav_api_key else ""
        return IgnavProvider(key, timeout=settings.http_timeout)
    if name == "travelpayouts":
        from .travelpayouts import TravelpayoutsProvider
        token = (settings.travelpayouts_token.get_secret_value()
                 if settings.travelpayouts_token else "")
        return TravelpayoutsProvider(token, timeout=settings.http_timeout)
    raise ProviderError(f"provider {name!r} has a policy but no adapter")
