"""
test_orders.py - tests for the whole project (normal cases + edge cases).

Every test is a small function named test_...  with a message on each assert,
so a failure tells you exactly WHICH check broke.

Run:
    python main.py --test      (plain Python, no extra library)
    python -m pytest           (if pytest is installed)
"""

import sys
from decimal import Decimal

import orders
import pricing
from data import get_starter_products, get_starter_orders
from helpers import add_up
from pricing import calculate_order_subtotal, calculate_discount, calculate_shipping
from validation import validate_order
from orders import process_order, process_all_orders
from pricing import make_discount_calculator
from reports import (generate_sales_report, generate_customer_report, get_low_stock_products,
                     build_sales_summary, format_sales_report)


# ---------------------------------------------------------------- helpers
def item(product_id, quantity):
    """One order line."""
    return {"product_id": product_id, "quantity": quantity}


def make_order(order_id="T1", customer="Test", items=None, status="paid"):
    """Build a test order (defaults: one laptop, paid)."""
    if items is None:
        items = [item("P001", 1)]
    return {"order_id": order_id, "customer": customer, "items": items, "payment_status": status}


def raises_type_error(function, *args, **kwargs):
    """True if calling function(...) raises a TypeError."""
    try:
        function(*args, **kwargs)
    except TypeError:
        return True
    return False


def rejected_with(order, products, text):
    """True if validate_order rejects the order and the reason contains `text`."""
    ok, why = validate_order(order, products)
    return (not ok) and text in why


# ---------------------------------------------------------------- pricing
def test_discount_slabs():
    """Test: discount slabs."""
    assert calculate_discount(1000) == 150, "1000 -> 15%"
    assert calculate_discount(1500) == 225, "1500 -> 15%"
    assert calculate_discount(999.99) == 100.0, "999.99 -> 10%"
    assert calculate_discount(500) == 50, "500 -> 10%"
    assert calculate_discount(499.99) == 25.0, "499.99 -> 5%"
    assert calculate_discount(200) == 10, "200 -> 5%"
    assert calculate_discount(199.99) == 0, "199.99 -> 0%"
    assert calculate_discount(0) == 0, "0 -> no discount"


def test_shipping_rules():
    """Test: shipping rules."""
    assert calculate_shipping(500) == 0, "500 -> free shipping"
    assert calculate_shipping(499.99) == 20, "499.99 -> $20"
    assert calculate_shipping(50) == 20, "50 -> $20"


def test_add_up_args():
    """Test: add up args."""
    assert add_up() == 0, "no values -> 0"
    assert add_up(10, 20.5, 3) == 33.5, "mixed int/float values"


def test_subtotal():
    """Test: subtotal."""
    products = get_starter_products()
    assert calculate_order_subtotal(get_starter_orders()[0], products) == 1250, "ORD001 subtotal"


# ---------------------------------------------------------------- validation
def test_valid_order_accepted():
    """Test: valid order accepted."""
    ok, why = validate_order(get_starter_orders()[0], get_starter_products())
    assert ok is True and why == "", "starter ORD001 must be valid"


def test_unknown_product_rejected():
    """Test: unknown product rejected."""
    order = make_order(items=[item("P999", 1)])
    assert rejected_with(order, get_starter_products(), "Unknown product"), "unknown product ID"


def test_zero_and_negative_quantity_rejected():
    """Test: zero and negative quantity rejected."""
    products = get_starter_products()
    assert rejected_with(make_order(items=[item("P001", 0)]), products, "positive"), "quantity 0"
    assert rejected_with(make_order(items=[item("P001", -3)]), products, "positive"), "quantity -3"


def test_quantity_above_stock_rejected():
    """Test: quantity above stock rejected."""
    order = make_order(items=[item("P001", 11)])
    assert rejected_with(order, get_starter_products(), "stock"), "11 laptops, only 10 in stock"


