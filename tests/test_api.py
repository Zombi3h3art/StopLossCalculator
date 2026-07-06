"""Tests for REST API endpoints."""

from decimal import Decimal

from fastapi.testclient import TestClient

from api.app import app
from stoploss import __version__

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self):
        """Health check should return 200 with status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["version"] == __version__


class TestSizingEndpoint:
    """Test position sizing endpoint (risk-first semantics)."""

    def test_size_es_golden(self):
        """ES long golden case (matches tests/test_sizing.py hand math).

        risk $2500 - $4 fees -> qty_risk 2; buying power 25000*12 caps at 1.
        """
        payload = {
            "symbol": "ES",
            "side": "long",
            "entry": "5050.00",
            "account_equity": "25000.00",
            "leverage": "12",
            "pct_stop": "0.004",
            "risk_cash": "2500.00",
            "fees_open": "2.00",
            "fees_close": "2.00",
        }

        response = client.post("/size", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["symbol"] == "ES"
        assert data["data"]["qty"] == 1
        assert Decimal(str(data["data"]["stop_price"])) == Decimal("5029.75")
        assert Decimal(str(data["data"]["risk_dollars_per_contract"])) == Decimal("1012.50")
        assert data["data"]["buying_power_qty_cap"] == 1
        assert data["data"]["capped_by_buying_power"] is True

    def test_size_nq_short_golden(self):
        """NQ short golden case: risk-bound qty 1, tick-exact stop above entry."""
        payload = {
            "symbol": "NQ",
            "side": "short",
            "entry": "18500.00",
            "account_equity": "50000.00",
            "leverage": "8",
            "pct_stop": "0.003",
            "risk_cash": "1500.00",
        }

        response = client.post("/size", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["symbol"] == "NQ"
        assert data["data"]["qty"] == 1
        assert Decimal(str(data["data"]["stop_price"])) == Decimal("18555.50")
        assert data["data"]["capped_by_buying_power"] is False

    def test_size_missing_risk_cash_rejected(self):
        """Percent-stop sizing without a risk budget must be a 400, not a guess."""
        payload = {
            "symbol": "ES",
            "side": "long",
            "entry": "5050.00",
            "account_equity": "25000.00",
            "leverage": "12",
            "pct_stop": "0.004",
        }

        response = client.post("/size", json=payload)
        assert response.status_code == 400
        assert "risk_cash" in response.json()["detail"]

    def test_size_buying_power_too_small(self):
        """Low declared leverage cannot control one ES contract -> 400 with guidance."""
        payload = {
            "symbol": "ES",
            "side": "long",
            "entry": "5050.00",
            "account_equity": "25000.00",
            "leverage": "2.5",
            "pct_stop": "0.004",
            "risk_cash": "2500.00",
        }

        response = client.post("/size", json=payload)
        assert response.status_code == 400
        assert "uying power" in response.json()["detail"]

    def test_size_invalid_symbol(self):
        """Test sizing with invalid symbol returns error."""
        payload = {
            "symbol": "INVALID",
            "side": "long",
            "entry": "5050.00",
            "account_equity": "25000.00",
            "leverage": "12",
            "pct_stop": "0.004",
            "risk_cash": "2500.00",
        }

        response = client.post("/size", json=payload)
        assert response.status_code == 400

    def test_size_invalid_side(self):
        """Test sizing with invalid side returns error."""
        payload = {
            "symbol": "ES",
            "side": "invalid",
            "entry": "5050.00",
            "account_equity": "25000.00",
            "leverage": "12",
            "pct_stop": "0.004",
            "risk_cash": "2500.00",
        }

        response = client.post("/size", json=payload)
        assert response.status_code == 400


class TestPnLEndpoint:
    """Test P&L calculation endpoint."""

    def test_pnl_es_basic(self):
        """Test ES P&L calculation via API."""
        payload = {
            "symbol": "ES",
            "side": "long",
            "entry": "5050.00",
            "target": "5100.00",
            "stop": "5030.00",
            "qty": 2,
            "fees_open": "2.00",
            "fees_close": "2.00",
            "tax_mode": "short_term",
            "st_rate": "0.24",
        }

        response = client.post("/pnl", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["symbol"] == "ES"
        gross_win = Decimal(str(data["data"]["gross_win"]))
        gross_loss = Decimal(str(data["data"]["gross_loss"]))
        assert gross_win > 0
        assert gross_loss > 0

    def test_pnl_with_1256_tax(self):
        """Test P&L with §1256 tax mode."""
        payload = {
            "symbol": "ES",
            "side": "long",
            "entry": "5050.00",
            "target": "5100.00",
            "stop": "5030.00",
            "qty": 2,
            "fees_open": "2.00",
            "fees_close": "2.00",
            "tax_mode": "1256",
            "st_rate": "0.24",
            "lt_rate": "0.15",
        }

        response = client.post("/pnl", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_pnl_with_margin(self):
        """Test P&L with margin loan."""
        payload = {
            "symbol": "ES",
            "side": "long",
            "entry": "5050.00",
            "target": "5100.00",
            "stop": "5030.00",
            "qty": 2,
            "fees_open": "2.00",
            "fees_close": "2.00",
            "margin_loans": [{"amount": "5000.00", "apr": "0.065", "days_held": 5}],
            "tax_mode": "short_term",
            "st_rate": "0.24",
        }

        response = client.post("/pnl", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_pnl_invalid_symbol(self):
        """Test P&L with invalid symbol returns error."""
        payload = {
            "symbol": "INVALID",
            "side": "long",
            "entry": "5050.00",
            "target": "5100.00",
            "stop": "5030.00",
            "qty": 2,
            "fees_open": "2.00",
            "fees_close": "2.00",
        }

        response = client.post("/pnl", json=payload)
        assert response.status_code == 400


class TestReferenceEndpoints:
    """Test reference data endpoints."""

    def test_electricity_reference(self):
        """Test electricity cost reference endpoint."""
        response = client.get("/refs/electricity")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "cost_per_kwh" in data["data"]
        assert "source" in data["data"]

    def test_sofr_reference(self):
        """Test SOFR reference endpoint."""
        response = client.get("/refs/sofr")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "current" in data["data"]
        assert "source" in data["data"]
