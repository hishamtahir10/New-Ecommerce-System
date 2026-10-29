"""reports.py - customer report, product report, low-stock list and the final sales report."""

from helpers import add_up, money
from validation import is_valid_stock
from config import SETTINGS


def make_low_stock_checker(threshold):
    """LEGB demo (the 'E' = Enclosing scope):
    the inner function is_low() uses `threshold`, which lives in the
    enclosing function - no global variable needed."""
    def is_low(product):
        """True if this product's stock is a valid number <= threshold."""
        stock = product.get("stock") if isinstance(product, dict) else None
        return is_valid_stock(stock) and stock <= threshold
    return is_low


def get_low_stock_products(products, threshold=None):
    """List of (product_id, product) with stock <= threshold, lowest stock first.
    threshold defaults to config.SETTINGS["low_stock_threshold"]."""
    if threshold is None:
        threshold = SETTINGS["low_stock_threshold"]
    is_low = make_low_stock_checker(threshold)
    low = [(pid, product) for pid, product in products.items() if is_low(product)]
    low.sort(key=lambda pair: (pair[1]["stock"], str(pair[1].get("name", ""))))
    return low


def generate_customer_report(processed_orders):
    """Spending per customer (PAID orders only) and the top customer(s).
    "Ali" and "ali " are the same customer (names are compared ignoring case/spaces).
    Rejected orders are ignored completely."""
    spend = {}      # normalised name -> total spent
    display = {}    # normalised name -> name as first seen (for printing)
    for record in processed_orders:
        if record["status"] == "rejected":
            continue
        name = str(record["customer"]).strip()
        key = name.casefold()
        display.setdefault(key, name)
        if record["status"] == "paid":
            spend[key] = add_up(spend.get(key, 0), record["total"])

    unique_customers = set(display.values())    # a set: customers with a valid (paid or pending) order
    spend_by_name = {display[key]: amount for key, amount in spend.items()}

    ranking = sorted(spend_by_name.items(), key=lambda pair: (-pair[1], pair[0]))
    top_spend = ranking[0][1] if ranking else 0
    top_customers = [name for name, amount in ranking if amount == top_spend]

    return {
        "spend": spend_by_name,
        "unique_customers": unique_customers,
        "top_customers": top_customers,   # a list, because of possible ties
        "top_spend": top_spend,
    }


def generate_product_report(processed_orders, products):
    """Units sold per product (PAID orders only) and the top-selling product(s)."""
    units_sold = {}
    for record in processed_orders:
        if record["status"] == "paid":
            for item in record["items"]:
                pid = item["product_id"]
                units_sold[pid] = units_sold.get(pid, 0) + item["quantity"]

    def name_of(pid):
        """Product name, or the ID itself if the product is unknown."""
        return products.get(pid, {}).get("name", pid)

    sold_categories = {products[pid]["category"] for pid in units_sold
                       if pid in products and "category" in products[pid]}  # a set

    top_units = max(units_sold.values()) if units_sold else 0
    top_products = sorted(str(name_of(pid)) for pid, qty in units_sold.items() if qty == top_units) \
        if units_sold else []

    return {
        "units_sold": units_sold,
        "top_products": top_products,     # a list, because of possible ties
        "top_units": top_units,
        "sold_categories": sold_categories,
    }


def build_sales_summary(processed_orders, products, low_stock_threshold=None):
    """All report numbers in ONE dictionary (nothing is printed here), so tests can check them."""
    paid = [r for r in processed_orders if r["status"] == "paid"]
    pending = [r for r in processed_orders if r["status"] == "pending"]
    rejected = [r for r in processed_orders if r["status"] == "rejected"]

    customer_report = generate_customer_report(processed_orders)
    product_report = generate_product_report(processed_orders, products)
    low_stock = get_low_stock_products(products, low_stock_threshold)

    return {
        "total_orders": len(processed_orders),
        "paid_orders": len(paid),
        "pending_orders": len(pending),
        "rejected_orders": len(rejected),
        "total_revenue": add_up(*[r["total"] for r in paid]),
        "total_discount": add_up(*[r["discount"] for r in paid]),
        "total_shipping": add_up(*[r["shipping"] for r in paid]),
        "customers_with_valid_order": len(customer_report["unique_customers"]),
        "top_customers": customer_report["top_customers"],
        "top_spend": customer_report["top_spend"],
        "top_products": product_report["top_products"],
        "top_units": product_report["top_units"],
        "categories_sold": sorted(product_report["sold_categories"]),
        "low_stock": [(pid, product.get("name", pid), product["stock"]) for pid, product in low_stock],
    }


def format_sales_report(summary):
    """Turn the summary dictionary into the report text (returns a string, does not print)."""
    if summary["top_customers"]:
        top_customer = ", ".join(summary["top_customers"]) + f" ({money(summary['top_spend'])})"
    else:
        top_customer = "N/A"

    if summary["top_products"]:
        names = ", ".join(summary["top_products"])
        if len(summary["top_products"]) > 1:
            top_product = f"{names} (tie, {summary['top_units']} units each)"
        else:
            top_product = f"{names} ({summary['top_units']} units)"
    else:
        top_product = "N/A"

    categories = ", ".join(summary["categories_sold"]) if summary["categories_sold"] else "N/A"

    lines = [
        "========== SALES REPORT ==========",
        "",
        f"Total Orders: {summary['total_orders']}",
        f"Paid Orders: {summary['paid_orders']}",
        f"Pending Orders: {summary['pending_orders']}",
        f"Rejected Orders: {summary['rejected_orders']}",
        "",
        f"Total Revenue: {money(summary['total_revenue'])}",
        f"Total Discount: {money(summary['total_discount'])}",
        f"Total Shipping: {money(summary['total_shipping'])}",
        "",
        f"Customers With A Valid Order: {summary['customers_with_valid_order']}",
        f"Top Customer: {top_customer}",
        f"Top Selling Product: {top_product}",
        f"Categories Sold: {categories}",
        "",
        "Low Stock Products:",
    ]
    if summary["low_stock"]:
        for pid, name, stock in summary["low_stock"]:
            lines.append(f"- {name} ({pid}): {stock} left")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("==================================")
    return "\n".join(lines)


def generate_sales_report(processed_orders, products, low_stock_threshold=None):
    """Build the full report text (summary dictionary -> formatted text). Returns a string."""
    return format_sales_report(build_sales_summary(processed_orders, products, low_stock_threshold))
