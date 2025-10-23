"""Unit tests for contracts module (ES, NQ, CL, GC specifications)."""

from decimal import Decimal

import pytest

from src.stoploss.contracts import get_contract


class TestContractSpecs:
    """Test CME futures contract specifications."""

    def test_es_specs(self):
        """Test ES (E-mini S&P 500) contract specifications."""
        contract = get_contract("ES")
        assert contract.symbol == "ES"
        assert contract.point_value == Decimal("50")  # $50 per point
        assert contract.min_tick == Decimal("0.25")  # 0.25 point tick
        assert contract.tick_value == Decimal("12.50")  # 0.25 * $50

    def test_nq_specs(self):
        """Test NQ (E-mini Nasdaq-100) contract specifications."""
        contract = get_contract("NQ")
        assert contract.symbol == "NQ"
        assert contract.point_value == Decimal("20")  # $20 per point
        assert contract.min_tick == Decimal("0.25")
        assert contract.tick_value == Decimal("5")  # 0.25 * $20

    def test_cl_specs(self):
        """Test CL (Crude Oil) contract specifications."""
        contract = get_contract("CL")
        assert contract.symbol == "CL"
        assert contract.point_value == Decimal("1000")  # $1000 per point
        assert contract.min_tick == Decimal("0.01")
        assert contract.tick_value == Decimal("10")  # 0.01 * $1000

    def test_gc_specs(self):
        """Test GC (Gold Futures) contract specifications."""
        contract = get_contract("GC")
        assert contract.symbol == "GC"
        assert contract.point_value == Decimal("100")  # $100 per point
        assert contract.min_tick == Decimal("0.10")
        assert contract.tick_value == Decimal("10")  # 0.10 * $100

    def test_invalid_symbol(self):
        """Test that invalid symbols raise ValueError."""
        with pytest.raises(ValueError, match="Unknown symbol"):
            get_contract("INVALID")


class TestTickRounding:
    """Test tick rounding for all contract types."""

    def test_es_tick_rounding_down(self):
        """ES should round to nearest 0.25."""
        contract = get_contract("ES")
        # 5050.10 should round to 5050.00
        rounded = contract.round_to_tick(Decimal("5050.10"))
        assert rounded == Decimal("5050.00")

    def test_es_tick_rounding_up(self):
        """ES should round to nearest 0.25."""
        contract = get_contract("ES")
        # 5050.13 should round to 5050.25
        rounded = contract.round_to_tick(Decimal("5050.13"))
        assert rounded == Decimal("5050.25")

    def test_es_tick_rounding_exact(self):
        """ES tick that is exact should remain unchanged."""
        contract = get_contract("ES")
        rounded = contract.round_to_tick(Decimal("5050.25"))
        assert rounded == Decimal("5050.25")

    def test_nq_tick_rounding(self):
        """NQ should round to nearest 0.25."""
        contract = get_contract("NQ")
        rounded = contract.round_to_tick(Decimal("18000.37"))
        assert rounded == Decimal("18000.25")

    def test_cl_tick_rounding(self):
        """CL should round to nearest 0.01."""
        contract = get_contract("CL")
        # 95.127 should round to 95.13
        rounded = contract.round_to_tick(Decimal("95.127"))
        assert rounded == Decimal("95.13")

    def test_gc_tick_rounding(self):
        """GC should round to nearest 0.10."""
        contract = get_contract("GC")
        # 2000.37 should round to 2000.40
        rounded = contract.round_to_tick(Decimal("2000.37"))
        assert rounded == Decimal("2000.40")

    def test_tick_rounding_preserves_precision(self):
        """Rounding should not cause loss of precision."""
        es = get_contract("ES")
        price = Decimal("5050.1234567890")
        rounded = es.round_to_tick(price)
        # Should be a valid ES tick
        assert (rounded * Decimal("4")) % 1 == 0  # All ticks are multiples of 0.25


class TestPointValueCalculation:
    """Test P&L calculations based on point values."""

    def test_es_pnl_calculation(self):
        """ES: 1 point = $50."""
        contract = get_contract("ES")
        qty = 2
        price_change = Decimal("5")  # 5 points
        # 2 * 5 * $50 = $500
        assert contract.pnl_for_move(qty, price_change) == Decimal("500")

    def test_nq_pnl_calculation(self):
        """NQ: 1 point = $20."""
        contract = get_contract("NQ")
        qty = 3
        price_change = Decimal("10")
        # 3 * 10 * $20 = $600
        assert contract.pnl_for_move(qty, price_change) == Decimal("600")

    def test_cl_pnl_calculation(self):
        """CL: 1 point = $1000."""
        contract = get_contract("CL")
        qty = 1
        price_change = Decimal("0.5")  # 0.5 point
        # $500
        assert contract.pnl_for_move(qty, price_change) == Decimal("500")

    def test_gc_pnl_calculation(self):
        """GC: 1 point = $100."""
        contract = get_contract("GC")
        qty = 5
        price_change = Decimal("20")
        # $10,000
        assert contract.pnl_for_move(qty, price_change) == Decimal("10000")

    def test_negative_pnl(self):
        """Negative price changes should produce negative P&L."""
        contract = get_contract("ES")
        qty = 1
        price_change = Decimal("-5")
        # -$250
        assert contract.pnl_for_move(qty, price_change) == Decimal("-250")


class TestContractValidation:
    """Test contract validation and bounds checking."""

    def test_all_symbols_available(self):
        """All four main futures contracts should be available."""
        symbols = ["ES", "NQ", "CL", "GC"]
        for symbol in symbols:
            contract = get_contract(symbol)
            assert contract is not None
            assert contract.symbol == symbol

    def test_contract_immutability(self):
        """Retrieved contracts should be consistent."""
        contract1 = get_contract("ES")
        contract2 = get_contract("ES")
        assert contract1.symbol == contract2.symbol
        assert contract1.point_value == contract2.point_value
        assert contract1.min_tick == contract2.min_tick