def test_non_integer_quantity_rejected():
    """Test: non integer quantity rejected."""
    products = get_starter_products()
    assert not validate_order(make_order(items=[item("P001", 1.5)]), products)[0], "quantity 1.5"
    assert not validate_order(make_order(items=[item("P001", "2")]), products)[0], "quantity '2'"
    assert not validate_order(make_order(items=[item("P001", True)]), products)[0], "quantity True"


def test_no_items_rejected():
    """Test: no items rejected."""
    assert rejected_with(make_order(items=[]), get_starter_products(), "no items"), "empty items list"


def test_invalid_payment_status_rejected():
    """Test: invalid payment status rejected."""
    order = make_order(status="refunded")
    assert rejected_with(order, get_starter_products(), "payment status"), "status 'refunded'"


def test_empty_products_dictionary():
    """Test: empty products dictionary."""
    assert rejected_with(make_order(), {}, "Unknown product"), "empty products dict"


def test_garbage_order_rejected():
    """Test: garbage order rejected."""
    assert not validate_order("not an order", get_starter_products())[0], "string instead of dict"
    assert not validate_order(None, get_starter_products())[0], "None instead of dict"
    result = process_order({}, get_starter_products())
    assert result["status"] == "rejected" and result["order_id"] == "UNKNOWN", "empty dict"


def test_duplicate_lines_checked_together():
    """Test: duplicate lines checked together."""
    order = make_order(items=[item("P001", 6), item("P001", 6)])
    assert rejected_with(order, get_starter_products(), "stock"), "6 + 6 laptops > stock 10"


def test_missing_order_id_rejected():
    """Test: missing order id rejected."""
    products = get_starter_products()
    no_id = {"customer": "Ali", "items": [item("P001", 1)], "payment_status": "paid"}
    assert rejected_with(no_id, products, "order ID"), "missing order_id"
    for bad_id in ("", "   ", None, 123):
        assert rejected_with(make_order(order_id=bad_id), products, "order ID"), f"order_id {bad_id!r}"


def test_missing_customer_rejected():
    """Test: missing customer rejected."""
    products = get_starter_products()
    no_customer = {"order_id": "X1", "items": [item("P001", 1)], "payment_status": "paid"}
    assert rejected_with(no_customer, products, "customer"), "missing customer"
    for bad_name in ("", "   ", None, 123):
        assert rejected_with(make_order(customer=bad_name), products, "customer"), \
            f"customer {bad_name!r}"


def test_bad_product_price_rejected():
    """Test: bad product price rejected."""
    for bad_price in ("25", None, -5, float("nan"), float("inf"), True):
        products = get_starter_products()
        products["P001"]["price"] = bad_price
        assert rejected_with(make_order(), products, "Invalid price"), f"price {bad_price!r}"
    products = get_starter_products()
    del products["P001"]["price"]
    assert rejected_with(make_order(), products, "Invalid price"), "missing price key"


def test_bad_product_stock_rejected():
    """Test: bad product stock rejected."""
    for bad_stock in ("10", None, -1, 2.5, True):
        products = get_starter_products()
        products["P001"]["stock"] = bad_stock
        assert rejected_with(make_order(), products, "Invalid stock"), f"stock {bad_stock!r}"


def test_bad_product_does_not_hurt_other_products():
    """Test: bad product does not hurt other products."""
    products = get_starter_products()
    products["P001"]["price"] = "25"           # broken laptop data
    assert validate_order(make_order(items=[item("P002", 1)]), products)[0], \
        "order for Mouse must still be valid"


