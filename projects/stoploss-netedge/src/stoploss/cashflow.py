"""Cashflow and P&L calculation with all costs."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from stoploss.contracts import Symbol
from stoploss.contracts import get_contract


@dataclass
class PnLResult:
    """Complete P&L breakdown with all costs and taxes."""

    symbol: Symbol
    qty: int
    entry_price: Decimal
    target_price: Decimal  # Where we want to exit on win
    stop_price: Decimal  # Where we stop out on loss

    gross_win: Decimal  # qty * ppv * (target - entry) for long
    gross_loss: Decimal  # qty * ppv * (entry - stop) for long

    fees_open: Decimal
    fees_close: Decimal
    slip_open: Decimal
    slip_close: Decimal
    total_fees_slip: Decimal

    energy_cost: Decimal
    margin_interest: Decimal

    tax_on_win: Decimal
    net_win: Decimal
    net_loss: Decimal


def calculate_gross_pnl(
    symbol: Symbol,
    side: Literal["long", "short"],
    qty: int,
    entry: Decimal,
    target: Decimal,
    stop: Decimal,
) -> tuple[Decimal, Decimal]:
    """Calculate gross P&L on win and loss (before fees/taxes).

    Args:
        symbol: "ES", "NQ", "CL", "GC"
        side: "long" or "short"
        qty: Number of contracts
        entry: Entry price
        target: Target exit price on win
        stop: Stop loss price on loss

    Returns:
        (gross_win, gross_loss) in dollars
    """
    contract = get_contract(symbol)
    qty_d = Decimal(qty)
    entry = Decimal(str(entry))
    target = Decimal(str(target))
    stop = Decimal(str(stop))

    if side == "long":
        delta_win = target - entry
        delta_loss = entry - stop
    else:  # short
        delta_win = entry - target
        delta_loss = stop - entry

    gross_win = qty_d * contract.ppv_per_unit * delta_win
    gross_loss = qty_d * contract.ppv_per_unit * delta_loss

    return gross_win, gross_loss


def calculate_pnl(
    symbol: Symbol,
    side: Literal["long", "short"],
    qty: int,
    entry: Decimal,
    target: Decimal,
    stop: Decimal,
    fees_open: Decimal = Decimal("0"),
    fees_close: Decimal = Decimal("0"),
    slip_open: Decimal = Decimal("0"),
    slip_close: Decimal = Decimal("0"),
    energy_cost: Decimal = Decimal("0"),
    margin_interest: Decimal = Decimal("0"),
    tax_on_win: Decimal = Decimal("0"),
) -> PnLResult:
    """Full P&L calculation with all costs.

    Args:
        symbol: "ES", "NQ", "CL", "GC"
        side: "long" or "short"
        qty: Number of contracts
        entry: Entry price
        target: Target price (win scenario)
        stop: Stop price (loss scenario)
        fees_open: Entry fee
        fees_close: Exit fee
        slip_open: Entry slippage
        slip_close: Exit slippage
        energy_cost: Energy cost in dollars
        margin_interest: Margin loan interest in dollars
        tax_on_win: Federal tax on winning trade

    Returns:
        PnLResult with breakdown
    """
    gross_win, gross_loss = calculate_gross_pnl(symbol, side, qty, entry, target, stop)

    fees_slip = Decimal(str(fees_open)) + Decimal(str(fees_close))
    fees_slip += Decimal(str(slip_open)) + Decimal(str(slip_close))
    energy_cost = Decimal(str(energy_cost))
    margin_interest = Decimal(str(margin_interest))
    tax_on_win = Decimal(str(tax_on_win))

    # Net results
    net_win = gross_win - fees_slip - energy_cost - margin_interest - tax_on_win
    net_loss = -(gross_loss + fees_slip + energy_cost + margin_interest)

    return PnLResult(
        symbol=symbol,
        qty=qty,
        entry_price=Decimal(str(entry)),
        target_price=Decimal(str(target)),
        stop_price=Decimal(str(stop)),
        gross_win=gross_win,
        gross_loss=gross_loss,
        fees_open=Decimal(str(fees_open)),
        fees_close=Decimal(str(fees_close)),
        slip_open=Decimal(str(slip_open)),
        slip_close=Decimal(str(slip_close)),
        total_fees_slip=fees_slip,
        energy_cost=energy_cost,
        margin_interest=margin_interest,
        tax_on_win=tax_on_win,
        net_win=net_win,
        net_loss=net_loss,
    )
