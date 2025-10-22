# Stop Loss Net Edge Calculator

Precision financial calculator for futures trading with comprehensive accounting for position sizing, stop-loss calculations, P&L, taxes, margin interest, and energy costs.

## Features

- **Contracts**: ES, NQ, CL, GC with proper point values and tick rounding
- **Sizing**: Percent-stop (risk-first) and ATR/structure-based stop calculations
- **P&L**: Gross and net profit/loss with all costs
- **Taxes**: Short-term ordinary income and §1256 60/40 split (Form 6781)
- **Margin**: Up to 3 separate loans with 360-day accrual interest
- **Energy**: EIA-based energy cost estimation
- **Fees**: Trading fees and slippage included
- **Interfaces**: CLI (Typer), REST API (FastAPI), UI (Streamlit)

## Installation

```bash
pip install stoploss-netedge
```

Or from source:

```bash
git clone https://github.com/yourusername/stoploss-netedge.git
cd stoploss-netedge
pip install -e ".[dev]"
```

## Quick Start

### CLI

Size an ES trade:

```bash
stoploss size --symbol ES --side long --entry 5050 \
  --equity 20000 --leverage 3 --pct-stop 0.004 \
  --risk 500 --fees-open 2 --fees-close 2
```

Calculate P&L for a hypothetical trade:

```bash
stoploss pnl --symbol ES --side long --entry 5050 --target 5100 --stop 5030 \
  --qty 2 --fees-open 2 --fees-close 2 \
  --tax-mode 1256 --st-rate 0.24 --lt-rate 0.15 \
  --energy-kwh 0.3 --loan 5000:0.065 --days 5
```

### Python API

```python
from decimal import Decimal
from stoploss.sizing import size_by_percent_stop
from stoploss.cashflow import calculate_pnl
from stoploss.taxes import calculate_tax

# Size a trade
size = size_by_percent_stop(
    symbol="ES",
    side="long",
    entry=Decimal("5050"),
    account_equity=Decimal("20000"),
    leverage=Decimal("3"),
    pct_stop=Decimal("0.004"),
)
print(f"Qty: {size.qty}, Stop: {size.stop_price}")

# Calculate P&L with taxes
tax = calculate_tax(
    gross_profit=Decimal("1000"),
    mode="section_1256",
    st_rate=Decimal("0.24"),
    lt_rate=Decimal("0.15"),
)

pnl = calculate_pnl(
    symbol="ES",
    side="long",
    qty=size.qty,
    entry=Decimal("5050"),
    target=Decimal("5100"),
    stop=size.stop_price,
    fees_open=Decimal("2"),
    fees_close=Decimal("2"),
    tax_on_win=tax,
)
print(f"Net Win: ${pnl.net_win}, Net Loss: ${pnl.net_loss}")
```

## Math Reference

### Position Sizing (Percent Stop, Risk-First)

$$\text{gross\_exposure} = \text{account\_equity} \times \text{leverage}$$

$$\text{loss\_per\_unit} = \text{entry} \times \text{pct\_stop}$$

$$\text{qty} = \left\lfloor \frac{\text{gross\_exposure}}{\text{entry} \times \text{ppv\_per\_unit}} \right\rfloor$$

$$\text{stop\_price} = \text{entry} - \text{loss\_per\_unit} \text{ (long)}$$

Stops are rounded to the nearest valid tick; loss is recomputed to keep risk honest.

### Gross P&L

$$\text{gross\_win} = \text{qty} \times \text{ppv} \times (\text{target} - \text{entry})$$

$$\text{gross\_loss} = \text{qty} \times \text{ppv} \times (\text{entry} - \text{stop})$$

### Costs

$$\text{total\_costs} = \text{fees\_open} + \text{fees\_close} + \text{slip\_open} + \text{slip\_close} + \text{energy} + \text{margin\_interest}$$

### Taxes (§1256 Futures)

$$\text{tax} = \text{gross\_profit} \times (0.60 \times \text{lt\_rate} + 0.40 \times \text{st\_rate})$$

### Net P&L

$$\text{net\_win} = \text{gross\_win} - \text{total\_costs} - \text{tax}$$

$$\text{net\_loss} = -(\text{gross\_loss} + \text{costs})$$

## Contract Specifications

| Symbol | PPV | Tick | Tick Value |
|--------|-----|------|-----------|
| ES     | $50 | 0.25 | $12.50    |
| NQ     | $20 | 0.25 | $5.00     |
| CL     | $1000 | $0.01 | $10.00 |
| GC     | $100 | $0.10 | $10.00 |

## Worked Example: ES Long Trade

