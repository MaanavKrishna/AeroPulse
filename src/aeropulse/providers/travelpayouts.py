"""Travelpayouts Aviasales Data API, v3 `prices_for_dates`.

Docs: https://support.travelpayouts.com/hc/en-us/articles/203956163

These are cached prices that Aviasales users found in roughly the last 48 hours, not live
searches. Busy routes are well covered; thin routes have gaps. One call returns tickets for
one departure month, so a 60-day horizon needs two or three calls.

The response shape below is taken from the public docs and has not yet been checked
against a live response. The provider spike (docs/operations/provider-spike.md) must
confirm it before this provider is enabled.
"""
from __future__ import annotations

import datetime as dt
import json

import httpx

from .base import DateFare, ProviderError, ProviderResponse, SchemaChangeError

BASE_URL = "https://api.travelpayouts.com"


def months_between(start: dt.date, end: dt.date) -> list[str]:
    out, cur = [], start.replace(day=1)
    while cur <= end:
        out.append(cur.strftime("%Y-%m"))
        cur = (cur + dt.timedelta(days=32)).replace(day=1)
    return out


def parse_prices_for_dates(payload: str) -> list[DateFare]:
    """Collapse tickets to the cheapest per departure date."""
    try:
        data = json.loads(payload)
        if not data.get("success", False):
            raise ValueError(f"success=false: {data.get('error')}")
        currency = str(data.get("currency", "")).upper()
        best: dict[dt.date, DateFare] = {}
        for t in data["data"]:
            day = dt.date.fromisoformat(str(t["departure_at"])[:10])
            fare = DateFare(day, float(t["price"]), currency, t.get("airline"), "cached")
            if day not in best or fare.fare < best[day].fare:
                best[day] = fare
        return sorted(best.values(), key=lambda f: f.departure_date)
    except (KeyError, TypeError, ValueError) as exc:
        raise SchemaChangeError(f"unexpected Travelpayouts response shape: {exc!r}") from exc


class TravelpayoutsProvider:
    name = "travelpayouts"
    is_demo = False

    def __init__(self, token: str, *, timeout: float = 30.0,
                 client: httpx.Client | None = None) -> None:
        if not token:
            raise ProviderError("AEROPULSE_TRAVELPAYOUTS_TOKEN is not set")
        self._client = client or httpx.Client(
            base_url=BASE_URL, timeout=timeout,
            headers={"X-Access-Token": token, "Accept": "application/json"})

    def cheapest_dates(self, origin: str, destination: str, start: dt.date,
                       end: dt.date) -> ProviderResponse:
        request = {"origin": origin, "destination": destination,
                   "months": months_between(start, end), "currency": "inr", "one_way": True}
        response = ProviderResponse(self.name, request, None, None,
                                    dt.datetime.now(dt.UTC))
        payloads, fares = [], {}
        for month in request["months"]:
            params = {"origin": origin, "destination": destination, "departure_at": month,
                      "one_way": "true", "direct": "false", "currency": "inr",
                      "sorting": "price", "limit": 1000}
            try:
                r = self._client.get("/aviasales/v3/prices_for_dates", params=params)
            except httpx.HTTPError as exc:
                response.error = f"network error: {exc!r}"
                break
            response.http_status = r.status_code
            payloads.append(r.text)
            if r.status_code != 200:
                response.error = f"HTTP {r.status_code}"
                break
            try:
                for f in parse_prices_for_dates(r.text):
                    if start <= f.departure_date <= end:
                        if f.departure_date not in fares or f.fare < fares[f.departure_date].fare:
                            fares[f.departure_date] = f
            except SchemaChangeError as exc:
                response.error = str(exc)
                break
        response.payload = json.dumps(payloads)
        response.calls = max(1, len(payloads))
        response.fares = sorted(fares.values(), key=lambda f: f.departure_date)
        return response

    def close(self) -> None:
        self._client.close()
