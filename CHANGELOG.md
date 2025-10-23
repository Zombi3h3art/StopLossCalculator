# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-10-23

### Added

- **Simple Dashboard (`simple_dashboard.py`)**: New Streamlit UI with two-column layout
  - Trade summary card with gradient background showing entry, direction, leverage, stop price, allowed move, max loss
  - Copyable stop price section with highlight styling
  - Real-time calculations as inputs change
  - Position details with notional exposure, max risk, units controlled, risk/leverage ratio
- **Desktop Launcher Files**:
  - `Launch Stop Loss Calculator.bat` - Double-click to launch dashboard (Windows batch)
  - `Launch Stop Loss Calculator.ps1` - PowerShell launcher with auto-browser opening
- **Simple Sizing Module (`src/stoploss/simple_sizing.py`)**: Lightweight stop-loss calculator

### Changed

- **UI Focus**: Streamlit dashboard is now the primary interface (replaces `ui_app.py`)
- **Documentation**: Updated README to highlight dashboard usage with quick start guide
- **Project Structure**: Removed CLI and REST API from primary focus (still available in code)

### Removed

- `ui_app.py` - Replaced by `simple_dashboard.py`
- `validate_math.py` - Validation now handled by Pydantic schemas
- `leverage_analysis.py` - Analysis features not needed in primary interface
- Obsolete documentation files: `ALIGNMENT_REVIEW.md`, `IMPLEMENTATION_REPORT.md`, `PROJECT_SUMMARY.md`, `WHAT_YOU_BUILT.md`

### Documentation

- Rewrote README for clarity and trader focus
- Added desktop launcher instructions
- Simplified installation guide
- Better math formulas and examples
- Added disclaimer section

## [0.1.0] - 2024-10-22

### Added

- Core position sizing module (percent-stop and ATR/structure paths)
- Futures contract specifications (ES, NQ, CL, GC) with tick rounding
- P&L calculation with gross/net win and loss
- Federal income tax calculation (short-term ordinary and §1256 60/40)
- Margin loan interest (up to 3 loans, 360-day accrual)
- Energy cost estimation (EIA-based)
- SOFR reference rates and context
- Trading fees and slippage integration
- Initial project scaffold and documentation
- Math formulas reference in README

### Math-Affecting Changes

- **Initial**: All formulas match referenced sources (CME, IRS, EIA, Federal Reserve)
- **Decimal precision**: Uses Python `Decimal` for financial math accuracy

---

Changelog follows [Keep a Changelog](https://keepachangelog.com/).
