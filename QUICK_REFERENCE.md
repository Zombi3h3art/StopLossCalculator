# 📌 QUICK REFERENCE CARD

## Your Stop Loss Calculator - At a Glance

### 🎯 What It Does

Calculates **precise P&L for futures trades** (ES, NQ, CL, GC) with:
- Position sizing (qty + stop price)
- All costs (fees, slippage, energy, margin interest, taxes)
- IRS-compliant taxes (short-term ordinary + §1256 60/40)
- 360-day margin accrual for up to 3 loans

### 🚀 Quick Start (3 Steps)

**Step 1: Install**
```bash
cd "c:\Users\cwmil\Desktop\Python_Projects\projects\Stop Loss Calculator"
pip install -e ".[dev]"
```

**Step 2: Run One of Three Ways**

*CLI (fastest):*
```bash
python -m stoploss size --symbol ES --side long --entry 5050 --equity 20000 --leverage 3 --pct-stop 0.004
```

*API (localhost):*
```bash
python -m uvicorn api.app:app --reload
# POST http://localhost:8000/size
```

*Web UI (easiest):*
```bash
streamlit run ui_app.py  # http://localhost:8501
```

**Step 3: Check Results**
- CLI: Terminal output
- API: JSON response
- UI: Dashboard with charts

### 📦 Files to Know

| File | Purpose |
|------|---------|
| `README.md` | User guide + math |
| `WHAT_YOU_BUILT.md` | Overview (this document's sibling) |
| `WORKED_EXAMPLES.md` | 4 complete trades (ES/NQ/CL/GC) |
| `src/stoploss/` | Core modules |
| `api/app.py` | REST API |
| `ui_app.py` | Streamlit dashboard |
| `tests/` | 90+ unit tests |

### 📊 Example: Single ES Trade

**Input:**
```
Symbol: ES, Side: Long, Entry: 5050, Target: 5100, Stop: 5030
Qty: 2, Fees: $2 open + $2 close
Loan: $5000 @ 6.5% for 2 days
Taxes: §1256 (24% ST, 15% LT)
```

**Output:**
```
Gross Win: $5,000
Costs: $7.84 (fees/slip/energy/margin)
Tax: $929.20
Net Win: $4,062.96
═══════════════════════════════════════
Gross Loss: $2,040
Costs: $7.84
Net Loss: -$2,047.84
═══════════════════════════════════════
Risk/Reward: 1.98:1
```

### 🔧 Key Features

| Feature | Example |
|---------|---------|
| **Symbols** | ES ($50/pt), NQ ($20/pt), CL ($1000/pt), GC ($100/pt) |
| **Position Sizing** | Qty: floor(gross_exposure / (entry × ppv)) |
| **Stop Rounding** | ES/NQ: 0.25 tick, CL: $0.01, GC: $0.10 |
| **Taxes** | ST: rate × profit; §1256: (0.60×LT + 0.40×ST) × profit |
| **Margin** | interest = principal × APR × (days / 360) |
| **Energy** | kwh × 14¢ (US avg) |

### 🏗️ Architecture

```
User Input (CLI/API/UI)
        ↓
  Pydantic Models (validation)
        ↓
Core Modules (Decimal math)
├─ contracts.py (CME specs)
├─ sizing.py (qty + stop)
├─ cashflow.py (P&L gross/net)
├─ taxes.py (IRS compliant)
├─ rates.py (margin + SOFR)
├─ energy.py (EIA estimate)
└─ schemas.py (output models)
        ↓
    Output (JSON/table/chart)
```

### 🧪 Testing

```bash
pytest tests/ -v                    # Run all tests
pytest tests/ --cov=src/stoploss    # With coverage
ruff check src/                     # Lint
black --check src/                  # Format check
mypy src/                           # Type check
```

### 📚 Math Cheat Sheet

```
Gross P&L:
  win = qty × ppv × (target - entry)
  loss = qty × ppv × (entry - stop)

Costs:
  total = fees + slip + energy + margin_int

Taxes (§1256):
  tax = gross_profit × (0.60 × LT_rate + 0.40 × ST_rate)

Net P&L:
  net_win = gross_win - costs - tax
  net_loss = -(gross_loss + costs)

Margin Interest (360-day basis):
  interest = principal × APR × (days / 360)
```

### 🌐 API Endpoints

```
POST /size          # Calculate position size and stop
POST /pnl           # Calculate full P&L with all costs
GET /refs/electricity    # US avg electricity cost (EIA)
GET /refs/sofr      # Current SOFR rate (Fed)
GET /health         # Health check
```

### 💾 Git Status

```
Repository: https://github.com/Zombi3h3art/StopLossCalculator
Branch: main
Status: 6 clean commits, ready to push
```

### 🎓 Learn More

1. **START HERE**: Read `README.md`
2. **See Examples**: Check `WORKED_EXAMPLES.md` (4 trades with JSON)
3. **How-To**: Use CLI, API, or UI (see Quick Start above)
4. **Deep Dive**: Read `PROJECT_COMPLETION_SUMMARY.md`
5. **Code**: Browse `src/stoploss/*.py` (well-documented)

### 🚨 Important Notes

⚠️ **US Federal Taxes Only** - no state/county  
⚠️ **Decimal Precision** - all math uses Decimal (no float errors)  
⚠️ **Per-Trade Basis** - each trade calculated independently  
⚠️ **Disclaimer** - educational tool, not investment advice  

### 💡 Pro Tips

- Always round stops to contract ticks (auto-done in calculator)
- §1256 tax mode is usually better than short-term ordinary
- Margin interest is tiny for 1-5 day trades
- Energy cost is negligible unless you're CPU farming
- Test the API with the provided curl examples in `WORKED_EXAMPLES.md`

---

**Questions?** → See full docs in `README.md` or `WHAT_YOU_BUILT.md`  
**Ready to deploy?** → Run `git push origin main` when network is available
