"""Position sizing and stop-loss calculations.

Two paths:
A) Percent stop (risk-first): qty = floor(gross_exposure / (entry * ppv))
   stop_price = entry ± (entry * pct_stop)

B) ATR/structure stop (risk-first): qty based on risk_cash and stop distance
   stop_price = entry ± k_atr * ATR (or swing low)

Both round stops to valid ticks and recompute loss to keep R honest.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from .contracts import Symbol, get_contract

Side = Literal["long", "short"]


@dataclass
class PositionSize:
    """Position sizing result."""

    qty: int  # Number of contracts/units
    entry_price: Decimal  # Entry price in contract units
    stop_price: Decimal  # Stop loss price (rounded to tick)
    loss_per_unit: Decimal  # Price loss per unit (contract)
    loss_dollars: Decimal  # Dollar loss at stop (qty * ppv * loss_per_unit)
    gross_exposure: Decimal  # Account equity * leverage
    method: str  # "percent_stop" or "atr_stop"


def size_by_percent_stop(
    symbol: Symbol,
    side: Side,
    entry: Decimal,
    account_equity: Decimal,
    leverage: Decimal,
    pct_stop: Decimal,
    fees_open: Decimal = Decimal("0"),
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
    entry = Decimal(str(entry))
    account_equity = Decimal(str(account_equity))
    leverage = Decimal(str(leverage))
    pct_stop = Decimal(str(pct_stop))
    fees_open = Decimal(str(fees_open))
    slip_open = Decimal(str(slip_open))

    if entry <= 0:
        raise ValueError(f"entry must be positive, got {entry}")
    if account_equity <= 0:
        raise ValueError(f"account_equity must be positive, got {account_equity}")
    if leverage < 1:
        raise ValueError(f"leverage must be >= 1, got {leverage}")
    if pct_stop <= 0 or pct_stop >= 1:
        raise ValueError(f"pct_stop must be in (0, 1), got {pct_stop}")

    gross_exposure = account_equity * leverage
    loss_per_unit = entry * pct_stop

    # Qty based on gross exposure
    qty_float = float(gross_exposure / (entry * contract.ppv_per_unit))
    qty = int(qty_float)

    if qty <= 0:
        raise ValueError(
            f"Insufficient capital for entry. Got qty={qty} (gross_exp={gross_exposure}, "
            f"entry={entry}, ppv={contract.ppv_per_unit})"
        )

    # Calculate stop price (not yet rounded)
    stop_price = entry - loss_per_unit if side == "long" else entry + loss_per_unit

    # Round stop to nearest tick
    stop_price_rounded = contract.round_to_tick(stop_price)

    # Recompute loss_per_unit with rounded stop
    loss_per_unit_actual = (
        entry - stop_price_rounded if side == "long" else stop_price_rounded - entry
    )

    # Verify risk alignment
    gross_loss_dollars = Decimal(qty) * contract.ppv_per_unit * loss_per_unit_actual

    return PositionSize(
        qty=qty,
        entry_price=entry,
        stop_price=stop_price_rounded,
        loss_per_unit=loss_per_unit_actual,
        loss_dollars=gross_loss_dollars,
        gross_exposure=gross_exposure,
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
    available_risk = risk_cash - fees_open - slip_open
    if available_risk <= 0:
        raise ValueError(f"risk_cash insufficient to cover fees/slip. available={available_risk}")

    qty_float = float(available_risk / (contract.ppv_per_unit * loss_per_unit))
    qty = int(qty_float)

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

    gross_loss_dollars = Decimal(qty) * contract.ppv_per_unit * loss_per_unit_actual

    return PositionSize(
        qty=qty,
        entry_price=entry,
        stop_price=stop_price_rounded,
        loss_per_unit=loss_per_unit_actual,
        loss_dollars=gross_loss_dollars,
        gross_exposure=entry * contract.ppv_per_unit * Decimal(qty),
        method="atr_stop",
    )
