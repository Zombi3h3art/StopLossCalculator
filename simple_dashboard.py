"""Stop Loss Calculator Dashboard - Two-column layout for instant results."""

from decimal import Decimal

import streamlit as st

from src.stoploss.contracts import get_contract
from src.stoploss.simple_sizing import calculate_stop_loss
from src.stoploss.sizing import size_by_percent_stop

# See CSS custom properties below for color definitions

st.set_page_config(
    page_title="Stop Loss Calculator",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """

    <style>
    :root {
        --primary: #1A365D;
        --secondary: #718096;
        --accent: #3182CE;
        --neutral-light: #F7FAFC;
        --neutral-mid: #E2E8F0;
        --text: #2D3748;
        --text-dark: #1A202C;
    }

    /* Typography */
    h1 {
        font-family: 'Source Serif 4', Georgia, serif;
        font-weight: 600;
        color: var(--primary);
        font-size: 2rem;
        margin-bottom: 1rem;
    }

    h3 {
        font-family: 'Source Sans 3', sans-serif;
        font-weight: 600;
        color: var(--primary);
        font-size: 1.1rem;
        margin-bottom: 0.75rem;
    }

    .stMetric {
        text-align: center;
    }

    /* Trade Summary Card - Flat bordered design */
    .trade-summary {
        background-color: var(--neutral-light);
        padding: 1.5rem;
        border: 1px solid var(--secondary);
        border-radius: 4px;
        color: #2C3E50;
    }

    .summary-header {
        font-family: 'Source Sans 3', sans-serif;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--secondary);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--secondary);
    }

    .summary-row {
        display: flex;
        justify-content: space-between;
        margin: 0.6rem 0;
        font-size: 0.95rem;
    }

    .summary-label {
        color: var(--secondary);
        font-weight: 500;
    }

    .summary-value {
        font-weight: 600;
        color: #2C3E50;
    }

    .summary-divider {
        border-top: 1px solid var(--secondary);
        margin: 0.75rem 0;
        padding-top: 0.75rem;
    }

    .summary-highlight {
        font-weight: 600;
        color: var(--primary);
    }

    .summary-loss {
        color: var(--text-dark);
        font-weight: 600;
    }

    /* Stop Price Highlight - Accent color */
    .stop-price-highlight {
        background-color: var(--neutral-light);
        padding: 1.25rem;
        border: 1px solid var(--accent);
        border-left: 3px solid var(--accent);
        border-radius: 4px;
        font-family: 'Source Sans 3', sans-serif;
        font-weight: 600;
        font-size: 1.5rem;
        text-align: center;
        color: var(--primary);
    }

    .stop-label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--accent);
        margin-bottom: 0.5rem;
    }

    /* Input Container - Bordered, no fill */
    .input-container {
        background-color: transparent;
        padding: 0.5rem 0;
        border: 1px solid var(--neutral-mid);
        border-radius: 4px;
        margin-bottom: 0.5rem;
    }

    /* Risk Summary Bar */
    .risk-bar {
        background-color: transparent;
        padding: 0.75rem 1rem;
        border: 1px solid var(--secondary);
        border-radius: 4px;
        font-family: 'Source Sans 3', sans-serif;
    }

    .risk-bar strong {
        color: var(--primary);
    }

    .risk-bar .risk-amount {
        color: var(--text-dark);
        font-weight: 600;
    }

    /* Empty State */
    .empty-state {
        background-color: var(--neutral-light);
        padding: 2rem;
        border: 1px solid var(--secondary);
        border-radius: 4px;
        text-align: center;
    }

    .empty-state h3 {
        color: var(--primary);
        margin-bottom: 0.5rem;
    }

    .empty-state p {
        color: var(--secondary);
        font-size: 0.9rem;
    }

    /* Direction Labels - Non-color dependent with accessibility */
    .direction-long {
        color: var(--primary);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .direction-long::before {
        content: "▲ ";
        aria-hidden: true;
        font-size: 0.8em;
    }

    .direction-short {
        color: var(--text-dark);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .direction-short::before {
        content: "▼ ";
        aria-hidden: true;
        font-size: 0.8em;
    }

    /* Screen reader only text */
    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }

    /* Section Labels */
    .section-label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--secondary);
        margin-bottom: 0.5rem;
    }

    /* Footer */
    .footer {
        color: var(--secondary);
        font-size: 0.85rem;
        line-height: 1.6;
    }

    .footer strong {
        color: var(--primary);
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

    # Track symbol for futures mode
    symbol = "ES"  # Default

    if mode == "Futures (Precision)":
        symbol = st.selectbox("Contract", ["ES", "NQ", "CL", "GC"])

        contract = get_contract(symbol)
        st.caption(f"Tick: {contract.min_tick} | Point Value: ${contract.point_value}")

    st.markdown('<div class="input-container">', unsafe_allow_html=True)

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

    # Direction - clean labels
    try:
        direction = st.segmented_control(
            "Direction",
            options=["long", "short"],
            selection_mode="single",
            format_func=lambda x: "Long" if x == "long" else "Short",
        )
    except AttributeError:
        # Fallback for older Streamlit versions
        direction = st.radio(
            "Direction",
            options=["long", "short"],
            format_func=lambda x: "Long" if x == "long" else "Short",
            horizontal=True,
        )

    side = direction if direction else "long"

    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    trade_amount = st.number_input(
        "Account Equity / Trade Amount ($)",
        min_value=1.0,
        step=100.0,
        value=10000.0 if mode == "Futures (Precision)" else 100.0,
        help="Total cash available for this trade setup",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    leverage = st.number_input(
        "Leverage",
        min_value=1,
        max_value=500,
        step=1,
        value=10,
        help="How much you're amplifying (10x, 100x, etc)",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    risk_pct = st.number_input(
        "Acceptable Loss (% of Equity)",
        min_value=0.01,
        max_value=100.0,
        value=1.0 if mode == "Futures (Precision)" else 9.0,
        step=0.1,
        help="Max % of trade amount to risk",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Risk summary bar
    risk_dollars = trade_amount * risk_pct / 100
    st.markdown(
        f"""
        <div class="risk-bar">
        Leverage: <strong>{leverage}X</strong> | Risk: <span class="risk-amount">${risk_dollars:.2f}</span>
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

            formula_desc = f"Stop = Entry * (1 {'+ ' if side == 'short' else '- '}{allowed_move_pct / 100:.6f})"

        else:  # Futures Mode
            # Stop Distance % = (Risk % of Equity) / Leverage
            # e.g. 1% risk / 10x lev = 0.1% stop distance
            pct_stop_decimal = (Decimal(str(risk_pct)) / Decimal("100")) / Decimal(str(leverage))
            # Risk budget in dollars: the most this trade is allowed to lose
            risk_budget = Decimal(str(trade_amount)) * Decimal(str(risk_pct)) / Decimal("100")

            try:
                fs_result = size_by_percent_stop(
                    symbol=symbol,
                    side=side,
                    entry=Decimal(str(ticker_price)),
                    account_equity=Decimal(str(trade_amount)),
                    leverage=Decimal(str(leverage)),
                    pct_stop=pct_stop_decimal,
                    risk_cash=risk_budget,
                )

                stop_price = fs_result.stop_price
                # Re-calculate actual allowed move based on rounded stop
                dist = abs(fs_result.entry - fs_result.stop_price)
                allowed_move_pct = (dist / fs_result.entry) * 100

                qty = fs_result.qty
                # Honest numbers: what the position actually risks and controls
                max_loss = Decimal(qty) * fs_result.risk_dollars_per_contract
                notional = Decimal(qty) * fs_result.entry * contract.point_value

                formula_desc = (
                    "Risk-first sizing: Qty = min(floor(risk_budget / risk_per_contract), "
                    "floor(equity * leverage / (entry * point_value))). "
                    "Stop rounded to nearest tick."
                )

                if fs_result.capped_by_buying_power:
                    st.info(
                        f"**Buying-power cap**: equity x leverage affords "
                        f"{fs_result.buying_power_qty_cap} contract(s); the risk budget "
                        f"alone would allow more. Max loss shown reflects the capped size."
                    )

            except ValueError as e:
                st.error(f"Calculation Error: {e}")
                st.stop()

        # TRADE SUMMARY CARD - Flat bordered design
        direction_label = (
            '<span class="direction-long">LONG</span>'
            if side == "long"
            else '<span class="direction-short">SHORT</span>'
        )
        direction_arrow = "↑" if side == "short" else "↓"

        st.markdown(
            f"""
            <div class="trade-summary">
                <div class="summary-header">Trade Summary</div>
                <div class="summary-row">
                    <span class="summary-label">Entry Price</span>
                    <span class="summary-value">${ticker_price:.4f}</span>
                </div>
                <div class="summary-row">
                    <span class="summary-label">Direction</span>
                    <span class="summary-value">{direction_label}</span>
                </div>
                <div class="summary-row">
                    <span class="summary-label">Leverage</span>
                    <span class="summary-value">{leverage}X</span>
                </div>
                <div class="summary-row summary-divider">
                    <span class="summary-label">Stop Loss Price</span>
                    <span class="summary-value summary-highlight">${stop_price:.4f}</span>
                </div>
                <div class="summary-row">
                    <span class="summary-label">Allowed Move</span>
                    <span class="summary-value">{direction_arrow} {allowed_move_pct:.4f}%</span>
                </div>
                <div class="summary-row">
                    <span class="summary-label">Max Loss</span>
                    <span class="summary-value summary-loss">${max_loss:.2f}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # STOP PRICE - Copyable highlight with accent border
        st.markdown('<div class="stop-label">Stop Price</div>', unsafe_allow_html=True)
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
                f"**High Leverage**: At {leverage}x, stop is {allowed_move_pct:.4f}% away. "
                f"Consider lower leverage for reliability.",
            )

        # Show the math
        st.markdown("### 📐 Calculation")
        st.markdown(formula_desc)

        if mode == "Futures (Precision)":
            st.info(
                f"**Tick Rounding Applied**: Stop price is rounded to the nearest {contract.min_tick} tick for {symbol}."
            )

    else:
        st.markdown(
            """
            <div class="empty-state">
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
    <div class="footer">
    <strong>How it works:</strong><br>
    • Enter your ticker price, direction, and trade amount<br>
    • Set your leverage and acceptable loss percentage<br>
    • Stop price calculates instantly on the right<br>
    <strong>Formula:</strong> allowed_move% = (acceptable_risk% ÷ leverage)
    </div>
    """,
    unsafe_allow_html=True,
)
