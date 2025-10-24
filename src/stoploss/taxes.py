"""Federal income tax calculation for trading.

Two regimes:
1. Short-term ordinary (stocks, non-§1256 trades): standard income tax rate (24%, 35%, 37%, etc.)
2. §1256 Futures (Form 6781): 60% long-term capital gains + 40% short-term ordinary

References:
- IRS Pub 550: Investment Income and Expenses
- IRS Form 6781: Gains and Losses from Section 1256 Contracts and Straddles
"""

from decimal import Decimal
from typing import Literal

TaxMode = Literal["short_term", "short_term_ordinary", "1256", "section_1256"]


def _normalize_rate(rate: Decimal) -> Decimal:
    """Return tax rate as a [0, 1] Decimal, accepting 0-100 percentages."""

    rate = Decimal(str(rate))
    if rate < 0:
        raise ValueError(f"tax rate must be non-negative, got {rate}")
    if rate > 1:
        if rate <= 100:
            rate = rate / Decimal("100")
        else:
            raise ValueError(f"tax rate must be <= 100, got {rate}")
    return rate


def calculate_tax_short_term(gross_profit: Decimal, tax_rate: Decimal) -> Decimal:
    """Calculate tax on short-term ordinary income.

    Args:
        gross_profit: Profit before tax (in dollars)
        tax_rate: Federal tax rate as decimal (e.g., 0.24 for 24%)

    Returns:
        Tax owed (0 if no profit)
    """
    gross_profit = Decimal(str(gross_profit))
    tax_rate = _normalize_rate(tax_rate)

    if gross_profit <= 0:
        return Decimal("0")

    return (gross_profit * tax_rate).quantize(Decimal("0.01"))


def calculate_tax_section_1256(
    gross_profit: Decimal,
    st_rate: Decimal,
    lt_rate: Decimal,
) -> Decimal:
    """Calculate tax on §1256 futures under 60/40 split.

    Formula:
        tax = gross_profit * (0.60 * lt_rate + 0.40 * st_rate)

    Args:
        gross_profit: Profit before tax (in dollars)
        st_rate: Short-term ordinary rate (e.g., 0.24)
        lt_rate: Long-term capital gains rate (e.g., 0.15)

    Returns:
        Tax owed (0 if no profit)

    References:
        Form 6781 treatment: 60% of gains taxed at LT LTCG rate, 40% at ordinary ST rate.
    """
    gross_profit = Decimal(str(gross_profit))
    st_rate = _normalize_rate(st_rate)
    lt_rate = _normalize_rate(lt_rate)

    if gross_profit <= 0:
        return Decimal("0")

    blended_rate = Decimal("0.60") * lt_rate + Decimal("0.40") * st_rate
    return (gross_profit * blended_rate).quantize(Decimal("0.01"))


def calculate_tax(
    gross_profit: Decimal,
    mode: TaxMode,
    st_rate: Decimal,
    lt_rate: Decimal | None = None,
) -> Decimal:
    """Calculate federal income tax based on mode.

    Args:
        gross_profit: Profit before tax (in dollars)
        mode: "short_term_ordinary" or "section_1256"
        st_rate: Short-term ordinary tax rate
        lt_rate: Long-term capital gains rate (required for section_1256, optional for ST)

    Returns:
        Tax owed in dollars
    """
    normalized_mode: str
    if mode in ("short_term", "short_term_ordinary"):
        normalized_mode = "short_term_ordinary"
    elif mode in ("1256", "section_1256"):
        normalized_mode = "section_1256"
    else:
        raise ValueError(f"Unknown tax mode: {mode}")

    if normalized_mode == "short_term_ordinary":
        return calculate_tax_short_term(gross_profit, st_rate)

    if lt_rate is None:
        raise ValueError("lt_rate required for section_1256 mode")

    return calculate_tax_section_1256(gross_profit, st_rate, lt_rate)
