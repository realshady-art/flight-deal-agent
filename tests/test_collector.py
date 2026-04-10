from datetime import date
from decimal import Decimal

from flight_deal_agent.collector import _parse_inspiration_item, _parse_offer


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
