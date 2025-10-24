"""Tests for REST API endpoints."""

from decimal import Decimal

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self):
        """Health check should return 200 with status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["version"] == "0.1.0"


class TestSizingEndpoint:
    """Test position sizing endpoint."""

    def test_size_es_basic(self):
        """Test ES sizing calculation via API."""
        payload = {
            "symbol": "ES",
            "side": "long",
            "entry": "5050.00",
            "account_equity": "20000.00",
            "leverage": "3.0",
            "pct_stop": "0.004",
        }

        response = client.post("/size", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["symbol"] == "ES"
        assert data["data"]["qty"] > 0
        stop_price = Decimal(str(data["data"]["stop_price"]))
        assert stop_price < Decimal("5050")

    def test_size_nq_basic(self):
        """Test NQ sizing calculation via API."""
        payload = {
            "symbol": "NQ",
            "side": "long",
            "entry": "18000.00",
            "account_equity": "50000.00",
            "leverage": "2.0",
            "pct_stop": "0.005",
        }

        response = client.post("/size", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["symbol"] == "NQ"

    def test_size_invalid_symbol(self):
        """Test sizing with invalid symbol returns error."""
        payload = {
            "symbol": "INVALID",
            "side": "long",
            "entry": "5050.00",
            "account_equity": "20000.00",
            "leverage": "3.0",
            "pct_stop": "0.004",
        }

        response = client.post("/size", json=payload)
        assert response.status_code == 400

    def test_size_invalid_side(self):
        """Test sizing with invalid side returns error."""
        payload = {
            "symbol": "ES",
            "side": "invalid",
            "entry": "5050.00",
            "account_equity": "20000.00",
            "leverage": "3.0",
            "pct_stop": "0.004",
        }

        response = client.post("/size", json=payload)
        assert response.status_code == 400

    def test_size_short(self):
        """Test short sizing calculation."""
        payload = {
            "symbol": "ES",
            "side": "short",
            "entry": "5050.00",
            "account_equity": "20000.00",
            "leverage": "3.0",
            "pct_stop": "0.004",
        }

        response = client.post("/size", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        stop_price = Decimal(str(data["data"]["stop_price"]))
        assert stop_price > Decimal("5050")  # Stop above entry for short


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
