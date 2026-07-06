# 📌 QUICK REFERENCE CARD

## Your Stop Loss Calculator - At a Glance

### 🎯 What It Does

Calculates **precise P&L for futures trades** (ES, NQ, CL, GC) with:
- Risk-first position sizing (qty + tick-rounded stop price)
- All costs (fees, slippage, energy, margin interest, taxes)
- IRS federal taxes (short-term ordinary + §1256 60/40)
- 360-day margin accrual for up to 3 loans

### 🚀 Quick Start (3 Steps)

**Step 1: Install**
```bash
git clone https://github.com/Zombi3h3art/StopLossCalculator.git
cd StopLossCalculator
pip install -e ".[dev]"
```

**Step 2: Run One of Three Ways**

*Web UI (easiest):*
```bash
streamlit run simple_dashboard.py  # http://localhost:8501
```

*CLI (fastest):*
```bash
stoploss size --symbol ES --side long --entry 5050 --equity 25000 \
  --leverage 12 --pct-stop 0.004 --risk 2500
```

*API (localhost):*
```bash
python -m uvicorn api.app:app --reload
# POST http://localhost:8000/size
```

**Step 3: Check Results**
- UI: Dashboard with trade summary card
- CLI: Terminal output
- API: JSON response

### 📦 Files to Know

| File | Purpose |
|------|---------|
| `README.md` | User guide + math |
| `WORKED_EXAMPLES.md` | 4 complete trades (ES/NQ/CL/GC), code-generated numbers |
| `simple_dashboard.py` | Streamlit dashboard (primary UI) |
| `src/stoploss/` | Core modules |
| `api/app.py` | REST API |
| `tests/` | Golden + property tests |

### 📊 Example: Single ES Trade (real code output)

**Input:**
```
Symbol: ES, Side: Long, Entry: 5050, Target: 5100, Stop: 5029.75
Qty: 1, Fees: $2.50 open + $2.50 close, Slippage: $0.50 each way
Loan: $5000 @ 6.5% for 2 days, Energy: 0.2 kWh
Taxes: §1256 (24% ST, 15% LT)
```

**Output:**
```
Gross Win: $2,500.00
Costs: $7.84 (fees/slip/energy/margin)
Tax: $465.00
Net Win: $2,027.16
═══════════════════════════════════════
Gross Loss: $1,012.50
Costs: $7.84
Net Loss: -$1,020.34
═══════════════════════════════════════
Risk/Reward: ~1.99:1 net
```

### 🔧 Key Features

| Feature | Rule |
|---------|------|
| **Symbols** | ES ($50/pt), NQ ($20/pt), CL ($1000/pt), GC ($100/pt) + micros MES/MNQ/MCL/MGC (1/10 size) |
| **Position Sizing** | Qty = min(floor(risk_budget ÷ risk_$/contract), floor(equity × leverage ÷ (entry × ppv))) |
| **Stop Rounding** | ES/NQ: 0.25 tick, CL: $0.01, GC: $0.10 — risk recomputed from rounded stop |
| **Taxes** | ST: rate × profit; §1256: (0.60×LT + 0.40×ST) × profit |
| **Margin** | interest = principal × APR × (days / 360) |
| **Energy** | kWh × 14¢ (US avg) |

### 🏗️ Architecture

```
User Input (UI/CLI/API)
        ↓
  Pydantic Models (validation)
        ↓
Core Modules (Decimal math)
├─ contracts.py (CME specs)
├─ sizing.py (risk-first qty + stop)
├─ cashflow.py (P&L gross/net)
├─ taxes.py (IRS federal)
├─ rates.py (margin + SOFR)
├─ energy.py (EIA estimate)
└─ schemas.py (validation models)
        ↓
    Output (JSON/table/dashboard)
```

### 🧪 Testing

```bash
pytest tests/ -v                    # Run all tests
pytest tests/ --cov=src/stoploss    # With coverage
ruff check src/ tests/              # Lint
black --check src/ tests/           # Format check
mypy src/                           # Type check
```

### 🌐 API Endpoints

```
POST /size          # Risk-first position size and stop (needs risk_cash)
POST /pnl           # Full P&L with all costs
GET /refs/electricity    # US avg electricity cost (live EIA with EIA_API_KEY, else 14c)
GET /refs/sofr      # SOFR (live NY Fed, 1h cache, static fallback)
GET /health         # Health check
```

### 🎓 Learn More

1. **START HERE**: Read `README.md`
2. **See Examples**: Check `WORKED_EXAMPLES.md` (4 trades with JSON)
3. **How-To**: Use UI, CLI, or API (see Quick Start above)
4. **Code**: Browse `src/stoploss/*.py` (docstrings cite IRS/CME/EIA sources)

### 🚨 Important Notes

⚠️ **US Federal Taxes Only** - no state/county
⚠️ **Decimal Precision** - all math uses Decimal (no float errors)
⚠️ **Per-Trade Basis** - each trade calculated independently
⚠️ **Buying-Power Cap** - qty never exceeds what equity × leverage controls
⚠️ **Disclaimer** - educational tool, not investment advice

### 💡 Pro Tips

- Stops are auto-rounded to contract ticks; the shown risk uses the rounded stop
- §1256 tax mode is usually better than short-term ordinary for futures
- Margin interest is tiny for 1–5 day trades
- If sizing errors with "buying power too small," raise leverage/equity or wait for micro contracts (roadmap)

---

**Questions?** → See full docs in `README.md`
