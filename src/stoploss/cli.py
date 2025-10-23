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
            )
        else:
            typer.echo("ATR/structure sizing not yet implemented in CLI; use pct-stop")
            raise typer.Exit(1)

        typer.echo(f"\n{symbol} {side.upper()} Position")
        typer.echo(f"  Entry:        {result.entry_price}")
        typer.echo(f"  Qty:          {result.qty} contracts")
        typer.echo(f"  Stop:         {result.stop_price}")
        typer.echo(f"  Loss/unit:    {result.loss_per_unit}")
        typer.echo(f"  Gross loss:   ${result.loss_dollars:.2f}")
        typer.echo(f"  Method:       {result.method}")
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


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
    from .energy import estimate_energy_cost
    from .rates import MarginLoan, calculate_total_margin_interest
    from .taxes import calculate_tax

    try:
        # Calculate tax
        gross_profit = Decimal(str(abs(float(target) - float(entry)) * qty * 50))  # approx
        tax = calculate_tax(
            gross_profit,
            mode=tax_mode,
            st_rate=Decimal(str(st_rate)),
            lt_rate=Decimal(str(lt_rate)),
        )

        # Energy cost
        energy_cost = Decimal("0")
        if energy_kwh > 0:
            energy_cost = estimate_energy_cost(
                power_kw=Decimal("0.2"),  # default estimate
                hours_used=Decimal("1"),
                kwh_price_cents=Decimal("14"),
            )

        # Margin interest
        loans_list = []
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

        margin_int = calculate_total_margin_interest(loans_list) if loans_list else Decimal("0")

        result = calculate_pnl(
            symbol=symbol,
            side=side,
            qty=qty,
            entry=Decimal(str(entry)),
            target=Decimal(str(target)),
            stop=Decimal(str(stop)),
            fees_open=Decimal(str(fees_open)),
            fees_close=Decimal(str(fees_close)),
            slip_open=Decimal(str(slip_open)),
            slip_close=Decimal(str(slip_close)),
            energy_cost=energy_cost,
            margin_interest=margin_int,
            tax_on_win=tax,
        )

        typer.echo(f"\n{symbol} {side.upper()} P&L Analysis")
        typer.echo(f"  Entry:        {result.entry_price}")
        typer.echo(f"  Target:       {result.target_price}")
        typer.echo(f"  Stop:         {result.stop_price}")
        typer.echo(f"  Qty:          {result.qty}")
        typer.echo("\n  Gross P&L:")
        typer.echo(f"    Win:        ${result.gross_win:,.2f}")
        typer.echo(f"    Loss:       ${result.gross_loss:,.2f}")
        typer.echo("\n  Costs:")
        typer.echo(f"    Fees/Slip:  ${result.total_fees_slip:,.2f}")
        typer.echo(f"    Energy:     ${result.energy_cost:,.2f}")
        typer.echo(f"    Margin Int: ${result.margin_interest:,.2f}")
        typer.echo(f"    Tax (win):  ${result.tax_on_win:,.2f}")
        typer.echo("\n  Net P&L:")
        typer.echo(f"    Win:        ${result.net_win:,.2f}")
        typer.echo(f"    Loss:       ${result.net_loss:,.2f}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
