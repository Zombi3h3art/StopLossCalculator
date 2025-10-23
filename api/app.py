"""REST API for Stop Loss Calculator using FastAPI."""

from decimal import Decimal

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from src.stoploss.cashflow import calculate_pnl
from src.stoploss.energy import estimate_energy_cost
from src.stoploss.rates import fetch_sofr_reference
from src.stoploss.schemas import ApiResponse, PnLInput, PnLOutput, SizingInput, SizingOutput
from src.stoploss.sizing import size_by_percent_stop

app = FastAPI(
    title="Stop Loss Net Edge Calculator API",
    description="Precision financial calculator for futures trading",
    version="0.1.0",
)

# Enable CORS for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


@app.post("/size", tags=["Sizing"], response_model=ApiResponse)
async def calculate_size(input_data: SizingInput) -> ApiResponse:
    """
    Calculate position size and stop price.

    Accepts a SizingInput with symbol, side, entry, account equity, leverage,
    and percent stop. Returns qty and stop price rounded to contract tick.

    **Request Example:**
    ```json
    {
        "symbol": "ES",
        "side": "long",
        "entry": "5050.00",
        "account_equity": "20000.00",
        "leverage": "3.0",
        "pct_stop": "0.004"
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
            "risk_per_unit": "20.20",
            "gross_exposure": "60000.00"
        }
    }
    ```
    """
    try:
        result = size_by_percent_stop(
            symbol=input_data.symbol,
            side=input_data.side,
            entry=Decimal(str(input_data.entry)),
            account_equity=Decimal(str(input_data.account_equity)),
            leverage=Decimal(str(input_data.leverage)),
            pct_stop=Decimal(str(input_data.pct_stop)),
        )

        output = SizingOutput(
            symbol=result.symbol,
            side=result.side,
            qty=result.qty,
            entry=result.entry,
            stop_price=result.stop_price,
            risk_per_unit=result.risk_per_unit,
            gross_exposure=result.gross_exposure,
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
            margin_loans=input_data.margin_loans or [],
            tax_mode=input_data.tax_mode or "short_term",
            st_rate=Decimal(str(input_data.st_rate or "0.24")),
            lt_rate=Decimal(str(input_data.lt_rate or "0.15")),
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
            net_win=result.net_win_scenario,
            net_loss=result.net_loss_scenario,
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
        cost = estimate_energy_cost(power_kw=Decimal("1"), hours_used=Decimal("1"))  # 1 kWh
        return ApiResponse(
            success=True,
            data={
                "cost_per_kwh": str(cost),  # cost is already $ per 1 kWh
                "source": "EIA Table 5.3 (US Average)",
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
        sofr_data = fetch_sofr_reference()
        return ApiResponse(
            success=True,
            data={
                "current": sofr_data.get("current", "5.33"),
                "30_day_avg": sofr_data.get("avg_30", "5.32"),
                "90_day_avg": sofr_data.get("avg_90", "5.30"),
                "source": "Federal Reserve",
                "currency": "USD",
                "unit": "Annual %",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
