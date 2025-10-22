# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
