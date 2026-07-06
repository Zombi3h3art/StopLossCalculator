"""Cashflow and P&L calculation with all costs."""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from .contracts import Symbol, get_contract
from .rates import MarginLoan, calculate_total_margin_interest
from .taxes import TaxMode, calculate_tax


@dataclass
class PnLResult:
    """Complete P&L breakdown with all costs and taxes."""

    symbol: Symbol
    side: Literal["long", "short"]
    qty: int
    entry: Decimal
    target: Decimal
    stop: Decimal

    gross_win: Decimal
    gross_loss: Decimal

    net_win_scenario: Decimal
    net_loss_scenario: Decimal
    breakdown: dict[str, Decimal]


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
    if side not in ("long", "short"):
        raise ValueError(f"side must be 'long' or 'short', got {side}")
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

    if delta_win < 0 or delta_loss < 0:
        raise ValueError("Invalid target/stop distances for the given side")

    gross_win = (qty_d * contract.point_value * delta_win).quantize(Decimal("0.01"))
    gross_loss = (qty_d * contract.point_value * delta_loss).quantize(Decimal("0.01"))

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
    slippage_open: Decimal = Decimal("0"),
    slippage_close: Decimal = Decimal("0"),
    energy_kwh: Decimal = Decimal("0"),
    energy_cost_per_kwh: Decimal = Decimal("0.14"),
    margin_loans: Iterable[MarginLoan] | None = None,
    tax_mode: TaxMode = "section_1256",
    st_rate: Decimal = Decimal("0.24"),
    lt_rate: Decimal | None = Decimal("0.15"),
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

    fees_open = Decimal(str(fees_open))
    fees_close = Decimal(str(fees_close))
    slippage_open = Decimal(str(slippage_open))
    slippage_close = Decimal(str(slippage_close))
    energy_kwh = Decimal(str(energy_kwh))
    energy_cost_per_kwh = Decimal(str(energy_cost_per_kwh))

    fees_open_q = fees_open.quantize(Decimal("0.01"))
    fees_close_q = fees_close.quantize(Decimal("0.01"))
    slippage_open_q = slippage_open.quantize(Decimal("0.01"))
    slippage_close_q = slippage_close.quantize(Decimal("0.01"))
    total_fees_slip = (fees_open_q + fees_close_q + slippage_open_q + slippage_close_q).quantize(
        Decimal("0.01")
    )

    if energy_kwh > 0:
        energy_cost = (energy_kwh * energy_cost_per_kwh).quantize(Decimal("0.01"))
    else:
        energy_cost = Decimal("0.00")

    loan_records = list(margin_loans) if margin_loans else []
    margin_interest = (
        calculate_total_margin_interest(loan_records) if loan_records else Decimal("0.00")
    )

    tax_on_win = (
        calculate_tax(gross_win, tax_mode, st_rate, lt_rate) if gross_win > 0 else Decimal("0.00")
    )

    net_win = gross_win - (total_fees_slip + energy_cost + margin_interest + tax_on_win)
    net_loss = -(gross_loss + total_fees_slip + energy_cost + margin_interest)

    breakdown = {
        "fees_open": fees_open_q,
        "fees_close": fees_close_q,
        "slippage_open": slippage_open_q,
        "slippage_close": slippage_close_q,
        "total_fees_slippage": total_fees_slip,
        "energy_cost": energy_cost,
        "margin_interest": margin_interest,
        "tax_on_win": tax_on_win,
    }

    return PnLResult(
        symbol=symbol,
        side=side,
        qty=qty,
        entry=Decimal(str(entry)),
        target=Decimal(str(target)),
        stop=Decimal(str(stop)),
        gross_win=gross_win,
        gross_loss=gross_loss,
        net_win_scenario=net_win.quantize(Decimal("0.01")),
        net_loss_scenario=net_loss.quantize(Decimal("0.01")),
        breakdown=breakdown,
    )
