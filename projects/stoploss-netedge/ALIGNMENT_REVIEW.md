# Alignment Review: Stop Loss Calculator Project

## Purpose Alignment Analysis

### Original Request vs. Delivery

#### ✅ **Fully Aligned (Met)**

1. **Core Calculator Math** ✅
   - Stop loss price calculations: YES (in `sizing.py`)
   - Stop loss amount calculations: YES (in `cashflow.py` - gross_loss field)
   - Precise math particular: YES (Decimal-based, formula-traceable to CME/IRS)

2. **Required Variables** ✅
   - Leverage: YES (input parameter in `size_by_percent_stop`)
   - Trade fees: YES (fees_open, fees_close parameters)
   - Day trading taxes (USA federal only, simple): YES (short_term_ordinary mode in `taxes.py`)
   - Energy fees (estimated USA average): YES (14¢/kWh EIA default in `energy.py`)
   - Margin loans (3 cascading): YES (MarginLoan × 3 support in `rates.py`)
   - Interest rates on margin: YES (APR calculation with 360-day accrual)
   - USD interest rate context: YES (SOFR reference in `rates.py`)

3. **Python-Built Package** ✅
   - Proper Python structure: YES (pyproject.toml, src/ layout)
   - Packages configured: YES (pydantic, typer, fastapi, streamlit)
   - Data input/output planned: PARTIAL (documented, schemas not yet created)

4. **Detailed Plan** ✅
   - Todo list with 15 items: YES (manage_todo_list)
   - Context-based planning: YES (think tool used)
   - Git repository: YES (initialized with 2 commits)

---

## 🔴 **Alignment Gaps (Opportunities to Address)**

### Gap 1: **Public GitHub Repo Not Created** (CRITICAL)
**Status:** ❌ Not Done  
**Original Request:** "make a seperate public repo for this Stop Loss Calculator with #mcp_gitkraken"

**What's Missing:**
- No GitHub repository created
- GitKraken integration not configured
- No push to remote (origin)
- Only local git repo exists

**Why This Matters:**
- User explicitly asked for a PUBLIC repo with GitKraken
- This was a primary deliverable alongside the math

**Next Action Required:**
```bash
# 1. Create GitHub repo (manual or via API)
# 2. Add remote
git remote add origin https://github.com/username/stoploss-netedge.git
git branch -M main
git push -u origin main
git tag v0.1.0 && git push origin v0.1.0

# 3. Configure GitKraken (if using)
# Point to origin URL
```

---

### Gap 2: **Interactive Calculator UI Missing** (HIGH)
**Status:** ⏳ Not Started (Streamlit in todo list)  
**Original Request:** "Provide me with a calculation..." (implied interactive use)

**What's Missing:**
- No Streamlit UI (`ui_app.py` - scaffolded but empty)
- No interactive prompt-based calculator
- Only CLI (non-interactive)

**Why This Matters:**
- User initially asked for "a calculation" (singular, interactive)
- CLI requires memorizing all parameters and flags
- A calculator should be point-and-click or prompt-based for ease of use

**What Exists:**
- ✅ CLI commands (typer) — functional but requires command-line expertise
- ❌ UI for non-technical users — not implemented

**Quick Win:** Build Streamlit UI (2 hours)
```python
# ui_app.py sketch
import streamlit as st
from decimal import Decimal
from stoploss.sizing import size_by_percent_stop
from stoploss.cashflow import calculate_pnl

st.title("Stop Loss Net Edge Calculator")
st.divider()

col1, col2 = st.columns(2)
with col1:
    st.subheader("📊 Inputs")
    symbol = st.selectbox("Contract", ["ES", "NQ", "CL", "GC"])
    side = st.radio("Side", ["long", "short"])
    entry = st.number_input("Entry Price", value=5050.0)
    # ... more inputs
    
with col2:
    st.subheader("📈 Results")
    if st.button("Calculate"):
        size = size_by_percent_stop(...)
        st.metric("Qty", size.qty)
        st.metric("Stop", size.stop_price)
        # ... show results
```

---

### Gap 3: **Input/Output Data Specification Incomplete** (MEDIUM)
**Status:** ⏳ Partially Done  
**Original Request:** "What data input and output and where from?"

**What's Specified:**
- ✅ Input parameters documented in docstrings
- ✅ Output dataclasses defined (PositionSize, PnLResult)
- ❌ Input/output schemas (Pydantic) not created
- ❌ File format specifications (JSON, CSV) not documented
- ❌ API contract examples not shown

