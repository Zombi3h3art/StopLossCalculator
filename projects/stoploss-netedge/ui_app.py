"""Interactive Streamlit UI for Stop Loss Calculator."""

import csv
import io
import json
from datetime import datetime
from decimal import Decimal

import streamlit as st

from src.stoploss.cashflow import calculate_pnl
from src.stoploss.schemas import MarginLoanInput, PnLInput, SizingInput
from src.stoploss.sizing import size_by_percent_stop


def setup_page():
    """Configure Streamlit page."""
    st.set_page_config(
        page_title="Stop Loss Calculator",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .metric-box { background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; }
        .win-color { color: #0d9e0d; font-weight: bold; }
        .loss-color { color: #d61e1e; font-weight: bold; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def sizing_panel():
    """Left panel: Position sizing inputs and results."""
    st.header("📍 Position Sizing")

    col1, col2 = st.columns(2)

    with col1:
        symbol = st.selectbox("Contract", ["ES", "NQ", "CL", "GC"], key="sizing_symbol")
        side = st.radio("Side", ["long", "short"], horizontal=True, key="sizing_side")
        entry = st.number_input(
            "Entry Price",
            min_value=0.0,
            value=5050.00,
            step=0.01,
            key="sizing_entry",
        )
        account_equity = st.number_input(
            "Account Equity ($)",
            min_value=0.0,
            value=20000.00,
            step=100.0,
            key="sizing_equity",
        )

    with col2:
        leverage = st.number_input(
            "Leverage",
            min_value=1.0,
            value=1.0,
            step=0.5,
            key="sizing_leverage",
        )
        pct_stop = st.number_input(
            "Stop Loss % (0.004 = 0.4%)",
            min_value=0.0,
            value=0.004,
            step=0.001,
            key="sizing_pct_stop",
        )
        fees_open = st.number_input(
            "Opening Fee ($)",
            min_value=0.0,
            value=2.0,
            step=1.0,
            key="sizing_fees_open",
        )
        fees_close = st.number_input(
            "Closing Fee ($)",
            min_value=0.0,
            value=2.0,
            step=1.0,
            key="sizing_fees_close",
        )

    # Calculate sizing
    try:
        sizing_input = SizingInput(
            symbol=symbol,
            side=side,
            entry=Decimal(str(entry)),
            account_equity=Decimal(str(account_equity)),
            leverage=Decimal(str(leverage)),
            pct_stop=Decimal(str(pct_stop)),
            fees_open=Decimal(str(fees_open)),
            fees_close=Decimal(str(fees_close)),
        )

        result = size_by_percent_stop(sizing_input)

        st.markdown("### Results")
        cols = st.columns(3)

        with cols[0]:
            st.metric("Qty", result.qty, delta=None)

        with cols[1]:
            st.metric("Entry", f"${float(result.entry_price):.2f}", delta=None)

        with cols[2]:
            st.metric("Stop", f"${float(result.stop_price):.2f}", delta=None)

        cols = st.columns(3)

        with cols[0]:
            st.metric("Loss/Unit", f"{float(result.loss_per_unit):.4f}", delta=None)

        with cols[1]:
            st.metric(
                "Loss ($)",
                f"${float(result.loss_dollars):.2f}",
                delta=None,
            )

        with cols[2]:
            st.metric(
                "Exposure",
                f"${float(result.gross_exposure):.0f}",
                delta=None,
            )

        # Store in session state for P&L calculation
        st.session_state.sizing_result = {
            "qty": result.qty,
            "entry": float(result.entry_price),
            "stop": float(result.stop_price),
            "symbol": symbol,
            "side": side,
        }

    except Exception as e:
        st.error(f"Sizing Error: {e!r}")


def pnl_panel():
    """Right panel: P&L scenario analysis."""
    st.header("💰 P&L Scenario Analysis")

    # Get sizing result or manual input
    if hasattr(st.session_state, "sizing_result"):
        sizing = st.session_state.sizing_result
        symbol = sizing["symbol"]
        side = sizing["side"]
        qty = sizing["qty"]
        entry = sizing["entry"]
        stop = sizing["stop"]
    else:
        col1, col2 = st.columns(2)
        with col1:
            symbol = st.selectbox("Contract", ["ES", "NQ", "CL", "GC"], key="pnl_symbol")
            side = st.radio("Side", ["long", "short"], horizontal=True, key="pnl_side")
            qty = st.number_input("Qty", min_value=1, value=1, key="pnl_qty")

        with col2:
            entry = st.number_input("Entry", min_value=0.0, value=5050.0, key="pnl_entry")
            stop = st.number_input("Stop", min_value=0.0, value=5029.75, key="pnl_stop")

    col1, col2 = st.columns(2)

    with col1:
        target = st.number_input(
            "Target (Win Price)",
            min_value=0.0,
            value=5100.0,
            step=0.25,
            key="pnl_target",
        )
        fees_open = st.number_input("Opening Fee ($)", value=2.0, key="pnl_fees_open")
        fees_close = st.number_input("Closing Fee ($)", value=2.0, key="pnl_fees_close")

    with col2:
        slip_open = st.number_input("Open Slippage ($)", value=0.0, key="pnl_slip_open")
        slip_close = st.number_input("Close Slippage ($)", value=0.0, key="pnl_slip_close")

    st.markdown("### Costs & Taxes")

    col1, col2, col3 = st.columns(3)

    with col1:
        tax_mode = st.selectbox(
            "Tax Mode",
            ["section_1256", "short_term_ordinary"],
            key="pnl_tax_mode",
        )
        st.write(f"📋 {tax_mode}")

    with col2:
        st.write("**Tax Rates**")
        st_rate = st.number_input(
            "ST Rate", min_value=0.0, max_value=1.0, value=0.24, step=0.01, key="pnl_st"
        )
        if tax_mode == "section_1256":
            lt_rate = st.number_input(
                "LT Rate", min_value=0.0, max_value=1.0, value=0.15, step=0.01, key="pnl_lt"
            )
        else:
            lt_rate = st_rate

    with col3:
        st.write("**Energy**")
        power_kw = st.number_input(
            "Power (kW)", min_value=0.0, value=0.2, step=0.05, key="pnl_power"
        )
        energy_rate = st.number_input(
            "Rate (¢/kWh)", min_value=0.0, value=14.0, step=1.0, key="pnl_energy_rate"
        )

    st.markdown("### Margin Loans (Optional)")

    num_loans = st.slider("Number of Margin Loans", 0, 3, 0, key="pnl_num_loans")

    margin_loans = []
    if num_loans > 0:
        for i in range(num_loans):
            with st.expander(f"Loan {i+1}", expanded=(i == 0)):
                col1, col2, col3 = st.columns(3)
                with col1:
                    loan_amt = st.number_input(
                        f"Amount Loan {i+1} ($)",
                        min_value=0.0,
                        value=5000.0,
                        key=f"pnl_loan_amt_{i}",
                    )
                with col2:
                    apr = st.number_input(
                        f"APR Loan {i+1} (%)",
                        min_value=0.0,
                        value=6.5,
                        step=0.1,
                        key=f"pnl_loan_apr_{i}",
                    ) / 100
                with col3:
                    days = st.number_input(
                        f"Days Loan {i+1}",
                        min_value=0,
                        value=1,
                        key=f"pnl_loan_days_{i}",
                    )

                margin_loans.append(
                    MarginLoanInput(
                        loan_amount=Decimal(str(loan_amt)),
                        apr=Decimal(str(apr)),
                        days_held=days,
                    )
                )

    # Calculate P&L
    try:
        pnl_input = PnLInput(
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
            power_kw=Decimal(str(power_kw)),
            energy_rate_cents=Decimal(str(energy_rate)),
            tax_mode=tax_mode,
            st_rate=Decimal(str(st_rate)),
            lt_rate=Decimal(str(lt_rate)) if tax_mode == "section_1256" else None,
            margin_loans=margin_loans,
        )

        result = calculate_pnl(pnl_input)

        st.markdown("### WIN Scenario")

        cols = st.columns(3)
        with cols[0]:
            st.metric("Gross Win", f"${float(result.gross_win):.2f}")
        with cols[1]:
            st.metric("Total Costs", f"${float(result.total_fees_slip):.2f}")
        with cols[2]:
            st.metric("Tax", f"${float(result.tax_on_win):.2f}")

        win_color = "green" if result.net_win > 0 else "red"
        net_win_msg = (
            f"### <span style='color:{win_color}'>"
            f"Net Win: ${float(result.net_win):.2f}</span>"
        )
        st.markdown(net_win_msg, unsafe_allow_html=True)

        st.markdown("### LOSS Scenario")

        cols = st.columns(3)
        with cols[0]:
            st.metric("Gross Loss", f"-${float(result.gross_loss):.2f}")
        with cols[1]:
            st.metric("Total Costs", f"${float(result.total_fees_slip):.2f}")
        with cols[2]:
            st.metric("Energy", f"${float(result.energy_cost):.2f}")

        loss_color = "red"
        net_loss = result.net_loss + result.total_fees_slip
        net_loss_msg = (
            f"### <span style='color:{loss_color}'>"
            f"Net Loss: -${float(net_loss):.2f}</span>"
        )
        st.markdown(net_loss_msg, unsafe_allow_html=True)

        # Margin interest display
        if result.margin_interest > 0:
            st.markdown("### Margin Costs")
            st.metric("Margin Interest", f"${float(result.margin_interest):.2f}")

        # Export button
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "input": pnl_input.model_dump(mode="json"),
            "win_scenario": {
                "gross_profit": float(result.gross_win),
                "total_costs": float(result.total_fees_slip),
                "tax": float(result.tax_on_win),
                "net_profit": float(result.net_win),
            },
            "loss_scenario": {
                "gross_loss": float(result.gross_loss),
                "total_costs": float(result.total_fees_slip),
                "margin_interest": float(result.margin_interest),
                "net_loss": float(net_loss),
            },
        }

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download JSON",
                data=json.dumps(export_data, indent=2),
                file_name=f"pnl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
            )
        with col2:
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Metric", "Win", "Loss"])
            writer.writerow(
                [
                    "Gross",
                    f"${float(result.gross_win):.2f}",
                    f"-${float(result.gross_loss):.2f}",
                ]
            )
            writer.writerow(
                [
                    "Costs",
                    f"${float(result.total_fees_slip):.2f}",
                    f"${float(result.total_fees_slip):.2f}",
                ]
            )
            writer.writerow(
                [
                    "Tax/Interest",
                    f"${float(result.tax_on_win):.2f}",
                    f"${float(result.margin_interest):.2f}",
                ]
            )
            writer.writerow(["NET", f"${float(result.net_win):.2f}", f"-${float(net_loss):.2f}"])

            st.download_button(
                label="📊 Download CSV",
                data=output.getvalue(),
                file_name=f"pnl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

    except Exception as e:
        st.error(f"P&L Error: {e!r}")


def main():
    """Main Streamlit app."""
    setup_page()

    st.title("🎯 Stop Loss Calculator")
    st.markdown(
        """
        **Futures Position Sizing & P&L Analysis**
        
        Calculate exact stop loss prices, position sizes, and scenario analysis
        with comprehensive cost accounting (fees, taxes, energy, margin interest).
        """
    )

    # Initialize session state
    if "sizing_result" not in st.session_state:
        st.session_state.sizing_result = None

    # Two-column layout
    col_sizing, col_pnl = st.columns(2)

    with col_sizing:
        sizing_panel()

    with col_pnl:
        pnl_panel()

    # Footer
    st.markdown("---")
    st.markdown(
        """
        **Sources:**
        - Contracts: CME Globex specifications
        - Taxes: IRS Form 6781 (§1256 60/40 split)
        - Energy: EIA Table 5.3 (14¢/kWh US average)
        - Margin: 360-day accrual (broker standard)
        """
    )


if __name__ == "__main__":
    main()
