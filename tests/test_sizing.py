"""Unit tests for sizing module (risk-first position sizing and stop calculations).

Golden values are hand-calculated in each docstring and follow the risk-first
semantics decided 2026-07-06:

    risk_budget (risk_cash, $) = what the trader is willing to lose
    qty_risk = floor((risk_cash - fees - slippage) / risk_dollars_per_contract)
    qty_cap  = floor(account_equity * leverage / (entry * point_value))
    qty      = min(qty_risk, qty_cap)   -- ValueError if either is 0
"""

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from stoploss.contracts import get_contract
from stoploss.sizing import size_by_atr_stop, size_by_percent_stop


class TestPercentStopGolden:
    """Golden-number tests for percent-stop, risk-first sizing."""

    def test_es_long_capped_by_buying_power(self):
        """ES long, entry=5050, equity=$25k, leverage=12, pct_stop=0.4%, risk=$2500, fees $2+$2.

        risk_per_unit          = 5050 * 0.004 = 20.20
        raw stop               = 5050 - 20.20 = 5029.80 -> tick 0.25 -> 5029.75
        risk_per_unit_actual   = 5050 - 5029.75 = 20.25
        risk_$/contract        = 20.25 * 50 = 1012.50
        available risk         = 2500 - 2 - 2 = 2496.00
        qty_risk               = floor(2496 / 1012.50) = 2
        gross_exposure         = 25000 * 12 = 300000
        qty_cap                = floor(300000 / (5050 * 50)) = floor(1.188) = 1
        qty                    = min(2, 1) = 1  (capped by buying power)
        """
        result = size_by_percent_stop(
            symbol="ES",
            side="long",
            entry=Decimal("5050"),
            account_equity=Decimal("25000"),
            leverage=Decimal("12"),
            pct_stop=Decimal("0.004"),
            risk_cash=Decimal("2500"),
            fees_open=Decimal("2"),
            fees_close=Decimal("2"),
        )

        assert result.qty == 1
        assert result.stop_price == Decimal("5029.75")
        assert result.risk_per_unit == Decimal("20.2000")
        assert result.risk_per_unit_actual == Decimal("20.2500")
        assert result.risk_dollars_per_contract == Decimal("1012.50")
        assert result.risk_cash == Decimal("2496.00")
        assert result.gross_exposure == Decimal("300000.00")
        assert result.buying_power_qty_cap == 1
        assert result.capped_by_buying_power is True
        assert result.method == "percent_stop"

    def test_nq_short_risk_bound(self):
        """NQ short, entry=18500, equity=$50k, leverage=8, pct_stop=0.3%, risk=$1500, no fees.

        risk_per_unit        = 18500 * 0.003 = 55.50
        raw stop             = 18500 + 55.50 = 18555.50 (already a valid 0.25 tick)
        risk_$/contract      = 55.50 * 20 = 1110.00
        qty_risk             = floor(1500 / 1110) = 1
        gross_exposure       = 50000 * 8 = 400000
        qty_cap              = floor(400000 / (18500 * 20)) = floor(1.081) = 1
        qty                  = 1 (risk-bound; cap does not reduce it)
        """
        result = size_by_percent_stop(
            symbol="NQ",
            side="short",
            entry=Decimal("18500"),
            account_equity=Decimal("50000"),
            leverage=Decimal("8"),
            pct_stop=Decimal("0.003"),
            risk_cash=Decimal("1500"),
        )

        assert result.qty == 1
        assert result.stop_price == Decimal("18555.50")
        assert result.stop_price > Decimal("18500")  # short: stop above entry
        assert result.risk_per_unit_actual == Decimal("55.5000")
        assert result.risk_dollars_per_contract == Decimal("1110.00")
        assert result.risk_cash == Decimal("1500.00")
        assert result.capped_by_buying_power is False

    def test_risk_budget_too_small_raises(self):
        """$250 risk budget cannot afford one ES contract at $1012.50 risk each."""
        with pytest.raises(ValueError, match=r"[Rr]isk budget"):
            size_by_percent_stop(
                symbol="ES",
                side="long",
                entry=Decimal("5050"),
                account_equity=Decimal("25000"),
                leverage=Decimal("12"),
                pct_stop=Decimal("0.004"),
                risk_cash=Decimal("250"),
            )

    def test_buying_power_too_small_raises(self):
        """$25k * 2.5 = $62.5k buying power < $252.5k ES notional -> cap = 0.

        The error must steer the trader toward micros or more leverage.
        """
        with pytest.raises(ValueError, match=r"[Bb]uying power"):
            size_by_percent_stop(
                symbol="ES",
                side="long",
                entry=Decimal("5050"),
                account_equity=Decimal("25000"),
                leverage=Decimal("2.5"),
                pct_stop=Decimal("0.004"),
                risk_cash=Decimal("2500"),
            )

    def test_tiny_entry_raises_clean_error_not_division_by_zero(self):
        """Entry 0.0001 (dashboard default) -> risk/contract quantizes to $0.00.

        Must raise a descriptive ValueError, not decimal.DivisionByZero.
        Regression: caught live in the Streamlit dashboard 2026-07-06.
        """
        with pytest.raises(ValueError, match=r"[Ss]top distance"):
            size_by_percent_stop(
                symbol="ES",
                side="long",
                entry=Decimal("0.0001"),
                account_equity=Decimal("25000"),
                leverage=Decimal("12"),
                pct_stop=Decimal("0.004"),
                risk_cash=Decimal("2500"),
            )

    def test_fees_reduce_available_risk(self):
        """Same as NQ golden but fees+slippage $390.01 drop available risk below one contract.

        available = 1500 - 200 - 100 - 90.01 = 1109.99 < 1110.00 -> qty_risk = 0
        """
        with pytest.raises(ValueError, match=r"[Rr]isk budget"):
            size_by_percent_stop(
                symbol="NQ",
                side="short",
                entry=Decimal("18500"),
                account_equity=Decimal("50000"),
                leverage=Decimal("8"),
                pct_stop=Decimal("0.003"),
                risk_cash=Decimal("1500"),
                fees_open=Decimal("200"),
                fees_close=Decimal("100"),
                slip_open=Decimal("90.01"),
            )