# ---------------------------------------------------------------- processing
def test_starter_data_full_run():
    """Test: starter data full run."""
    products = get_starter_products()
    processed = process_all_orders(get_starter_orders(), products)
    assert [r["status"] for r in processed] == ["paid", "paid", "pending"], "statuses"

    assert processed[0]["subtotal"] == 1250 and processed[0]["discount"] == 187.5, "ORD001 money"
    assert processed[0]["shipping"] == 0 and processed[0]["total"] == 1062.5, "ORD001 total"
    assert processed[1]["subtotal"] == 450 and processed[1]["discount"] == 22.5, "ORD002 money"
    assert processed[1]["shipping"] == 20 and processed[1]["total"] == 447.5, "ORD002 total"

    report = generate_sales_report(processed, products)
    for expected in ("Total Orders: 3", "Paid Orders: 2", "Pending Orders: 1", "Rejected Orders: 0",
                     "Total Revenue: $1,510.00", "Total Discount: $210.00", "Total Shipping: $20.00",
                     "Customers With A Valid Order: 2", "Top Customer: Ali ($1,062.50)",
                     "Keyboard, Mouse (tie, 2 units each)", "- Laptop (P001): 9 left"):
        assert expected in report, f"report is missing: {expected}"


def test_inventory_reduced_only_for_paid():
    """Test: inventory reduced only for paid."""
    products = get_starter_products()
    process_all_orders(get_starter_orders(), products)
    assert products["P001"]["stock"] == 9, "Laptop 10 - 1"
    assert products["P002"]["stock"] == 48, "Mouse 50 - 2 (pending order must NOT reduce stock)"
    assert products["P003"]["stock"] == 18, "Keyboard 20 - 2"
    assert products["P004"]["stock"] == 14, "Monitor 15 - 1"


def test_rejected_order_does_not_change_stock():
    """Test: rejected order does not change stock."""
    products = get_starter_products()
    result = process_order(make_order(items=[item("P001", 99)]), products)
    assert result["status"] == "rejected", "99 laptops must be rejected"
    assert products["P001"]["stock"] == 10, "stock must stay 10"


def test_stock_checked_against_stock_left():
    """Test: stock checked against stock left."""
    products = get_starter_products()
    first = make_order("A", "X", [item("P001", 6)])
    second = make_order("B", "Y", [item("P001", 6)])
    processed = process_all_orders([first, second], products)
    assert [r["status"] for r in processed] == ["paid", "rejected"], "second order lacks stock"
    assert products["P001"]["stock"] == 4, "only the first order reduced stock"


def test_duplicate_order_id_rejected():
    """Test: duplicate order id rejected."""
    products = get_starter_products()
    orders_list = get_starter_orders() + [dict(get_starter_orders()[0])]   # ORD001 again
    processed = process_all_orders(orders_list, products)
    assert [r["status"] for r in processed] == ["paid", "paid", "pending", "rejected"], "statuses"
    assert processed[3]["reason"] == "Duplicate order ID ORD001", "duplicate reason"
    assert products["P001"]["stock"] == 9, "Laptop must be reduced only once"
    report = generate_sales_report(processed, products)
    assert "Total Revenue: $1,510.00" in report, "revenue must not be counted twice"
    assert "Rejected Orders: 1" in report, "duplicate counted as rejected"
    assert "Top Customer: Ali ($1,062.50)" in report, "Ali must not be double-charged"


def test_rejected_order_id_can_be_resubmitted():
    """Test: rejected order id can be resubmitted."""
    products = get_starter_products()
    first = make_order("R1", "Ali", [item("P001", 99)])    # rejected: no stock
    second = make_order("R1", "Ali", [item("P001", 1)])    # fixed and sent again
    processed = process_all_orders([first, second], products)
    assert [r["status"] for r in processed] == ["rejected", "paid"], "fixed order is accepted"


def test_safety_net_keeps_order_id():
    """Test: safety net keeps order id."""
    original = orders.process_order

    def broken(order, products, seen_ids=None, **options):
        """Always crashes (used to test the safety net)."""
        raise RuntimeError("boom")

    orders.process_order = broken
    try:
        result = process_all_orders([make_order("ORD777", "Sara")], get_starter_products())
    finally:
        orders.process_order = original            # always restore
    record = result[0]
    assert record["status"] == "rejected", "crashed order is rejected"
    assert record["order_id"] == "ORD777", "order ID must survive the crash"
    assert record["customer"] == "Sara", "customer must survive the crash"
    assert "boom" in record["reason"], "reason shows the error"


