# Worked Examples: All 4 Contracts

Complete JSON examples for ES, NQ, CL, and GC trades with sizing, P&L, taxes, and margin interest.

## Example 1: ES Swing Trade (Long, §1256 Taxes)

**Scenario**: E-mini S&P 500 swing trade, 2-day hold, targeting $50 profit per contract

### API Request (Sizing)

```json
{
  "symbol": "ES",
  "side": "long",
  "entry": "5050.00",
  "account_equity": "25000.00",
  "leverage": "2.5",
  "pct_stop": "0.004"
}
```

### Sizing Response

```json
{
  "success": true,
  "data": {
    "symbol": "ES",
    "side": "long",
    "qty": 2,
    "entry": "5050.00",
    "stop_price": "5029.80",
    "risk_per_unit": "20.20",
    "gross_exposure": "62500.00"
  }
}
```

**Interpretation**: 2 ES contracts, stop at 5029.80 (5.20 points below entry, = ~$260 risk per contract).

### API Request (P&L with §1256)

```json
{
  "symbol": "ES",
  "side": "long",
  "entry": "5050.00",
  "target": "5100.00",
  "stop": "5029.80",
  "qty": 2,
  "fees_open": "2.50",
  "fees_close": "2.50",
  "slippage_open": "0.50",
  "slippage_close": "0.50",
  "energy_kwh": "0.2",
  "energy_cost_per_kwh": "0.14",
  "margin_loans": [
    {
      "amount": "5000.00",
      "apr": "0.065",
      "days_held": 2
    }
  ],
  "tax_mode": "1256",
  "st_rate": "0.24",
  "lt_rate": "0.15"
}
```

### P&L Response

```json
{
  "success": true,
  "data": {
    "symbol": "ES",
    "side": "long",
    "qty": 2,
    "entry": "5050.00",
    "target": "5100.00",
    "stop": "5029.80",
    "gross_win": "5000.00",
    "gross_loss": "2050.00",
    "breakdown": {
      "fees_total": "6.00",
      "slippage_total": "2.00",
      "energy_cost": "0.03",
      "margin_interest": "1.81",
      "tax_on_win": "774.00",
      "total_costs_win": "783.84",
      "total_costs_loss": "9.81"
    },
    "net_win": "4216.16",
    "net_loss": "-2059.81"
  }
}
```

**Interpretation**:
- **Win at $5100**: Gross $5,000, net $4,216.16 after fees/taxes/margin (84.3% of gross)
- **Loss at $5029.80**: Lose $2,000 gross + $60 costs = $2,060 total loss
- **Risk/Reward**: 2.05:1 (win $4,216 / lose $2,060)
- **Tax efficiency**: §1256 60/40 saves ~$200 vs. straight 24% short-term

---

## Example 2: NQ Intraday Scalp (Short, Short-Term Ordinary)

**Scenario**: E-mini Nasdaq scalp, 30-minute hold, expecting $2–3 tick moves

### API Request (Sizing)

```json
{
  "symbol": "NQ",
  "side": "short",
  "entry": "18500.00",
  "account_equity": "15000.00",
  "leverage": "2.0",
  "pct_stop": "0.003"
}
```

### Sizing Response

```json
{
  "success": true,
  "data": {
    "symbol": "NQ",
    "side": "short",
    "qty": 3,
    "entry": "18500.00",
    "stop_price": "18555.25",
    "risk_per_unit": "55.50",
    "gross_exposure": "30000.00"
  }
}
```

**Interpretation**: 3 NQ contracts short, stop at 18,555.25 (55.5 points above entry).

### API Request (P&L with Short-Term Tax)

```json
{
  "symbol": "NQ",
  "side": "short",
  "entry": "18500.00",
  "target": "18450.00",
  "stop": "18555.25",
  "qty": 3,
  "fees_open": "3.00",
  "fees_close": "3.00",
  "slippage_open": "1.00",
  "slippage_close": "1.00",
  "energy_kwh": "0.05",
  "energy_cost_per_kwh": "0.14",
  "tax_mode": "short_term",
  "st_rate": "0.37"
}
```

### P&L Response

