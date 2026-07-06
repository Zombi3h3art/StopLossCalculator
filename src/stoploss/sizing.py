"""Position sizing and stop-loss calculations (risk-first).

Both paths size from an explicit risk budget (``risk_cash``, in dollars):

A) Percent stop: stop_price = entry ± (entry * pct_stop), rounded to tick.
   qty = min(floor(available_risk / risk_$_per_contract),
             floor(account_equity * leverage / (entry * point_value)))
   The second term is the buying-power cap implied by the trader's declared
   leverage; sizing never exceeds what that notional can control.

B) ATR/structure stop: stop_price = entry ± max(k_atr * ATR, structure distance),
   rounded to tick. qty = floor(available_risk / risk_$_per_contract).

Both round the stop to a valid tick FIRST and recompute the per-contract risk
from the rounded stop, so the reported R is honest.
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
    risk_cash: Decimal  # risk budget remaining after fees/slippage
    fees_open: Decimal
    fees_close: Decimal
    slippage_open: Decimal
    method: str
    buying_power_qty_cap: int | None = None  # max contracts the declared leverage affords
    capped_by_buying_power: bool = False  # True when the cap reduced qty below risk-based qty


def size_by_percent_stop(
    symbol: Symbol,
    side: Side,
    entry: Decimal,
    account_equity: Decimal,
    leverage: Decimal,
    pct_stop: Decimal,
    risk_cash: Decimal,
    fees_open: Decimal = Decimal("0"),
    fees_close: Decimal = Decimal("0"),
    slip_open: Decimal = Decimal("0"),
) -> PositionSize:
    """Size position using a percent stop and an explicit risk budget (risk-first).

    Args:
        symbol: "ES", "NQ", "CL", "GC"
        side: "long" or "short"
        entry: Entry price
        account_equity: Account size in dollars
        leverage: Declared leverage multiplier (e.g., 3.0); with account_equity it
            defines the buying power that caps position size
        pct_stop: Stop distance as a fraction of entry (e.g., 0.004 for 0.4%)
        risk_cash: Maximum acceptable loss in dollars (the risk budget)
        fees_open: Opening fees in dollars
        fees_close: Closing fees in dollars
        slip_open: Opening slippage in dollars

    Returns:
        PositionSize with qty, tick-rounded stop_price, and honest risk numbers.

    Raises:
        ValueError: if the risk budget cannot afford one contract, or the
            declared buying power cannot control one contract (use micros or
            adjust leverage/equity).

    Formulas:
        stop = entry -/+ (entry * pct_stop), rounded to contract tick
        risk_$_per_contract = |entry - stop| * point_value
        available_risk = risk_cash - fees_open - fees_close - slip_open
        qty_risk = floor(available_risk / risk_$_per_contract)
        qty_cap  = floor(account_equity * leverage / (entry * point_value))
        qty = min(qty_risk, qty_cap)
    """
    contract = get_contract(symbol)
    if side not in ("long", "short"):
        raise ValueError(f"side must be 'long' or 'short', got {side}")

    entry = Decimal(str(entry))
    account_equity = Decimal(str(account_equity))
    leverage = Decimal(str(leverage))
    pct_stop = Decimal(str(pct_stop))
    risk_cash = Decimal(str(risk_cash))
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
    if risk_cash <= 0:
        raise ValueError(f"risk_cash must be positive, got {risk_cash}")

    gross_exposure = (account_equity * leverage).quantize(Decimal("0.01"))
    risk_per_unit = (entry * pct_stop).quantize(Decimal("0.0001"))

    # Round the stop to a valid tick, then recompute the true risk distance
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
    if risk_dollars_per_contract <= 0:
        raise ValueError(
            f"Stop distance {risk_per_unit_actual} is too small to size {symbol}: "
            "risk per contract rounds to $0.00. Increase pct_stop or the entry price."
        )

    # Buying-power cap: how many contracts the declared leverage can control
    contract_notional = entry * contract.point_value
    buying_power_qty_cap = int(
        (gross_exposure / contract_notional).to_integral_value(rounding=ROUND_DOWN)
    )
    if buying_power_qty_cap <= 0:
        raise ValueError(
            f"Buying power too small: equity {account_equity} x leverage {leverage} "
            f"= {gross_exposure} cannot control one {symbol} contract "
            f"(notional {contract_notional.quantize(Decimal('0.01'))}). "
            "Increase leverage/equity or trade micro contracts."
        )

    # Risk budget: how many contracts the acceptable loss affords
    available_risk_cash = (risk_cash - fees_open - fees_close - slip_open).quantize(Decimal("0.01"))
    qty_risk = (
        int(
            (available_risk_cash / risk_dollars_per_contract).to_integral_value(rounding=ROUND_DOWN)
        )
        if available_risk_cash > 0
        else 0
    )
    if qty_risk <= 0:
        raise ValueError(
            f"Risk budget too small: available risk {available_risk_cash} "
            f"(risk_cash {risk_cash} minus fees/slippage) is below the "
            f"{risk_dollars_per_contract} risk of one {symbol} contract at this stop."
        )

    qty = min(qty_risk, buying_power_qty_cap)

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
        buying_power_qty_cap=buying_power_qty_cap,
        capped_by_buying_power=buying_power_qty_cap < qty_risk,
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
        PositionSize with qty computed from the tick-rounded stop distance.

    Formulas (long example):
        loss_per_unit = max(k_atr * ATR, entry - swing_low)
        stop = round_to_tick(entry - loss_per_unit)
        qty = floor((risk_cash - fees_open - slip_open) / (point_value * |entry - stop|))
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

    # Calculate theoretical loss per unit (ATR vs structure, whichever is wider)
    atr_loss = k_atr * atr

    if swing_low is not None:
        swing_low = Decimal(str(swing_low))
        if side == "long":
            structure_loss = entry - swing_low
        else:
            # short: swing_low carries the swing high
            structure_loss = swing_low - entry
        loss_per_unit = max(atr_loss, structure_loss)
    else:
        loss_per_unit = atr_loss

    # Round the stop to a valid tick, then recompute the true risk distance
    raw_stop = entry - loss_per_unit if side == "long" else entry + loss_per_unit
    stop_price = contract.round_to_tick(raw_stop)

    loss_per_unit_actual = (
        (entry - stop_price) if side == "long" else (stop_price - entry)
    ).quantize(Decimal("0.0001"))

    if loss_per_unit_actual <= 0:
        raise ValueError("Rounded stop produced non-positive risk distance")

    risk_dollars_per_contract = (loss_per_unit_actual * contract.point_value).quantize(
        Decimal("0.01")
    )
    if risk_dollars_per_contract <= 0:
        raise ValueError(
            f"Stop distance {loss_per_unit_actual} is too small to size {symbol}: "
            "risk per contract rounds to $0.00. Increase the ATR distance or entry price."
        )

    available_risk = (risk_cash - fees_open - slip_open).quantize(Decimal("0.01"))
    if available_risk <= 0:
        raise ValueError(f"risk_cash insufficient to cover fees/slip. available={available_risk}")

    qty = int((available_risk / risk_dollars_per_contract).to_integral_value(rounding=ROUND_DOWN))

    if qty <= 0:
        raise ValueError(
            f"Insufficient risk allocation. qty={qty} (avail_risk={available_risk}, "
            f"loss_per_unit={loss_per_unit_actual}, ppv={contract.ppv_per_unit})"
        )

    gross_exposure = (entry * contract.point_value * Decimal(qty)).quantize(Decimal("0.01"))

    return PositionSize(
        symbol=symbol,
        side=side,
        qty=qty,
        entry=entry,
        stop_price=stop_price,
        risk_per_unit=loss_per_unit.quantize(Decimal("0.0001")),
        risk_per_unit_actual=loss_per_unit_actual,
        risk_dollars_per_contract=risk_dollars_per_contract,
        gross_exposure=gross_exposure,
        risk_cash=available_risk,
        fees_open=fees_open,
        fees_close=Decimal("0"),
        slippage_open=slip_open,
        method="atr_stop",
    )
