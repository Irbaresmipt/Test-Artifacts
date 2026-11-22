"""POST /orders — создание заказа."""
from decimal import Decimal

import allure
import pytest

from api.assertions import assert_error, assert_schema, assert_status
from data.order_factory import (
    DEFAULT_TOTAL,
    expected_total,
    payload_with_address,
    payload_with_item,
    valid_order_payload,
)
from schemas.order_schemas import ORDER_SCHEMA

pytestmark = [allure.epic("Pizza Delivery API"), allure.feature("Создание заказа")]


@allure.story("Позитивные сценарии")
@pytest.mark.positive
class TestCreateOrderPositive:
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("Валидный заказ создаётся: 201, Location, схема ответа")
    def test_create_valid_order(self, orders_api, created_ids):
        payload = valid_order_payload()

        response = orders_api.create(payload)
        assert_status(response, 201)
        body = response.json()
        created_ids.append(body["id"])

        assert_schema(body, ORDER_SCHEMA)
        with allure.step("Проверить значения полей ответа"):
            assert response.headers["Location"].endswith(f"/orders/{body['id']}")
            assert body["status"] == "CREATED"
            assert body["currency"] == "EUR"
            assert body["cancellationReason"] is None
            assert Decimal(str(body["totalAmount"])) == DEFAULT_TOTAL
            assert body["address"] == payload["address"]
            assert body["items"] == payload["items"]

    @allure.title("Цена считается по тарифу: {size} x {qty}")
    @pytest.mark.parametrize(
        "size, qty, total",
        [("SMALL", 1, "8.00"), ("MEDIUM", 1, "10.00"), ("LARGE", 1, "12.00"), ("SMALL", 3, "24.00")],
    )
    def test_price_calculation(self, orders_api, created_ids, size, qty, total):
        response = orders_api.create(payload_with_item(size=size, qty=qty))
        assert_status(response, 201)
        body = response.json()
        created_ids.append(body["id"])
        assert Decimal(str(body["totalAmount"])) == Decimal(total)

    @allure.title("Сумма нескольких позиций суммируется")
    def test_total_of_multiple_items(self, orders_api, created_ids):
        items = [
            {"name": "A", "size": "SMALL", "qty": 2},
            {"name": "B", "size": "MEDIUM", "qty": 1},
            {"name": "C", "size": "LARGE", "qty": 3},
        ]
        response = orders_api.create(valid_order_payload(items=items))
        assert_status(response, 201)
        body = response.json()
        created_ids.append(body["id"])
        assert Decimal(str(body["totalAmount"])) == expected_total(items) == Decimal("62.00")

    @allure.title("Зона доставки по почтовому индексу {postcode} -> {zone}")
    @pytest.mark.parametrize(
        "postcode, zone",
        [("1012", "CENTER"), ("1100", "CENTER"), ("1199", "CENTER"), ("2011", "OUTSKIRTS"), ("9999", "OUTSKIRTS")],
    )
    def test_delivery_zone(self, orders_api, created_ids, postcode, zone):
        response = orders_api.create(payload_with_address(postcode=postcode))
        assert_status(response, 201)
        body = response.json()
        created_ids.append(body["id"])
        assert body["deliveryZone"] == zone

    @allure.title("Размер пиццы нечувствителен к регистру")
    def test_size_is_case_insensitive(self, orders_api, created_ids):
        response = orders_api.create(payload_with_item(size="medium"))
        assert_status(response, 201)
        body = response.json()
        created_ids.append(body["id"])
        assert body["items"][0]["size"] == "MEDIUM"
        assert Decimal(str(body["totalAmount"])) == Decimal("10.00")

    @allure.title("Квартира (apartment) необязательна")
    def test_apartment_is_optional(self, orders_api, created_ids):
        payload = valid_order_payload()
        del payload["address"]["apartment"]
        response = orders_api.create(payload)
        assert_status(response, 201)
        body = response.json()
        created_ids.append(body["id"])
        assert_schema(body, ORDER_SCHEMA)
        assert body["address"]["apartment"] is None

    @allure.title("Каждый запрос создаёт новый заказ с уникальным id")
    def test_ids_are_unique(self, orders_api, created_ids):
        first = orders_api.create(valid_order_payload()).json()
        second = orders_api.create(valid_order_payload()).json()
        created_ids.extend([first["id"], second["id"]])
        assert first["id"] != second["id"]


_NEG = [
    pytest.param({}, "items must be non-empty", id="empty-body"),
    pytest.param(valid_order_payload(items=[]), "items must be non-empty", id="empty-items"),
    pytest.param({"address": valid_order_payload()["address"]}, "items must be non-empty", id="no-items"),
    pytest.param({"items": valid_order_payload()["items"]}, "address.city must be non-blank", id="no-address"),
    pytest.param(payload_with_address(city=""), "address.city", id="blank-city"),
    pytest.param(payload_with_address(street="   "), "address.street", id="blank-street"),
    pytest.param(payload_with_address(house=""), "address.house", id="blank-house"),
    pytest.param(payload_with_address(postcode=""), "address.postcode", id="blank-postcode"),
    pytest.param(payload_with_address(postcode=None), "address.postcode", id="null-postcode"),
    pytest.param(payload_with_item(name=""), "item.name", id="blank-item-name"),
    pytest.param(payload_with_item(name=None), "item.name", id="null-item-name"),
    pytest.param(payload_with_item(size=""), "item.size", id="blank-size"),
    pytest.param(payload_with_item(size="HUGE"), "Unknown size", id="unknown-size"),
    pytest.param(payload_with_item(qty=0), "item.qty must be > 0", id="qty-zero"),
    pytest.param(payload_with_item(qty=-1), "item.qty must be > 0", id="qty-negative"),
    pytest.param(valid_order_payload(items=[{"name": "X", "size": "SMALL"}]), "item.qty", id="qty-missing"),
]


@allure.story("Негативные сценарии")
@pytest.mark.negative
class TestCreateOrderNegative:
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Невалидный payload -> 400 и корректный формат ошибки")
    @pytest.mark.parametrize("payload, message", _NEG)
    def test_invalid_payload_returns_400(self, orders_api, payload, message):
        response = orders_api.create(payload)
        assert_error(response, 400, message)

    @allure.title("Невалидный заказ не попадает в список заказов")
    def test_invalid_order_not_persisted(self, orders_api):
        before = len(orders_api.list().json())
        assert_error(orders_api.create(payload_with_item(qty=0)), 400)
        after = len(orders_api.list().json())
        assert after == before
