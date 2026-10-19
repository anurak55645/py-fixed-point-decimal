"""Fixed-point decimal arithmetic built on plain Python integers.

Python's standard-library Decimal is correct and convenient, but every
operation allocates a context-aware object and rounds according to a
configurable precision that can surprise you. For the common case where
you know up front that two digits after the decimal point is all you
need (money is the canonical example), storing a scaled integer and
only dividing at presentation time is faster and easier to reason
about.

This module implements exactly one fixed scale (two digits, i.e.
hundredths) by design. Supporting multiple scales in a single value
type would require either a per-instance scale field—erasing the
performance advantage of plain-int arithmetic—or a global scale that
silently changes the meaning of every previously constructed value.
Neither is worth the complexity for the problem this library exists
to solve.
"""

from __future__ import annotations


class FixedPointDecimal:
    """A decimal number with exactly two fractional digits.

    Internally every value is stored as an int counting hundredths.
    Arithmetic therefore never introduces binary floating-point error,
    and no rounding context is involved: the result of each operation
    is exact, then truncated to two places if the operation would
    otherwise produce a finer scale.

    Rounding strategy
    -----------------
    All operations that can produce a third fractional digit—multiply
    and divide—truncate toward zero. This is the most predictable
    choice: it never magnifies a value by rounding up, and it is
    trivially auditable. Banker's rounding is available in the
    standard library's Decimal if you need it; this library
    deliberately does not offer a knob.

    Division semantics
    ------------------
    Division by a FixedPointDecimal divides the scaled integer of the
    dividend by that of the divisor and truncates back to two places.
    ``a / b`` is therefore the integer-quotient of hundredths, not
    the real-number quotient. This mirrors how integer division works
    in Python and avoids any surprise from hidden precision.
    """

    __slots__ = ("_value",)

    SCALE = 100
    """Number of stored units per whole unit (two decimal places)."""

    def __init__(self, value=0):
        """Construct from an int, a str, or another FixedPointDecimal.

        ``int`` is stored as-is after scaling. A ``str`` is parsed via
        plain Python integer arithmetic so that no float is ever
        created; a string like '1.23' becomes the integer 123. An
        existing FixedPointDecimal is copied so that callers cannot
        accidentally alias mutable state.

        This deliberately does not accept float. Converting a binary
        float to a fixed-point decimal would silently bake in the
        float's representation error, which defeats the purpose. Callers
        who have a float should pass it through str() first, which makes
        the rounding explicit.
        """
        if isinstance(value, FixedPointDecimal):
            self._value = value._value
        elif isinstance(value, int):
            self._value = value * self.SCALE
        elif isinstance(value, str):
            self._value = self._parse_string(value)
        else:
            raise TypeError(
                "FixedPointDecimal requires int, str, or FixedPointDecimal, "
                f"not {type(value).__name__}"
            )

    @staticmethod
    def _parse_string(text):
        """Parse a decimal string into a scaled integer.

        The string must contain an optional sign, an integer part,
        optionally a '.' followed by a fractional part. At most two
        fractional digits are honoured; extra digits are truncated
        toward zero so that '1.239' becomes 123, not 124.

        Whitespace is rejected. Leading plus signs are accepted for
        symmetry with minus. An empty string is an error rather than
        silently becoming zero.
        """
        s = text
        if not s:
            raise ValueError("empty string is not a valid FixedPointDecimal")

        sign = 1
        start = 0
        if s[0] == "-":
            sign = -1
            start = 1
        elif s[0] == "+":
            start = 1

        if start == len(s):
            raise ValueError(f"no digits in {text!r}")

        dot = s.find(".", start)
        if dot == -1:
            digits = s[start:]
            if not _all_digits(digits):
                raise ValueError(f"invalid characters in {text!r}")
            return sign * int(digits) * 100

        if s.find(".", dot + 1) != -1:
            raise ValueError(f"multiple decimal points in {text!r}")

        int_part = s[start:dot]
        frac_part = s[dot + 1:]

        if int_part == "" and frac_part == "":
            raise ValueError(f"no digits around decimal point in {text!r}")
        if int_part and not _all_digits(int_part):
            raise ValueError(f"invalid characters in {text!r}")
        if frac_part and not _all_digits(frac_part):
            raise ValueError(f"invalid characters in {text!r}")

        int_val = int(int_part) if int_part else 0
        # Truncate fractional digits beyond two toward zero, so
        # negative values stay negative rather than rounding away from
        # zero. Taking the first two characters works for both signs
        # because we apply sign at the very end.
        frac = frac_part[:2]
        frac_val = int(frac) if frac else 0
        if len(frac_part) == 1:
            frac_val *= 10

        return sign * (int_val * 100 + frac_val)

    @property
    def raw(self):
        """The underlying scaled integer (hundredths). Read-only."""
        return self._value

    def to_str(self):
        """Render to a canonical decimal string with exactly two places.

        The output always has a sign for negatives, a leading digit
        before the decimal point, and exactly two digits after. This
        makes it safe to sort lexicographically and safe to round-trip
        back through the constructor.
        """
        v = self._value
        if v < 0:
            sign = "-"
            v = -v
        else:
            sign = ""
        whole = v // 100
        frac = v % 100
        return f"{sign}{whole}.{frac:02d}"

    def __add__(self, other):
        other = self._coerce(other)
        return self._from_raw(self._value + other._value)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        other = self._coerce(other)
        return self._from_raw(self._value - other._value)

    def __rsub__(self, other):
        return self._coerce(other).__sub__(self)

    def __mul__(self, other):
        other = self._coerce(other)
        return self._from_raw(self._value * other._value // self.SCALE)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        other = self._coerce(other)
        if other._value == 0:
            raise ZeroDivisionError("division by zero in FixedPointDecimal")
        return self._from_raw(self._value * self.SCALE // other._value)

    def __rtruediv__(self, other):
        return self._coerce(other).__truediv__(self)

    def __neg__(self):
        return self._from_raw(-self._value)

    def __pos__(self):
        return self._from_raw(self._value)

    def __abs__(self):
        return self._from_raw(abs(self._value))

    def __eq__(self, other):
        try:
            other = self._coerce(other)
        except TypeError:
            return NotImplemented
        return self._value == other._value

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __lt__(self, other):
        other = self._coerce(other)
        return self._value < other._value

    def __le__(self, other):
        other = self._coerce(other)
        return self._value <= other._value

    def __gt__(self, other):
        other = self._coerce(other)
        return self._value > other._value

    def __ge__(self, other):
        other = self._coerce(other)
        return self._value >= other._value

    def __hash__(self):
        return hash(self._value)

    def __int__(self):
        """Truncate toward zero to a plain int (drop fractional digits)."""
        return self._value // self.SCALE if self._value >= 0 else -(-self._value // self.SCALE)

    def __repr__(self):
        return f"FixedPointDecimal({self.to_str()!r})"

    def __str__(self):
        return self.to_str()

    def __bool__(self):
        return self._value != 0

    @classmethod
    def _from_raw(cls, raw):
        """Build an instance directly from an already-scaled int."""
        obj = cls.__new__(cls)
        obj._value = raw
        return obj

    @classmethod
    def _coerce(cls, other):
        """Accept int/str/FixedPointDecimal; raise TypeError otherwise.

        Integers are treated as whole-valued fixed-point numbers so that
        ``FixedPointDecimal(1,50) + 2`` works without ceremony. Strings
        are parsed because reading from a file is the common source of
        fixed-point data. Floats are rejected to avoid importing binary
        representation error silently.
        """
        if isinstance(other, FixedPointDecimal):
            return other
        if isinstance(other, int):
            return cls(other)
        if isinstance(other, str):
            return cls(other)
        raise TypeError(
            "operand must be int, str, or FixedPointDecimal, "
            f"not {type(other).__name__}"
        )


def _all_digits(s):
    """True if every character of ``s`` is an ASCII digit."""
    if not s:
        return False
    for ch in s:
        if ch < "0" or ch > "9":
            return False
    return True
