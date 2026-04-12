"""
Collector: fetch flight quotes from external APIs.

Supported providers:
  - stub       : returns nothing (for local testing)
  - amadeus    : Amadeus Self-Service via httpx (free tier)
  - searchapi  : SearchApi Google Flights via httpx
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import httpx

from flight_deal_agent.models import QuoteSnapshot
from flight_deal_agent.orchestrator import SearchTask
from flight_deal_agent.settings import AmadeusConfig, AppConfig, SearchApiConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Amadeus HTTP client (uses httpx, no SDK dependency)
# ---------------------------------------------------------------------------

class AmadeusClient:
    """Thin wrapper around the Amadeus Self-Service REST API."""

    def __init__(self, config: AmadeusConfig):
        self._cfg = config
        self._token: Optional[str] = None
        self._token_expires: Optional[datetime] = None

    def _ensure_token(self, client: httpx.Client) -> str:
        now = datetime.now(tz=timezone.utc)
        if self._token and self._token_expires and now < self._token_expires:
            return self._token

        resp = client.post(
            f"{self._cfg.base_url}/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self._cfg.client_id,
                "client_secret": self._cfg.client_secret,
            },
        )
        resp.raise_for_status()
        body = resp.json()
        self._token = body["access_token"]
        expires_in = int(body.get("expires_in", 1799))
        from datetime import timedelta
        self._token_expires = now + timedelta(seconds=max(expires_in - 60, 60))
        return self._token  # type: ignore[return-value]

    # -- Flight Inspiration Search (cached prices, 1 call → many destinations) --

    def search_inspiration(
        self,
        client: httpx.Client,
        origin: str,
        *,
        max_price: Optional[int] = None,
        non_stop: bool = False,
    ) -> List[Dict[str, Any]]:
        token = self._ensure_token(client)
        params: Dict[str, Any] = {"origin": origin}
        if max_price is not None:
            params["maxPrice"] = max_price
        if non_stop:
            params["nonStop"] = "true"
        resp = client.get(
            f"{self._cfg.base_url}/v1/shopping/flight-destinations",
            params=params,
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code == 200:
            return resp.json().get("data", [])
        logger.warning("Inspiration search %s → HTTP %s: %s", origin, resp.status_code, resp.text[:300])
        return []

    # -- Flight Offers Search (real-time, 1 call per OD+date) --

    def search_offers(
        self,
        client: httpx.Client,
        origin: str,
        destination: str,
        departure_date: str,
        *,
        return_date: Optional[str] = None,
        currency: str = "USD",
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        token = self._ensure_token(client)
        params: Dict[str, Any] = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": 1,
            "currencyCode": currency,
            "max": max_results,
        }
        if return_date:
            params["returnDate"] = return_date
        resp = client.get(
            f"{self._cfg.base_url}/v2/shopping/flight-offers",
            params=params,
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code == 200:
            return resp.json().get("data", [])
        logger.warning(
            "Offers search %s->%s %s → HTTP %s: %s",
            origin, destination, departure_date, resp.status_code, resp.text[:300],
        )
        return []


class SearchApiClient:
    """Thin wrapper around SearchApi Google Flights."""

    def __init__(self, config: SearchApiConfig):
        self._cfg = config

    def search_flights(
        self,
        client: httpx.Client,
        task: SearchTask,
        *,
        currency: str = "USD",
        max_price: Optional[int] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "engine": "google_flights",
            "flight_type": "round_trip" if task.return_date else "one_way",
            "departure_id": task.origin,
            "arrival_id": task.destination,
            "outbound_date": task.departure_date.isoformat(),
            "currency": currency,
            "sort_by": "price",
            "show_cheapest_flights": "true",
            "gl": self._cfg.gl,
            "hl": self._cfg.hl,
        }
        if task.return_date:
            params["return_date"] = task.return_date.isoformat()
        if max_price is not None:
            params["max_price"] = max_price
        resp = client.get(
            f"{self._cfg.base_url}/api/v1/search",
            params=params,
            headers={"Authorization": f"Bearer {self._cfg.api_key}"},
        )
        if resp.status_code == 200:
            return resp.json()
        logger.warning(
            "SearchApi search %s->%s %s → HTTP %s: %s",
            task.origin,
            task.destination,
            task.departure_date.isoformat(),
            resp.status_code,
            resp.text[:300],
        )
        return {}


# ---------------------------------------------------------------------------
# Response parsing helpers
# ---------------------------------------------------------------------------

def _parse_inspiration_item(item: Dict[str, Any], run_id: str) -> Optional[QuoteSnapshot]:
    """Parse one element from /v1/shopping/flight-destinations response."""
    try:
        from datetime import date as _date
        dep = _date.fromisoformat(item["departureDate"])
        ret_str = item.get("returnDate")
        ret = _date.fromisoformat(ret_str) if ret_str else None
        return QuoteSnapshot(
            search_ts=datetime.now(tz=timezone.utc),
            run_id=run_id,
            origin=item["origin"],
            destination=item["destination"],
            departure_date=dep,
            return_date=ret,
            trip_type="round_trip" if ret else "one_way",
            currency=item.get("price", {}).get("currency", "USD"),
            total_price=Decimal(str(item["price"]["total"])),
            source="amadeus-inspiration",
        )
    except Exception:
        logger.debug("Failed to parse inspiration item: %s", item, exc_info=True)
        return None


def _parse_offer(offer: Dict[str, Any], run_id: str) -> Optional[QuoteSnapshot]:
    """Parse one element from /v2/shopping/flight-offers response."""
    try:
        from datetime import date as _date
        price_info = offer["price"]
        itineraries = offer.get("itineraries", [])

        # departure info from first itinerary
        first_itin = itineraries[0]
        first_seg = first_itin["segments"][0]
        origin = first_seg["departure"]["iataCode"]
        dep_dt = first_seg["departure"]["at"][:10]

        last_seg = first_itin["segments"][-1]
        destination = last_seg["arrival"]["iataCode"]

        outbound_stops = max(len(first_itin["segments"]) - 1, 0)

        carriers: List[str] = []
        for seg in first_itin["segments"]:
            cc = seg.get("carrierCode", "")
            if cc and cc not in carriers:
                carriers.append(cc)

        ret_date = None
        if len(itineraries) > 1:
            ret_seg = itineraries[1]["segments"][0]
            ret_date = _date.fromisoformat(ret_seg["departure"]["at"][:10])

        return QuoteSnapshot(
            search_ts=datetime.now(tz=timezone.utc),
            run_id=run_id,
            origin=origin,
            destination=destination,
            departure_date=_date.fromisoformat(dep_dt),
            return_date=ret_date,
            trip_type="round_trip" if ret_date else "one_way",
            currency=price_info.get("currency", "USD"),
            total_price=Decimal(str(price_info.get("grandTotal", price_info["total"]))),
            source="amadeus-offers",
            stops=outbound_stops,
            carrier_codes=carriers or None,
        )
    except Exception:
        logger.debug("Failed to parse offer: %s", offer, exc_info=True)
        return None


def _parse_searchapi_flight(
    item: Dict[str, Any],
    task: SearchTask,
    run_id: str,
) -> Optional[QuoteSnapshot]:
    """Parse one itinerary from SearchApi Google Flights results."""
    try:
        flights = item["flights"]
        first_leg = flights[0]
        last_leg = flights[-1]

        carriers: List[str] = []
        for leg in flights:
            flight_number = str(leg.get("flight_number", "")).strip()
            code = flight_number.split()[0] if flight_number else ""
            if code and code not in carriers:
                carriers.append(code)

        return QuoteSnapshot(
            search_ts=datetime.now(tz=timezone.utc),
            run_id=run_id,
            origin=first_leg["departure_airport"]["id"],
            destination=last_leg["arrival_airport"]["id"],
            departure_date=task.departure_date,
            return_date=task.return_date,
            trip_type="round_trip" if task.return_date else "one_way",
            currency="USD",
            total_price=Decimal(str(item["price"])),
            source="searchapi-google-flights",
            stops=max(len(flights) - 1, 0),
            carrier_codes=carriers or None,
        )
    except Exception:
        logger.debug("Failed to parse SearchApi flight: %s", item, exc_info=True)
        return None


# ---------------------------------------------------------------------------
# Public collect functions
# ---------------------------------------------------------------------------

def collect_quotes_stub(
    config: AppConfig,
    tasks: List[SearchTask],
    run_id: str,
) -> Tuple[List[QuoteSnapshot], int]:
    """Stub: returns nothing. api_calls=0."""
    return [], 0


def collect_quotes_amadeus(
    config: AppConfig,
    tasks: List[SearchTask],
    run_id: str,
) -> Tuple[List[QuoteSnapshot], int]:
    """
    Two-stage collection via Amadeus:
      Stage 1 – Inspiration Search (1 call/origin, cached data, many destinations).
      Stage 2 – Flight Offers Search for specific tasks not covered by Stage 1.
    Respects request_budget_per_run.
    """
    amadeus = AmadeusClient(config.amadeus)
    budget = config.collector.request_budget_per_run
    api_calls = 0
    quotes: List[QuoteSnapshot] = []

    # -- which destinations are in our region? --
    dest_set = {t.destination for t in tasks}

    origin_set = sorted({t.origin for t in tasks})

    with httpx.Client(timeout=30) as client:
        # Stage 1: Inspiration (very cheap in API calls)
        for origin in origin_set:
            if api_calls >= budget:
                break
            raw = amadeus.search_inspiration(
                client, origin,
                max_price=int(config.thresholds.max_total_price) if config.thresholds.max_total_price else None,
            )
            api_calls += 1
            for item in raw:
                if item.get("destination") in dest_set:
                    q = _parse_inspiration_item(item, run_id)
                    if q:
                        quotes.append(q)

        # Stage 2: Offers for any tasks not yet covered by inspiration
        covered = {(q.origin, q.destination) for q in quotes}
        for task in tasks:
            if api_calls >= budget:
                break
            if (task.origin, task.destination) in covered:
                continue
            raw_offers = amadeus.search_offers(
                client,
                task.origin,
                task.destination,
                task.departure_date.isoformat(),
                return_date=task.return_date.isoformat() if task.return_date else None,
                currency=config.currency,
                max_results=3,
            )
            api_calls += 1
            for offer in raw_offers:
                q = _parse_offer(offer, run_id)
                if q:
                    quotes.append(q)
            covered.add((task.origin, task.destination))

    logger.info("Amadeus collection done: api_calls=%d quotes=%d", api_calls, len(quotes))
    return quotes, api_calls


def collect_quotes_searchapi(
    config: AppConfig,
    tasks: List[SearchTask],
    run_id: str,
) -> Tuple[List[QuoteSnapshot], int]:
    """Collect the cheapest Google Flights quote per task via SearchApi."""
    searchapi = SearchApiClient(config.searchapi)
    quotes: List[QuoteSnapshot] = []
    api_calls = 0

    with httpx.Client(timeout=30) as client:
        for task in tasks:
            body = searchapi.search_flights(
                client,
                task,
                currency=config.currency,
                max_price=int(config.thresholds.max_total_price) if config.thresholds.max_total_price else None,
            )
            api_calls += 1
            candidates = body.get("best_flights", []) + body.get("other_flights", [])
            if not candidates:
                continue
            candidates = sorted(
                candidates,
                key=lambda item: Decimal(str(item.get("price", "999999999"))),
            )
            quote = _parse_searchapi_flight(candidates[0], task, run_id)
            if quote:
                quote.currency = config.currency
                quotes.append(quote)

    logger.info("SearchApi collection done: api_calls=%d quotes=%d", api_calls, len(quotes))
    return quotes, api_calls


def collect_quotes(
    config: AppConfig,
    tasks: List[SearchTask],
    run_id: str,
) -> Tuple[List[QuoteSnapshot], int]:
    provider = config.collector.provider
    if provider == "stub":
        return collect_quotes_stub(config, tasks, run_id)
    if provider == "amadeus":
        return collect_quotes_amadeus(config, tasks, run_id)
    if provider == "searchapi":
        return collect_quotes_searchapi(config, tasks, run_id)
    raise NotImplementedError(f"collector.provider={provider!r} not implemented")
