"""reports.py - customer report, product report, low-stock list and the final sales report."""

from helpers import add_up, money


def make_low_stock_checker(threshold):
    """LEGB demo (the 'E' = Enclosing scope):
    the inner function is_low() uses `threshold`, which lives in the
    enclosing function - no global variable needed."""
    def is_low(product):
        return product.get("stock", 0) <= threshold
    return is_low


def get_low_stock_products(products, threshold=10):
    """List of (product_id, product) with stock <= threshold, lowest stock first."""
    is_low = make_low_stock_checker(threshold)
    low = [(pid, product) for pid, product in products.items() if is_low(product)]
    low.sort(key=lambda pair: (pair[1].get("stock", 0), pair[1].get("name", "")))
    return low


def generate_customer_report(processed_orders):
    """Spending per customer (PAID orders only) and the top customer(s)."""
    spend = {}
    for record in processed_orders:
        if record["status"] == "paid":
            name = record["customer"]
            spend[name] = add_up(spend.get(name, 0), record["total"])

    unique_customers = {record["customer"] for record in processed_orders}  # a set

    ranking = sorted(spend.items(), key=lambda pair: (-pair[1], pair[0]))
    top_spend = ranking[0][1] if ranking else 0
    top_customers = [name for name, amount in ranking if amount == top_spend] if ranking else []

    return {
        "spend": spend,
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
        return products.get(pid, {}).get("name", pid)

    sold_categories = {products[pid]["category"] for pid in units_sold
                       if pid in products and "category" in products[pid]}  # a set

    top_units = max(units_sold.values()) if units_sold else 0
    top_products = sorted(name_of(pid) for pid, qty in units_sold.items() if qty == top_units) \
        if units_sold else []

    return {
        "units_sold": units_sold,
        "top_products": top_products,     # a list, because of possible ties
        "top_units": top_units,
        "sold_categories": sold_categories,
    }


def generate_sales_report(processed_orders, products, low_stock_threshold=10):
    """Build the full report text in the required format."""
    paid = [r for r in processed_orders if r["status"] == "paid"]
    pending = [r for r in processed_orders if r["status"] == "pending"]
    rejected = [r for r in processed_orders if r["status"] == "rejected"]

    total_revenue = add_up(*[r["total"] for r in paid])
    total_discount = add_up(*[r["discount"] for r in paid])
    total_shipping = add_up(*[r["shipping"] for r in paid])

    customer_report = generate_customer_report(processed_orders)
    product_report = generate_product_report(processed_orders, products)
    low_stock = get_low_stock_products(products, low_stock_threshold)

    if customer_report["top_customers"]:
        top_customer = ", ".join(customer_report["top_customers"]) \
            + f" ({money(customer_report['top_spend'])})"
    else:
        top_customer = "N/A"

    if product_report["top_products"]:
        names = ", ".join(product_report["top_products"])
        if len(product_report["top_products"]) > 1:
            top_product = f"{names} (tie, {product_report['top_units']} units each)"
        else:
            top_product = f"{names} ({product_report['top_units']} units)"
    else:
        top_product = "N/A"

    lines = [
        "========== SALES REPORT ==========",
        "",
        f"Total Orders: {len(processed_orders)}",
        f"Paid Orders: {len(paid)}",
        f"Pending Orders: {len(pending)}",
        f"Rejected Orders: {len(rejected)}",
        "",
        f"Total Revenue: {money(total_revenue)}",
        f"Total Discount: {money(total_discount)}",
        f"Total Shipping: {money(total_shipping)}",
        "",
        f"Top Customer: {top_customer}",
        f"Top Selling Product: {top_product}",
        "",
        "Low Stock Products:",
    ]
    if low_stock:
        for pid, product in low_stock:
            lines.append(f"- {product.get('name', pid)} ({pid}): {product.get('stock', 0)} left")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("==================================")
    return "\n".join(lines)
