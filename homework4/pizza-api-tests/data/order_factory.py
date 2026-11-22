"""Тестовые данные: фабрики payload'ов и справочные значения бизнес-правил."""
import copy
import uuid
from decimal import Decimal
from typing import Any

# Цены из OrderPricingPolicy
PRICES = {"SMALL": Decimal("8.00"), "MEDIUM": Decimal("10.00"), "LARGE": Decimal("12.00")}

# Допустимые переходы из OrderStatusTransitionPolicy
ALLOWED_TRANSITIONS = {
    "CREATED": {"PAID", "CANCELLED"},
    "PAID": {"COOKING", "CANCELLED"},
    "COOKING": {"OUT_FOR_DELIVERY", "CANCELLED"},
    "OUT_FOR_DELIVERY": {"DELIVERED"},
    "DELIVERED": set(),
    "CANCELLED": set(),
}

# Цепочка «счастливого пути» после CREATED
HAPPY_PATH = ["PAID", "COOKING", "OUT_FOR_DELIVERY", "DELIVERED"]

DEFAULT_ADDRESS = {
    "city": "Amsterdam",
    "street": "Damrak",
    "house": "1",
    "apartment": "12",
    "postcode": "1012",
}

DEFAULT_ITEMS = [
    {"name": "Margherita", "size": "MEDIUM", "qty": 2},
    {"name": "Pepperoni", "size": "LARGE", "qty": 1},
]
DEFAULT_TOTAL = Decimal("32.00")  # 2*10 + 1*12


def random_uuid() -> str:
    return str(uuid.uuid4())


def valid_order_payload(**overrides: Any) -> dict:
    """Валидный payload заказа; верхнеуровневые ключи можно переопределить."""
    payload = {
        "address": copy.deepcopy(DEFAULT_ADDRESS),
        "items": copy.deepcopy(DEFAULT_ITEMS),
    }
    payload.update(overrides)
    return payload


def payload_with_address(**address_overrides: Any) -> dict:
    payload = valid_order_payload()
    payload["address"].update(address_overrides)
    return payload


def payload_with_item(**item_overrides: Any) -> dict:
    item = {"name": "Margherita", "size": "SMALL", "qty": 1}
    item.update(item_overrides)
    return valid_order_payload(items=[item])


def expected_total(items: list[dict]) -> Decimal:
    return sum((PRICES[i["size"].upper()] * i["qty"] for i in items), Decimal("0.00"))
