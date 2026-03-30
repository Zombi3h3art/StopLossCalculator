"""Position sizing and stop-loss calculations.

Two paths:
A) Percent stop (risk-first): qty = floor(gross_exposure / (entry * ppv))
   stop_price = entry ± (entry * pct_stop)

B) ATR/structure stop (risk-first): qty based on risk_cash and stop distance
   stop_price = entry ± k_atr * ATR (or swing low)

Both round stops to valid ticks and recompute loss to keep R honest.
"""

from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal
from typing import Literal

from .contracts import Symbol, get_contract

Side = Literal["long", "short"]


@dataclass
class PositionSize:
    """Position sizing result for percent/ATR workflows."""

    symbol: Symbol
    side: Side
    qty: int
    entry: Decimal
    stop_price: Decimal
    risk_per_unit: Decimal  # theoretical stop distance before tick rounding
    risk_per_unit_actual: Decimal  # stop distance after tick rounding
    risk_dollars_per_contract: Decimal
    gross_exposure: Decimal
    risk_cash: Decimal
    fees_open: Decimal
    fees_close: Decimal
    slippage_open: Decimal
    method: str


def size_by_percent_stop(
    symbol: Symbol,
    side: Side,
    entry: Decimal,
    account_equity: Decimal,
    leverage: Decimal,
    pct_stop: Decimal,
    fees_open: Decimal = Decimal("0"),
    fees_close: Decimal = Decimal("0"),
    slip_open: Decimal = Decimal("0"),
) -> PositionSize:
    """Size position using percent-stop method (risk-first).

    Args:
        symbol: "ES", "NQ", "CL", "GC"
        side: "long" or "short"
        entry: Entry price
        account_equity: Account size in dollars
        leverage: Leverage multiplier (e.g., 3.0)
        pct_stop: Stop loss as percent of entry (e.g., 0.004 for 0.4%)
        fees_open: Opening fees in dollars
        slip_open: Opening slippage in dollars

    Returns:
        PositionSize with qty, stop_price, and validation.

    Formulas:
        gross_exposure = account_equity * leverage
        loss_per_unit = entry * pct_stop
        qty = floor(gross_exposure / (entry * ppv_per_unit))
        stop = entry - loss_per_unit (long) or entry + loss_per_unit (short)
        round stop to nearest tick, recompute loss_per_unit
    """
    contract = get_contract(symbol)
    if side not in ("long", "short"):
        raise ValueError(f"side must be 'long' or 'short', got {side}")

    entry = Decimal(str(entry))
    account_equity = Decimal(str(account_equity))
    leverage = Decimal(str(leverage))
    pct_stop = Decimal(str(pct_stop))
    fees_open = Decimal(str(fees_open))
    fees_close = Decimal(str(fees_close))
    slip_open = Decimal(str(slip_open))

    if entry <= 0:
        raise ValueError(f"entry must be positive, got {entry}")
    if account_equity <= 0:
        raise ValueError(f"account_equity must be positive, got {account_equity}")
    if leverage < 1:
        raise ValueError(f"leverage must be >= 1, got {leverage}")
    if pct_stop <= 0 or pct_stop >= 1:
        raise ValueError(f"pct_stop must be in (0, 1), got {pct_stop}")

    gross_exposure = (account_equity * leverage).quantize(Decimal("0.01"))
    risk_per_unit = (entry * pct_stop).quantize(Decimal("0.0001"))

    # Calculate stop price (before rounding)
    raw_stop = entry - risk_per_unit if side == "long" else entry + risk_per_unit
    stop_price = contract.round_to_tick(raw_stop)

    risk_per_unit_actual = (
        (entry - stop_price) if side == "long" else (stop_price - entry)
    ).quantize(Decimal("0.0001"))

    if risk_per_unit_actual <= 0:
        raise ValueError("Rounded stop produced non-positive risk distance")

    risk_dollars_per_contract = (risk_per_unit_actual * contract.point_value).quantize(
        Decimal("0.01")
    )

    available_risk_cash = (gross_exposure - fees_open - fees_close - slip_open).quantize(
        Decimal("0.01")
    )
    if available_risk_cash <= 0:
        raise ValueError("Risk cash unavailable after fees/slippage")

    qty_decimal = (available_risk_cash / risk_dollars_per_contract).to_integral_value(
        rounding=ROUND_DOWN
    )
    qty = int(qty_decimal)

    if qty <= 0:
        raise ValueError(
            "Insufficient capital for entry. "
            f"risk_cash={available_risk_cash}, risk_per_contract={risk_dollars_per_contract}"
        )

    return PositionSize(
        symbol=symbol,
        side=side,
        qty=qty,
        entry=entry,
        stop_price=stop_price,
        risk_per_unit=risk_per_unit,
        risk_per_unit_actual=risk_per_unit_actual,
        risk_dollars_per_contract=risk_dollars_per_contract,
        gross_exposure=gross_exposure,
        risk_cash=available_risk_cash,
        fees_open=fees_open,
        fees_close=fees_close,
        slippage_open=slip_open,
        method="percent_stop",
    )


