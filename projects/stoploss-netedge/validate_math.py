"""Quick validation test for core math modules."""

import sys
from decimal import Decimal

# Add src to path for testing
sys.path.insert(0, "src")

from stoploss.cashflow import calculate_pnl
from stoploss.contracts import get_contract
from stoploss.energy import estimate_energy_cost
from stoploss.rates import calculate_margin_interest
from stoploss.sizing import size_by_percent_stop
from stoploss.taxes import calculate_tax


def test_contracts():
    """Validate contract specs."""
    print("Testing contracts...")
    es = get_contract("ES")
    assert es.ppv_per_unit == Decimal("50")
    assert es.min_tick == Decimal("0.25")

    # Test tick rounding
    rounded = es.round_to_tick(Decimal("5029.8"))
    assert rounded == Decimal("5029.75"), f"Expected 5029.75, got {rounded}"
    print("  ✓ ES contract specs correct")
    print(f"  ✓ Tick rounding: 5029.8 → {rounded}")


def test_sizing():
    """Validate position sizing."""
    print("\nTesting sizing...")
    size = size_by_percent_stop(
        symbol="ES",
        side="long",
        entry=Decimal("5050"),
        account_equity=Decimal("20000"),
        leverage=Decimal("3"),
        pct_stop=Decimal("0.004"),
    )
    assert size.qty > 0, "Qty should be positive"
    assert size.stop_price < Decimal("5050"), "Stop should be below entry for long"
    print(f"  ✓ Qty: {size.qty} contracts")
    print(f"  ✓ Entry: {size.entry_price}, Stop: {size.stop_price}")
    print(f"  ✓ Loss/unit: {size.loss_per_unit} pts")
    return size


def test_pnl(size):
    """Validate P&L calculation."""
    print("\nTesting P&L...")
    pnl = calculate_pnl(
        symbol="ES",
        side="long",
        qty=size.qty,
        entry=size.entry_price,
        target=Decimal("5100"),
        stop=size.stop_price,
        fees_open=Decimal("2"),
        fees_close=Decimal("2"),
        slip_open=Decimal("0"),
        slip_close=Decimal("0"),
    )
    assert pnl.gross_win > 0, "Gross win should be positive"
    assert pnl.gross_loss > 0, "Gross loss should be positive"
    print(f"  ✓ Gross win: ${pnl.gross_win:.2f}")
    print(f"  ✓ Gross loss: ${pnl.gross_loss:.2f}")
    print(f"  ✓ Total costs: ${pnl.total_fees_slip:.2f}")
    return pnl


def test_taxes(pnl):
    """Validate tax calculation."""
    print("\nTesting taxes (§1256)...")
    tax = calculate_tax(
        gross_profit=pnl.gross_win - pnl.total_fees_slip,
        mode="section_1256",
        st_rate=Decimal("0.24"),
        lt_rate=Decimal("0.15"),
    )
    assert tax >= 0, "Tax should be non-negative"
    blended_rate = Decimal("0.60") * Decimal("0.15") + Decimal("0.40") * Decimal("0.24")
    expected = (pnl.gross_win - pnl.total_fees_slip) * blended_rate
    assert abs(tax - expected) < Decimal("0.01"), "Tax calculation mismatch"
    print(f"  ✓ §1256 tax (60% LT @ 15% + 40% ST @ 24%): ${tax:.2f}")
    print(f"  ✓ Blended rate: {float(blended_rate):.2%}")
    return tax


def test_energy():
    """Validate energy cost."""
    print("\nTesting energy cost...")
    cost = estimate_energy_cost(
        power_kw=Decimal("0.2"),
        hours_used=Decimal("1"),
        kwh_price_cents=Decimal("14"),
    )
    assert cost > 0, "Energy cost should be positive"
    expected = Decimal("0.2") * Decimal("1") * Decimal("14") / Decimal("100")
    assert cost == expected.quantize(Decimal("0.01")), "Energy cost calculation mismatch"
    print(f"  ✓ Energy (0.2 kW × 1 hr @ 14¢/kWh): ${cost:.2f}")


def test_margin():
    """Validate margin interest."""
    print("\nTesting margin interest...")
    interest = calculate_margin_interest(
        loan_amount=Decimal("5000"),
        apr=Decimal("0.065"),
        days_held=3,
    )
    assert interest > 0, "Interest should be positive"
    expected = Decimal("5000") * Decimal("0.065") * Decimal("3") / Decimal("360")
    assert interest == expected.quantize(Decimal("0.01")), "Margin interest calculation mismatch"
    print(f"  ✓ Margin interest (${5000} @ 6.5% APR for 3 days): ${interest:.2f}")


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("STOPLOSS-NETEDGE: Math Validation Suite")
    print("=" * 60)

    try:
        test_contracts()
        size = test_sizing()
        pnl = test_pnl(size)
        tax = test_taxes(pnl)
        test_energy()
        test_margin()

        print("\n" + "=" * 60)
        print("✅ All math validations PASSED")
        print("=" * 60)

        # Show full scenario
        print("\n📊 Full ES Trade Scenario:")
        print(f"  Entry: {size.entry_price} | Stop: {size.stop_price} | Target: 5100")
        print(
            f"  Qty: {size.qty} contracts | Gross Win: ${pnl.gross_win:.2f} | Net Win: ${pnl.net_win - tax:.2f}"
        )
        print(f"  Tax (§1256): ${tax:.2f} | Net after tax: ${pnl.net_win - tax:.2f}")

    except Exception as e:
        print(f"\n❌ Test failed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