**Inputs:**
- Symbol: ES
- Side: long
- Entry: 5050.00
- Account equity: $20,000
- Leverage: 3.0
- Pct stop: 0.4% (40 basis points)
- Risk: $500
- Fees: $2 open, $2 close
- Energy: 0.3 kWh @ 14¢
- 1 margin loan: $5,000 @ 6.5% APR for 3 days
- Tax mode: §1256 (60/40)
- ST rate: 24%, LT rate: 15%

**Calculations:**

1. **Position Size**
   - Gross exposure: $20,000 × 3 = $60,000
   - Loss per unit: 5050 × 0.004 = 20.2 pts
   - Qty: floor(60,000 / (5050 × 50)) = floor(0.237) = **can't sustain; size by risk instead**
   
   **Size by risk:**
   - Risk cash: $500
   - Qty: (500 - 2) / (50 × 20.2) ≈ 0.49 → **Use 1 contract (or 0.5 MES)**
   - Stop: 5050 - 20.2 = **5029.8 → round to 5029.75 (nearest 0.25 tick)**

2. **Gross P&L (win scenario, target 5100)**
   - Gross win: 1 × 50 × (5100 - 5050) = **$2,500**
   - Gross loss: 1 × 50 × (5050 - 5029.75) = **$1,012.50**

3. **Costs**
   - Fees/slip: 2 + 2 = $4
   - Energy: 0.3 kWh × 14¢ = 4.2¢ = **$0.04**
   - Margin: 5000 × 0.065 × (3/360) = **$2.71**
   - Total: **$6.75**

4. **Tax on Win**
   - Gross: $2,500 - $4 = $2,496
   - Tax: 2496 × (0.60 × 0.15 + 0.40 × 0.24) = 2496 × 0.186 = **$464.66**

5. **Net P&L**
   - Net win: 2,500 - 4 - 0.04 - 2.71 - 464.66 = **$2,028.59**
   - Net loss: -(1,012.50 + 4 + 0.04 + 2.71) = **-$1,019.25**

## Tax References

- **IRS Pub 550** (Investment Income & Expenses): https://www.irs.gov/publications/p550
- **IRS Form 6781** (§1256 Contracts): https://www.irs.gov/forms/about-form-6781
- **60/40 Split**: 60% of gains taxed at LTCG rate, 40% at ordinary ST rate

## Energy Estimation

- **Data**: EIA Table 5.3 (Electric Power Monthly)
- **Typical US residential**: ~14¢/kWh (2024 average)
- **Desktop setup**: 0.15–0.35 kW depending on configuration

Reference: https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=epmt_5_3

## Margin Interest

- **Basis**: 360-day year (broker standard)
- **Formula**: interest = principal × APR × (days / 360)
- **Accrual**: Daily, billed monthly
- **Reference**: Schwab, IBKR, etc.

## SOFR Reference

- **Current rate** (Oct 2024): ~5.33% p.a.
- **Brokers peg to**: SOFR + spread (e.g., +150 bps = 6.83%)
- **Source**: Federal Reserve Bank of New York
- **Link**: https://www.newyorkfed.org/markets/reference-rates/sofr

## Limitations & Assumptions

### Tax Calculation Limitations

1. **Daily Trading Tax Wash Sales**
   - Wash sale rules (IRS Sec 1091) are NOT calculated. In futures, you must manually track wash sales with other positions in the same *contract* if closed at a loss and re-entered within 30 days.
   - **Recommendation**: Use tax software (e.g., TurboTax for traders) to detect wash sales across your full portfolio.

2. **No State/Local Income Tax**
   - This calculator includes **US federal taxes only** (Form 6781 for §1256 or ordinary income).
   - State income taxes (CA, NY, IL, etc.) vary 1–13% and must be added separately based on your state.
   - Futures may qualify for special treatment in some states (e.g., Illinois has no income tax on §1256 gains).

3. **Section §1256 Futures Only**
   - 60% long-term / 40% short-term split applies ONLY to:
     - Exchange-traded futures (ES, NQ, CL, GC ✓)
     - NOT to options, forex, or crypto
   - Per-trade basis: Each win/loss is segregated 60/40, not netted annually.

4. **No Tax Credits or Deductions**
   - Does NOT calculate:
     - Trader status mark-to-market (MTM) election
     - Home office deduction
     - Margin interest deduction (partial via Sch B)
     - Depreciation
     - Vehicle/equipment costs
   - These are valuable but require tax professional input.

### Margin Loan Cascading

Up to **3 separate margin loans** are supported, calculated sequentially for 360-day accrual:

#### All 3 loans filled example