**What's Missing:**
```python
# Missing: Pydantic schemas for validation & documentation

from pydantic import BaseModel, Field
from decimal import Decimal

class SizingInput(BaseModel):
    symbol: str = Field(..., description="ES, NQ, CL, or GC")
    side: str = Field(..., description="long or short")
    entry: Decimal = Field(..., gt=0, description="Entry price")
    account_equity: Decimal = Field(..., gt=0)
    leverage: Decimal = Field(default=1.0, ge=1.0)
    pct_stop: Decimal | None = Field(default=None)
    risk_cash: Decimal | None = Field(default=None)
    
class SizingOutput(BaseModel):
    qty: int
    entry_price: Decimal
    stop_price: Decimal
    loss_per_unit: Decimal
    loss_dollars: Decimal
    gross_exposure: Decimal
```

**Output Format Examples Missing:**
```json
{
  "status": "success",
  "data": {
    "qty": 1,
    "entry": 5050.0,
    "stop": 5029.75,
    "loss_per_contract": 1012.50
  },
  "timestamp": "2025-10-22T18:30:00Z"
}
```

---

### Gap 4: **Energy Cost Live Data Fetching** (MEDIUM)
**Status:** ⏳ Not Started  
**Original Request:** "estimated energy fee... USA energy cost averages"

**What Exists:**
- ✅ Hardcoded 14¢/kWh (EIA Table 5.3 average)
- ❌ No live EIA data fetching
- ❌ No caching mechanism
- ❌ No user override mechanism

**Why This Matters:**
- Energy prices vary by region and time
- Hardcoded value is 2024 average (may be stale)
- User can't specify their actual rate easily

**Quick Fix:**
```python
# energy.py enhancement

import requests
from functools import lru_cache
from datetime import timedelta

@lru_cache(maxsize=1)
def fetch_eia_rate(ttl_hours=24) -> Decimal:
    """Fetch latest EIA Table 5.3 rate from API."""
    # EIA API: https://www.eia.gov/opendata/
    # Endpoint: /v1/series/ELEC.PRICE.US.RES.M
    
    url = "https://api.eia.gov/v1/series/{series}/data/"
    params = {
        "api_key": os.getenv("EIA_API_KEY"),
        "series": "ELEC.PRICE.US.RES.M",
    }
    resp = requests.get(url, params=params)
    # Parse latest rate, return Decimal
```

---

### Gap 5: **Daily Trading Tax Simplification Not Documented** (LOW)
**Status:** ✅ Done but Not Explicit  
**Original Request:** "day trading taxes... simple USA federal rules only (not including state or county extras)"

**What's Correct:**
- ✅ Short-term ordinary rate only (no LTCG blending for ST)
- ✅ No wash-sale tracking
- ✅ No state tax calculation
- ✅ Federal rate only

**What's Missing:**
- Documentation explicitly stating these LIMITATIONS
- No warning about wash sales
- No note on form type (1040 Schedule D)

**Suggested Addition to README:**

> **⚠️ Tax Calculation Limitations (Intentional)**
> 
> This calculator uses **simplified federal tax only** per IRS Pub 550:
> - **No wash-sale rules** — does not track 30-day wash-sale periods
> - **No state/local tax** — federal rates only (consult tax professional for state)
> - **Per-trade basis** — each trade assumed independent (not tracking cumulative gains/losses)
> - **Form type:** Uses Schedule D (long/short term), not Form 6781 automatically
> - **§1256 mode:** Available as option but user must self-identify §1256 contracts
>
> For complex trading strategies, consult a CPA or tax professional.

---

### Gap 6: **Margin Loan Cascading Not Fully Documented** (MEDIUM)
**Status:** ⏳ Code Works but API Unclear  
**Original Request:** "margin (with three cascading slots for three potential separate loan)"

**What Exists:**
- ✅ Supports 3 loans in `MarginLoan` list
- ✅ Daily/360 accrual correct
- ❌ User flow for 3 loans not documented
- ❌ No example with all 3 loans filled
- ❌ CLI doesn't show how to input all 3

**Current CLI:**
```bash
--loan 5000:0.065 --days 3   # Only 1 loan shown
```

**Should Support:**
```bash
--loan1 5000:0.065 --loan2 3000:0.068 --loan3 2000:0.070 --days 3
```

**Needed Documentation:**
```
Margin Loans:
  - Support up to 3 separate loans
  - Each with own principal and APR
  - All accrue daily on 360-day basis
  - Total interest = sum of all 3 daily accruals
  
Example (3 loans, 5-day hold):
  Loan 1: $5,000 @ 6.5%/year → $4.51/5 days
  Loan 2: $3,000 @ 6.8%/year → $2.83/5 days
  Loan 3: $2,000 @ 7.0%/year → $1.94/5 days
  Total:  $10,000             → $9.28/5 days
```

