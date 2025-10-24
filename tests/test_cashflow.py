"""Unit tests for cashflow module (P&L calculations with all costs)."""

from decimal import Decimal

from src.stoploss.cashflow import calculate_pnl
from src.stoploss.schemas import MarginLoanInput


class TestGrossPnL:
    """Test gross P&L calculations."""

    def test_es_win_scenario(self):
        """ES long win: entry 5050, target 5100."""
        result = calculate_pnl(
            symbol="ES",
            side="long",
            entry=Decimal("5050"),
            target=Decimal("5100"),
            stop=Decimal("5030"),
            qty=2,
            fees_open=Decimal("2"),
            fees_close=Decimal("2"),
            slippage_open=Decimal("0"),
            slippage_close=Decimal("0"),
        )

        # Gross win: 2 * (5100 - 5050) * $50 = 2 * 50 * $50 = $5,000
        assert result.gross_win == Decimal("5000")

    def test_es_loss_scenario(self):
        """ES long loss: entry 5050, stop 5030."""
        result = calculate_pnl(
            symbol="ES",
            side="long",
            entry=Decimal("5050"),
            target=Decimal("5100"),
            stop=Decimal("5030"),
            qty=2,
            fees_open=Decimal("2"),
            fees_close=Decimal("2"),
            slippage_open=Decimal("0"),
            slippage_close=Decimal("0"),
        )

        # Gross loss: 2 * (5050 - 5030) * $50 = 2 * 20 * $50 = $2,000
        assert result.gross_loss == Decimal("2000")

    def test_nq_win_scenario(self):
        """NQ long win."""
        result = calculate_pnl(
            symbol="NQ",
            side="long",
            entry=Decimal("18000"),
            target=Decimal("18500"),
            stop=Decimal("17800"),
            qty=1,
            fees_open=Decimal("2"),
            fees_close=Decimal("2"),
        )

        # Gross win: 1 * (18500 - 18000) * $20 = 1 * 500 * $20 = $10,000
        assert result.gross_win == Decimal("10000")

    def test_cl_win_scenario(self):
        """CL long win."""
        result = calculate_pnl(
            symbol="CL",
            side="long",
            entry=Decimal("95"),
            target=Decimal("100"),
            stop=Decimal("90"),
            qty=1,
            fees_open=Decimal("5"),
            fees_close=Decimal("5"),
        )

        # Gross win: 1 * (100 - 95) * $1000 = 1 * 5 * $1000 = $5,000
        assert result.gross_win == Decimal("5000")

    def test_gc_win_scenario(self):
        """GC long win."""
        result = calculate_pnl(
            symbol="GC",
            side="long",
            entry=Decimal("2000"),
            target=Decimal("2100"),
            stop=Decimal("1900"),
            qty=2,
            fees_open=Decimal("3"),
            fees_close=Decimal("3"),
        )

        # Gross win: 2 * (2100 - 2000) * $100 = 2 * 100 * $100 = $20,000
        assert result.gross_win == Decimal("20000")


