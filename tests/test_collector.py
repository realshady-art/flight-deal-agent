from datetime import date
from decimal import Decimal
from pathlib import Path

from flight_deal_agent.collector import (
    _parse_inspiration_item,
    _parse_offer,
    _parse_searchapi_flight,
    collect_quotes,
)
from flight_deal_agent.orchestrator import SearchTask
from flight_deal_agent.settings import load_app_config


def test_parse_inspiration_item():
    item = {
        "type": "flight-destination",
        "origin": "BOS",
        "destination": "CHI",
        "departureDate": "2026-07-22",
        "returnDate": "2026-07-28",
        "price": {"total": "52.18"},
    }
    q = _parse_inspiration_item(item, "run1")
    assert q is not None
    assert q.origin == "BOS"
    assert q.destination == "CHI"
    assert q.total_price == Decimal("52.18")
    assert q.departure_date == date(2026, 7, 22)
    assert q.return_date == date(2026, 7, 28)
    assert q.source == "amadeus-inspiration"


def test_parse_inspiration_item_bad_data():
    assert _parse_inspiration_item({}, "r") is None


def test_parse_offer():
    offer = {
        "type": "flight-offer",
        "id": "1",
        "itineraries": [
            {
                "segments": [
                    {
                        "departure": {"iataCode": "BOS", "at": "2026-07-22T10:00:00"},
                        "arrival": {"iataCode": "LHR", "at": "2026-07-22T22:00:00"},
                        "carrierCode": "BA",
                        "number": "100",
                        "numberOfStops": 0,
                    }
                ]
            },
            {
                "segments": [
                    {
                        "departure": {"iataCode": "LHR", "at": "2026-07-29T10:00:00"},
                        "arrival": {"iataCode": "BOS", "at": "2026-07-29T14:00:00"},
                        "carrierCode": "BA",
                        "number": "101",
                        "numberOfStops": 0,
                    }
                ]
            },
        ],
        "price": {
            "currency": "USD",
            "total": "456.00",
            "grandTotal": "456.00",
        },
    }
    q = _parse_offer(offer, "run1")
    assert q is not None
    assert q.origin == "BOS"
    assert q.destination == "LHR"
    assert q.total_price == Decimal("456.00")
    assert q.trip_type == "round_trip"
    assert q.stops == 0
    assert q.carrier_codes == ["BA"]
    assert q.return_date == date(2026, 7, 29)


def test_parse_offer_bad_data():
    assert _parse_offer({}, "r") is None


def test_parse_searchapi_flight():
    item = {
        "flights": [
            {
                "departure_airport": {"id": "YVR", "date": "2026-07-22", "time": "10:00"},
                "arrival_airport": {"id": "LAX", "date": "2026-07-22", "time": "13:00"},
                "flight_number": "AC 123",
            }
        ],
        "price": 89,
    }
    task = SearchTask(
        origin="YVR",
        destination="LAX",
        departure_date=date(2026, 7, 22),
        return_date=date(2026, 7, 29),
    )
    q = _parse_searchapi_flight(item, task, "run1")
    assert q is not None
    assert q.origin == "YVR"
    assert q.destination == "LAX"
    assert q.total_price == Decimal("89")
    assert q.return_date == date(2026, 7, 29)
    assert q.source == "searchapi-google-flights"
    assert q.carrier_codes == ["AC"]


def test_collect_quotes_searchapi(tmp_config: Path, monkeypatch):
    cfg = load_app_config(tmp_config)
    cfg.collector.provider = "searchapi"
    task = SearchTask(
        origin="YVR",
        destination="LAX",
        departure_date=date(2026, 7, 22),
        return_date=date(2026, 7, 29),
    )

    def fake_search(self, client, task, currency="USD", max_price=None):
        return {
            "best_flights": [
                {
                    "flights": [
                        {
                            "departure_airport": {"id": "YVR", "date": "2026-07-22", "time": "10:00"},
                            "arrival_airport": {"id": "LAX", "date": "2026-07-22", "time": "13:00"},
                            "flight_number": "AC 123",
                        }
                    ],
                    "price": 89,
                }
            ]
        }

    monkeypatch.setattr("flight_deal_agent.collector.SearchApiClient.search_flights", fake_search)
    quotes, api_calls = collect_quotes(cfg, [task], "run1")
    assert api_calls == 1
    assert len(quotes) == 1
    assert quotes[0].source == "searchapi-google-flights"
    assert quotes[0].total_price == Decimal("89")
