"""Energy cost estimation using EIA data."""

from decimal import Decimal


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