def test_non_list_inputs():
    """Test: non list inputs."""
    products = get_starter_products()
    for bad_orders in (None, "text", 5, {"order_id": "X"}):
        assert raises_type_error(process_all_orders, bad_orders, products), \
            f"orders={bad_orders!r} must raise a clear TypeError"
    assert raises_type_error(process_all_orders, [], None), "products=None must raise TypeError"


# ---------------------------------------------------------------- options (**kwargs)
def test_options_shipping_and_discount():
    """Test: options shipping and discount."""
    order = make_order("K", "Z", [item("P004", 2)])        # subtotal 600
    small = make_order("S", "Z", [item("P002", 1)])        # subtotal 25
    assert process_order(order, get_starter_products())["total"] == 540, "600 - 10%, free shipping"
    assert process_order(order, get_starter_products(), apply_discount=False)["total"] == 600, "no discount"
    assert process_order(small, get_starter_products())["total"] == 45, "25 + $20 shipping"
    assert process_order(small, get_starter_products(), include_shipping=False)["total"] == 25, "no shipping"
    both_off = process_order(small, get_starter_products(), include_shipping=False, apply_discount=False)
    assert both_off["total"] == 25, "both options off"


def test_unknown_option_rejected():
    """Test: unknown option rejected."""
    products = get_starter_products()
    assert raises_type_error(process_order, make_order(), products, include_shiping=False), \
        "misspelt option in process_order"
    assert raises_type_error(process_all_orders, [make_order()], products, include_shiping=False), \
        "misspelt option in process_all_orders"


def test_option_wrong_type_rejected():
    """Test: option wrong type rejected."""
    products = get_starter_products()
    assert raises_type_error(process_order, make_order(), products, apply_discount="no"), \
        "string 'no' is not a bool"
    assert raises_type_error(process_order, make_order(), products, include_shipping=0), \
        "0 is not a bool"


# ---------------------------------------------------------------- reports
def test_customer_names_normalised():
    """Test: customer names normalised."""
    products = get_starter_products()
    first = make_order("A1", "Ali", [item("P002", 1)])
    second = make_order("A2", "ali ", [item("P002", 1)])
    processed = process_all_orders([first, second], products)
    report = generate_customer_report(processed)
    assert report["spend"] == {"Ali": 90.0}, "'Ali' and 'ali ' are one customer"
    assert report["unique_customers"] == {"Ali"}, "one unique customer"


def test_unique_customers_ignore_rejected_orders():
    """Test: unique customers ignore rejected orders."""
    products = get_starter_products()
    ghost = make_order("G1", "Ghost", [item("P999", 1)])
    processed = process_all_orders(get_starter_orders() + [ghost], products)
    report = generate_sales_report(processed, products)
    assert "Customers With A Valid Order: 2" in report, "only Ali and Ahmed"
    assert "Ghost" not in report, "rejected customer must not appear"


def test_non_string_customers_do_not_crash_report():
    """Test: non string customers do not crash report."""
    products = get_starter_products()
    processed = process_all_orders([make_order("N1", 123), make_order("N2", "Ali")], products)
    assert processed[0]["status"] == "rejected", "customer 123 is rejected"
    report = generate_sales_report(processed, products)
    assert "Top Customer: Ali" in report, "report works with mixed customer types"


def test_tie_in_top_customers():
    """Test: tie in top customers."""
    products = get_starter_products()
    processed = process_all_orders([make_order("T1", "Zara", [item("P002", 1)]),
                                    make_order("T2", "Amir", [item("P002", 1)])], products)
    assert generate_customer_report(processed)["top_customers"] == ["Amir", "Zara"], "both, A-Z"


