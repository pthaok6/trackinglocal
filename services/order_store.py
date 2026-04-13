import json
import os

FILE = "data/orders.json"

def load_orders():
    if not os.path.exists(FILE):
        return []
    with open(FILE, "r") as f:
        return json.load(f)

def save_orders(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_order(code, note):
    orders = load_orders()

    orders.append({
        "code": code,
        "note": note
    })

    save_orders(orders)
    return orders

def delete_order(index):
    orders = load_orders()

    if 0 <= index < len(orders):
        orders.pop(index)

    save_orders(orders)
    return orders
