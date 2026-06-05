import json
import os
import random
import string
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
USERS_PATH = os.path.join(DATA_DIR, "users.json")
ORDERS_PATH = os.path.join(DATA_DIR, "orders.json")


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _read_json(path):
    _ensure_dir()
    if not os.path.exists(path):
        _write_json(path, [])
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _get_user(users, user_id):
    for u in users:
        if u["user_id"] == user_id:
            return u
    return None


def get_balance(user_id):
    users = _read_json(USERS_PATH)
    user = _get_user(users, user_id)
    return user["balance"] if user else 0.0


def add_balance(user_id, amount):
    users = _read_json(USERS_PATH)
    user = _get_user(users, user_id)
    if user:
        user["balance"] = user["balance"] + amount
    else:
        users.append({"user_id": user_id, "balance": amount, "created_at": datetime.now().isoformat()})
    _write_json(USERS_PATH, users)
    return True


def deduct_balance(user_id, amount):
    users = _read_json(USERS_PATH)
    user = _get_user(users, user_id)
    if user and user["balance"] >= amount:
        user["balance"] = user["balance"] - amount
        _write_json(USERS_PATH, users)
        return True
    return False


def generate_id(prefix="ORD"):
    chars = string.ascii_uppercase + string.digits
    return f"{prefix}-" + "".join(random.choices(chars, k=8))


def create_order(user_id, username, account_type, price):
    orders = _read_json(ORDERS_PATH)
    order = {
        "id": generate_id(),
        "user_id": user_id,
        "username": username,
        "account_type": account_type,
        "price": price,
        "status": "completed",
        "created_at": datetime.now().isoformat()
    }
    orders.append(order)
    _write_json(ORDERS_PATH, orders)
    return order


def get_user_orders(user_id):
    orders = _read_json(ORDERS_PATH)
    return [o for o in orders if o["user_id"] == user_id]
