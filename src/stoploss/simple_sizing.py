"""Generic stop loss calculator - works with any entry price and leverage.

No futures tickers needed. Just enter:
- Entry price
- Account equity
- Leverage
- Acceptable risk %

Core formula:
    Stop (SHORT) = Entry x (1 + adverse_move_pct)
    Stop (LONG) = Entry x (1 - adverse_move_pct)

Where: adverse_move_pct = (acceptable_risk / leverage) / 100
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class SimpleSizingResult:
    """Generic position sizing result."""

    entry_price: Decimal
    side: str  # "long" or "short"
    leverage: Decimal
    account_equity: Decimal  # your cash
    notional_exposure: Decimal  # equity * leverage
    quantity: Decimal  # units controlled
    acceptable_risk_pct: Decimal  # your risk cap (%)
    allowed_adverse_move_pct: Decimal  # breathing room (%)
    stop_price: Decimal  # where you exit
    max_loss_dollars: Decimal  # max loss if stopped


def calculate_stop_loss(
    entry_price,
    side: str,
    account_equity,
    leverage,
    acceptable_risk_pct,
) -> SimpleSizingResult:
    """Calculate stop loss placement for any asset.

    Args:
        entry_price: Entry price (any currency, any asset)
        side: "long" or "short"
        account_equity: Your trading account equity in dollars
        leverage: Leverage multiplier (1x, 10x, 100x, etc.)
        acceptable_risk_pct: Max risk as % of equity (e.g., 11 for 11%)

    Returns:
        SimpleSizingResult with stop price, allowed move, max loss

    Example:
        >>> result = calculate_stop_loss(
        ...     entry_price=22.8524,
        ...     side="short",
        ...     account_equity=100,
        ...     leverage=10,
        ...     acceptable_risk_pct=11
        ... )
        >>> print(f"Stop: ${result.stop_price}")
        >>> print(f"Room: {result.allowed_adverse_move_pct}%")
    """
    entry = Decimal(str(entry_price))
    equity = Decimal(str(account_equity))
    lev = Decimal(str(leverage))
    risk_pct = Decimal(str(acceptable_risk_pct))

    # Notional = equity * leverage
    notional = equity * lev

    # Quantity = notional / entry price
    # (how many "units" you control at entry)
    qty = notional / entry

    # Allowed adverse move % = risk_pct / leverage
    # This is the formula from your analysis
    allowed_adverse_pct = risk_pct / lev

    # Convert % to decimal (11% -> 0.11 -> divide by 100 -> 0.0011 factor)
    move_factor = allowed_adverse_pct / Decimal("100")

    # Calculate stop based on side
    if side.lower() == "short":
        # For SHORT: price goes UP to stop you out
        # Stop = Entry * (1 + move_factor)
        stop = entry * (Decimal("1") + move_factor)
    elif side.lower() == "long":
        # For LONG: price goes DOWN to stop you out
        # Stop = Entry * (1 - move_factor)
        stop = entry * (Decimal("1") - move_factor)
    else:
        raise ValueError(f"side must be 'long' or 'short', got {side}")

    # Max loss = acceptable_risk_pct * equity / 100
    max_loss = (risk_pct / Decimal("100")) * equity

    return SimpleSizingResult(
        entry_price=entry,
        side=side.lower(),
        leverage=lev,
        account_equity=equity,
        notional_exposure=notional,
        quantity=qty,
        acceptable_risk_pct=risk_pct,
        allowed_adverse_move_pct=allowed_adverse_pct,
        stop_price=stop,
        max_loss_dollars=max_loss,
    )
