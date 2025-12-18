"""Simplified Stop Loss Calculator Dashboard - Two-column layout for instant results."""

from decimal import Decimal

import streamlit as st

from src.stoploss.contracts import get_contract
from src.stoploss.simple_sizing import calculate_stop_loss
from src.stoploss.sizing import size_by_percent_stop

st.set_page_config(
    page_title="Stop Loss Calculator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stMetric { text-align: center; }
    .trade-summary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    .summary-row {
        display: flex;
        justify-content: space-between;
        margin: 0.8rem 0;
        font-size: 1.1rem;
    }
    .summary-label {
        opacity: 0.9;
        font-weight: 500;
    }
    .summary-value {
        font-weight: bold;
        font-size: 1.2rem;
    }
    .stop-price-highlight {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff6b6b;
        font-weight: bold;
        font-size: 1.3rem;
        text-align: center;
        color: #d32f2f;
    }
    .input-highlight {
        background-color: #e3f2fd;
        padding: 0.5rem;
        border-radius: 0.5rem;
        border-left: 3px solid #2196f3;
    }
    .metric-box {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 0.5rem;
        border-top: 3px solid #667eea;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🎯 Stop Loss Calculator")

# Mode Selection
mode = st.radio(
    "Calculator Mode",
    ["Simple / Generic", "Futures (Precision)"],
    horizontal=True,
    help="Choose 'Futures' for ES/NQ/CL/GC with tick rounding.",
)

# Two-column layout
left_col, right_col = st.columns([1, 1], gap="large")

# LEFT COLUMN: INPUTS
with left_col:
    st.markdown("### 📝 Trade Details")

    if mode == "Futures (Precision)":
        st.markdown('<div class="input-highlight">', unsafe_allow_html=True)
        symbol = st.selectbox("Contract", ["ES", "NQ", "CL", "GC"])
        st.markdown("</div>", unsafe_allow_html=True)

        contract = get_contract(symbol)
        st.caption(f"Tick: {contract.min_tick} | Point Value: ${contract.point_value}")

    st.markdown('<div class="input-highlight">', unsafe_allow_html=True)

    # Calculate step value safely
    step_value = 0.01
    if mode == "Futures (Precision)" and symbol in ["ES", "NQ"]:
        step_value = 0.25

    ticker_price = st.number_input(
        "Entry Price",
        min_value=0.0001,
        step=step_value,
        format="%.4f",
        help="Current price of the asset",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Direction with color
    try:
        direction = st.segmented_control(
            "Direction",
            options=["long", "short"],
            selection_mode="single",
            format_func=lambda x: ("🟢 Buy / Long" if x == "long" else "🔴 Sell / Short"),
        )
    except AttributeError:
        # Fallback for older Streamlit versions
        direction = st.radio(
            "Direction",
            options=["long", "short"],
            format_func=lambda x: ("🟢 Buy / Long" if x == "long" else "🔴 Sell / Short"),
            horizontal=True,
        )

    side = direction if direction else "long"

    st.markdown('<div class="input-highlight">', unsafe_allow_html=True)
    trade_amount = st.number_input(
        "Account Equity / Trade Amount ($)",
        min_value=1.0,
        step=100.0,
        value=10000.0 if mode == "Futures (Precision)" else 100.0,
        help="Total cash available for this trade setup",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="input-highlight">', unsafe_allow_html=True)
    leverage = st.number_input(
        "Leverage",
        min_value=1,
        max_value=500,
        step=1,
        value=10,
        help="How much you're amplifying (10x, 100x, etc)",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="input-highlight">', unsafe_allow_html=True)
    risk_pct = st.number_input(
        "Acceptable Loss (% of Equity)",
        min_value=0.01,
        max_value=100.0,
        value=1.0 if mode == "Futures (Precision)" else 9.0,
        step=0.1,
        help="Max % of trade amount to risk",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Display leverage visually with color
    risk_dollars = trade_amount * risk_pct / 100
    st.markdown(
        f"""
        <div style="background-color: #e8f5e9; padding: 1rem; border-radius: 0.5rem; border-left: 3px solid #4caf50;">
        <strong>📊 Leverage: {leverage}X</strong> | Risk: <strong style="color: #d32f2f;">${risk_dollars:.2f}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

# RIGHT COLUMN: RESULTS
with right_col:
    # Calculate
    if ticker_price > 0 and trade_amount > 0 and leverage > 0 and risk_pct > 0:
        if mode == "Simple / Generic":
            result = calculate_stop_loss(
                entry_price=ticker_price,
                side=side,
                account_equity=trade_amount,
                leverage=leverage,
                acceptable_risk_pct=risk_pct,
            )

            stop_price = result.stop_price
            allowed_move_pct = result.allowed_adverse_move_pct
            max_loss = result.max_loss_dollars
            notional = result.notional_exposure
            qty = result.quantity

            formula_desc = f"Stop = Entry × (1 {'+ ' if side == 'short' else '- '}{allowed_move_pct / 100:.6f})"

        else:  # Futures Mode
            # Convert Risk % of Equity to Stop Distance %
            # Stop Distance % = (Risk % of Equity) / Leverage
            # e.g. 1% risk / 10x lev = 0.1% stop distance
            pct_stop_decimal = (Decimal(str(risk_pct)) / Decimal("100")) / Decimal(str(leverage))

            try:
                fs_result = size_by_percent_stop(
                    symbol=symbol,
                    side=side,
                    entry=Decimal(str(ticker_price)),
                    account_equity=Decimal(str(trade_amount)),
                    leverage=Decimal(str(leverage)),
                    pct_stop=pct_stop_decimal,
                )

                stop_price = fs_result.stop_price
                # Re-calculate actual allowed move based on rounded stop
                dist = abs(fs_result.entry - fs_result.stop_price)
                allowed_move_pct = (dist / fs_result.entry) * 100

                max_loss = fs_result.risk_cash  # This includes fees if any, but here 0
                notional = fs_result.gross_exposure
                qty = fs_result.qty

                formula_desc = (
                    "Stop rounded to nearest tick. Qty = floor(Exposure / (Entry × PointValue))"
                )

            except ValueError as e:
                st.error(f"Calculation Error: {e}")
                st.stop()

        # TRADE SUMMARY CARD - Beautiful gradient card
        st.markdown(
            f"""
            <div class="trade-summary">
                <div style="font-size: 1.4rem; font-weight: bold; margin-bottom: 1rem;">TRADE SUMMARY</div>
                <div class="summary-row">
                    <span class="summary-label">Entry Price:</span>
                    <span class="summary-value">${ticker_price:.4f}</span>
                </div>
                <div class="summary-row">
                    <span class="summary-label">Direction:</span>
                    <span class="summary-value">{"🟢 BUY / LONG" if side == "long" else "🔴 SELL / SHORT"}</span>
                </div>
                <div class="summary-row">
                    <span class="summary-label">Leverage:</span>
                    <span class="summary-value">{leverage}X</span>
                </div>
                <div class="summary-row" style="border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.8rem; margin-top: 0.8rem;">
                    <span class="summary-label">Stop Loss Price:</span>
                    <span class="summary-value">${stop_price:.4f}</span>
                </div>
                <div class="summary-row">
                    <span class="summary-label">Allowed Move:</span>
                    <span class="summary-value">{"↑" if side == "short" else "↓"} {allowed_move_pct:.4f}%</span>
                </div>
                <div class="summary-row">
                    <span class="summary-label">Max Loss:</span>
                    <span class="summary-value" style="color: #ff6b6b;">${max_loss:.2f}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # COPYABLE STOP PRICE - Highlight for easy copying
        st.markdown("### 📋 Copy Your Stop Price")
        st.markdown(
            f'<div class="stop-price-highlight">${stop_price:.4f}</div>',
            unsafe_allow_html=True,
        )

        # POSITION DETAILS
        st.markdown("### 📊 Position Details")
        col3, col4 = st.columns(2)
        with col3:
            st.metric("Notional Exposure", f"${notional:,.0f}")
            st.metric("Max Risk ($)", f"${max_loss:.2f}")
        with col4:
            st.metric("Units Controlled", f"{qty:.2f}")
            # Risk/Leverage Ratio
            ratio = risk_pct / leverage
            st.metric("Risk/Leverage Ratio", f"{ratio:.4f}%")

        # Warning for extreme leverage
        if leverage > 100:
            st.warning(
                f"⚠️ **High Leverage**: At {leverage}x, stop is {allowed_move_pct:.4f}% away. "
                f"Consider lower leverage for reliability.",
                icon="⚠️",
            )

        # Show the math
        st.markdown("### 📐 The Formula")
        st.markdown(formula_desc)

        if mode == "Futures (Precision)":
            st.info(
                f"ℹ️ **Tick Rounding Applied**: Stop price is rounded to the nearest {contract.min_tick} tick for {symbol}."
            )

    else:
        st.markdown(
            """
            <div style="background-color: #e3f2fd; padding: 2rem; border-radius: 1rem; text-align: center; border-left: 4px solid #2196f3;">
            <h3>👈 Enter Trade Details</h3>
            <p>Fill in the left column to see your stop loss calculation</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# FOOTER
st.markdown("---")
st.markdown(
    """
    **How it works:**
    - Enter your ticker price, direction, and trade amount
    - Set your leverage and acceptable loss percentage
    - Stop price calculates instantly on the right
    - **Formula**: allowed_move% = (acceptable_risk% ÷ leverage)
    """
)
