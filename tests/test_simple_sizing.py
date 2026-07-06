"""Tests for generic (non-futures) stop loss calculator."""

from decimal import Decimal

import pytest

from stoploss.simple_sizing import calculate_stop_loss


class TestSimpleSizingBasic:
    """Test basic stop loss calculation without futures contracts."""

    def test_short_entry_22_8524_equity_100_leverage_10_risk_11pct(self):
        """Your exact scenario: short $22.8524, $100 equity, 10x, 11% risk."""
        result = calculate_stop_loss(
            entry_price=22.8524,
            side="short",
            account_equity=100,
            leverage=10,
            acceptable_risk_pct=11,
        )

        assert result.entry_price == Decimal("22.8524")
        assert result.side == "short"
        assert result.leverage == Decimal("10")
        assert result.account_equity == Decimal("100")
        assert result.notional_exposure == Decimal("1000")
        assert result.acceptable_risk_pct == Decimal("11")
        assert result.allowed_adverse_move_pct == Decimal("1.1")
        assert result.max_loss_dollars == Decimal("11")
        # Stop should be entry + (entry * 0.011)
        assert result.stop_price == pytest.approx(Decimal("23.1037764"), rel=1e-5)

    def test_long_entry_100_equity_1000_leverage_5_risk_5pct(self):
        """Long scenario: entry $100, $1k equity, 5x leverage, 5% risk."""
        result = calculate_stop_loss(
            entry_price=100,
            side="long",
            account_equity=1000,
            leverage=5,
            acceptable_risk_pct=5,
        )

        assert result.entry_price == Decimal("100")
        assert result.side == "long"
        assert result.allowed_adverse_move_pct == Decimal("1")
        assert result.max_loss_dollars == Decimal("50")
        # Stop should be entry - (entry * 0.01)
        assert result.stop_price == Decimal("99")

    def test_leverage_squeeze_higher_leverage_tighter_stop(self):
        """Higher leverage = tighter stop (smaller adverse move %)."""
        result_10x = calculate_stop_loss(100, "short", 100, 10, 10)
        result_100x = calculate_stop_loss(100, "short", 100, 100, 10)

        # 100x should have 1/10th the breathing room
        assert result_100x.allowed_adverse_move_pct == Decimal("0.1")
        assert result_10x.allowed_adverse_move_pct == Decimal("1")

        # Both should have same max loss (10% of $100)
        assert result_10x.max_loss_dollars == result_100x.max_loss_dollars

        # But stops are very different
        assert result_100x.stop_price < result_10x.stop_price

    def test_short_vs_long_stop_placement(self):
        """SHORT stop is above entry, LONG stop is below entry."""
        result_short = calculate_stop_loss(100, "short", 1000, 2, 10)
        result_long = calculate_stop_loss(100, "long", 1000, 2, 10)

        assert result_short.stop_price > result_short.entry_price
        assert result_long.stop_price < result_long.entry_price

    def test_zero_risk_returns_stop_at_entry(self):
        """0% risk means stop = entry (no breathing room)."""
        result = calculate_stop_loss(50, "short", 1000, 1, 0)
        assert result.stop_price == result.entry_price
        assert result.max_loss_dollars == Decimal("0")

    def test_quantity_calculation(self):
        """Quantity = notional / entry price."""
        result = calculate_stop_loss(
            entry_price=10,
            side="long",
            account_equity=1000,
            leverage=20,
            acceptable_risk_pct=5,
        )
        # notional = 1000 * 20 = 20000
        # qty = 20000 / 10 = 2000
        assert result.quantity == Decimal("2000")

    def test_decimal_precision_maintained(self):
        """All calculations use Decimal for precision."""
        result = calculate_stop_loss(
            entry_price=22.8524,
            side="short",
            account_equity=100,
            leverage=10,
            acceptable_risk_pct=11,
        )
        assert isinstance(result.entry_price, Decimal)
        assert isinstance(result.stop_price, Decimal)
        assert isinstance(result.max_loss_dollars, Decimal)


class TestSimpleSizingEdgeCases:
    """Test edge cases and extreme scenarios."""

    def test_extreme_leverage_200x(self):
        """At 200x, allowed move is very small."""
        result = calculate_stop_loss(100, "short", 100, 200, 11)
        # 11% / 200 = 0.055%
        assert result.allowed_adverse_move_pct == Decimal("0.055")
        assert result.max_loss_dollars == Decimal("11")

    def test_micro_price_movement(self):
        """Handle very small price like $0.0001."""
        result = calculate_stop_loss(0.0001, "long", 1, 1, 10)
        assert result.entry_price == Decimal("0.0001")
        assert result.notional_exposure == Decimal("1")

    def test_large_equity_amount(self):
        """Handle large account equity ($10M+)."""
        result = calculate_stop_loss(
            entry_price=5000,
            side="long",
            account_equity=10_000_000,
            leverage=10,
            acceptable_risk_pct=2,
        )
        assert result.account_equity == Decimal("10000000")
        assert result.notional_exposure == Decimal("100000000")
        assert result.max_loss_dollars == Decimal("200000")

    def test_invalid_side_raises_error(self):
        """Invalid side parameter raises ValueError."""
        with pytest.raises(ValueError, match="side must be 'long' or 'short'"):
            calculate_stop_loss(100, "invalid", 1000, 10, 10)

    def test_string_inputs_coerced_to_decimal(self):
        """String inputs are properly converted to Decimal."""
        result = calculate_stop_loss(
            entry_price="22.8524",
            side="short",
            account_equity="100",
            leverage="10",
            acceptable_risk_pct="11",
        )
        assert isinstance(result.entry_price, Decimal)
        assert result.entry_price == Decimal("22.8524")


class TestSimpleSizingFormula:
    """Verify the mathematical formula."""

    def test_short_formula_entry_times_1_plus_move_factor(self):
        """SHORT: Stop = Entry * (1 + move_factor)."""
        # Entry $100, equity $1000, leverage 20, risk 5%
        # allowed_move = 5% / 20 = 0.25%
        # Stop = 100 * (1 + 0.0025) = 100.25
        result = calculate_stop_loss(100, "short", 1000, 20, 5)

        assert result.allowed_adverse_move_pct == Decimal("0.25")
        # 0.25% as factor = 0.0025
        expected_stop = Decimal("100") * (Decimal("1") + Decimal("0.0025"))
        assert result.stop_price == expected_stop

    def test_long_formula_entry_times_1_minus_move_factor(self):
        """LONG: Stop = Entry * (1 - move_factor)."""
        # Entry $100, equity $1000, leverage 20, risk 5%
        # allowed_move = 5% / 20 = 0.25%
        # Stop = 100 * (1 - 0.0025) = 99.75
        result = calculate_stop_loss(100, "long", 1000, 20, 5)

        assert result.allowed_adverse_move_pct == Decimal("0.25")
        # 0.25% as factor = 0.0025
        expected_stop = Decimal("100") * (Decimal("1") - Decimal("0.0025"))
        assert result.stop_price == expected_stop

    def test_allowed_move_is_risk_divided_by_leverage(self):
        """Allowed move % = acceptable risk % / leverage."""
        result = calculate_stop_loss(100, "short", 1000, 50, 10)
        # 10% / 50 = 0.2%
        assert result.allowed_adverse_move_pct == Decimal("0.2")
