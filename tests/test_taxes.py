"""Unit tests for taxes module (federal income tax calculations)."""

from decimal import Decimal

from src.stoploss.taxes import calculate_tax_section_1256, calculate_tax_short_term


class TestShortTermTax:
    """Test short-term ordinary income tax calculations."""

    def test_short_term_24_percent(self):
        """24% short-term tax bracket."""
        gross_profit = Decimal("1000")
        tax_rate = Decimal("0.24")
        tax = calculate_tax_short_term(gross_profit, tax_rate)
        assert tax == Decimal("240")

    def test_short_term_35_percent(self):
        """35% short-term tax bracket."""
        gross_profit = Decimal("1000")
        tax_rate = Decimal("0.35")
        tax = calculate_tax_short_term(gross_profit, tax_rate)
        assert tax == Decimal("350")

    def test_short_term_37_percent(self):
        """37% short-term tax bracket (top)."""
        gross_profit = Decimal("1000")
        tax_rate = Decimal("0.37")
        tax = calculate_tax_short_term(gross_profit, tax_rate)
        assert tax == Decimal("370")

    def test_short_term_zero_profit(self):
        """No tax on zero profit."""
        tax = calculate_tax_short_term(Decimal("0"), Decimal("0.24"))
        assert tax == Decimal("0")

    def test_short_term_loss_produces_zero_tax(self):
        """Losses do not produce tax (should be 0)."""
        tax = calculate_tax_short_term(Decimal("-500"), Decimal("0.24"))
        assert tax == Decimal("0")

    def test_short_term_small_profit(self):
        """Test with small profit."""
        gross_profit = Decimal("100")
        tax_rate = Decimal("0.24")
        tax = calculate_tax_short_term(gross_profit, tax_rate)
        assert tax == Decimal("24")

    def test_short_term_large_profit(self):
        """Test with large profit."""
        gross_profit = Decimal("50000")
        tax_rate = Decimal("0.37")
        tax = calculate_tax_short_term(gross_profit, tax_rate)
        assert tax == Decimal("18500")

    def test_short_term_with_decimal_rate(self):
        """Test with non-standard decimal tax rate."""
        gross_profit = Decimal("1000")
        tax_rate = Decimal("0.2525")  # Between brackets
        tax = calculate_tax_short_term(gross_profit, tax_rate)
        assert tax == Decimal("252.50")


class TestSection1256Tax:
    """Test IRS §1256 60/40 blended tax calculations (Form 6781)."""

    def test_1256_basic_es_trade(self):
        """ES trade with standard rates."""
        gross_profit = Decimal("1000")
        st_rate = Decimal("0.24")  # Short-term ordinary
        lt_rate = Decimal("0.15")  # Long-term capital gains
        tax = calculate_tax_section_1256(gross_profit, st_rate, lt_rate)

        # Tax = 1000 * (0.60 * 0.15 + 0.40 * 0.24)
        # = 1000 * (0.09 + 0.096) = 1000 * 0.186 = 186
        expected = Decimal("186")
        assert tax == expected

    def test_1256_zero_profit(self):
        """No tax on zero profit."""
        tax = calculate_tax_section_1256(Decimal("0"), Decimal("0.24"), Decimal("0.15"))
        assert tax == Decimal("0")

    def test_1256_loss_produces_zero_tax(self):
        """Losses do not produce tax."""
        tax = calculate_tax_section_1256(Decimal("-500"), Decimal("0.24"), Decimal("0.15"))
        assert tax == Decimal("0")

    def test_1256_60_40_split(self):
        """Verify 60/40 split in formula."""
        gross_profit = Decimal("100")
        st_rate = Decimal("0.40")
        lt_rate = Decimal("0.20")

        # Tax = 100 * (0.60 * 0.20 + 0.40 * 0.40)
        # = 100 * (0.12 + 0.16) = 100 * 0.28 = 28
        tax = calculate_tax_section_1256(gross_profit, st_rate, lt_rate)
        assert tax == Decimal("28")

    def test_1256_high_st_rate(self):
        """Test with high short-term rate (37%)."""
        gross_profit = Decimal("1000")
        st_rate = Decimal("0.37")
        lt_rate = Decimal("0.20")

        # Tax = 1000 * (0.60 * 0.20 + 0.40 * 0.37)
        # = 1000 * (0.12 + 0.148) = 1000 * 0.268 = 268
        tax = calculate_tax_section_1256(gross_profit, st_rate, lt_rate)
        assert tax == Decimal("268")

    def test_1256_equal_rates(self):
        """Test when both rates are equal."""
        gross_profit = Decimal("1000")
        rate = Decimal("0.25")

        # Tax = 1000 * (0.60 * 0.25 + 0.40 * 0.25)
        # = 1000 * (0.15 + 0.10) = 1000 * 0.25 = 250
        tax = calculate_tax_section_1256(gross_profit, rate, rate)
        assert tax == Decimal("250")

    def test_1256_vs_short_term_comparison(self):
        """§1256 should generally be favorable vs straight short-term."""
        gross_profit = Decimal("1000")

        # Compare 37% short-term vs §1256 with 37% ST and 20% LT
        st_only = calculate_tax_short_term(gross_profit, Decimal("0.37"))
        sec_1256 = calculate_tax_section_1256(gross_profit, Decimal("0.37"), Decimal("0.20"))

        # §1256 should be less than straight 37%
        assert sec_1256 < st_only

    def test_1256_large_profit(self):
        """Test with large profit."""
        gross_profit = Decimal("100000")
        st_rate = Decimal("0.37")
        lt_rate = Decimal("0.15")

        tax = calculate_tax_section_1256(gross_profit, st_rate, lt_rate)

        # Tax = 100000 * (0.60 * 0.15 + 0.40 * 0.37)
        # = 100000 * (0.09 + 0.148) = 100000 * 0.238 = 23800
        assert tax == Decimal("23800")

    def test_1256_precision_with_decimal(self):
        """Verify Decimal precision is maintained."""
        gross_profit = Decimal("1234.56")
        st_rate = Decimal("0.37")
        lt_rate = Decimal("0.15")

        tax = calculate_tax_section_1256(gross_profit, st_rate, lt_rate)

        # Should maintain precision
        assert tax == tax.quantize(Decimal("0.01"))


class TestTaxComparison:
    """Compare tax modes for the same scenario."""

    def test_st_vs_1256_favorable(self):
        """Show §1256 advantage in many scenarios."""
        scenarios = [
            (Decimal("1000"), Decimal("0.37"), Decimal("0.15")),
            (Decimal("5000"), Decimal("0.35"), Decimal("0.20")),
            (Decimal("50000"), Decimal("0.37"), Decimal("15")),
        ]

        for profit, st_rate, lt_rate in scenarios:
            st_tax = calculate_tax_short_term(profit, st_rate)
            sec_1256_tax = calculate_tax_section_1256(profit, st_rate, lt_rate)

            # Usually §1256 is better or equal when rates differ significantly
            assert sec_1256_tax <= st_tax
