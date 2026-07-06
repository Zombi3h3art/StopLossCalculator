"""REST API for Stop Loss Calculator using FastAPI."""

import sys
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# Allow `uvicorn api.app:app` from a source checkout without installing
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from stoploss import __version__
from stoploss.cashflow import calculate_pnl
from stoploss.energy import fetch_electricity_price_cents
from stoploss.rates import MarginLoan, fetch_sofr_reference
from stoploss.schemas import (
    ApiResponse,
    PnLInput,
    PnLOutput,
    SizingInput,
    SizingOutput,
)
from stoploss.sizing import size_by_percent_stop

app = FastAPI(
    title="Stop Loss Net Edge Calculator API",
    description="Precision financial calculator for futures trading",
    version=__version__,
)

# Enable CORS for web UI
# ponytail: credentials dropped — wildcard origins + credentials is an invalid
# CORS combo browsers reject; scope allow_origins when a real frontend exists
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "version": __version__}


@app.post("/size", tags=["Sizing"], response_model=ApiResponse)
async def calculate_size(input_data: SizingInput) -> ApiResponse:
    """
    Calculate position size and stop price (risk-first).

    Accepts a SizingInput with symbol, side, entry, account equity, leverage,
    percent stop, and a risk budget (`risk_cash`, the maximum acceptable loss
    in dollars). Returns qty = min(risk-based qty, buying-power cap) and the
    stop price rounded to the contract tick.

    **Request Example:**
    ```json
    {
        "symbol": "ES",
        "side": "long",
        "entry": "5050.00",
        "account_equity": "25000.00",
        "leverage": "12",
        "pct_stop": "0.004",
        "risk_cash": "2500.00",
        "fees_open": "2.00",
        "fees_close": "2.00"
    }
    ```

    **Response Example:**
    ```json
    {
        "success": true,
        "data": {
            "symbol": "ES",
            "side": "long",
            "qty": 1,
            "entry": "5050.00",
            "stop_price": "5029.75",
            "risk_per_unit": "20.2000",
            "risk_per_unit_actual": "20.2500",
            "risk_dollars_per_contract": "1012.50",
            "gross_exposure": "300000.00",
            "risk_cash": "2496.00",
            "fees_open": "2.00",
            "fees_close": "2.00",
            "slippage_open": "0",
            "method": "percent_stop",
            "buying_power_qty_cap": 1,
            "capped_by_buying_power": true
        }
    }
    ```
    """
    if input_data.pct_stop is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="pct_stop is required for percent-stop sizing",
        )
    if input_data.risk_cash is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="risk_cash (risk budget in dollars) is required for percent-stop sizing",
        )

    try:
        result = size_by_percent_stop(
            symbol=input_data.symbol,
            side=input_data.side,
            entry=Decimal(str(input_data.entry)),
            account_equity=Decimal(str(input_data.account_equity)),
            leverage=Decimal(str(input_data.leverage)),
            pct_stop=Decimal(str(input_data.pct_stop)),
            risk_cash=Decimal(str(input_data.risk_cash)),
            fees_open=Decimal(str(input_data.fees_open)),
            fees_close=Decimal(str(input_data.fees_close)),
        )

        output = SizingOutput(
            symbol=result.symbol,
            side=result.side,
            qty=result.qty,
            entry=result.entry,
            stop_price=result.stop_price,
            risk_per_unit=result.risk_per_unit,
            risk_per_unit_actual=result.risk_per_unit_actual,
            risk_dollars_per_contract=result.risk_dollars_per_contract,
            gross_exposure=result.gross_exposure,
            risk_cash=result.risk_cash,
            fees_open=result.fees_open,
            fees_close=result.fees_close,
            slippage_open=result.slippage_open,
            method=result.method,
            buying_power_qty_cap=result.buying_power_qty_cap,
            capped_by_buying_power=result.capped_by_buying_power,
        )

        return ApiResponse(success=True, data=output)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@app.post("/pnl", tags=["P&L Analysis"], response_model=ApiResponse)
