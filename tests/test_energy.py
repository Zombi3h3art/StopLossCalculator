"""Tests for energy cost estimation and the optional EIA live price fetch."""

from decimal import Decimal

import pytest
import requests

from stoploss import energy
from stoploss.energy import estimate_energy_cost, fetch_electricity_price_cents


class TestEstimateEnergyCost:
    def test_golden_default_price(self):
        """0.2 kW * 1 h * 14 c/kWh = 2.8 cents -> $0.03"""
        assert estimate_energy_cost(Decimal("0.2"), Decimal("1")) == Decimal("0.03")

    def test_explicit_price(self):
        """0.35 kW * 2 h * 20 c/kWh = 14 cents -> $0.14"""
        assert estimate_energy_cost(Decimal("0.35"), Decimal("2"), Decimal("20")) == Decimal("0.14")

    def test_invalid_inputs_raise(self):
        with pytest.raises(ValueError):
            estimate_energy_cost(Decimal("0"), Decimal("1"))


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class TestElectricityFetch:
    def _clear_cache(self):
        energy._price_cache = None
        energy._price_cache_at = 0.0

    def test_no_api_key_returns_default(self, monkeypatch):
        self._clear_cache()
        monkeypatch.delenv("EIA_API_KEY", raising=False)
        assert fetch_electricity_price_cents(force_refresh=True) == Decimal("14")
        self._clear_cache()

    def test_live_payload_is_parsed(self, monkeypatch):
        self._clear_cache()
        payload = {"response": {"data": [{"price": 16.42}]}}
        monkeypatch.setattr(
            energy.requests, "get", lambda url, params, timeout: _FakeResponse(payload)
        )
        got = fetch_electricity_price_cents(api_key="test-key", force_refresh=True)
        assert got == Decimal("16.42")
        self._clear_cache()

    def test_network_failure_falls_back(self, monkeypatch):
        self._clear_cache()

        def boom(*args, **kwargs):
            raise requests.ConnectionError("offline")

        monkeypatch.setattr(energy.requests, "get", boom)
        assert fetch_electricity_price_cents(api_key="test-key", force_refresh=True) == Decimal(
            "14"
        )
        self._clear_cache()
