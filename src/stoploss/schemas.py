"""Input validation and output schemas using Pydantic v2."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class SizingInput(BaseModel):
    """Input schema for position sizing calculation."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "ES",
                    "side": "long",
                    "entry": 5050.00,
                    "account_equity": 25000.00,
                    "leverage": 12.0,
                    "pct_stop": 0.004,
                    "risk_cash": 2500.00,
                }
            ]
        }
    }

    symbol: str = Field(
        ...,
        description="Futures contract symbol (validated downstream)",
        min_length=1,
    )
    side: str = Field(
        ...,
        description="Trade direction: long or short",
        min_length=1,
    )
    entry: Decimal = Field(
        ...,
        gt=0,
        decimal_places=4,
        description="Entry price in contract units",
    )
    account_equity: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        description="Account equity in dollars",
    )
    leverage: Decimal = Field(
        default=Decimal("1"),
        ge=Decimal("1"),
        decimal_places=2,
        description="Leverage multiplier (1 = no leverage)",
    )
    pct_stop: Decimal | None = Field(
        default=None,
        ge=0,
        le=1,
        decimal_places=4,
        description="Stop loss as percent of entry (e.g., 0.004 for 0.4%)",
    )
    risk_cash: Decimal | None = Field(
        default=None,
        gt=0,
        decimal_places=2,
        description="Risk budget in dollars — the maximum acceptable loss (required)",
    )
    fees_open: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        decimal_places=2,
        description="Opening trade fee in dollars",
    )
    fees_close: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        decimal_places=2,
        description="Closing trade fee in dollars",
    )


class SizingOutput(BaseModel):
    """Output schema for position sizing result."""

    symbol: str
    side: Literal["long", "short"]
    qty: int = Field(..., gt=0)
    entry: Decimal = Field(..., gt=0)
    stop_price: Decimal = Field(..., gt=0)
    risk_per_unit: Decimal = Field(..., gt=0)
    risk_per_unit_actual: Decimal = Field(..., gt=0)
    risk_dollars_per_contract: Decimal = Field(..., gt=0)
    gross_exposure: Decimal = Field(..., gt=0)
    risk_cash: Decimal = Field(..., gt=0)
    fees_open: Decimal = Field(..., ge=0)
    fees_close: Decimal = Field(..., ge=0)
    slippage_open: Decimal = Field(..., ge=0)
    method: str
    buying_power_qty_cap: int | None = Field(
        default=None,
        description="Max contracts the declared equity x leverage can control",
    )
    capped_by_buying_power: bool = Field(
        default=False,
        description="True when buying power reduced qty below the risk-based qty",
    )


class MarginLoanInput(BaseModel):
    """Single margin loan with APR and duration."""

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "examples": [
                {"amount": 5000.0, "apr": 0.065, "days_held": 5},
            ]
        },
    }

    amount: Decimal = Field(
        ...,
        alias="loan_amount",
        gt=0,
        decimal_places=2,
        description="Principal borrowed in dollars",
    )
    apr: Decimal = Field(
        ...,
        gt=0,
        le=1,
        decimal_places=4,
        description="Annual percentage rate (e.g., 0.065 for 6.5%)",
    )
    days_held: int = Field(
        default=1,
        ge=0,
        description="Number of days held (for accrual calculation)",
    )


class PnLInput(BaseModel):
    """Input schema for P&L calculation."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "ES",
                    "side": "long",
                    "qty": 1,
                    "entry": 5050.00,
                    "target": 5100.00,
                    "stop": 5029.75,
                    "fees_open": 2.00,
                    "fees_close": 2.00,
                    "tax_mode": "section_1256",
                    "st_rate": 0.24,
                    "lt_rate": 0.15,
                    "margin_loans": [
                        {
                            "loan_amount": 5000.00,
                            "apr": 0.065,
                            "days_held": 3,
                        }
                    ],
                }
            ]
        }
    }

    symbol: str = Field(
        ...,
        description="Futures contract symbol (validated downstream)",
        min_length=1,
    )
    side: str = Field(
        ...,
        description="Trade direction",
        min_length=1,
    )
    qty: int = Field(
        ...,
        gt=0,
        description="Number of contracts",
    )
    entry: Decimal = Field(
        ...,
        gt=0,
        decimal_places=4,
        description="Entry price",
    )
    target: Decimal = Field(
        ...,
        gt=0,
        decimal_places=4,
        description="Target exit price (win scenario)",
    )
    stop: Decimal = Field(
        ...,
        gt=0,
        decimal_places=4,
        description="Stop loss price",
    )
    fees_open: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        decimal_places=2,
    )
    fees_close: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        decimal_places=2,
    )
    slippage_open: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        decimal_places=2,
    )
    slippage_close: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        decimal_places=2,
    )
    energy_kwh: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        decimal_places=2,
        description="Energy used in kWh (0.2 kW x 1 hour ≈ 0.2)",
    )
    energy_cost_per_kwh: Decimal = Field(
        default=Decimal("0.14"),
        gt=0,
        decimal_places=4,
        description="Energy price in dollars per kWh",
    )
    tax_mode: Literal["short_term", "short_term_ordinary", "1256", "section_1256"] = Field(
        default="section_1256",
        description="Tax calculation mode",
    )
    st_rate: Decimal = Field(
        default=Decimal("0.24"),
        ge=0,
        le=1,
        decimal_places=4,
        description="Short-term ordinary tax rate",
    )
    lt_rate: Decimal | None = Field(
        default=Decimal("0.15"),
        ge=0,
        le=1,
        decimal_places=4,
        description="Long-term capital gains rate (for §1256 mode)",
    )
    margin_loans: list[MarginLoanInput] = Field(
        default_factory=list,
        max_length=3,
        description="Up to 3 separate margin loans (optional)",
    )


class PnLOutput(BaseModel):
    """Output schema for P&L calculation."""

    symbol: str
    side: Literal["long", "short"]
    qty: int
    entry: Decimal
    target: Decimal
    stop: Decimal
    gross_win: Decimal
    gross_loss: Decimal
    net_win_scenario: Decimal
    net_loss_scenario: Decimal
    breakdown: dict[str, Decimal]


class ApiResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool
    data: SizingOutput | PnLOutput | dict | None = None
    error: str | None = None
