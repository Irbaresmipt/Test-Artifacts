"""DELETE /orders/{id}/remove?reason=... — полное удаление заказа."""
import allure
import pytest

from api.assertions import assert_error, assert_status
from data.order_factory import random_uuid

pytestmark = [allure.epic("Pizza Delivery API"), allure.feature("Полное удаление заказа")]

REASON = "Тестовый заказ, удалить"


@allure.story("Позитивные сценарии")
@pytest.mark.positive
class TestRemovePositive:
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("Удаление заказа в статусе {status}: 204, затем GET -> 404")
    @pytest.mark.parametrize("status", ["CREATED", "PAID", "COOKING"])
    def test_remove_allowed_statuses(self, orders_api, order_factory, status):
        order = order_factory(status)

        response = orders_api.remove(order["id"], REASON)

        assert_status(response, 204)
        assert response.content == b""
        with allure.step("Заказ больше недоступен"):
            assert_error(orders_api.get(order["id"]), 404)

    @allure.title("Удалённый заказ исчезает из списка")
    def test_removed_order_not_in_list(self, orders_api, order):
        assert_status(orders_api.remove(order["id"], REASON), 204)
        assert order["id"] not in [o["id"] for o in orders_api.list().json()]

    @allure.title("Удаление отменённого заказа с той же причиной: 204")
    def test_remove_cancelled_with_same_reason(self, orders_api, order):
        assert_status(orders_api.cancel(order["id"], REASON), 204)
        assert_status(orders_api.remove(order["id"], REASON), 204)
        assert_error(orders_api.get(order["id"]), 404)


@allure.story("Негативные сценарии")
@pytest.mark.negative
class TestRemoveNegative:
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Удаление заказа в статусе {status} запрещено: 409, заказ сохранён")
    @pytest.mark.parametrize("status", ["OUT_FOR_DELIVERY", "DELIVERED"])
    def test_remove_forbidden_statuses(self, orders_api, order_factory, status):
        order = order_factory(status)

        assert_error(orders_api.remove(order["id"], REASON), 409)

        assert_status(orders_api.get(order["id"]), 200)

    @allure.title("Удаление отменённого заказа с другой причиной: 409")
    def test_remove_cancelled_with_other_reason(self, orders_api, order):
        assert_status(orders_api.cancel(order["id"], "reason A"), 204)
        assert_error(orders_api.remove(order["id"], "reason B"), 409)
        assert_status(orders_api.get(order["id"]), 200)

    @allure.title("Повторное удаление -> 404")
    def test_repeat_remove(self, orders_api, order):
        assert_status(orders_api.remove(order["id"], REASON), 204)
        assert_error(orders_api.remove(order["id"], REASON), 404, "Order not found")

    @allure.title("Некорректная причина ({case}) -> 400, заказ сохранён")
    @pytest.mark.parametrize(
        "case, reason",
        [("missing", None), ("empty", ""), ("blank", "   "), ("too-long", "x" * 1001)],
    )
    def test_invalid_reason(self, orders_api, order, case, reason):
        assert_error(orders_api.remove(order["id"], reason), 400)
        assert_status(orders_api.get(order["id"]), 200)

    @allure.title("Несуществующий заказ -> 404")
    def test_unknown_order(self, orders_api):
        assert_error(orders_api.remove(random_uuid(), REASON), 404)

    @allure.title("Некорректный UUID -> 400")
    def test_invalid_uuid(self, orders_api):
        assert_error(orders_api.remove("not-a-uuid", REASON), 400)
