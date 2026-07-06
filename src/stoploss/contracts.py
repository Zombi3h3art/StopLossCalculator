"""Futures contract specifications (ES, NQ, CL, GC + CME micros).

Reference: CME Group specifications:
- ES (E-mini S&P 500): $50 per full point, 0.25 index point tick = $12.50
- NQ (E-mini Nasdaq 100): $20 per full point, 0.25 index point tick = $5.00
- CL (Light Sweet Crude Oil): $1,000 per contract per full point, $0.01 tick = $10.00
- GC (Gold Futures): $100 per full ounce, $0.10 tick = $10.00

Micros (each exactly 1/10 of its parent; verified vs CME/TradeStation 2026-07):
- MES: $5/pt, 0.25 tick = $1.25   - MNQ: $2/pt, 0.25 tick = $0.50
- MCL: $100/pt, $0.01 tick = $1.00 - MGC: $10/pt, $0.10 tick = $1.00
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

Symbol = Literal["ES", "NQ", "CL", "GC", "MES", "MNQ", "MCL", "MGC"]


@dataclass(frozen=True)
class FuturesContract:
    """Contract specification with price/tick conversion."""

    symbol: Symbol
    ppv_per_unit: Decimal  # $ per one price unit (ES=$50/pt, NQ=$20/pt, CL=$1000/pt, GC=$100/pt)
    min_tick: Decimal  # Minimum tick size in price units
    tick_value: Decimal  # $ value of one minimum tick
    description: str

    @property
    def point_value(self) -> Decimal:
        """Dollar value per full price point (alias for ppv_per_unit)."""

        return self.ppv_per_unit

    def round_to_tick(self, price: Decimal) -> Decimal:
        """Round a price to the nearest valid tick."""
        price = Decimal(str(price))
        if self.min_tick <= 0:
            raise ValueError(f"min_tick must be positive, got {self.min_tick}")
        units = (price / self.min_tick).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return units * self.min_tick

    def pnl_for_move(self, qty: int | float, price_move: Decimal) -> Decimal:
        """Calculate P&L for a given quantity and price move."""
        qty_decimal = Decimal(str(qty))
        price_move_decimal = Decimal(str(price_move))
        return qty_decimal * price_move_decimal * self.point_value


# Contract specifications from CME
CONTRACTS: dict[Symbol, FuturesContract] = {
    "ES": FuturesContract(
        symbol="ES",
        ppv_per_unit=Decimal("50"),  # $50 per index point
        min_tick=Decimal("0.25"),  # 0.25 index points
        tick_value=Decimal("12.50"),  # $12.50 per tick
        description="E-mini S&P 500 (CME ES)",
    ),
    "NQ": FuturesContract(
        symbol="NQ",
        ppv_per_unit=Decimal("20"),  # $20 per index point
        min_tick=Decimal("0.25"),  # 0.25 index points
        tick_value=Decimal("5.00"),  # $5.00 per tick
        description="E-mini Nasdaq 100 (CME NQ)",
    ),
    "CL": FuturesContract(
        symbol="CL",
        ppv_per_unit=Decimal("1000"),  # $1,000 per full point (per barrel)
        min_tick=Decimal("0.01"),  # $0.01 per barrel
        tick_value=Decimal("10.00"),  # $10.00 per tick
        description="Light Sweet Crude Oil (NYMEX CL)",
    ),
    "GC": FuturesContract(
        symbol="GC",
        ppv_per_unit=Decimal("100"),  # $100 per troy ounce
        min_tick=Decimal("0.10"),  # $0.10 per ounce
        tick_value=Decimal("10.00"),  # $10.00 per tick
        description="Gold Futures (COMEX GC)",
    ),
    "MES": FuturesContract(
        symbol="MES",
        ppv_per_unit=Decimal("5"),  # $5 per index point (1/10 ES)
        min_tick=Decimal("0.25"),
        tick_value=Decimal("1.25"),
        description="Micro E-mini S&P 500 (CME MES)",
    ),
    "MNQ": FuturesContract(
        symbol="MNQ",
        ppv_per_unit=Decimal("2"),  # $2 per index point (1/10 NQ)
        min_tick=Decimal("0.25"),
        tick_value=Decimal("0.50"),
        description="Micro E-mini Nasdaq 100 (CME MNQ)",
    ),
    "MCL": FuturesContract(
        symbol="MCL",
        ppv_per_unit=Decimal("100"),  # $100 per full point, 100 barrels (1/10 CL)
        min_tick=Decimal("0.01"),
        tick_value=Decimal("1.00"),
        description="Micro WTI Crude Oil (NYMEX MCL)",
    ),
    "MGC": FuturesContract(
        symbol="MGC",
        ppv_per_unit=Decimal("10"),  # $10 per troy ounce, 10 oz (1/10 GC)
        min_tick=Decimal("0.10"),
        tick_value=Decimal("1.00"),
        description="Micro Gold (COMEX MGC)",
    ),
}

# Parent -> micro sibling (1/10 size), used for sizing guidance
MICRO_OF: dict[str, str] = {"ES": "MES", "NQ": "MNQ", "CL": "MCL", "GC": "MGC"}


def get_contract(symbol: Symbol) -> FuturesContract:
    """Retrieve contract specification by symbol."""
    if symbol not in CONTRACTS:
        raise ValueError(f"Unknown symbol {symbol}. Valid: {', '.join(CONTRACTS.keys())}")
    return CONTRACTS[symbol]


def validate_symbol(symbol: str) -> Symbol:
    """Validate and normalize symbol."""
    upper_sym = symbol.upper().strip()
    if upper_sym not in CONTRACTS:
        raise ValueError(f"Unknown symbol {upper_sym}. Valid: {', '.join(CONTRACTS.keys())}")
    return upper_sym  # type: ignore