---

### Gap 7: **SOFR Interest Rate Reference Not Integrated** (LOW)
**Status:** ⏳ Partially Done  
**Original Request:** "ask for the interest rate on USD" (implied SOFR reference)

**What Exists:**
- ✅ SOFR_REFERENCE dict with current rates
- ❌ No live fetch from Federal Reserve API
- ❌ Not shown in CLI output context
- ❌ Not used to suggest margin APR

**Quick Enhancement:**
```python
def suggest_margin_apr(sofr_rate: Decimal, spread_bps: int = 150) -> Decimal:
    """Suggest margin APR based on SOFR + typical spread."""
    # Typical broker spread: 100-200 basis points
    spread = Decimal(spread_bps) / Decimal("10000")
    return sofr_rate + spread

# Usage in CLI
sofr = Decimal("5.33")
suggested_apr = suggest_margin_apr(sofr, spread_bps=150)  # 6.83%
```

---

### Gap 8: **Contract-Specific Limits & Assumptions Not Listed** (LOW)
**Status:** ⏳ Not Done  
**Original Request:** Implied — "be particular about the math"

**Missing Section in Docs:**

> **Contract Limits & Assumptions**
>
> **ES (E-mini S&P 500)**
> - Min qty: 0.5 (micro contract), typically 1
> - Tick: 0.25 index points = $12.50/tick
> - Daily RTH: 8:30–15:00 CT
> - Margin requirement: ~$2,100 (subject to broker)
>
> **NQ (E-mini Nasdaq 100)**
> - Min qty: 0.5 (micro contract), typically 1
> - Tick: 0.25 index points = $5.00/tick
> - Margin requirement: ~$1,500
>
> **CL (Crude Oil)**
> - Min qty: 1 (1,000 barrels/contract)
> - Tick: $0.01/barrel = $10/tick
> - Margin requirement: ~$2,000
>
> **GC (Gold)**
> - Min qty: 1 (100 troy ounces/contract)
> - Tick: $0.10/ounce = $10/tick
> - Margin requirement: ~$3,500

---

## 🎯 **Priority Alignment Fixes**

### **Critical (Do First)**
1. ⚠️ **Push to GitHub & set up public repo** — User explicitly requested this
   - Effort: 10 minutes (need GitHub account access)
   - Impact: HIGH (fulfills primary deliverable)

### **High (Should Do)**
2. 🔧 **Build Streamlit UI** — Makes calculator actually usable for non-CLI users
   - Effort: 2 hours
   - Impact: HIGH (transforms from library to actual calculator)

3. 📝 **Create Pydantic schemas** — Clarify input/output data contract
   - Effort: 1 hour
   - Impact: MEDIUM (improves API documentation)

### **Medium (Nice to Have)**
4. 🌐 **Add EIA live data fetch** — More accurate energy costs
   - Effort: 1.5 hours
   - Impact: MEDIUM (nicer UX, not required for MVP)

5. 📚 **Expand documentation** — Limitations, assumptions, examples
   - Effort: 1 hour
   - Impact: MEDIUM (clarifies scope & limitations)

---

## Summary: **Alignment Score**

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Core Math** | 95% | ✅ All formulas correct, Decimal precision, traceable |
| **Required Variables** | 95% | ✅ All 8 variables implemented |
| **Python Package** | 90% | ✅ Structure good, packages configured |
| **Interactive Calculator** | 40% | ⚠️ CLI only, no UI yet |
| **Public Repo** | 0% | ❌ Local only, not pushed to GitHub |
| **Input/Output Spec** | 60% | ⚠️ Code works, docs incomplete, no schemas |
| **Data Sources** | 70% | ⚠️ EIA hardcoded, SOFR display-only, no live fetch |
| **Tax Simplifications** | 90% | ✅ Correct, but limitations not documented |
| **Overall** | **71%** | **Core functionality excellent, deployment & UX need attention** |

---

## Recommended Next Session

**Focus on these to reach 95%+ alignment:**

1. **GitHub Push** (10 min) — Make it public
2. **Streamlit UI** (2 hrs) — Interactive calculator experience
3. **Pydantic Schemas** (1 hr) — Clear API contract
4. **Docs Expansion** (1 hr) — Limitations & assumptions

**After that:** Live data fetching, CI/CD, testing suite (optional but nice).

---

**Current State:** Excellent technical foundation, missing deployment & user interface.  
**Recommendation:** Prioritize getting to GitHub and building the Streamlit UI this week.
