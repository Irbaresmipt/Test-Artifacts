"""Общие фикстуры: клиенты, создание заказов, приведение заказа к нужному статусу."""
import allure
import pytest

from api.assertions import assert_status
from api.orders_client import OrdersClient
from api.workflow_client import WorkflowClient
from data.order_factory import HAPPY_PATH, valid_order_payload

CLEANUP_REASON = "autotest cleanup"


@pytest.fixture(scope="session")
def orders_api() -> OrdersClient:
    return OrdersClient()


@pytest.fixture(scope="session")
def workflow_api() -> WorkflowClient:
    return WorkflowClient()


@pytest.fixture
def created_ids(orders_api):
    """Собирает id созданных в тесте заказов и по возможности удаляет их после теста."""
    ids: list[str] = []
    yield ids
    for order_id in ids:
        try:
            orders_api.remove(order_id, CLEANUP_REASON)  # best-effort, статус может не позволять
        except Exception:
            pass


@pytest.fixture
def order_factory(orders_api, created_ids):
    """Фабрика: создаёт заказ и (опционально) переводит его в нужный статус через API."""

    def _make(status: str = "CREATED", payload: dict | None = None) -> dict:
        with allure.step(f"Подготовка: заказ в статусе {status}"):
            response = orders_api.create(payload or valid_order_payload())
            assert_status(response, 201)
            order = response.json()
            created_ids.append(order["id"])

            if status == "CANCELLED":
                assert_status(orders_api.change_status(order["id"], "CANCELLED"), 200)
            elif status != "CREATED":
                for step in HAPPY_PATH:
                    assert_status(orders_api.change_status(order["id"], step), 200)
                    if step == status:
                        break
                else:
                    raise ValueError(f"Неизвестный статус: {status}")
            return orders_api.get(order["id"]).json()

    return _make


@pytest.fixture
def order(order_factory) -> dict:
    """Свежесозданный заказ в статусе CREATED."""
    return order_factory("CREATED")
