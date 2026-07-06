"""Margin loan interest calculation and SOFR reference rates.

- Margin interest uses a 360-day basis with daily accrual (Schwab/IBKR standard).
- SOFR is fetched live from the NY Fed API (markets.newyorkfed.org) with a
  1-hour cache; on any network/parse failure the Oct-2024 static values are
  returned, clearly labeled as a fallback.
"""

import time
from dataclasses import dataclass
from decimal import Decimal

import requests


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
SOFR_REFERENCE: dict[str, Decimal | str] = {
    "current_rate": Decimal("5.33"),  # % per annum
    "30_day_avg": Decimal("5.35"),
    "90_day_avg": Decimal("5.30"),
    "source": "Federal Reserve Bank of New York",
    "note": "Display reference only; fetch live rates via API for trades",
}


# NY Fed public reference-rate API (no key required)
_NYFED_SOFR_URL = "https://markets.newyorkfed.org/api/rates/secured/sofr/last/1.json"
_NYFED_SOFR_AVG_URL = "https://markets.newyorkfed.org/api/rates/secured/sofrai/last/1.json"
_CACHE_TTL_SECONDS = 3600.0

_sofr_cache: dict[str, str] | None = None
_sofr_cache_at: float = 0.0


def _fetch_sofr_live(timeout: float = 5.0) -> dict[str, str]:
    """Fetch the current SOFR rate and 30/90-day averages from the NY Fed.

    Raises requests.RequestException (or KeyError/IndexError on schema
    surprises); callers are expected to fall back to the static reference.
    """
    rate_resp = requests.get(_NYFED_SOFR_URL, timeout=timeout)
    rate_resp.raise_for_status()
    rate = rate_resp.json()["refRates"][0]

    avg_resp = requests.get(_NYFED_SOFR_AVG_URL, timeout=timeout)
    avg_resp.raise_for_status()
    avg = avg_resp.json()["refRates"][0]

    return {
        "current": str(rate["percentRate"]),
        "avg_30": str(avg["average30day"]),
        "avg_90": str(avg["average90day"]),
        "source": "Federal Reserve Bank of New York (live)",
        "as_of": str(rate.get("effectiveDate", "")),
    }


def fetch_sofr_reference(force_refresh: bool = False) -> dict[str, str]:
    """Return SOFR reference values (live NY Fed, cached 1h, static fallback).

    Returns a dict with keys expected by the API layer/tests:
    - current: current SOFR rate as a string
    - avg_30 / avg_90: moving averages as strings
    - source: where the numbers came from (says "fallback" when static)
    - as_of: effective date of the live rate, or the vintage of the fallback
    """
    global _sofr_cache, _sofr_cache_at

    now = time.monotonic()
    if not force_refresh and _sofr_cache is not None and now - _sofr_cache_at < _CACHE_TTL_SECONDS:
        return dict(_sofr_cache)

    try:
        data = _fetch_sofr_live()
    except (requests.RequestException, KeyError, IndexError, ValueError, TypeError):
        data = {
            "current": str(SOFR_REFERENCE["current_rate"]),
            "avg_30": str(SOFR_REFERENCE["30_day_avg"]),
            "avg_90": str(SOFR_REFERENCE["90_day_avg"]),
            "source": f"{SOFR_REFERENCE['source']} (static fallback)",
            "as_of": "2024-10",
        }

    _sofr_cache, _sofr_cache_at = data, now
    return dict(data)
