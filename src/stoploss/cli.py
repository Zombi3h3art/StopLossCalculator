"""CLI for stop-loss calculator (Typer)."""

from decimal import Decimal
from typing import cast

import typer

from .contracts import validate_symbol
from .sizing import Side
from .taxes import TaxMode

app = typer.Typer(help="Stop Loss Net Edge: Precision futures calculator with full cost accounting")

_TAX_MODES = ("short_term", "short_term_ordinary", "1256", "section_1256")


def _validate_side(side: str) -> Side:
    normalized = side.lower().strip()
    if normalized not in ("long", "short"):
        raise ValueError(f"side must be 'long' or 'short', got {side}")
    return cast(Side, normalized)


@app.command()
def size(
    symbol: str = typer.Option(..., "--symbol", help="Contract: ES, NQ, CL, GC"),
    side: str = typer.Option(..., "--side", help="long or short"),
    entry: float = typer.Option(..., "--entry", help="Entry price"),
    equity: float = typer.Option(..., "--equity", help="Account equity ($)"),
    leverage: float = typer.Option(1.0, "--leverage", help="Declared leverage multiplier"),
    pct_stop: float = typer.Option(
        None, "--pct-stop", help="Stop distance as fraction of entry (e.g., 0.004)"
    ),
    risk: float = typer.Option(None, "--risk", help="Risk budget in dollars (max acceptable loss)"),
    atr: float = typer.Option(None, "--atr", help="Average True Range for ATR-based stop"),
    k_atr: float = typer.Option(2.0, "--k-atr", help="ATR multiplier (default 2.0)"),
    swing: float = typer.Option(
        None, "--swing", help="Swing low (long) / swing high (short) structure override"
    ),
    fees_open: float = typer.Option(0, "--fees-open", help="Opening fee ($)"),
    fees_close: float = typer.Option(0, "--fees-close", help="Closing fee ($)"),
    slip_open: float = typer.Option(0, "--slip-open", help="Opening slippage ($)"),
) -> None:
    """Calculate position size and stop price (risk-first).

    Percent stop:  --pct-stop 0.004 --risk 2500
    ATR/structure: --atr 10.0 [--k-atr 2.0] [--swing 5030] --risk 2500
    """
    from .sizing import size_by_atr_stop, size_by_percent_stop

    if pct_stop is None and atr is None:
        typer.echo("Error: specify one of --pct-stop or --atr (both need --risk)")
        raise typer.Exit(1)
    if pct_stop is not None and atr is not None:
        typer.echo("Error: specify only one of --pct-stop or --atr, not both")
        raise typer.Exit(1)
    if risk is None:
        typer.echo("Error: --risk (risk budget in dollars) is required for sizing")
        raise typer.Exit(1)

    try:
        symbol_v = validate_symbol(symbol)
        side_v = _validate_side(side)

        if pct_stop is not None:
            result = size_by_percent_stop(
                symbol=symbol_v,
                side=side_v,
                entry=Decimal(str(entry)),
                account_equity=Decimal(str(equity)),
                leverage=Decimal(str(leverage)),
                pct_stop=Decimal(str(pct_stop)),
                risk_cash=Decimal(str(risk)),
                fees_open=Decimal(str(fees_open)),
                fees_close=Decimal(str(fees_close)),
                slip_open=Decimal(str(slip_open)),
            )
        else:
            result = size_by_atr_stop(
                symbol=symbol_v,
                side=side_v,
                entry=Decimal(str(entry)),
                atr=Decimal(str(atr)),
                k_atr=Decimal(str(k_atr)),
                swing_low=Decimal(str(swing)) if swing is not None else None,
                risk_cash=Decimal(str(risk)),
                fees_open=Decimal(str(fees_open)),
                slip_open=Decimal(str(slip_open)),
            )

        typer.echo(f"\n{symbol_v} {side_v.upper()} Position")
        typer.echo(f"  Entry:        {result.entry}")
        typer.echo(f"  Qty:          {result.qty} contracts")
        typer.echo(f"  Stop:         {result.stop_price}")
        typer.echo(f"  Risk/unit:    {result.risk_per_unit_actual}")
        typer.echo(f"  Risk$/ctr:    {result.risk_dollars_per_contract}")
        typer.echo(f"  Risk budget:  {result.risk_cash} (after fees/slippage)")
        typer.echo(f"  Max loss:     {Decimal(result.qty) * result.risk_dollars_per_contract}")
        typer.echo(f"  Fees (open):  {result.fees_open}")
        typer.echo(f"  Fees (close): {result.fees_close}")
        typer.echo(f"  Method:       {result.method}")
        if result.buying_power_qty_cap is not None:
            typer.echo(f"  BP cap:       {result.buying_power_qty_cap} contracts")
            if result.capped_by_buying_power:
                typer.echo("  Note:         qty capped by buying power (equity x leverage)")
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@app.command()
def pnl(
    symbol: str = typer.Option(..., "--symbol", help="Contract: ES, NQ, CL, GC"),
    side: str = typer.Option(..., "--side", help="long or short"),
    entry: float = typer.Option(..., "--entry", help="Entry price"),
    target: float = typer.Option(..., "--target", help="Target (win) price"),
    stop: float = typer.Option(..., "--stop", help="Stop loss price"),
    qty: int = typer.Option(..., "--qty", help="Number of contracts"),
    fees_open: float = typer.Option(0, "--fees-open"),
    fees_close: float = typer.Option(0, "--fees-close"),
    slip_open: float = typer.Option(0, "--slip-open"),
    slip_close: float = typer.Option(0, "--slip-close"),
    tax_mode: str = typer.Option("short_term_ordinary", "--tax-mode"),
    st_rate: float = typer.Option(0.24, "--st-rate"),
    lt_rate: float = typer.Option(0.15, "--lt-rate"),
    energy_kwh: float = typer.Option(0, "--energy-kwh"),
    loan1: str = typer.Option("", "--loan1", help="loan_amt:apr (e.g., 5000:0.065)"),
    loan2: str = typer.Option("", "--loan2"),
    loan3: str = typer.Option("", "--loan3"),
    days: int = typer.Option(1, "--days"),
) -> None:
    """Calculate gross and net P&L with all costs."""
    from .cashflow import calculate_pnl
    from .rates import MarginLoan

    try:
        symbol_v = validate_symbol(symbol)
        side_v = _validate_side(side)
        if tax_mode not in _TAX_MODES:
            raise ValueError(f"tax_mode must be one of {_TAX_MODES}, got {tax_mode}")
        tax_mode_v = cast(TaxMode, tax_mode)

        # Margin interest
        loans_list: list[MarginLoan] = []
        for loan_str in [loan1, loan2, loan3]:
            if loan_str and ":" in loan_str:
                amt, apr = loan_str.split(":")
                loans_list.append(
                    MarginLoan(
                        loan_amount=Decimal(str(amt)),
                        apr=Decimal(str(apr)),
                        days_held=days,
                    )
                )

        result = calculate_pnl(
            symbol=symbol_v,
            side=side_v,
            qty=qty,
            entry=Decimal(str(entry)),
            target=Decimal(str(target)),
            stop=Decimal(str(stop)),
            fees_open=Decimal(str(fees_open)),
            fees_close=Decimal(str(fees_close)),
            slippage_open=Decimal(str(slip_open)),
            slippage_close=Decimal(str(slip_close)),
            energy_kwh=Decimal(str(energy_kwh)),
            margin_loans=loans_list,
            tax_mode=tax_mode_v,
            st_rate=Decimal(str(st_rate)),
            lt_rate=Decimal(str(lt_rate)),
        )

        typer.echo(f"\n{symbol_v} {side_v.upper()} P&L Analysis")
        typer.echo(f"  Entry:        {result.entry}")
        typer.echo(f"  Target:       {result.target}")
        typer.echo(f"  Stop:         {result.stop}")
        typer.echo(f"  Qty:          {result.qty}")
        typer.echo("\n  Gross P&L:")
        typer.echo(f"    Win:        ${result.gross_win:,.2f}")
        typer.echo(f"    Loss:       ${result.gross_loss:,.2f}")
        typer.echo("\n  Costs:")
        breakdown = result.breakdown
        typer.echo(f"    Fees Open:  ${breakdown.get('fees_open', Decimal('0')):,.2f}")
        typer.echo(f"    Fees Close: ${breakdown.get('fees_close', Decimal('0')):,.2f}")
        typer.echo(f"    Total Fees: ${breakdown.get('total_fees_slippage', Decimal('0')):,.2f}")
        typer.echo(f"    Energy:     ${breakdown.get('energy_cost', Decimal('0')):,.2f}")
        typer.echo(f"    Margin Int: ${breakdown.get('margin_interest', Decimal('0')):,.2f}")
        typer.echo(f"    Tax (win):  ${breakdown.get('tax_on_win', Decimal('0')):,.2f}")
        typer.echo("\n  Net P&L:")
        typer.echo(f"    Win:        ${result.net_win_scenario:,.2f}")
        typer.echo(f"    Loss:       ${result.net_loss_scenario:,.2f}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


if __name__ == "__main__":
    app()