async def calculate_pnl_api(input_data: PnLInput) -> ApiResponse:
    """
    Calculate P&L with all costs, taxes, and margin interest.

    Accepts PnLInput with symbol, side, entry, target, stop, qty, and all costs
    (fees, energy, margin loans, taxes). Returns gross and net P&L scenarios.

    **Request Example:**
    ```json
    {
        "symbol": "ES",
        "side": "long",
        "entry": "5050.00",
        "target": "5100.00",
        "stop": "5030.00",
        "qty": 2,
        "fees_open": "2.00",
        "fees_close": "2.00",
        "tax_mode": "1256",
        "st_rate": "0.24",
        "lt_rate": "0.15"
    }
    ```

    **Response Example:**
    ```json
    {
        "success": true,
        "data": {
            "symbol": "ES",
            "side": "long",
            "qty": 2,
            "entry": "5050.00",
            "target": "5100.00",
            "stop": "5030.00",
            "gross_win": "5000.00",
            "gross_loss": "2000.00",
            "net_win": "4828.65",
            "net_loss": "2032.80",
            "breakdown": {...}
        }
    }
    ```
    """
    try:
        result = calculate_pnl(
            symbol=input_data.symbol,
            side=input_data.side,
            entry=Decimal(str(input_data.entry)),
            target=Decimal(str(input_data.target)),
            stop=Decimal(str(input_data.stop)),
            qty=input_data.qty,
            fees_open=Decimal(str(input_data.fees_open)),
            fees_close=Decimal(str(input_data.fees_close)),
            slippage_open=Decimal(str(input_data.slippage_open or 0)),
            slippage_close=Decimal(str(input_data.slippage_close or 0)),
            energy_kwh=Decimal(str(input_data.energy_kwh or 0)),
            energy_cost_per_kwh=Decimal(str(input_data.energy_cost_per_kwh or "0.14")),
            margin_loans=[
                MarginLoan(loan_amount=loan.amount, apr=loan.apr, days_held=loan.days_held)
                for loan in input_data.margin_loans
            ],
            tax_mode=input_data.tax_mode,
            st_rate=Decimal(str(input_data.st_rate or "0.24")),
            lt_rate=Decimal(str(input_data.lt_rate)) if input_data.lt_rate is not None else None,
        )

        output = PnLOutput(
            symbol=result.symbol,
            side=result.side,
            qty=result.qty,
            entry=result.entry,
            target=result.target,
            stop=result.stop,
            gross_win=result.gross_win,
            gross_loss=result.gross_loss,
            net_win_scenario=result.net_win_scenario,
            net_loss_scenario=result.net_loss_scenario,
            breakdown=result.breakdown,
        )

        return ApiResponse(success=True, data=output)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@app.get("/refs/electricity", tags=["References"])
async def get_electricity_reference() -> ApiResponse:
    """
    Fetch current US average electricity cost (EIA Table 5.3).

    Returns the estimated cost per kWh in dollars.

    **Response Example:**
    ```json
    {
        "success": true,
        "data": {
            "cost_per_kwh": "0.14",
            "source": "EIA Table 5.3 (US Average)",
            "currency": "USD",
            "unit": "per kWh"
        }
    }
    ```
    """
    try:
        cents = fetch_electricity_price_cents()  # live EIA if key set, else 14c avg
        cost = (cents / Decimal("100")).quantize(Decimal("0.0001"))
        return ApiResponse(
            success=True,
            data={
                "cost_per_kwh": str(cost),
                "source": "EIA electricity retail sales (US residential average)",
                "currency": "USD",
                "unit": "per kWh",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@app.get("/refs/sofr", tags=["References"])
async def get_sofr_reference() -> ApiResponse:
    """
    Fetch current SOFR (Secured Overnight Financing Rate) and moving averages.

    Returns the latest SOFR and 30/90-day moving averages.

    **Response Example:**
    ```json
    {
        "success": true,
        "data": {
            "current": "5.33",
            "30_day_avg": "5.32",
            "90_day_avg": "5.30",
            "source": "Federal Reserve",
            "currency": "USD",
            "unit": "Annual %"
        }
    }
    ```
    """
    try:
        sofr_data = fetch_sofr_reference()  # live NY Fed, 1h cache, static fallback
        return ApiResponse(
            success=True,
            data={
                "current": sofr_data.get("current", "5.33"),
                "30_day_avg": sofr_data.get("avg_30", "5.32"),
                "90_day_avg": sofr_data.get("avg_90", "5.30"),
                "source": sofr_data.get("source", "Federal Reserve"),
                "as_of": sofr_data.get("as_of", ""),
                "currency": "USD",
                "unit": "Annual %",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
