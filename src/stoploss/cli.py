"""CLI for stop-loss calculator (Typer)."""

from decimal import Decimal

import typer

app = typer.Typer(help="Stop Loss Net Edge: Precision futures calculator with full cost accounting")


@app.command()
def size(
    symbol: str = typer.Option(..., "--symbol", help="Contract: ES, NQ, CL, GC"),
    side: str = typer.Option(..., "--side", help="long or short"),
    entry: float = typer.Option(..., "--entry", help="Entry price"),
    equity: float = typer.Option(..., "--equity", help="Account equity ($)"),
    leverage: float = typer.Option(1.0, "--leverage", help="Leverage multiplier"),
    pct_stop: float = typer.Option(None, "--pct-stop", help="Stop as % of entry (e.g., 0.004)"),
    risk: float = typer.Option(None, "--risk", help="Max risk in dollars"),
    fees_open: float = typer.Option(0, "--fees-open", help="Opening fee ($)"),
    fees_close: float = typer.Option(0, "--fees-close", help="Closing fee ($)"),
    slip_open: float = typer.Option(0, "--slip-open", help="Opening slippage ($)"),
) -> None:
    """Calculate position size and stop price."""
    from .sizing import size_by_percent_stop

    if pct_stop is None and risk is None:
        typer.echo("Error: specify either --pct-stop or --risk")
        raise typer.Exit(1)

    try:
        if pct_stop is not None:
            result = size_by_percent_stop(
                symbol=symbol,
                side=side,
                entry=Decimal(str(entry)),
                account_equity=Decimal(str(equity)),
                leverage=Decimal(str(leverage)),
                pct_stop=Decimal(str(pct_stop)),
                fees_open=Decimal(str(fees_open)),
                fees_close=Decimal(str(fees_close)),
                slip_open=Decimal(str(slip_open)),
            )
        else:
            typer.echo("ATR/structure sizing not yet implemented in CLI; use pct-stop")
            raise typer.Exit(1)

        typer.echo(f"\n{symbol} {side.upper()} Position")
        typer.echo(f"  Entry:        {result.entry}")
        typer.echo(f"  Qty:          {result.qty} contracts")
        typer.echo(f"  Stop:         {result.stop_price}")
        typer.echo(f"  Risk/unit:    {result.risk_per_unit}")
        typer.echo(f"  Risk$/ctr:    {result.risk_dollars_per_contract}")
        typer.echo(f"  Risk cash:    {result.risk_cash}")
        typer.echo(f"  Fees (open):  {result.fees_open}")
        typer.echo(f"  Fees (close): {result.fees_close}")
        typer.echo(f"  Method:       {result.method}")
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
            symbol=symbol,
            side=side,
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
            tax_mode=tax_mode,
            st_rate=Decimal(str(st_rate)),
            lt_rate=Decimal(str(lt_rate)),
        )

        typer.echo(f"\n{symbol} {side.upper()} P&L Analysis")
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
