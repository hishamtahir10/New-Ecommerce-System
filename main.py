"""
E-Commerce Order Processing System
----------------------------------
Python Intern Real-World Assessment (standard library only, no classes).

Run:
    python main.py          -> demo with starter data + sales report
    python main.py --test   -> run all built-in tests

Files:
    config.py      all business-rule numbers in one SETTINGS dictionary
    data.py        starter products and orders
    helpers.py     add_up (*args) and money formatting
    pricing.py     subtotal, discount (closure), shipping
    validation.py  validate_order
    orders.py      process_order (**kwargs), process_all_orders
    reports.py     summary dictionary + formatted sales report
    test_orders.py small test_ functions (works with plain Python and with pytest)
"""

import sys

from data import get_starter_products, get_starter_orders
from helpers import money
from orders import process_all_orders
from reports import generate_sales_report


def run_demo():
    """Process the starter orders, print an order log and the sales report."""
    products = get_starter_products()
    orders = get_starter_orders()

    processed = process_all_orders(orders, products)

    print("Order log:")
    for r in processed:
        if r["status"] == "rejected":
            print(f"  {r['order_id']} ({r['customer']}): REJECTED - {r['reason']}")
        else:
            print(f"  {r['order_id']} ({r['customer']}): {r['status'].upper()} | "
                  f"subtotal {money(r['subtotal'])}, discount {money(r['discount'])}, "
                  f"shipping {money(r['shipping'])}, total {money(r['total'])}")
    print()
    print(generate_sales_report(processed, products))


if __name__ == "__main__":
    if "--test" in sys.argv:
        from test_orders import run_all_tests   # loaded only when needed
        run_all_tests()
    else:
        run_demo()
