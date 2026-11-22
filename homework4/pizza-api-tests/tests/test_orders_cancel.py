"""DELETE /orders/{id}?reason=... — отмена заказа (мягкая: статус CANCELLED)."""
import allure
import pytest

from api.assertions import assert_error, assert_status
from data.order_factory import random_uuid

pytestmark = [allure.epic("Pizza Delivery API"), allure.feature("Отмена заказа")]

REASON = "Пользователь сообщил об ошибочном заказе"


@allure.story("Позитивные сценарии")
@pytest.mark.positive
class TestCancelPositive:
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("Отмена заказа в статусе {status}: 204, статус CANCELLED, причина сохранена")
    @pytest.mark.parametrize("status", ["CREATED", "PAID", "COOKING"])
    def test_cancel_allowed_statuses(self, orders_api, order_factory, status):
        order = order_factory(status)

        response = orders_api.cancel(order["id"], REASON)

        assert_status(response, 204)
        assert response.content == b""
        with allure.step("Проверить заказ после отмены"):
            body = orders_api.get(order["id"]).json()
            assert body["status"] == "CANCELLED"
            assert body["cancellationReason"] == REASON

    @allure.title("Пробелы по краям причины обрезаются")
    def test_reason_is_stripped(self, orders_api, order):
        assert_status(orders_api.cancel(order["id"], "   duplicate order   "), 204)
        assert orders_api.get(order["id"]).json()["cancellationReason"] == "duplicate order"

    @allure.title("Повторная отмена с той же причиной идемпотентна: 204")
    def test_repeat_cancel_same_reason(self, orders_api, order):
        assert_status(orders_api.cancel(order["id"], REASON), 204)
        assert_status(orders_api.cancel(order["id"], REASON), 204)
        assert orders_api.get(order["id"]).json()["cancellationReason"] == REASON

    @allure.title("Граничные длины причины: {length} символ(ов) допустимы")
    @pytest.mark.parametrize("length", [1, 1000])
    def test_reason_length_boundaries(self, orders_api, order, length):
        assert_status(orders_api.cancel(order["id"], "x" * length), 204)

    @allure.title("Отменённый заказ остаётся в списке со статусом CANCELLED")
    def test_cancelled_order_in_list(self, orders_api, order):
        assert_status(orders_api.cancel(order["id"], REASON), 204)
        found = next(o for o in orders_api.list().json() if o["id"] == order["id"])
        assert found["status"] == "CANCELLED"


@allure.story("Негативные сценарии")
@pytest.mark.negative
class TestCancelNegative:
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Отмена заказа в статусе {status} запрещена: 409")
    @pytest.mark.parametrize("status", ["OUT_FOR_DELIVERY", "DELIVERED"])
    def test_cancel_forbidden_statuses(self, orders_api, order_factory, status):
        order = order_factory(status)

        assert_error(orders_api.cancel(order["id"], REASON), 409, "Illegal status transition")

        assert orders_api.get(order["id"]).json()["status"] == status

    @allure.title("Повторная отмена с другой причиной: 409, исходная причина не перезаписана")
    def test_repeat_cancel_other_reason(self, orders_api, order):
        assert_status(orders_api.cancel(order["id"], "first reason"), 204)

        assert_error(orders_api.cancel(order["id"], "second reason"), 409)

        assert orders_api.get(order["id"]).json()["cancellationReason"] == "first reason"

    @allure.title("Некорректная причина ({case}) -> 400, заказ не изменён")
    @pytest.mark.parametrize(
        "case, reason",
        [("missing", None), ("empty", ""), ("blank", "   "), ("too-long", "x" * 1001)],
    )
    def test_invalid_reason(self, orders_api, order, case, reason):
        assert_error(orders_api.cancel(order["id"], reason), 400)
        assert orders_api.get(order["id"]).json()["status"] == "CREATED"

    @allure.title("Несуществующий заказ -> 404")
    def test_unknown_order(self, orders_api):
        assert_error(orders_api.cancel(random_uuid(), REASON), 404, "Order not found")

    @allure.title("Некорректный UUID -> 400")
    def test_invalid_uuid(self, orders_api):
        assert_error(orders_api.cancel("not-a-uuid", REASON), 400)