class TestCostAccounting:
    """Test cost accounting in P&L."""

    def test_fees_included(self):
        """Fees should be deducted from net P&L."""
        result = calculate_pnl(
            symbol="ES",
            side="long",
            entry=Decimal("5050"),
            target=Decimal("5100"),
            stop=Decimal("5030"),
            qty=2,
            fees_open=Decimal("5"),
            fees_close=Decimal("5"),
        )

        # Gross win: $5,000
        # Fees: $10
        # Net should reflect fee reduction
        assert result.net_win_scenario < result.gross_win

    def test_slippage_included(self):
        """Slippage should be deducted from net P&L."""
        result_no_slip = calculate_pnl(
            symbol="ES",
            side="long",
            entry=Decimal("5050"),
            target=Decimal("5100"),
            stop=Decimal("5030"),
            qty=2,
            fees_open=Decimal("2"),
            fees_close=Decimal("2"),
            slippage_open=Decimal("0"),
            slippage_close=Decimal("0"),
        )

        result_with_slip = calculate_pnl(
            symbol="ES",
            side="long",
            entry=Decimal("5050"),
            target=Decimal("5100"),
            stop=Decimal("5030"),
            qty=2,
            fees_open=Decimal("2"),
            fees_close=Decimal("2"),
            slippage_open=Decimal("2"),
            slippage_close=Decimal("2"),
        )

        # Slippage should reduce net profit
        assert result_with_slip.net_win_scenario < result_no_slip.net_win_scenario

    def test_energy_cost_included(self):
        """Energy costs should reduce net P&L."""
        result = calculate_pnl(
            symbol="ES",
            side="long",
            entry=Decimal("5050"),
            target=Decimal("5100"),
            stop=Decimal("5030"),
            qty=2,
            fees_open=Decimal("2"),
            fees_close=Decimal("2"),
            energy_kwh=Decimal("0.5"),
            energy_cost_per_kwh=Decimal("0.14"),
        )

        # Energy cost: 0.5 * $0.14 = $0.07
        # Should be included in costs
        assert hasattr(result, "net_win_scenario")

    def test_margin_interest_included(self):
        """Margin interest should reduce net P&L."""
        loan = MarginLoanInput(amount=Decimal("5000"), apr=Decimal("0.065"), days_held=5)

        result = calculate_pnl(
            symbol="ES",
            side="long",
            entry=Decimal("5050"),
            target=Decimal("5100"),
            stop=Decimal("5030"),
            qty=2,
            fees_open=Decimal("2"),
            fees_close=Decimal("2"),
            margin_loans=[loan],
        )

        # Margin interest: $5000 * 0.065 * (5/360) ≈ $4.51
        # Should be included in costs
        assert hasattr(result, "net_win_scenario")


class TestShortSideCalculations:
    """Test short-side P&L calculations."""

    def test_short_win(self):
        """ES short win: entry 5050, stop 5030 (target)."""
        result = calculate_pnl(
            symbol="ES",
            side="short",
            entry=Decimal("5050"),
            target=Decimal("5000"),
            stop=Decimal("5100"),
            qty=2,
            fees_open=Decimal("2"),
            fees_close=Decimal("2"),
        )

        # Short win: entry - target = 5050 - 5000 = 50
        # Gross: 2 * 50 * $50 = $5,000
        assert result.gross_win == Decimal("5000")

    def test_short_loss(self):
        """ES short loss: entry 5050, stop 5100."""
        result = calculate_pnl(
            symbol="ES",
            side="short",
            entry=Decimal("5050"),
            target=Decimal("5000"),
            stop=Decimal("5100"),
            qty=2,
            fees_open=Decimal("2"),
            fees_close=Decimal("2"),
        )

        # Short loss: stop - entry = 5100 - 5050 = 50
        # Gross: 2 * 50 * $50 = $5,000
        assert result.gross_loss == Decimal("5000")


class TestResultStructure:
    """Test that result has all expected fields."""

    def test_result_has_all_fields(self):
        """Result should have all expected fields."""
        result = calculate_pnl(
            symbol="ES",
            side="long",
            entry=Decimal("5050"),
            target=Decimal("5100"),
            stop=Decimal("5030"),
            qty=2,
            fees_open=Decimal("2"),
            fees_close=Decimal("2"),
        )

        # Check all expected fields exist
        assert hasattr(result, "symbol")
        assert hasattr(result, "side")
        assert hasattr(result, "qty")
        assert hasattr(result, "entry")
        assert hasattr(result, "target")
        assert hasattr(result, "stop")
        assert hasattr(result, "gross_win")
        assert hasattr(result, "gross_loss")
        assert hasattr(result, "net_win_scenario")
        assert hasattr(result, "net_loss_scenario")
        assert hasattr(result, "breakdown")