def size_by_atr_stop(
    symbol: Symbol,
    side: Side,
    entry: Decimal,
    atr: Decimal,
    k_atr: Decimal = Decimal("2.0"),
    swing_low: Decimal | None = None,
    risk_cash: Decimal = Decimal("500"),
    fees_open: Decimal = Decimal("0"),
    slip_open: Decimal = Decimal("0"),
) -> PositionSize:
    """Size position using ATR/structure-based stop (risk-first).

    Args:
        symbol: "ES", "NQ", "CL", "GC"
        side: "long" or "short"
        entry: Entry price
        atr: Average True Range (or volatility measure) in price units
        k_atr: ATR multiplier (default 2.0)
        swing_low: Optional swing low (long) or swing high (short) override
        risk_cash: Maximum risk in dollars
        fees_open: Opening fees in dollars
        slip_open: Opening slippage in dollars

    Returns:
        PositionSize with qty, stop_price, and validation.

    Formulas (long example):
        loss_per_unit = max(k_atr * ATR, entry - swing_low)
        qty = (risk_cash - fees_open - slip_open) / (ppv_per_unit * loss_per_unit)
    """
    contract = get_contract(symbol)
    if side not in ("long", "short"):
        raise ValueError(f"side must be 'long' or 'short', got {side}")

    entry = Decimal(str(entry))
    atr = Decimal(str(atr))
    k_atr = Decimal(str(k_atr))
    risk_cash = Decimal(str(risk_cash))
    fees_open = Decimal(str(fees_open))
    slip_open = Decimal(str(slip_open))

    if entry <= 0:
        raise ValueError(f"entry must be positive, got {entry}")
    if atr <= 0:
        raise ValueError(f"atr must be positive, got {atr}")
    if k_atr <= 0:
        raise ValueError(f"k_atr must be positive, got {k_atr}")
    if risk_cash <= 0:
        raise ValueError(f"risk_cash must be positive, got {risk_cash}")

    # Calculate loss per unit
    atr_loss = k_atr * atr

    if swing_low is not None:
        swing_low = Decimal(str(swing_low))
        if side == "long":
            # Use whichever is larger (more conservative)
            structure_loss = entry - swing_low
            loss_per_unit = max(atr_loss, structure_loss)
        else:
            # short: swing_high is the structure
            structure_loss = swing_low - entry
            loss_per_unit = max(atr_loss, structure_loss)
    else:
        loss_per_unit = atr_loss

    # Calculate qty
    available_risk = (risk_cash - fees_open - slip_open).quantize(Decimal("0.01"))
    if available_risk <= 0:
        raise ValueError(f"risk_cash insufficient to cover fees/slip. available={available_risk}")

    risk_dollars_per_contract = (loss_per_unit * contract.point_value).quantize(Decimal("0.01"))

    qty_decimal = (available_risk / risk_dollars_per_contract).to_integral_value(
        rounding=ROUND_DOWN
    )
    qty = int(qty_decimal)

    if qty <= 0:
        raise ValueError(
            f"Insufficient risk allocation. qty={qty} (avail_risk={available_risk}, "
            f"loss_per_unit={loss_per_unit}, ppv={contract.ppv_per_unit})"
        )

    # Calculate stop price
    stop_price = entry - loss_per_unit if side == "long" else entry + loss_per_unit

    # Round stop to nearest tick
    stop_price_rounded = contract.round_to_tick(stop_price)

    # Recompute loss_per_unit with rounded stop
    loss_per_unit_actual = (
        entry - stop_price_rounded if side == "long" else stop_price_rounded - entry
    )

    gross_exposure = (entry * contract.point_value * Decimal(qty)).quantize(Decimal("0.01"))

    return PositionSize(
        symbol=symbol,
        side=side,
        qty=qty,
        entry=entry,
        stop_price=stop_price_rounded,
        risk_per_unit=loss_per_unit.quantize(Decimal("0.0001")),
        risk_per_unit_actual=loss_per_unit_actual.quantize(Decimal("0.0001")),
        risk_dollars_per_contract=risk_dollars_per_contract,
        gross_exposure=gross_exposure,
        risk_cash=available_risk,
        fees_open=fees_open,
        fees_close=Decimal("0"),
        slippage_open=slip_open,
        method="atr_stop",
    )
