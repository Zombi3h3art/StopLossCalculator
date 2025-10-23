"""Unit tests for sizing module (position sizing and stop calculations)."""

from decimal import Decimal

import pytest

from src.stoploss.contracts import get_contract
from src.stoploss.sizing import size_by_percent_stop


class TestPercentStopSizing:
    """Test percent-stop (risk-first) sizing calculations."""

    def test_es_percent_stop_basic(self):
        """ES long trade with 0.4% stop."""
        result = size_by_percent_stop(
            symbol="ES",
            side="long",
            entry=Decimal("5050"),
            account_equity=Decimal("20000"),
            leverage=Decimal("3"),
            pct_stop=Decimal("0.004"),
        )

        # Verify result has expected fields
        assert result.qty > 0
        assert result.stop_price < Decimal("5050")  # Stop should be below entry for long
        assert result.risk_per_unit == Decimal("5050") * Decimal("0.004")

    def test_es_short_percent_stop(self):
        """ES short trade with 0.4% stop."""
        result = size_by_percent_stop(
            symbol="ES",
            side="short",
            entry=Decimal("5050"),
            account_equity=Decimal("20000"),
            leverage=Decimal("3"),
            pct_stop=Decimal("0.004"),
        )

        # Verify result has expected fields
        assert result.qty > 0
        assert result.stop_price > Decimal("5050")  # Stop should be above entry for short

    def test_nq_percent_stop(self):
        """NQ sizing with percent stop."""
        result = size_by_percent_stop(
            symbol="NQ",
            side="long",
            entry=Decimal("18000"),
            account_equity=Decimal("50000"),
            leverage=Decimal("2"),
            pct_stop=Decimal("0.005"),
        )

        assert result.qty > 0
        assert result.stop_price < Decimal("18000")

    def test_cl_percent_stop(self):
        """CL sizing with percent stop."""
        result = size_by_percent_stop(
            symbol="CL",
            side="long",
            entry=Decimal("95"),
            account_equity=Decimal("10000"),
            leverage=Decimal("1"),
            pct_stop=Decimal("0.02"),
        )

        assert result.qty > 0
        assert result.stop_price < Decimal("95")

    def test_gc_percent_stop(self):
        """GC sizing with percent stop."""
        result = size_by_percent_stop(
            symbol="GC",
            side="long",
            entry=Decimal("2000"),
            account_equity=Decimal("25000"),
            leverage=Decimal("2"),
            pct_stop=Decimal("0.03"),
        )

        assert result.qty > 0
        assert result.stop_price < Decimal("2000")

    def test_stop_is_rounded_to_tick(self):
        """Stop price should be rounded to contract tick."""
        result = size_by_percent_stop(
            symbol="ES",
            side="long",
            entry=Decimal("5050.123"),
            account_equity=Decimal("20000"),
            leverage=Decimal("3"),
            pct_stop=Decimal("0.004"),
        )

        # ES tick is 0.25
        contract = get_contract("ES")
        rounded = contract.round_to_tick(result.stop_price)
        assert result.stop_price == rounded

    def test_invalid_symbol_raises_error(self):
        """Invalid symbol should raise ValueError."""
        with pytest.raises(ValueError):
            size_by_percent_stop(
                symbol="INVALID",
                side="long",
                entry=Decimal("5050"),
                account_equity=Decimal("20000"),
                leverage=Decimal("3"),
                pct_stop=Decimal("0.004"),
            )

    def test_invalid_side_raises_error(self):
        """Invalid side should raise ValueError."""
        with pytest.raises(ValueError):
            size_by_percent_stop(
                symbol="ES",
                side="invalid",  # type: ignore
                entry=Decimal("5050"),
                account_equity=Decimal("20000"),
                leverage=Decimal("3"),
                pct_stop=Decimal("0.004"),
            )

    def test_zero_pct_stop_raises_error(self):
        """Zero percent stop should raise ValueError."""
        with pytest.raises(ValueError):
            size_by_percent_stop(
                symbol="ES",
                side="long",
                entry=Decimal("5050"),
                account_equity=Decimal("20000"),
                leverage=Decimal("3"),
                pct_stop=Decimal("0"),
            )

    def test_negative_equity_raises_error(self):
        """Negative equity should raise ValueError."""
        with pytest.raises(ValueError):
            size_by_percent_stop(
                symbol="ES",
                side="long",
                entry=Decimal("5050"),
                account_equity=Decimal("-20000"),
                leverage=Decimal("3"),
                pct_stop=Decimal("0.004"),
            )

    def test_qty_scales_with_equity(self):
        """Higher equity should result in larger qty."""
        result_small = size_by_percent_stop(
            symbol="ES",
            side="long",
            entry=Decimal("5050"),
            account_equity=Decimal("10000"),
            leverage=Decimal("3"),
            pct_stop=Decimal("0.004"),
        )

        result_large = size_by_percent_stop(
            symbol="ES",
            side="long",
            entry=Decimal("5050"),
            account_equity=Decimal("20000"),
            leverage=Decimal("3"),
            pct_stop=Decimal("0.004"),
        )

        assert result_large.qty >= result_small.qty

    def test_qty_scales_with_leverage(self):
        """Higher leverage should result in larger qty."""
        result_low_lev = size_by_percent_stop(
            symbol="ES",
            side="long",
            entry=Decimal("5050"),
            account_equity=Decimal("20000"),
            leverage=Decimal("1"),
            pct_stop=Decimal("0.004"),
        )

        result_high_lev = size_by_percent_stop(
            symbol="ES",
            side="long",
            entry=Decimal("5050"),
            account_equity=Decimal("20000"),
            leverage=Decimal("3"),
            pct_stop=Decimal("0.004"),
        )

        assert result_high_lev.qty >= result_low_lev.qty

    def test_result_has_all_expected_fields(self):
        """Result should have all required fields."""
        result = size_by_percent_stop(
            symbol="ES",
            side="long",
            entry=Decimal("5050"),
            account_equity=Decimal("20000"),
            leverage=Decimal("3"),
            pct_stop=Decimal("0.004"),
        )

        assert hasattr(result, "symbol")
        assert hasattr(result, "side")
        assert hasattr(result, "qty")
        assert hasattr(result, "entry")
        assert hasattr(result, "stop_price")
        assert hasattr(result, "risk_per_unit")
        assert hasattr(result, "gross_exposure")
