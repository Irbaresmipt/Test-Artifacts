"""PATCH /orders/{id}/status — смена статуса и правила переходов."""
import allure
import pytest

from api.assertions import assert_error, assert_schema, assert_status
from data.order_factory import ALLOWED_TRANSITIONS, HAPPY_PATH, random_uuid
from schemas.order_schemas import ORDER_SCHEMA

pytestmark = [allure.epic("Pizza Delivery API"), allure.feature("Смена статуса заказа")]

BUG_NULL_STATUS = (
    "БАГ приложения: {\"status\": null} -> 500 вместо 400. "
    "ChangeOrderStatusCommand делает Objects.requireNonNull(newStatus) -> NPE -> общий handler."
)

_ALL = list(ALLOWED_TRANSITIONS)
_VALID = [(src, dst) for src, dsts in ALLOWED_TRANSITIONS.items() for dst in sorted(dsts)]
_INVALID = [(src, dst) for src in _ALL for dst in _ALL if dst not in ALLOWED_TRANSITIONS[src]]


@allure.story("Допустимые переходы")
@pytest.mark.positive
class TestStatusPositive:
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("Допустимый переход {src} -> {dst}: 200 и новый статус сохранён")
    @pytest.mark.parametrize("src, dst", _VALID, ids=[f"{s}-{d}" for s, d in _VALID])
    def test_valid_transition(self, orders_api, order_factory, src, dst):
        order = order_factory(src)

        response = orders_api.change_status(order["id"], dst)

        assert_status(response, 200)
        body = response.json()
        assert_schema(body, ORDER_SCHEMA)
        assert body["id"] == order["id"]
        assert body["status"] == dst
        with allure.step("Убедиться, что статус сохранился (GET)"):
            assert orders_api.get(order["id"]).json()["status"] == dst

    @allure.title("Полный жизненный цикл: CREATED -> PAID -> COOKING -> OUT_FOR_DELIVERY -> DELIVERED")
    def test_full_lifecycle(self, orders_api, order):
        for status in HAPPY_PATH:
            response = orders_api.change_status(order["id"], status)
            assert_status(response, 200)
            assert response.json()["status"] == status

    @allure.title("Статус нечувствителен к регистру ('paid')")
    def test_status_case_insensitive(self, orders_api, order):
        response = orders_api.change_status(order["id"], "paid")
        assert_status(response, 200)
        assert response.json()["status"] == "PAID"

    @allure.title("Смена статуса не меняет остальные поля заказа")
    def test_other_fields_unchanged(self, orders_api, order):
        body = orders_api.change_status(order["id"], "PAID").json()
        for field in ("id", "address", "items", "totalAmount", "currency", "deliveryZone"):
            assert body[field] == order[field], field


@allure.story("Недопустимые переходы и ошибки запроса")
@pytest.mark.negative
class TestStatusNegative:
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Запрещённый переход {src} -> {dst}: 409 и статус не изменился")
    @pytest.mark.parametrize("src, dst", _INVALID, ids=[f"{s}-{d}" for s, d in _INVALID])
    def test_illegal_transition_returns_409(self, orders_api, order_factory, src, dst):
        order = order_factory(src)

        response = orders_api.change_status(order["id"], dst)

        assert_error(response, 409, "Illegal status transition")
        with allure.step("Убедиться, что статус не изменился"):
            assert orders_api.get(order["id"]).json()["status"] == src

    @allure.title("Недопустимое значение статуса {status!r} -> 400")
    @pytest.mark.parametrize(
        "status",
        [
            "FLYING", "", "   ", "PAID!",
            pytest.param(None, marks=pytest.mark.xfail(
                strict=True, reason=BUG_NULL_STATUS), id="null"),
        ],
    )
    def test_invalid_status_value(self, orders_api, order, status):
        assert_error(orders_api.change_status(order["id"], status), 400)

    @allure.title("Несуществующий заказ -> 404")
    def test_unknown_order(self, orders_api):
        assert_error(orders_api.change_status(random_uuid(), "PAID"), 404, "Order not found")

    @allure.title("Некорректный UUID -> 400")
    def test_invalid_uuid(self, orders_api):
        assert_error(orders_api.change_status("not-a-uuid", "PAID"), 400)
