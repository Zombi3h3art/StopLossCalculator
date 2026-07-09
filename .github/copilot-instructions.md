# Stop Loss Calculator - AI Coding Agent Instructions

## Project Overview

**Stop Loss Net Edge Calculator** is a precision financial calculator for futures trading (ES, NQ, CL, GC) with comprehensive cost accounting. It provides multiple interfaces (REST API, Streamlit UI) and uses Decimal-based math for precision.

**Key Mission**: Enable traders to model P&L accurately by accounting for all costs: position sizing, stop-loss placement, fees, slippage, federal taxes (short-term ordinary + §1256 60/40), margin interest (up to 3 cascading loans), and energy costs.

---

## Architecture & Data Flow

```
User Input (API/UI)
    ↓
Pydantic Schemas (validation)
    ↓
Core Calculation Modules
├─ contracts.py (ES/NQ/CL/GC specs from CME)
├─ sizing.py (qty + stop math)
├─ cashflow.py (gross/net P&L)
├─ taxes.py (IRS §1256 and short-term ordinary)
├─ rates.py (margin interest, SOFR reference)
└─ energy.py (EIA energy cost estimation)
    ↓
Output (JSON/CSV/table)
```

### Critical Files & Patterns

1. **`src/stoploss/contracts.py`**: Hard-coded CME contract specs (ES=$50/pt, NQ=$20/pt, CL=$1000/pt, GC=$100/pt) plus micros (MES=$5, MNQ=$2, MCL=$100, MGC=$10 — each 1/10 of its parent, see `MICRO_OF`). All have `min_tick` and `tick_value`. Use `get_contract(symbol)` to retrieve; call `.round_to_tick(price)` to ensure valid stops.

2. **`src/stoploss/sizing.py`**: Two sizing paths, both **risk-first** (require a `risk_cash` budget in dollars):
   - **Percent-stop**: `stop = entry ± (entry * pct_stop)` rounded to tick, then
     `qty = min(floor(available_risk / risk_$_per_contract), floor(equity * leverage / (entry * ppv)))`.
     The second term is the buying-power cap; distinct ValueErrors explain which constraint failed.
   - **ATR/structure**: `stop = entry ± max(k_atr * ATR, structure distance)` rounded to tick;
     qty from the *rounded* stop distance.

3. **`src/stoploss/cashflow.py`**: Calculates `PnLResult` with gross/net for win and loss scenarios. Includes all costs: fees, slippage, energy, margin interest, taxes.

4. **`src/stoploss/taxes.py`**: Two modes (IRS-mandated):
   - **Short-term ordinary**: `tax = gross_profit * tax_rate` (24%, 35%, 37%).
   - **§1256 futures (Form 6781)**: `tax = gross_profit * (0.60 * lt_rate + 0.40 * st_rate)` (60% LTCG, 40% ordinary).

5. **`src/stoploss/rates.py`**: Margin interest on 360-day basis (daily accrual, billed monthly). Up to 3 loans per trade.

6. **`src/stoploss/energy.py`**: Estimates energy cost using EIA Table 5.3 (US avg ~14¢/kWh). Cache-friendly design.

7. **`src/stoploss/schemas.py`**: Pydantic v2 models for input validation and output serialization. All have JSON examples for the API.

---

## Math & Precision Rules

- **Use `Decimal` throughout** — no floats. All inputs coerced to `Decimal(str(...))` before computation.
- **Tick rounding is mandatory**: After computing stop, call `contract.round_to_tick(stop_price)`, then recompute `loss_per_unit` to keep R (risk) honest.
- **360-day basis** for margin interest (IBKR/Schwab standard), **daily accrual**.
- **No state/county taxes**, **no wash-sale logic** — simple federal only, as documented in README.md.
- **Formulas are scriptural anchors** (Luke 14:28, Proverbs 11:1): count costs fully; no false math.

### Example: ES Long, Percent Stop (risk-first)

```python
# Entry=5050, pct_stop=0.4%, equity=$25k, lev=12, risk_cash=$2500, fees $2+$2
stop = 5050 - 20.20 = 5029.80 -> tick-rounded to 5029.75 (risk 20.25 pts)
risk_$_per_contract = 20.25 * 50 = $1,012.50
qty_risk = floor((2500 - 4) / 1012.50) = 2
qty_cap  = floor(25000 * 12 / (5050 * 50)) = 1   # buying-power cap
qty = min(2, 1) = 1  (capped_by_buying_power=True)
```

---

## Development Workflows

### Running Tests
```bash
pytest tests/ -v                          # All tests
pytest tests/test_sizing.py -v            # Specific module
pytest -m "not slow" -v                   # Skip external API calls
pytest --cov=src/stoploss                 # Coverage report
```

### Running the Streamlit UI
```bash
streamlit run simple_dashboard.py
# Opens localhost:8501 with two-column UI (inputs left, results right)
```

### Code Quality
```bash
ruff check src/ tests/              # Linting (100-char lines, strict rules)
black --check src/ tests/           # Formatting
mypy src/                           # Type checking
```

---

## Conventions & Patterns

