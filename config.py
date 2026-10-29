"""config.py - every business rule number in ONE place (no magic numbers in the code).

Change a rule here and the whole program follows.
"""

from decimal import Decimal

SETTINGS = {
    # (minimum subtotal, discount rate) - the highest matching tier wins
    "discount_tiers": (
        (1000, Decimal("0.15")),
        (500, Decimal("0.10")),
        (200, Decimal("0.05")),
    ),
    "free_shipping_from": 500,     # subtotal (before discount) from which shipping is free
    "shipping_cost": 20,           # otherwise this much
    "low_stock_threshold": 10,     # stock <= this is "low stock"
}