class TestPercentStopValidation:
    """Input validation still raises descriptive ValueErrors."""

    def _kwargs(self, **overrides):
        base = {
            "symbol": "ES",
            "side": "long",
            "entry": Decimal("5050"),
            "account_equity": Decimal("20000"),
            "leverage": Decimal("13"),  # 260k buying power > one ES contract (~252.5k)
            "pct_stop": Decimal("0.004"),
            "risk_cash": Decimal("2500"),
        }
        base.update(overrides)
        return base

    def test_invalid_symbol_raises_error(self):
        with pytest.raises(ValueError):
            size_by_percent_stop(**self._kwargs(symbol="INVALID"))

    def test_invalid_side_raises_error(self):
        with pytest.raises(ValueError):
            size_by_percent_stop(**self._kwargs(side="invalid"))

    def test_zero_pct_stop_raises_error(self):
        with pytest.raises(ValueError):
            size_by_percent_stop(**self._kwargs(pct_stop=Decimal("0")))

    def test_negative_equity_raises_error(self):
        with pytest.raises(ValueError):
            size_by_percent_stop(**self._kwargs(account_equity=Decimal("-20000")))

    def test_non_positive_risk_cash_raises_error(self):
        with pytest.raises(ValueError):
            size_by_percent_stop(**self._kwargs(risk_cash=Decimal("0")))

    def test_stop_is_rounded_to_tick(self):
        result = size_by_percent_stop(**self._kwargs(entry=Decimal("5050.123")))
        contract = get_contract("ES")
        assert result.stop_price == contract.round_to_tick(result.stop_price)

    def test_qty_scales_with_risk_budget(self):
        """Doubling the risk budget must not shrink qty (cap held constant & loose)."""
        small = size_by_percent_stop(**self._kwargs(leverage=Decimal("50")))
        large = size_by_percent_stop(
            **self._kwargs(leverage=Decimal("50"), risk_cash=Decimal("5000"))
        )
        assert large.qty >= small.qty


