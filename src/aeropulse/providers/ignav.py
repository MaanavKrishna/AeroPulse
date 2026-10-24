"""Ignav fare API: https://ignav.com/docs (OpenAPI at https://ignav.com/api/openapi.json).

We use one endpoint, POST /api/fares/cheapest-dates, which returns the lowest qualifying
fare for every departure date in a range. One call covers a route's whole booking horizon.
"""
from __future__ import annotations

import datetime as dt
import json

import httpx

from .base import DateFare, ProviderError, ProviderResponse, SchemaChangeError

BASE_URL = "https://ignav.com/api"
USER_AGENT = "AeroPulse/0.1 (+https://github.com/MaanavKrishna/aeropulse)"


def parse_cheapest_dates(payload: str) -> tuple[list[DateFare], dt.datetime | None]:
    """Parse a CheapestDatesResponseModel. Raises SchemaChangeError on any surprise."""
    try:
        data = json.loads(payload)
        dates = data["dates"]
        if not isinstance(dates, list):
            raise TypeError("dates is not a list")
        observed = data.get("observed_at")
        observed_at = dt.datetime.fromisoformat(observed.replace("Z", "+00:00")) \
            if observed else None
        fares = []
        for row in dates:
            price = row.get("price")
            if price is None:                 # no fare found for that date
                continue
            fares.append(DateFare(
                departure_date=dt.date.fromisoformat(row["departure_date"][:10]),
                fare=float(price["amount"]),
                currency=str(price["currency"]).upper(),
                price_status=price.get("status")))
        return fares, observed_at
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise SchemaChangeError(f"unexpected Ignav response shape: {exc!r}") from exc


class IgnavProvider:
    name = "ignav"
    is_demo = False

    def __init__(self, api_key: str, *, market: str = "IN", timeout: float = 30.0,
                 client: httpx.Client | None = None) -> None:
        if not api_key:
            raise ProviderError("AEROPULSE_IGNAV_API_KEY is not set")
        self.market = market
        self._client = client or httpx.Client(
            base_url=BASE_URL, timeout=timeout,
            headers={"X-Api-Key": api_key, "User-Agent": USER_AGENT,
                     "Accept": "application/json"})

    def cheapest_dates(self, origin: str, destination: str, start: dt.date,
                       end: dt.date) -> ProviderResponse:
        body = {"origin": origin, "destination": destination,
                "departure_date_range": {"start": start.isoformat(), "end": end.isoformat()},
                "cabin_class": "economy", "adults": 1, "market": self.market}
        response = ProviderResponse(self.name, body, None, None, None)
        try:
            r = self._client.post("/fares/cheapest-dates", json=body)
        except httpx.HTTPError as exc:
            response.error = f"network error: {exc!r}"
            return response
        response.http_status = r.status_code
        response.payload = r.text
        if r.status_code != 200:
            response.error = _error_message(r)
            return response
        try:
            response.fares, response.observed_at = parse_cheapest_dates(r.text)
        except SchemaChangeError as exc:
            response.error = str(exc)
        return response

    def close(self) -> None:
        self._client.close()


def _error_message(r: httpx.Response) -> str:
    try:
        err = r.json()["error"]
        return f"HTTP {r.status_code} {err.get('code')}: {err.get('message')}"
    except (ValueError, KeyError, TypeError):
        return f"HTTP {r.status_code}"
