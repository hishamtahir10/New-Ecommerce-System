"""validation.py - checks whether an order is valid (never crashes)."""

from decimal import Decimal


def is_non_empty_string(value):
    """True only for a string that has at least one non-space character."""
    return isinstance(value, str) and value.strip() != ""


def is_valid_price(price):
    """Number (int, float or Decimal; not bool, not NaN/infinity) that is 0 or more."""
    if isinstance(price, bool) or not isinstance(price, (int, float, Decimal)):
        return False
    number = Decimal(str(price))
    return number.is_finite() and number >= 0


def is_valid_stock(stock):
    """Whole number (not bool) that is 0 or more."""
    return isinstance(stock, int) and not isinstance(stock, bool) and stock >= 0


def validate_order(order, products):
    """Return (True, "") if the order is fine, else (False, "reason").
    It never raises an error - a bad order just gets a reason."""
    if not isinstance(order, dict):
        return False, "Order is not a valid dictionary"
    if not isinstance(products, dict):
        return False, "Product catalogue is not a valid dictionary"

    if not is_non_empty_string(order.get("order_id")):
        return False, "Missing or invalid order ID"
    if not is_non_empty_string(order.get("customer")):
        return False, "Missing or invalid customer name"

    items = order.get("items")
    if not isinstance(items, list) or len(items) == 0:
        return False, "Order has no items"

    if order.get("payment_status") not in ("paid", "pending"):
        return False, "Invalid payment status: " + str(order.get("payment_status"))

    requested = {}  # product_id -> total quantity asked in this order
    for item in items:
        if not isinstance(item, dict):
            return False, "Item is not a valid dictionary"

        product_id = item.get("product_id")
        quantity = item.get("quantity")

        if not isinstance(product_id, str) or product_id not in products:
            return False, "Unknown product ID: " + str(product_id)

        # The product data itself must be sane (price and stock)
        product = products[product_id]
        if not isinstance(product, dict):
            return False, f"Product {product_id} data is not a valid dictionary"
        if not is_valid_price(product.get("price")):
            return False, f"Invalid price for product {product_id}"
        if not is_valid_stock(product.get("stock")):
            return False, f"Invalid stock for product {product_id}"

        # bool is a subtype of int in Python, so reject it explicitly
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            return False, f"Quantity for {product_id} must be a whole number"
        if quantity <= 0:
            return False, f"Quantity for {product_id} must be positive (got {quantity})"

        requested[product_id] = requested.get(product_id, 0) + quantity

    # Stock check AFTER adding duplicate lines of the same product together
    for product_id, quantity in requested.items():
        available = products[product_id]["stock"]
        if quantity > available:
            return False, f"Insufficient stock for {product_id} (wanted {quantity}, have {available})"

    return True, ""
