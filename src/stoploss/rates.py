"""Margin loan interest calculation and SOFR reference rates."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class MarginLoan:
    """Single margin loan with APR and days held."""

    loan_amount: Decimal
    apr: Decimal
    days_held: int = 1


def calculate_margin_interest(
    loan_amount: Decimal,
    apr: Decimal,
    days_held: int = 1,
    basis: int = 360,
) -> Decimal:
    """Calculate margin interest accrual (daily, 360-day year basis).

    Formula:
        interest = loan_amount * apr * (days_held / 360)

    Args:
        loan_amount: Principal in dollars
        apr: Annual percentage rate (e.g., 0.10 for 10%)
        days_held: Number of days held
        basis: Day count basis (360 or 365; brokers typically use 360)

    Returns:
        Interest accrued in dollars

    References:
        Schwab, IBKR, and most brokers use 360-day basis for daily accrual,
        billed monthly.
    """
    loan_amount = Decimal(str(loan_amount))
    apr = Decimal(str(apr))

    if loan_amount <= 0:
        raise ValueError(f"loan_amount must be positive, got {loan_amount}")
    if apr < 0 or apr > 1:
        raise ValueError(f"apr must be in [0, 1], got {apr}")
    if days_held < 0:
        raise ValueError(f"days_held must be non-negative, got {days_held}")

    interest = loan_amount * apr * Decimal(days_held) / Decimal(basis)
    return interest.quantize(Decimal("0.01"))


def calculate_total_margin_interest(loans: list[MarginLoan]) -> Decimal:
    """Sum interest across up to 3 margin loans.

    Args:
        loans: List of MarginLoan objects (typically 1-3)

    Returns:
        Total margin interest in dollars
    """
    if len(loans) > 3:
        raise ValueError(f"Maximum 3 loans supported, got {len(loans)}")

    total = Decimal("0")
    for loan in loans:
        interest = calculate_margin_interest(
            loan.loan_amount,
            loan.apr,
            loan.days_held,
        )
        total += interest

    return total.quantize(Decimal("0.01"))


# Reference SOFR rates (as of Oct 2024, from Federal Reserve)
# These are display-only; update periodically or fetch live
SOFR_REFERENCE = {
    "current_rate": Decimal("5.33"),  # % per annum
    "30_day_avg": Decimal("5.35"),
    "90_day_avg": Decimal("5.30"),
    "source": "Federal Reserve Bank of New York",
    "note": "Display reference only; fetch live rates via API for trades",
}


def sofr_context_display() -> dict:
    """Return current SOFR for UI reference (display only).

    Typical brokers (Schwab, IBKR, etc.) peg margin rates to SOFR + spread.
    Example: margin APR = SOFR + 150 bps = 5.33% + 1.50% = 6.83%

    Returns:
        Dictionary with SOFR rates and context
    """
    return SOFR_REFERENCE.copy()