### Input Coercion
All module functions accept numeric inputs and coerce to `Decimal`:
```python
entry = Decimal(str(entry))  # Always this pattern
```

### Validation
- **Pydantic schemas** handle UI/API input validation (`SizingInput`, `PnLInput`, etc.).
- **Calculation modules** (sizing, cashflow) do minimal validation; assume clean Decimals.

### Error Handling
- Raise `ValueError` with descriptive messages in core modules.
- Streamlit UI catches and displays errors in red alert boxes.

### Margin Loans (3-Slot Cascading)
Store as list of `MarginLoan(amount, apr, days_held)`:
```python
# Schemas accept: --loan 5000:0.065 --loan 2000:0.10 (up to 3 times)
loans = [MarginLoan(5000, 0.065, 5), MarginLoan(2000, 0.10, 5), ...]
total_interest = calculate_total_margin_interest(loans)
```

---

## Common Tasks

### Add a New Calculation Module
1. Create `src/stoploss/<module>.py` with docstring (math references + IRS links).
2. Define Decimal-based functions; return dataclass or Decimal.
3. Add unit tests in `tests/test_<module>.py` with golden-file fixtures (e.g., test data from IRS examples).
4. Export in `src/stoploss/__init__.py` for API convenience.

### Update Streamlit UI
1. Edit `ui_app.py`; add input widget (left column) or result display (right column).
2. Call calculation function with Streamlit session state values.
3. Display results using `st.metric()`, `st.dataframe()`, or `st.write()`.
4. Export: CSV/JSON download button in `export_results()`.

### Add External Data (EIA/SOFR)
1. Create fetch function in module (e.g., `energy.py`, `rates.py`).
2. Cache with `@functools.lru_cache(maxsize=1)` or `@st.cache_data`.
3. Fall back to hardcoded US average on network error.
4. Mark test with `@pytest.mark.slow` to skip in fast runs.

---

## Testing Patterns

### Golden-File Tests (Math Verification)
```python
# test_sizing.py
def test_es_percent_stop_example():
    """ES long, entry=5050, pct_stop=0.4% → stop~5030, qty based on exposure."""
    result = size_by_percent_stop(
        symbol="ES", side="long", entry=Decimal("5050"),
        account_equity=Decimal("20000"), leverage=Decimal("3"),
        pct_stop=Decimal("0.004")
    )
    # Compare to hand-calculated expected values
    assert result.qty == expected_qty
    assert result.stop_price == Decimal("5029.75")  # Rounded to 0.25 tick
```

### Property Tests (Tick Rounding)
```python
# Ensure stop rounding preserves contract specs
from hypothesis import given, strategies as st

@given(st.decimals(min_value=1000, max_value=10000, places=2))
def test_round_to_tick_valid(price):
    contract = get_contract("ES")
    rounded = contract.round_to_tick(price)
    # Verify: (rounded - price) % min_tick ≈ 0 (within rounding)
```

---

## External Dependencies & Data Sources

| Source | Purpose | Default/Fallback |
|--------|---------|------------------|
| CME Group specs | ES/NQ/CL/GC tick/ppv | Hard-coded in `contracts.py` |
| IRS Pub 550 + Form 6781 | Tax calculation | Hard-coded rates; user supplies tax_rate |
| EIA Table 5.3 | Energy ¢/kWh avg | ~14¢/kWh (US avg); requests fallback |
| Federal Reserve SOFR | Margin context (display only) | hardcoded 5.33% (illustrative) |

---

## Git & Release Workflow

- **Branch**: Work on feature branches; PR to `main`.
- **Commits**: Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `style:`, `refactor:`).
- **Tests**: All tests must pass before merge (GitHub Actions CI/CD).
- **Versioning**: SemVer (v0.1.0, v0.2.0, etc.); tag on release.
- **CHANGELOG.md**: Document math-affecting changes prominently.

---

## Quick Reference: Key Functions

| Module | Function | Returns |
|--------|----------|---------|
| `contracts` | `get_contract(symbol)` | `FuturesContract` |
| `sizing` | `size_by_percent_stop(...)` | `PositionSize` |
| `cashflow` | `calculate_pnl(...)` | `PnLResult` |
| `taxes` | `calculate_tax_section_1256(...)` | `Decimal` (tax owed) |
| `rates` | `calculate_total_margin_interest(...)` | `Decimal` (interest accrued) |
| `energy` | `estimate_energy_cost(...)` | `Decimal` (cost in $) |

---

## Documentation Anchors

- **Math**: See README.md "Math Reference" section with formulas.
- **Limits**: See README.md "Contract Limits & Assumptions" table.
- **IRS Rules**: Form 6781 (futures §1256), Pub 550 (short-term).
- **Margin**: Schwab/IBKR 360-day basis; Charles Schwab website for rate context.
- **Energy**: EIA Electric Power Monthly, Table 5.3 (eia.gov).

---

## When in Doubt

1. **Always use Decimal** for financial values.
2. **Always round stops to contract ticks** after computing.
3. **Always cite IRS/CME sources** for new calculation logic in docstrings.
4. **Always run tests before committing** math changes.
5. **Always update CHANGELOG.md** if a change affects calculated P&L.

