"""helpers.py - small reusable helper functions.

All money is handled with Decimal (exact decimal numbers) and rounded
"half up" to cents, because float numbers and Python's round() give wrong
results for half-cent cases (for example 150.675 must become 150.68).
"""

from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")   # a constant (never changed), not a changing global variable


def to_decimal(value):
    """int / float / str / Decimal -> Decimal.
    Floats go through str() first, so 19.99 stays exactly 19.99."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def round_money(value):
    """Round to 2 decimals, half up (0.125 -> 0.13)."""
    return to_decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def add_up(*values):
    """*args demo: add any number of amounts exactly, round ONCE at the end.
    Example: add_up(10, 20.5, 3) -> Decimal('33.50'), add_up(0.1, 0.2) -> Decimal('0.30')"""
    total = Decimal("0")
    for value in values:
        total += to_decimal(value)
    return round_money(total)


def money(amount):
    """Format a number as money, e.g. 1062.5 -> '$1,062.50'."""
    return f"${round_money(amount):,.2f}"