def test_empty_orders_list_report():
    """Test: empty orders list report."""
    report = generate_sales_report([], get_starter_products())
    for expected in ("Total Orders: 0", "Total Revenue: $0.00", "Customers With A Valid Order: 0",
                     "Top Customer: N/A", "Top Selling Product: N/A"):
        assert expected in report, f"report is missing: {expected}"


def test_empty_products_dictionary_report():
    """Test: empty products dictionary report."""
    processed = process_all_orders(get_starter_orders(), {})
    assert all(r["status"] == "rejected" for r in processed), "nothing can be sold"
    report = generate_sales_report(processed, {})
    assert "Rejected Orders: 3" in report and "- None" in report, "report for empty catalogue"


def test_no_low_stock_products():
    """Test: no low stock products."""
    rich = {"P1": {"name": "Pen", "price": 1, "category": "Office", "stock": 500}}
    assert get_low_stock_products(rich) == [], "stock 500 is not low"
    assert "- None" in generate_sales_report([], rich), "report says None"


def test_low_stock_threshold_and_bad_stock():
    """Test: low stock threshold and bad stock."""
    assert len(get_low_stock_products(get_starter_products(), 15)) == 2, "Laptop 10 and Monitor 15"
    assert len(get_low_stock_products(get_starter_products(), 5)) == 0, "nothing <= 5"
    broken = get_starter_products()
    broken["P002"]["stock"] = "many"                        # bad data must not crash the report
    assert len(get_low_stock_products(broken, 10)) == 1, "bad stock value is skipped"
    broken["P002"]["stock"] = 2.5                           # float stock: same rule as validation
    assert len(get_low_stock_products(broken, 10)) == 1, "float stock is skipped too"


# ---------------------------------------------------------------- money (Decimal)
def test_discount_rounds_half_up():
    """Test: discount rounds half up."""
    assert calculate_discount(1004.50) == Decimal("150.68"), "150.675 -> 150.68 (not 150.67)"
    assert calculate_discount(202.50) == Decimal("10.13"), "10.125 -> 10.13 (not 10.12)"
    assert add_up(0.1, 0.2) == Decimal("0.30"), "no float error: 0.1 + 0.2"


def test_money_values_are_decimals():
    """Test: money values are decimals."""
    result = process_order(get_starter_orders()[0], get_starter_products())
    for field in ("subtotal", "discount", "shipping", "total"):
        assert isinstance(result[field], Decimal), f"{field} must be a Decimal"


def test_half_cent_order_total():
    """Test: half cent order total."""
    products = {"P1": {"name": "Gadget", "price": 1004.50, "category": "Test", "stock": 5}}
    order = make_order("H1", "Ali", [item("P1", 1)])
    result = process_order(order, products)
    assert result["discount"] == Decimal("150.68"), "discount rounded half up"
    assert result["total"] == Decimal("853.82"), "1004.50 - 150.68 + free shipping"


def test_shipping_uses_subtotal_before_discount():
    """Test: shipping uses subtotal before discount."""
    products = {"P1": {"name": "Gadget", "price": 520, "category": "Test", "stock": 5}}
    result = process_order(make_order("S1", "Ali", [item("P1", 1)]), products)
    assert result["subtotal"] == 520 and result["discount"] == 52, "10% of 520"
    assert result["shipping"] == 0, "520 before discount -> free shipping (even though 468 after)"
    assert result["total"] == 468, "520 - 52 + 0"


# ---------------------------------------------------------------- duplicates (one rule, one place)
def test_duplicate_order_id_ignores_case_and_spaces():
    """Test: duplicate order id ignores case and spaces."""
    products = get_starter_products()
    first = make_order("ORD009", "Ali", [item("P001", 1)])
    second = make_order("ord009 ", "Ali", [item("P001", 1)])
    processed = process_all_orders([first, second], products)
    assert [r["status"] for r in processed] == ["paid", "rejected"], "'ord009 ' is the same order"
    assert processed[0]["order_id"] == "ORD009", "ID is stored in normalised form"
    assert processed[1]["reason"] == "Duplicate order ID ORD009", "duplicate reason"
    assert products["P001"]["stock"] == 9, "stock reduced only once"


