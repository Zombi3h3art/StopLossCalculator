"""Headless dashboard tests via Streamlit AppTest.

Golden values match tests/test_sizing.py / tests/test_cashflow.py hand math:
ES long, entry 5050, equity $25k, leverage 12, risk 1% -> risk budget $250:
    pct_stop = 1%/12 -> stop 5045.75 (tick), risk/contract $212.50
    qty = min(floor(250/212.50), floor(300000/252500)) = 1 -> Max Loss $212.50
P&L at target 5100 (defaults: no fees/energy, 1256 @ 24/15):
    gross_win 2500.00, tax 465.00 -> net win 2035.00; net loss -212.50
"""

from streamlit.testing.v1 import AppTest

APP = "simple_dashboard.py"


def _all_markdown(at: AppTest) -> str:
    return "\n".join(str(m.value) for m in at.markdown)


class TestDashboardBoot:
    def test_boots_without_exception_and_shows_empty_state(self):
        """With no entry price yet, the app must show the empty state, not calculate."""
        at = AppTest.from_file(APP)
        at.run()
        assert not at.exception
        assert at.number_input(key="entry").value is None
        assert "Enter Trade Details" in _all_markdown(at)


class TestFuturesGoldenFlow:
    def _golden(self) -> AppTest:
        at = AppTest.from_file(APP)
        at.run()
        at.radio(key="mode").set_value("Futures (Precision)")
        at.run()
        at.number_input(key="entry").set_value(5050.0)
        at.number_input(key="equity").set_value(25000.0)
        at.number_input(key="leverage").set_value(12)
        # Explicit: switching modes preserves prior widget state, so pin risk to 1%
        at.number_input(key="risk_pct").set_value(1.0)
        at.run()
        return at

    def test_golden_sizing_numbers_rendered(self):
        at = self._golden()
        assert not at.exception
        md = _all_markdown(at)
        assert "5045.7500" in md  # tick-rounded stop price
        assert "$212.50" in md  # honest max loss = qty x risk/contract

    def test_pnl_scenario_full_cost_stack(self):
        """Setting a target in the P&L panel renders net win/loss with taxes."""
        at = self._golden()
        at.number_input(key="target").set_value(5100.0)
        at.run()
        assert not at.exception
        values = [str(m.value) for m in at.metric]
        assert any("2,500.00" in v for v in values)  # gross win
        assert any("2,035.00" in v for v in values)  # net win after 1256 tax
        assert any("212.50" in v for v in values)  # net loss (no extra costs)

    def test_pnl_respects_short_term_tax_mode(self):
        """Short-term ordinary at 37% changes the net win."""
        at = self._golden()
        at.number_input(key="target").set_value(5100.0)
        at.run()
        at.selectbox(key="tax_mode").set_value("Short-term ordinary")
        at.number_input(key="st_rate").set_value(37.0)
        at.run()
        assert not at.exception
        # tax = 2500 * 0.37 = 925 -> net win 1575.00
        values = [str(m.value) for m in at.metric]
        assert any("1,575.00" in v for v in values)


class TestSimpleModeUnchanged:
    def test_simple_mode_calculates(self):
        at = AppTest.from_file(APP)
        at.run()
        at.number_input(key="entry").set_value(100.0)
        at.run()
        assert not at.exception
        md = _all_markdown(at)
        assert "TRADE SUMMARY" in md.upper() or "Trade Summary" in md
