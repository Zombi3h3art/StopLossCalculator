"""
Stop Loss Net Edge Calculator

A precision financial calculator for futures trading with comprehensive accounting for:
- Position sizing and stop-loss calculations (percent and ATR/structure-based)
- Gross and net P&L including all costs
- Federal income taxes (short-term ordinary and §1256 60/40 for futures)
- Margin loan interest (up to 3 separate loans on 360-day accrual)
- Energy cost estimation (EIA data)
- Trading fees and slippage
- Contract-specific math (ES, NQ, CL, GC with proper tick rounding)

Supports CLI, REST API, and Streamlit UI.
"""

__version__ = "0.1.0"
