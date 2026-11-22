"""GET /orders и GET /orders/{id}."""
import allure
import pytest

from api.assertions import assert_error, assert_schema, assert_status
from data.order_factory import random_uuid
from schemas.order_schemas import ORDER_LIST_SCHEMA, ORDER_SCHEMA, ORDER_SUMMARY_SCHEMA

pytestmark = [allure.epic("Pizza Delivery API"), allure.feature("Просмотр заказов")]


@allure.story("Получение заказа по id")
class TestGetOrder:
    @pytest.mark.positive
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("Созданный заказ возвращается по id: 200 и схема")
    def test_get_existing_order(self, orders_api, order):
        response = orders_api.get(order["id"])
        assert_status(response, 200)
        body = response.json()
        assert_schema(body, ORDER_SCHEMA)
        assert body == order

    @pytest.mark.negative
    @allure.title("Несуществующий заказ -> 404")
    def test_get_unknown_order(self, orders_api):
        assert_error(orders_api.get(random_uuid()), 404, "Order not found")

    @pytest.mark.negative
    @allure.title("Некорректный UUID '{bad_id}' -> 400")
    @pytest.mark.parametrize("bad_id", ["not-a-uuid", "123", "00000000-0000-0000-0000-00000000000Z"])
    def test_get_with_invalid_uuid(self, orders_api, bad_id):
        assert_error(orders_api.get(bad_id), 400)


@allure.story("Список заказов")
class TestListOrders:
    @pytest.mark.positive
    @pytest.mark.smoke
    @allure.title("Список заказов: 200, массив, элементы соответствуют схеме")
    def test_list_structure(self, orders_api, order):
        response = orders_api.list()
        assert_status(response, 200)
        body = response.json()
        assert_schema(body, ORDER_LIST_SCHEMA)
        assert len(body) >= 1

    @pytest.mark.positive
    @allure.title("Созданный заказ присутствует в списке с корректными данными")
    def test_created_order_in_list(self, orders_api, order):
        items = orders_api.list().json()
        found = [o for o in items if o["id"] == order["id"]]
        assert len(found) == 1
        assert_schema(found[0], ORDER_SUMMARY_SCHEMA)
        with allure.step("Сверить поля сводки с заказом"):
            assert found[0]["status"] == order["status"]
            assert found[0]["totalAmount"] == order["totalAmount"]
            assert found[0]["currency"] == order["currency"]
            assert found[0]["deliveryZone"] == order["deliveryZone"]

    @pytest.mark.positive
    @allure.title("Смена статуса отражается в списке")
    def test_status_change_reflected_in_list(self, orders_api, order):
        assert_status(orders_api.change_status(order["id"], "PAID"), 200)
        found = next(o for o in orders_api.list().json() if o["id"] == order["id"])
        assert found["status"] == "PAID"
