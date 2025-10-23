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
                    "account_equity": 20000.00,
                    "leverage": 3.0,
                    "pct_stop": 0.004,
                }
            ]
        }
    }

    symbol: str = Field(
        ...,
        description="Futures contract: ES, NQ, CL, or GC",
        pattern="^(ES|NQ|CL|GC)$",
    )
    side: Literal["long", "short"] = Field(
        ...,
        description="Trade direction: long or short",
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
        description="Maximum risk in dollars (for ATR method)",
    )
    atr: Decimal | None = Field(
        default=None,
        gt=0,
        decimal_places=4,
        description="Average True Range (for ATR method)",
    )
    k_atr: Decimal = Field(
        default=Decimal("2"),
        gt=0,
        decimal_places=2,
        description="ATR multiplier (default 2.0)",
    )
    swing_low: Decimal | None = Field(
        default=None,
        decimal_places=4,
        description="Swing low/high for structure-based stop (optional)",
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

    qty: int = Field(
        ...,
        gt=0,
        description="Number of contracts to trade",
    )
    entry_price: Decimal = Field(
        ...,
        gt=0,
        description="Entry price (validated)",
    )
    stop_price: Decimal = Field(
        ...,
        gt=0,
        description="Stop loss price (rounded to nearest tick)",
    )
    loss_per_unit: Decimal = Field(
        ...,
        gt=0,
        description="Loss per contract in price units",
    )
    loss_dollars: Decimal = Field(
        ...,
        gt=0,
        description="Dollar loss if stopped out (qty x ppv x loss_per_unit)",
    )
    gross_exposure: Decimal = Field(
        ...,
        gt=0,
        description="Total exposure (account_equity x leverage)",
    )
    method: str = Field(
        ...,
        description="Sizing method used: percent_stop or atr_stop",
    )


class MarginLoanInput(BaseModel):
    """Single margin loan with APR and duration."""

    loan_amount: Decimal = Field(
        ...,
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
        description="Futures contract: ES, NQ, CL, or GC",
        pattern="^(ES|NQ|CL|GC)$",
    )
    side: Literal["long", "short"] = Field(
        ...,
        description="Trade direction",
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
    slip_open: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        decimal_places=2,
    )
    slip_close: Decimal = Field(
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
    power_kw: Decimal = Field(
        default=Decimal("0.2"),
        gt=0,
        decimal_places=2,
        description="Equipment power draw in kilowatts (default 0.2 kW)",
    )
    energy_rate_cents: Decimal = Field(
        default=Decimal("14"),
        gt=0,
        decimal_places=1,
        description="Energy price in cents per kWh (default 14¢ US average)",
    )
    tax_mode: Literal["short_term_ordinary", "section_1256"] = Field(
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
    qty: int
    entry_price: Decimal
    target_price: Decimal
    stop_price: Decimal

    gross_win: Decimal = Field(
        ...,
        description="Gross profit at target (before costs/taxes)",
    )
    gross_loss: Decimal = Field(
        ...,
        description="Gross loss at stop",
    )

    fees_open: Decimal
    fees_close: Decimal
    slip_open: Decimal
    slip_close: Decimal
    total_fees_slip: Decimal = Field(
        ...,
        description="Sum of all fees and slippage",
    )

    energy_cost: Decimal = Field(
        ...,
        description="Energy cost in dollars",
    )
    margin_interest: Decimal = Field(
        ...,
        description="Total margin interest (sum of all loans)",
    )
    tax_on_win: Decimal = Field(
        ...,
        description="Federal income tax on win scenario",
    )

    net_win: Decimal = Field(
        ...,
        description="Net profit after all costs and taxes",
    )
    net_loss: Decimal = Field(
        ...,
        description="Net loss (including all costs, no tax benefit)",
    )


class ApiResponse(BaseModel):
    """Standard API response wrapper."""

    status: Literal["success", "error"] = Field(...)
    data: SizingOutput | PnLOutput | None = Field(
        default=None,
        description="Result data (null on error)",
    )
    error: str | None = Field(
        default=None,
        description="Error message (null on success)",
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp",
    )