```python
loans = [
    MarginLoanInput(loan_amount=5000, apr=0.065, days_held=5),   # Loan 1: Reg T (6.5%)
    MarginLoanInput(loan_amount=3000, apr=0.085, days_held=3),   # Loan 2: Short rebate tier (8.5%)
    MarginLoanInput(loan_amount=2000, apr=0.120, days_held=1),   # Loan 3: Emergency (12%)
]

# Total margin interest for 5 days:
# Loan 1: 5000 × 0.065 × (5/360) = $4.51
# Loan 2: 3000 × 0.085 × (3/360) = $2.13
# Loan 3: 2000 × 0.120 × (1/360) = $0.67
# Total: $7.31
```

Brokers with cascading tiers:

- **Interactive Brokers**: Reg T (IBKR base), then Portfolio Margin excess
- **Schwab/E*TRADE**: Tiered by account size and balance
- **Tradovate**: Flat rate (no cascade)

### Contract Limits & Assumptions

| Contract | PPV | Tick | Min Stop (points) | RTH Hours | Margin (Reg T) |
|----------|-----|------|-------------------|-----------|----------------|
| ES       | 50  | 0.25 | 2–5               | 9:30–16:00 EST | $500–$1500 |
| NQ       | 20  | 0.25 | 2–5               | 9:30–16:00 EST | $1000–$3000 |
| CL       | 100 | 0.01 | 0.5–2.0           | 17:00–16:00 CT | $3000–$5000 |
| GC       | 100 | 0.10 | 2–5               | 17:00–16:00 NY | $3000–$5000 |

**Assumptions:**

- **No CME holidays** applied (exchange closed).
- **RTH (Regular Trading Hours) only**. Overnight/weekend sessions not modeled.
- **Margin requirement** is static (actual requirement varies by broker and market conditions).
- **No gap risk** over weekends/holidays.
- **Slippage** is user-provided; actual market impact not calculated.

### SOFR & Margin APR Context

**Fed Funds Effective Rate vs. SOFR:**

- **Fed Funds (Old)**: 2008–2023, manual administered rate
- **SOFR (Secured Overnight Financing Rate)**: April 2023+, overnight repo-based rate
  - Less volatile, more transparent than Fed Funds
  - Brokers lag SOFR by 30–60 bps, then add spread

**Example (as of Oct 2024):**

```text
SOFR (overnight): 5.33% p.a.
Broker markup: +150 bps = 6.83% APR (typical retail)
Interactive Brokers: SOFR + 25 bps = 5.58% (tightest)
Schwab: SOFR + 100 bps = 6.33%
```

**To get live SOFR:**

- [Federal Reserve SOFR rates](https://www.newyorkfed.org/markets/reference-rates/sofr)
- Your broker's margin rates API (if available)

---

## Running the UI

### Streamlit Web App

```bash
# Install dependencies
pip install streamlit pydantic fastapi

# Run the interactive calculator
streamlit run ui_app.py
```

Open [`http://localhost:8501`](http://localhost:8501) in your browser. Two-panel layout:

- **Left**: Position sizing (symbol, entry, stop loss %)
- **Right**: P&L scenarios (win/loss analysis, taxes, margin costs)
- **Export**: JSON or CSV for record-keeping

---

## Development

### Testing

```bash
pytest tests/ -v
```

With coverage:

```bash
pytest tests/ --cov=stoploss --cov-report=html
```

### Code Quality

```bash
ruff check src/
black --check src/
mypy src/
```

Auto-fix:

```bash
ruff check --fix src/
black src/
```

### Build & Release

```bash
# Build wheel
python -m build

# Release to PyPI (requires token)
twine upload dist/*
```

## Roadmap

- [x] Core math (sizing, P&L, taxes, margin)
- [x] CLI with Typer
- [ ] FastAPI REST API
- [ ] Streamlit UI
- [ ] Live EIA/SOFR fetch + caching
- [ ] GitHub Actions CI/CD
- [ ] Comprehensive test suite (>90% coverage)
- [ ] Math whitepaper with derivations
- [ ] Contract futures data for CME holidays/RTH

## License

MIT

## References

**Scripture anchors (KJV):**

- Luke 14:28 — "For which of you, intending to build a tower, sitteth not down first, and counteth the cost, whether he have sufficient to finish it?"
- Proverbs 11:1 — "A false balance is abomination to the LORD: but a just weight is his delight."
- Ecclesiastes 3:1 — "To every thing there is a season, and a time to every purpose under the heaven."

---

**Disclaimer:** This calculator is for educational and planning purposes. It does not constitute investment advice. Always consult a tax professional and risk manager before trading. Past performance does not guarantee future results.
