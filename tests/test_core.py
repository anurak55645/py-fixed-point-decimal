import unittest

from py_fixed_point_decimal import FixedPointDecimal


class TestConstruction(unittest.TestCase):
    def test_from_int(self):
        v = FixedPointDecimal(3)
        self.assertEqual(v.raw, 300)
        self.assertEqual(v.to_str(), "3.00")

    def test_from_negative_int(self):
        v = FixedPointDecimal(-3)
        self.assertEqual(v.raw, -300)
        self.assertEqual(v.to_str(), "-3.00")

    def test_from_zero(self):
        v = FixedPointDecimal(0)
        self.assertEqual(v.raw, 0)
        self.assertEqual(v.to_str(), "0.00")

    def test_from_string_with_fraction(self):
        v = FixedPointDecimal("1.23")
        self.assertEqual(v.raw, 123)
        self.assertEqual(v.to_str(), "1.23")

    def test_from_string_single_fraction_digit(self):
        v = FixedPointDecimal("1.2")
        self.assertEqual(v.raw, 120)
        self.assertEqual(v.to_str(), "1.20")

    def test_from_string_no_fraction(self):
        v = FixedPointDecimal("42")
        self.assertEqual(v.raw, 4200)
        self.assertEqual(v.to_str(), "42.00")

    def test_from_negative_string(self):
        v = FixedPointDecimal("-1.50")
        self.assertEqual(v.raw, -150)
        self.assertEqual(v.to_str(), "-1.50")

    def test_from_string_with_plus_sign(self):
        v = FixedPointDecimal("+1.50")
        self.assertEqual(v.raw, 150)
        self.assertEqual(v.to_str(), "1.50")

    def test_from_string_leading_dot(self):
        v = FixedPointDecimal(".50")
        self.assertEqual(v.raw, 50)
        self.assertEqual(v.to_str(), "0.50")

    def test_from_string_trailing_dot(self):
        v = FixedPointDecimal("1.")
        self.assertEqual(v.raw, 100)
        self.assertEqual(v.to_str(), "1.00")

    def test_string_truncates_extra_fraction_digits(self):
        v = FixedPointDecimal("1.239")
        self.assertEqual(v.raw, 123)
        self.assertEqual(v.to_str(), "1.23")

    def test_negative_string_truncates_toward_zero(self):
        v = FixedPointDecimal("-1.239")
        self.assertEqual(v.raw, -123)
        self.assertEqual(v.to_str(), "-1.23")

    def test_copy_from_existing(self):
        a = FixedPointDecimal("5.00")
        b = FixedPointDecimal(a)
        self.assertIsNot(a, b)
        self.assertEqual(a.raw, b.raw)

    def test_float_rejected(self):
        with self.assertRaises(TypeError):
            FixedPointDecimal(1.5)

    def test_empty_string_rejected(self):
        with self.assertRaises(ValueError):
            FixedPointDecimal("")

    def test_lone_sign_rejected(self):
        with self.assertRaises(ValueError):
            FixedPointDecimal("-")

    def test_multiple_dots_rejected(self):
        with self.assertRaises(ValueError):
            FixedPointDecimal("1.2.3")

    def test_non_digit_chars_rejected(self):
        with self.assertRaises(ValueError):
            FixedPointDecimal("1.2a")

    def test_lone_dot_rejected(self):
        with self.assertRaises(ValueError):
            FixedPointDecimal(".")

    def test_default_is_zero(self):
        self.assertEqual(FixedPointDecimal().raw, 0)


