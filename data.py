"""data.py - starter data. Functions return a FRESH copy every time,
so no global variables are needed and tests never affect each other."""


def get_starter_products():
    """Fresh copy of the starter product catalogue (id -> name, price, category, stock)."""
    return {
        "P001": {"name": "Laptop", "price": 1200, "category": "Electronics", "stock": 10},
        "P002": {"name": "Mouse", "price": 25, "category": "Accessories", "stock": 50},
        "P003": {"name": "Keyboard", "price": 75, "category": "Accessories", "stock": 20},
        "P004": {"name": "Monitor", "price": 300, "category": "Electronics", "stock": 15},
    }


def get_starter_orders():
    """Fresh copy of the three starter orders (ORD001, ORD002, ORD003)."""
    return [
        {
            "order_id": "ORD001", "customer": "Ali",
            "items": [
                {"product_id": "P001", "quantity": 1},
                {"product_id": "P002", "quantity": 2},
            ],
            "payment_status": "paid",
        },
        {
            "order_id": "ORD002", "customer": "Ahmed",
            "items": [
                {"product_id": "P003", "quantity": 2},
                {"product_id": "P004", "quantity": 1},
            ],
            "payment_status": "paid",
        },
        {
            "order_id": "ORD003", "customer": "Ali",
            "items": [{"product_id": "P002", "quantity": 5}],
            "payment_status": "pending",
        },
    ]