def test_process_order_duplicate_check_with_seen_ids():
    """Test: process order duplicate check with seen ids."""
    products = get_starter_products()
    seen = set()
    order = make_order("D1", "Ali", [item("P001", 1)])
    first = process_order(order, products, seen)
    second = process_order(make_order("d1", "Ali", [item("P001", 1)]), products, seen)
    assert first["status"] == "paid" and second["status"] == "rejected", "second call is a duplicate"
    assert "Duplicate order ID D1" in second["reason"], "reason"
    assert products["P001"]["stock"] == 9, "reduced once"
    assert seen == {"D1"}, "accepted ID is remembered in normalised form"


def test_seen_ids_must_be_a_set():
    """Test: seen ids must be a set."""
    assert raises_type_error(process_order, make_order(), get_starter_products(), ["T1"]), \
        "a list is not a set"


def test_rejected_order_is_not_remembered_in_seen_ids():
    """Test: rejected order is not remembered in seen ids."""
    products = get_starter_products()
    seen = set()
    process_order(make_order("R9", "Ali", [item("P001", 99)]), products, seen)
    assert seen == set(), "rejected order must not block its ID"


# ---------------------------------------------------------------- pending orders are provisional
def test_pending_orders_are_provisional():
    """Test: pending orders are provisional."""
    products = get_starter_products()
    pending_a = make_order("PA", "Ali", [item("P001", 10)], "pending")
    pending_b = make_order("PB", "Sara", [item("P001", 10)], "pending")
    processed = process_all_orders([pending_a, pending_b], products)
    assert [r["status"] for r in processed] == ["pending", "pending"], "both accepted as pending"
    assert products["P001"]["stock"] == 10, "pending orders do not reserve stock"

    paid_a = make_order("PC", "Ali", [item("P001", 10)])         # first one to pay gets the stock
    paid_b = make_order("PD", "Sara", [item("P001", 10)])
    processed = process_all_orders([paid_a, paid_b], products)
    assert [r["status"] for r in processed] == ["paid", "rejected"], "stock is checked again at payment"
    assert products["P001"]["stock"] == 0, "all 10 laptops sold once"


# ---------------------------------------------------------------- stock used by several orders
def test_stock_is_subtracted_only_once():
    """Test: stock is subtracted only once."""
    products = get_starter_products()
    processed = process_all_orders([make_order("A", "x", [item("P001", 6)]),
                                    make_order("B", "y", [item("P001", 3)])], products)
    assert [r["status"] for r in processed] == ["paid", "paid"], "6 + 3 laptops fit into 10"
    assert products["P001"]["stock"] == 1, "10 - 6 - 3 = 1 (no double subtraction)"
    products = get_starter_products()
    processed = process_all_orders([make_order("C", "x", [item("P001", 5)]),
                                    make_order("D", "y", [item("P001", 5)])], products)
    assert [r["status"] for r in processed] == ["paid", "paid"], "5 + 5 laptops fit into 10"
    assert products["P001"]["stock"] == 0, "all laptops sold"


def test_pending_order_above_stock_rejected():
    """Test: pending order above stock rejected."""
    products = get_starter_products()
    result = process_order(make_order("P1", "Ali", [item("P001", 999)], "pending"), products)
    assert result["status"] == "rejected", "999 laptops must be rejected even when pending"
    assert "stock" in result["reason"], "reason mentions stock"