class TestArithmetic(unittest.TestCase):
    def test_add(self):
        self.assertEqual(
            (FixedPointDecimal("1.23") + FixedPointDecimal("4.56")).to_str(),
            "5.79",
        )

    def test_add_with_int(self):
        self.assertEqual(
            (FixedPointDecimal("1.50") + 2).to_str(),
            "3.50",
        )

    def test_radd_with_int(self):
        self.assertEqual(
            (2 + FixedPointDecimal("1.50")).to_str(),
            "3.50",
        )

    def test_add_negative(self):
        self.assertEqual(
            (FixedPointDecimal("1.00") + FixedPointDecimal("-2.50")).to_str(),
            "-1.50",
        )

    def test_sub(self):
        self.assertEqual(
            (FixedPointDecimal("5.00") - FixedPointDecimal("1.50")).to_str(),
            "3.50",
        )

    def test_rsub_with_int(self):
        self.assertEqual(
            (5 - FixedPointDecimal("1.50")).to_str(),
            "3.50",
        )

    def test_mul_basic(self):
        self.assertEqual(
            (FixedPointDecimal("1.50") * FixedPointDecimal("2.00")).to_str(),
            "3.00",
        )

    def test_mul_truncates(self):
        # 1.50 * 1.50 = 2.25 exactly
        self.assertEqual(
            (FixedPointDecimal("1.50") * FixedPointDecimal("1.50")).to_str(),
            "2.25",
        )

    def test_mul_truncates_third_digit(self):
        # 0.99 * 0.99 = 0.9801, truncates to 0.98
        self.assertEqual(
            (FixedPointDecimal("0.99") * FixedPointDecimal("0.99")).to_str(),
            "0.98",
        )

    def test_mul_by_int(self):
        self.assertEqual(
            (FixedPointDecimal("1.50") * 3).to_str(),
            "4.50",
        )

    def test_div_exact(self):
        self.assertEqual(
            (FixedPointDecimal("10.00") / FixedPointDecimal("2.00")).to_str(),
            "5.00",
        )

    def test_div_truncates(self):
        # 10.00 / 3.00 -> 1000 / 300 = 3 (hundredths) -> 0.03
        self.assertEqual(
            (FixedPointDecimal("10.00") / FixedPointDecimal("3.00")).to_str(),
            "3.33",
        )

    def test_div_by_zero_raises(self):
        with self.assertRaises(ZeroDivisionError):
            FixedPointDecimal("1.00") / FixedPointDecimal("0.00")

    def test_neg(self):
        self.assertEqual(
            (-FixedPointDecimal("1.50")).to_str(),
            "-1.50",
        )

    def test_abs_negative(self):
        self.assertEqual(
            abs(FixedPointDecimal("-1.50")).to_str(),
            "1.50",
        )

    def test_abs_positive(self):
        self.assertEqual(
            abs(FixedPointDecimal("1.50")).to_str(),
            "1.50",
        )


class TestComparison(unittest.TestCase):
    def test_equal(self):
        self.assertTrue(FixedPointDecimal("1.00") == FixedPointDecimal("1.00"))

    def test_not_equal(self):
        self.assertTrue(FixedPointDecimal("1.00") != FixedPointDecimal("2.00"))

    def test_equal_to_int(self):
        self.assertTrue(FixedPointDecimal("1.00") == 1)

    def test_equal_to_string(self):
        self.assertTrue(FixedPointDecimal("1.00") == "1.00")

    def test_less_than(self):
        self.assertTrue(FixedPointDecimal("1.00") < FixedPointDecimal("2.00"))

    def test_less_or_equal(self):
        self.assertTrue(FixedPointDecimal("1.00") <= FixedPointDecimal("1.00"))

    def test_greater_than(self):
        self.assertTrue(FixedPointDecimal("2.00") > FixedPointDecimal("1.00"))

    def test_greater_or_equal(self):
        self.assertTrue(FixedPointDecimal("1.00") >= FixedPointDecimal("1.00"))

    def test_compare_with_int(self):
        self.assertTrue(FixedPointDecimal("1.50") > 1)

    def test_eq_with_unrelated_type_returns_not_implemented(self):
        # Python translates NotImplemented on == to identity check,
        # so the result is False, not an error.
        self.assertFalse(FixedPointDecimal("1.00") == 1.5)


class TestConversion(unittest.TestCase):
    def test_to_str_negative_zero_fraction(self):
        v = FixedPointDecimal("-0.05")
        self.assertEqual(v.to_str(), "-0.05")

    def test_to_str_round_trips(self):
        for s in ["0.00", "1.23", "-1.23", "99.99", "-0.01", "0.50"]:
            self.assertEqual(FixedPointDecimal(s).to_str(), s)

    def test_int_truncates_positive(self):
        self.assertEqual(int(FixedPointDecimal("3.99")), 3)

    def test_int_truncates_negative(self):
        self.assertEqual(int(FixedPointDecimal("-3.99")), -3)

    def test_repr(self):
        self.assertEqual(repr(FixedPointDecimal("1.50")), "FixedPointDecimal('1.50')")

    def test_str_matches_to_str(self):
        v = FixedPointDecimal("1.50")
        self.assertEqual(str(v), v.to_str())

    def test_bool_false_for_zero(self):
        self.assertFalse(FixedPointDecimal("0.00"))

    def test_bool_true_for_nonzero(self):
        self.assertTrue(FixedPointDecimal("0.01"))

    def test_hash_equal_for_equal_values(self):
        self.assertEqual(
            hash(FixedPointDecimal("1.50")),
            hash(FixedPointDecimal("1.50")),
        )


class TestChainedOperations(unittest.TestCase):
    def test_sum_of_three(self):
        total = (
            FixedPointDecimal("1.00")
            + FixedPointDecimal("2.00")
            + FixedPointDecimal("3.00")
        )
        self.assertEqual(total.to_str(), "6.00")

    def test_mixed_chain(self):
        # (1.00 + 2.00) * 1.50 = 4.50
        result = (FixedPointDecimal("1.00") + FixedPointDecimal("2.00")) * FixedPointDecimal("1.50")
        self.assertEqual(result.to_str(), "4.50")


if __name__ == "__main__":
    unittest.main()
