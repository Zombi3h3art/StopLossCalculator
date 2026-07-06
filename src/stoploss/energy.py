"""Energy cost estimation using EIA data.

The US-average residential electricity price can be fetched live from the EIA
API v2 (requires a free key in the EIA_API_KEY env var); otherwise the ~14c/kWh
2024 average from EIA Table 5.3 is used.
"""

import os
import time
from decimal import Decimal

import requests


def estimate_energy_cost(
    power_kw: Decimal,
    hours_used: Decimal,
    kwh_price_cents: Decimal | None = None,
) -> Decimal:
    """Estimate energy cost for trading session.

    Args:
        power_kw: Power draw in kilowatts (typical desktop ~0.15-0.25 kW)
        hours_used: Hours of session
        kwh_price_cents: Price per kWh in cents (default ~14¢ US average from EIA)

    Returns:
        Energy cost in dollars

    Note:
        Default 14¢/kWh is approximate US residential average (2024).
        Source: EIA Table 5.3 (Electric Power Monthly)
    """
    power_kw = Decimal(str(power_kw))
    hours_used = Decimal(str(hours_used))

    if kwh_price_cents is None:
        kwh_price_cents = Decimal("14")  # US average ¢/kWh

    kwh_price_cents = Decimal(str(kwh_price_cents))

    if power_kw <= 0:
        raise ValueError(f"power_kw must be positive, got {power_kw}")
    if hours_used <= 0:
        raise ValueError(f"hours_used must be positive, got {hours_used}")
    if kwh_price_cents <= 0:
        raise ValueError(f"kwh_price_cents must be positive, got {kwh_price_cents}")

    kwh_used = power_kw * hours_used
    cost_cents = kwh_used * kwh_price_cents
    cost_dollars = cost_cents / Decimal("100")

    return cost_dollars.quantize(Decimal("0.01"))


_DEFAULT_PRICE_CENTS = Decimal("14")  # EIA Table 5.3, US residential avg (2024)
_EIA_URL = "https://api.eia.gov/v2/electricity/retail-sales/data/"
_CACHE_TTL_SECONDS = 3600.0

_price_cache: Decimal | None = None
_price_cache_at: float = 0.0


def fetch_electricity_price_cents(
    api_key: str | None = None,
    timeout: float = 5.0,
    force_refresh: bool = False,
) -> Decimal:
    """US-average residential electricity price in cents/kWh.

    Uses the EIA API v2 when a key is provided (or in EIA_API_KEY); cached for
    an hour. Any failure — or no key — returns the static ~14c/kWh average.
    """
    global _price_cache, _price_cache_at

    now = time.monotonic()
    if (
        not force_refresh
        and _price_cache is not None
        and now - _price_cache_at < _CACHE_TTL_SECONDS
    ):
        return _price_cache

    key = api_key or os.environ.get("EIA_API_KEY")
    if not key:
        return _DEFAULT_PRICE_CENTS

    try:
        resp = requests.get(
            _EIA_URL,
            params={
                "api_key": key,
                "frequency": "monthly",
                "data[0]": "price",
                "facets[sectorid][]": "RES",
                "facets[stateid][]": "US",
                "sort[0][column]": "period",
                "sort[0][direction]": "desc",
                "length": "1",
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        price = Decimal(str(resp.json()["response"]["data"][0]["price"]))
    except (requests.RequestException, KeyError, IndexError, ValueError, TypeError):
        return _DEFAULT_PRICE_CENTS

    _price_cache, _price_cache_at = price, now
    return price


# Typical energy costs for trading setup (reference)
ENERGY_PROFILES = {
    "laptop": {
        "power_kw": Decimal("0.15"),
        "description": "Laptop + 1 external monitor",
    },
    "desktop_single": {
        "power_kw": Decimal("0.20"),
        "description": "Desktop PC + 2 monitors",
    },
    "desktop_multi": {
        "power_kw": Decimal("0.35"),
        "description": "Desktop PC + 4 monitors + peripherals",
    },
    "datacenter_tier": {
        "power_kw": Decimal("0.50"),
        "description": "High-end colocation setup",
    },
}
