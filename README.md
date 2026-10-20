# py-fixed-point-decimal

Fixed-point decimal arithmetic with exactly two fractional digits, stored as a plain Python integer counting hundredths. No floating-point, no rounding context, no surprises.

## Usage

```python
from py_fixed_point_decimal import FixedPointDecimal

price = FixedPointDecimal("1.23")
tax = FixedPointDecimal("0.12")
total = price + tax
print(total)            # 1.35
print(total.raw)        # 135
print(int(total))       # 1

discount = total * FixedPointDecimal("0.10")
print(discount)         # 0.13 (truncated toward zero)

print(FixedPointDecimal("1.00") > 0)  # True
```

## Why

The standard library's `Decimal` is correct and general-purpose, but every operation consults a context and allocates a full object. When the problem is specifically "money with two decimal places," that generality is overhead you pay for on every line. This library stores each value as a single `int` (hundredths), so addition and subtraction are plain integer ops, and the only place rounding enters is multiply and divide.

The trade-off: the scale is fixed at two digits, period. There is no per-instance scale field and no configurable precision. If you need four places, you need a different library.

## The awkward edge

Multiplication and division **truncate toward zero**, never round. `FixedPointDecimal("0.99") * FixedPointDecimal("0.99")` is `0.98`, not `0.98` rounded up to `0.98` — the true product is `0.9801`, and the third digit is dropped. If you need banker's rounding or half-up, use `decimal.Decimal`.

Floats are not accepted by the constructor. Converting a binary float to fixed-point would silently import the float's representation error. If you have a float, pass it through `str()` first so the rounding is explicit.

Division by another `FixedPointDecimal` divides the scaled integers and truncates: `FixedPointDecimal("10.00") / FixedPointDecimal("3.00")` is `3.33`, not `3.33...`. This mirrors Python's integer division and avoids any hidden precision.
