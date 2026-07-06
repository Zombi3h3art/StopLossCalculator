"""Tests for margin interest and the live-SOFR fetch with fallback."""

from decimal import Decimal

import pytest
import requests

from stoploss import rates
from stoploss.rates import (
    MarginLoan,
    calculate_margin_interest,
    calculate_total_margin_interest,
    fetch_sofr_reference,
)


class TestMarginInterest:
    def test_golden_360_day_accrual(self):
        """5000 * 0.065 * 2/360 = 1.8055... -> 1.81"""
        assert calculate_margin_interest(Decimal("5000"), Decimal("0.065"), 2) == Decimal("1.81")

    def test_three_loan_cascade(self):
        """Matches WORKED_EXAMPLES GC trade: 9.03 + 4.72 + 1.33 = 15.08"""
        loans = [
            MarginLoan(Decimal("10000"), Decimal("0.065"), 5),
            MarginLoan(Decimal("5000"), Decimal("0.085"), 4),
            MarginLoan(Decimal("2000"), Decimal("0.120"), 2),
        ]
        assert calculate_total_margin_interest(loans) == Decimal("15.08")

    def test_more_than_three_loans_rejected(self):
        loans = [MarginLoan(Decimal("1000"), Decimal("0.05"), 1)] * 4
        with pytest.raises(ValueError):
            calculate_total_margin_interest(loans)


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class TestSofrFetch:
    def _clear_cache(self):
        rates._sofr_cache = None
        rates._sofr_cache_at = 0.0

    def test_network_failure_falls_back_to_static(self, monkeypatch):
        self._clear_cache()

        def boom(*args, **kwargs):
            raise requests.ConnectionError("no network")

        monkeypatch.setattr(rates.requests, "get", boom)
        data = fetch_sofr_reference(force_refresh=True)
        assert data["current"] == "5.33"
        assert data["avg_30"] == "5.35"
        assert data["avg_90"] == "5.30"
        assert "fallback" in data["source"].lower()
        self._clear_cache()

    def test_live_payload_is_parsed(self, monkeypatch):
        self._clear_cache()
        payloads = {
            rates._NYFED_SOFR_URL: {
                "refRates": [{"effectiveDate": "2026-07-02", "percentRate": 4.31}]
            },
            rates._NYFED_SOFR_AVG_URL: {"refRates": [{"average30day": 4.35, "average90day": 4.42}]},
        }

        monkeypatch.setattr(
            rates.requests, "get", lambda url, timeout: _FakeResponse(payloads[url])
        )
        data = fetch_sofr_reference(force_refresh=True)
        assert data["current"] == "4.31"
        assert data["avg_30"] == "4.35"
        assert data["avg_90"] == "4.42"
        assert "live" in data["source"].lower()
        assert data["as_of"] == "2026-07-02"
        self._clear_cache()

    def test_result_is_cached_until_forced(self, monkeypatch):
        self._clear_cache()
        calls = {"n": 0}

        def counting_get(url, timeout):
            calls["n"] += 1
            raise requests.ConnectionError("offline")

        monkeypatch.setattr(rates.requests, "get", counting_get)
        fetch_sofr_reference(force_refresh=True)
        first_calls = calls["n"]
        fetch_sofr_reference()  # served from cache, no new network attempts
        assert calls["n"] == first_calls
        self._clear_cache()

    @pytest.mark.slow
    def test_live_nyfed_endpoint_shape(self):
        """Real network: NY Fed payload parses; skip cleanly when offline."""
        self._clear_cache()
        try:
            data = rates._fetch_sofr_live(timeout=10)
        except requests.RequestException:
            pytest.skip("NY Fed unreachable")
        assert Decimal(data["current"]) > 0
        assert Decimal(data["avg_30"]) > 0
        assert Decimal(data["avg_90"]) > 0
        self._clear_cache()