```json
{
  "success": true,
  "data": {
    "symbol": "NQ",
    "side": "short",
    "qty": 3,
    "entry": "18500.00",
    "target": "18450.00",
    "stop": "18555.25",
    "gross_win": "3000.00",
    "gross_loss": "3331.50",
    "breakdown": {
      "fees_total": "8.00",
      "slippage_total": "4.00",
      "energy_cost": "0.01",
      "margin_interest": "0.00",
      "tax_on_win": "740.00",
      "total_costs_win": "752.01",
      "total_costs_loss": "12.00"
    },
    "net_win": "2247.99",
    "net_loss": "-3343.50"
  }
}
```

**Interpretation**:
- **Win**: Gross $3,000, net $2,248 (75% after 37% tax)
- **Loss**: Lose $3,331.50 (wider loss due to wider stop)
- **Risk/Reward**: 0.67:1 (not favorable; stop too wide for scalp)
- **Recommendation**: Tighten stop to 18,520 (smaller risk) or reduce qty

---

## Example 3: CL Energy Trade (Long, Energy-Focused)

**Scenario**: Crude oil trade during EIA report, expecting volatility, 1-day hold

### API Request (Sizing)

```json
{
  "symbol": "CL",
  "side": "long",
  "entry": "95.50",
  "account_equity": "10000.00",
  "leverage": "1.5",
  "pct_stop": "0.025"
}
```

### Sizing Response

```json
{
  "success": true,
  "data": {
    "symbol": "CL",
    "side": "long",
    "qty": 1,
    "entry": "95.50",
    "stop_price": "93.12",
    "risk_per_unit": "2.38",
    "gross_exposure": "15000.00"
  }
}
```

**Interpretation**: 1 CL contract long, stop at 93.12 ($238 risk per barrel).

### API Request (P&L with Energy)

```json
{
  "symbol": "CL",
  "side": "long",
  "entry": "95.50",
  "target": "100.00",
  "stop": "93.12",
  "qty": 1,
  "fees_open": "5.00",
  "fees_close": "5.00",
  "slippage_open": "2.00",
  "slippage_close": "2.00",
  "energy_kwh": "0.35",
  "energy_cost_per_kwh": "0.14",
  "margin_loans": [
    {
      "amount": "3000.00",
      "apr": "0.070",
      "days_held": 1
    }
  ],
  "tax_mode": "1256",
  "st_rate": "0.24",
  "lt_rate": "0.15"
}
```

### P&L Response

```json
{
  "success": true,
  "data": {
    "symbol": "CL",
    "side": "long",
    "qty": 1,
    "entry": "95.50",
    "target": "100.00",
    "stop": "93.12",
    "gross_win": "4500.00",
    "gross_loss": "2380.00",
    "breakdown": {
      "fees_total": "14.00",
      "slippage_total": "4.00",
      "energy_cost": "0.05",
      "margin_interest": "0.58",
      "tax_on_win": "697.41",
      "total_costs_win": "715.99",
      "total_costs_loss": "18.58"
    },
    "net_win": "3784.01",
    "net_loss": "-2398.58"
  }
}
```

**Interpretation**:
- **Win**: Gross $4,500, net $3,784 (energy-efficient trade)
- **Loss**: Lose $2,398.58
- **Risk/Reward**: 1.58:1 (solid setup)
- **Energy note**: 0.35 kWh costs only 5¢ (negligible for day trade)

---

## Example 4: GC Macro Trade (Long, Extended Hold)

**Scenario**: Gold play on macro Fed decision, 5-day multi-position trade

### API Request (Sizing)

```json
{
  "symbol": "GC",
  "side": "long",
  "entry": "2050.00",
  "account_equity": "30000.00",
  "leverage": "1.8",
  "pct_stop": "0.02"
}
```

### Sizing Response

```json
{
  "success": true,
  "data": {
    "symbol": "GC",
    "side": "long",
    "qty": 2,
    "entry": "2050.00",
    "stop_price": "2009.00",
    "risk_per_unit": "41.00",
    "gross_exposure": "54000.00"
  }
}
```

**Interpretation**: 2 GC contracts, stop at $2,009/oz (41 points below entry = $4,100 risk).

### API Request (P&L with 3 Margin Loans)

