"""CLI tests (Typer) — golden values match tests/test_sizing.py hand math."""

from typer.testing import CliRunner

from src.stoploss.cli import app

runner = CliRunner()


class TestSizeCommand:
    def test_size_percent_stop_golden(self):
        """ES long golden: qty 1 (buying-power capped), stop 5029.75."""
        result = runner.invoke(
            app,
            [
                "size",
                "--symbol",
                "ES",
                "--side",
                "long",
                "--entry",
                "5050",
                "--equity",
                "25000",
                "--leverage",
                "12",
                "--pct-stop",
                "0.004",
                "--risk",
                "2500",
                "--fees-open",
                "2",
                "--fees-close",
                "2",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "1 contracts" in result.output
        assert "5029.75" in result.output
        assert "capped" in result.output.lower()

    def test_size_percent_stop_requires_risk(self):
        """Percent-stop sizing without --risk must exit 1 and explain."""
        result = runner.invoke(
            app,
            [
                "size",
                "--symbol",
                "ES",
                "--side",
                "long",
                "--entry",
                "5050",
                "--equity",
                "25000",
                "--leverage",
                "12",
                "--pct-stop",
                "0.004",
            ],
        )
        assert result.exit_code == 1
        assert "--risk" in result.output

    def test_size_atr_golden(self):
        """ATR path golden: rounded stop 5030.00 -> qty 2 at $2010 risk."""
        result = runner.invoke(
            app,
            [
                "size",
                "--symbol",
                "ES",
                "--side",
                "long",
                "--entry",
                "5050.10",
                "--equity",
                "25000",
                "--atr",
                "10.07",
                "--k-atr",
                "2",
                "--risk",
                "2010",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "2 contracts" in result.output
        assert "5030.00" in result.output

    def test_size_requires_a_method(self):
        result = runner.invoke(
            app,
            [
                "size",
                "--symbol",
                "ES",
                "--side",
                "long",
                "--entry",
                "5050",
                "--equity",
                "25000",
            ],
        )
        assert result.exit_code == 1


class TestPnlCommand:
    def test_pnl_smoke_1256(self):
        """P&L smoke: ES long 1 contract, entry 5050 -> target 5100 / stop 5029.75.

        gross_win = 1 * 50 * 50 = 2500; tax = 2496 * (0.6*0.15 + 0.4*0.24) = 464.26
        (blended 0.186 on gross AFTER nothing — tax applies to gross_win 2500: 465.00)
        We assert only structural output here; exact tax goldens live in test_taxes.py.
        """
        result = runner.invoke(
            app,
            [
                "pnl",
                "--symbol",
                "ES",
                "--side",
                "long",
                "--entry",
                "5050",
                "--target",
                "5100",
                "--stop",
                "5029.75",
                "--qty",
                "1",
                "--fees-open",
                "2",
                "--fees-close",
                "2",
                "--tax-mode",
                "1256",
                "--st-rate",
                "0.24",
                "--lt-rate",
                "0.15",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "$2,500.00" in result.output  # gross win
        assert "Net P&L" in result.output
