"""
E-Commerce Order Processing System
----------------------------------
Python Intern Real-World Assessment (standard library only, no classes).

Run:
    python main.py          -> demo with starter data + sales report
    python main.py --test   -> run all built-in tests

Files:
    data.py        starter products and orders
    helpers.py     add_up (*args) and money formatting
    pricing.py     subtotal, discount, shipping
    validation.py  validate_order
    orders.py      process_order (**kwargs), process_all_orders
    reports.py     customer / product / low-stock / sales report
    test_orders.py small test_ functions (works with plain Python and with pytest)
"""

import sys

from data import get_starter_products, get_starter_orders
from helpers import money
from orders import process_all_orders
from reports import generate_sales_report


def run_demo():
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