def test_malformed_orders_do_not_crash():
    """Test: malformed orders do not crash."""
    products = get_starter_products()
    bad_orders = [None, "ORD9", 5, [], {"order_id": "X"}]
    processed = process_all_orders(bad_orders, products)
    assert [r["status"] for r in processed] == ["rejected"] * 5, "all garbage orders rejected"
    products["P001"] = "oops"                                   # product entry that is not a dict
    assert not validate_order(make_order(), products)[0], "non-dict product entry"
    list_id = make_order(items=[{"product_id": ["P001"], "quantity": 1}])   # unhashable product ID
    assert not validate_order(list_id, get_starter_products())[0], "list as product ID"


# ---------------------------------------------------------------- report summary / settings
def test_sales_summary_is_a_testable_dictionary():
    """Test: sales summary is a testable dictionary."""
    products = get_starter_products()
    processed = process_all_orders(get_starter_orders(), products)
    summary = build_sales_summary(processed, products)
    assert summary["total_orders"] == 3 and summary["paid_orders"] == 2, "order counts"
    assert summary["total_revenue"] == Decimal("1510.00"), "revenue"
    assert summary["top_customers"] == ["Ali"], "top customer"
    assert summary["top_products"] == ["Keyboard", "Mouse"], "top products (tie)"
    assert summary["categories_sold"] == ["Accessories", "Electronics"], "categories"
    assert summary["low_stock"] == [("P001", "Laptop", 9)], "low stock"
    assert "Categories Sold: Accessories, Electronics" in format_sales_report(summary), "report line"


def test_discount_calculator_closure_remembers_tiers():
    """Test: discount calculator closure remembers tiers."""
    calculate = make_discount_calculator(((100, Decimal("0.50")), (10, Decimal("0.10"))))
    assert calculate(100) == 50, "top tier"
    assert calculate(20) == 2, "second tier"
    assert calculate(5) == 0, "below all tiers"


# ---------------------------------------------------------------- review: build once / unit price
def test_discount_calculator_is_built_only_once():
    """Test: calculate_discount is created once at import time, not on every call."""
    original = pricing.make_discount_calculator

    def must_not_be_called(tiers):
        """Fails the test if a new calculator is built during a call."""
        raise AssertionError("make_discount_calculator was called again")

    pricing.make_discount_calculator = must_not_be_called
    try:
        assert pricing.calculate_discount(1000) == 150, "still works without rebuilding"
        assert pricing.calculate_discount(250) == Decimal("12.50"), "5% of 250"
    finally:
        pricing.make_discount_calculator = original          # always restore
    assert pricing.calculate_discount.__closure__ is not None, "it is still a closure"


def test_item_records_keep_unit_price_and_line_total():
    """Test: every recorded item has unit_price and line_total (record is complete alone)."""
    products = get_starter_products()
    result = process_order(get_starter_orders()[0], products)
    first, second = result["items"]
    assert first == {"product_id": "P001", "quantity": 1,
                     "unit_price": Decimal("1200.00"), "line_total": Decimal("1200.00")}, "laptop line"
    assert second == {"product_id": "P002", "quantity": 2,
                      "unit_price": Decimal("25.00"), "line_total": Decimal("50.00")}, "mouse line"
    assert add_up(*[line["line_total"] for line in result["items"]]) == result["subtotal"], \
        "line totals add up to the subtotal"
    products["P001"]["price"] = 999                         # price changes AFTER the order
    assert result["items"][0]["unit_price"] == Decimal("1200.00"), "record keeps the sold price"


# ---------------------------------------------------------------- runner
def run_all_tests():
    """Run every test_ function above. A failure is printed and the rest still run."""
    tests = [(name, func) for name, func in globals().items()
             if name.startswith("test_") and callable(func)]
    failed = 0
    for name, func in tests:
        try:
            func()
        except AssertionError as error:
            failed += 1
            print(f"FAIL  {name}: {error}")
        except Exception as error:
            failed += 1
            print(f"ERROR {name}: {type(error).__name__}: {error}")
    if failed:
        print(f"\n{failed} of {len(tests)} tests FAILED")
        sys.exit(1)
    print(f"All {len(tests)} tests passed!")


if __name__ == "__main__":
    run_all_tests()