```json
{
  "symbol": "GC",
  "side": "long",
  "entry": "2050.00",
  "target": "2150.00",
  "stop": "2009.00",
  "qty": 2,
  "fees_open": "4.00",
  "fees_close": "4.00",
  "slippage_open": "1.00",
  "slippage_close": "1.00",
  "energy_kwh": "1.5",
  "energy_cost_per_kwh": "0.14",
  "margin_loans": [
    {
      "amount": "10000.00",
      "apr": "0.065",
      "days_held": 5
    },
    {
      "amount": "5000.00",
      "apr": "0.085",
      "days_held": 4
    },
    {
      "amount": "2000.00",
      "apr": "0.120",
      "days_held": 2
    }
  ],
  "tax_mode": "1256",
  "st_rate": "0.24",
  "lt_rate": "0.15"
}
```

### P&L Response

```json
{
  "success": true,
  "data": {
    "symbol": "GC",
    "side": "long",
    "qty": 2,
    "entry": "2050.00",
    "target": "2150.00",
    "stop": "2009.00",
    "gross_win": "20000.00",
    "gross_loss": "8200.00",
    "breakdown": {
      "fees_total": "10.00",
      "slippage_total": "4.00",
      "energy_cost": "0.21",
      "margin_interest_loan_1": "9.03",
      "margin_interest_loan_2": "4.72",
      "margin_interest_loan_3": "0.80",
      "total_margin_interest": "14.55",
      "tax_on_win": "3099.53",
      "total_costs_win": "3128.29",
      "total_costs_loss": "28.76"
    },
    "net_win": "16871.71",
    "net_loss": "-8228.76"
  }
}
```

**Interpretation**:
- **Win**: Gross $20,000, net $16,872 (84.4% after multi-loan cascade)
- **Loss**: Lose $8,228.76
- **Risk/Reward**: 2.05:1 (strong setup)
- **Margin insight**: 3 loans over 5 days cost only $14.55 total
  - Loan 1 (Reg T): $10k @ 6.5% = $9.03
  - Loan 2 (Portfolio): $5k @ 8.5% = $4.72
  - Loan 3 (Emergency): $2k @ 12% = $0.80
- **Tax efficiency**: §1256 blended rate (23.25%) vs. 24% straight short-term saves ~$97

---

## JSON Template for API Integration

Use this template for custom trades:

```json
{
  "symbol": "ES|NQ|CL|GC",
  "side": "long|short",
  "entry": "XXXX.XX",
  "target": "XXXX.XX",
  "stop": "XXXX.XX",
  "qty": 1,
  "fees_open": "X.XX",
  "fees_close": "X.XX",
  "slippage_open": "X.XX",
  "slippage_close": "X.XX",
  "energy_kwh": "X.XX",
  "energy_cost_per_kwh": "0.14",
  "margin_loans": [
    {"amount": "XXXX.XX", "apr": "0.065", "days_held": 1},
    {"amount": "XXXX.XX", "apr": "0.085", "days_held": 1},
    {"amount": "XXXX.XX", "apr": "0.120", "days_held": 1}
  ],
  "tax_mode": "short_term|1256",
  "st_rate": "0.24|0.35|0.37",
  "lt_rate": "0.15|0.20|0.25"
}
```

---

## CLI Examples

### ES Sizing

```bash
stoploss size \
  --symbol ES \
  --side long \
  --entry 5050 \
  --equity 25000 \
  --leverage 2.5 \
  --pct-stop 0.004 \
  --fees-open 2.5 \
  --fees-close 2.5
```

### NQ P&L with §1256

```bash
stoploss pnl \
  --symbol NQ \
  --side short \
  --entry 18500 \
  --target 18450 \
  --stop 18555.25 \
  --qty 3 \
  --fees-open 3 \
  --fees-close 3 \
  --tax-mode 1256 \
  --st-rate 0.24 \
  --lt-rate 0.15
```

### CL with Energy + Margin

```bash
stoploss pnl \
  --symbol CL \
  --side long \
  --entry 95.50 \
  --target 100 \
  --stop 93.12 \
  --qty 1 \
  --fees-open 5 \
  --fees-close 5 \
  --energy-kwh 0.35 \
  --loan 3000:0.070 \
  --days 1 \
  --tax-mode 1256 \
  --st-rate 0.24 \
  --lt-rate 0.15
```

---

**Note**: All examples assume US federal tax brackets and broker margin rates as of Q4 2024. Always verify current rates with your broker and tax professional.