class TestPercentStopProperties:
    """Property tests: invariants that must hold for every successful sizing."""

    @settings(deadline=None)  # avoid deadline flakes on loaded CI runners
    @given(
        symbol=st.sampled_from(["ES", "NQ", "CL", "GC"]),
        side=st.sampled_from(["long", "short"]),
        entry=st.decimals(min_value="10", max_value="30000", places=2),
        equity=st.decimals(min_value="1000", max_value="500000", places=2),
        leverage=st.decimals(min_value="1", max_value="100", places=1),
        pct_stop=st.decimals(min_value="0.001", max_value="0.05", places=4),
        risk_cash=st.decimals(min_value="50", max_value="50000", places=2),
    )
    def test_invariants(self, symbol, side, entry, equity, leverage, pct_stop, risk_cash):
        contract = get_contract(symbol)
        try:
            result = size_by_percent_stop(
                symbol=symbol,
                side=side,
                entry=entry,
                account_equity=equity,
                leverage=leverage,
                pct_stop=pct_stop,
                risk_cash=risk_cash,
            )
        except ValueError:
            # Unsizeable draw: raising a *clean* ValueError is the contract.
            # Anything else (e.g. DivisionByZero) must fail the property.
            return

        # Stop is a valid tick and on the correct side of entry
        assert result.stop_price == contract.round_to_tick(result.stop_price)
        if side == "long":
            assert result.stop_price < entry
        else:
            assert result.stop_price > entry

        # Total risk never exceeds the (fee-adjusted) risk budget
        assert result.qty * result.risk_dollars_per_contract <= result.risk_cash

        # Notional never exceeds declared buying power
        assert Decimal(result.qty) * entry * contract.point_value <= equity * leverage

        assert result.qty >= 1


class TestAtrStopSizing:
    """ATR path: qty must be computed from the tick-rounded stop distance."""

    def test_atr_qty_uses_rounded_stop_distance(self):
        """ES long, entry=5050.10, ATR=10.07, k=2, risk=$2010.

        raw loss/unit  = 2 * 10.07 = 20.14 -> raw stop = 5029.96
        tick-rounded   = 5030.00 -> actual loss/unit = 20.10
        risk_$/contract = 20.10 * 50 = 1005.00
        qty            = floor(2010 / 1005) = 2   (unrounded 20.14 would give 1)
        """
        result = size_by_atr_stop(
            symbol="ES",
            side="long",
            entry=Decimal("5050.10"),
            atr=Decimal("10.07"),
            k_atr=Decimal("2"),
            risk_cash=Decimal("2010"),
        )

        assert result.stop_price == Decimal("5030.00")
        assert result.risk_per_unit_actual == Decimal("20.1000")
        assert result.risk_dollars_per_contract == Decimal("1005.00")
        assert result.qty == 2

    def test_atr_insufficient_risk_raises(self):
        with pytest.raises(ValueError):
            size_by_atr_stop(
                symbol="ES",
                side="long",
                entry=Decimal("5050"),
                atr=Decimal("10"),
                k_atr=Decimal("2"),
                risk_cash=Decimal("500"),
            )

    def test_atr_swing_structure_widens_stop(self):
        """Swing low farther than k*ATR must win (more conservative).

        entry=5050, ATR=5, k=2 -> atr distance 10; swing_low=5030 -> distance 20.
        stop = 5030.00, risk_$/contract = 20 * 50 = 1000, qty = floor(3000/1000) = 3.
        """
        result = size_by_atr_stop(
            symbol="ES",
            side="long",
            entry=Decimal("5050"),
            atr=Decimal("5"),
            k_atr=Decimal("2"),
            swing_low=Decimal("5030"),
            risk_cash=Decimal("3000"),
        )

        assert result.stop_price == Decimal("5030.00")
        assert result.qty == 3
