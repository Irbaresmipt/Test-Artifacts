"""/seminar/workflow/orders — Event Storming demo API (command -> event -> policy -> read model)."""
from decimal import Decimal

import allure
import pytest

from api.assertions import assert_error, assert_schema, assert_status
from data.order_factory import (
    DEFAULT_TOTAL,
    payload_with_item,
    random_uuid,
    valid_order_payload,
)
from schemas.order_schemas import BOARD_SCHEMA, ORDER_SCHEMA, WORKFLOW_STEP_SCHEMA

pytestmark = [allure.epic("Pizza Delivery API"), allure.feature("Seminar workflow API"), pytest.mark.workflow]

BUG_WORKFLOW_409 = (
    "БАГ приложения: недопустимая workflow-команда даёт 500 вместо 409. "
    "Order.markPaid/startCooking/... бросают IllegalStateException, который в workflow-интеракторах "
    "не переводится в BusinessRuleViolationException."
)
workflow_bug = pytest.mark.xfail(strict=True, reason=BUG_WORKFLOW_409)

# (метод клиента, executedCommand, emittedEvent, статус после, подсказка policy: имя, следующая команда)
STEPS = [
    ("payment_received", "ReceivePayment", "PaymentReceived", "PAID", "KitchenStartPolicy", "StartCooking"),
    ("start_cooking", "StartCooking", "CookingStarted", "COOKING", "CourierAssignmentPolicy", "AssignCourier"),
    ("assign_courier", "AssignCourier", "CourierAssigned", "OUT_FOR_DELIVERY", "DeliveryCompletionPolicy", "DeliverOrder"),
    ("deliver", "DeliverOrder", "OrderDelivered", "DELIVERED", "WorkflowCompleted", "None"),
]
STEP_METHODS = [s[0] for s in STEPS]


@pytest.fixture
def wf_order(workflow_api, created_ids) -> dict:
    """Заказ, созданный через workflow API (ответ первого шага)."""
    response = workflow_api.create(valid_order_payload())
    assert_status(response, 200)
    body = response.json()
    created_ids.append(body["orderId"])
    return body


@allure.story("Позитивные сценарии")
@pytest.mark.positive
class TestWorkflowPositive:
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("CreateOrder: событие OrderCreated и подсказка PaymentRequestedPolicy")
    def test_create_order_step(self, wf_order):
        assert_schema(wf_order, WORKFLOW_STEP_SCHEMA)
        assert wf_order["executedCommand"] == "CreateOrder"
        assert wf_order["emittedEvent"] == "OrderCreated"
        assert wf_order["currentStatus"] == "CREATED"
        assert wf_order["policyName"] == "PaymentRequestedPolicy"
        assert wf_order["suggestedNextCommand"] == "ReceivePayment"
        assert Decimal(str(wf_order["board"]["totalAmount"])) == DEFAULT_TOTAL

    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Полная цепочка команд проходит по бизнес-процессу до DELIVERED")
    def test_full_workflow_chain(self, workflow_api, wf_order):
        order_id = wf_order["orderId"]
        for method, command, event, status, policy, next_cmd in STEPS:
            response = getattr(workflow_api, method)(order_id)

            assert_status(response, 200)
            body = response.json()
            assert_schema(body, WORKFLOW_STEP_SCHEMA)
            with allure.step(f"Проверить шаг {command}"):
                assert body["orderId"] == order_id
                assert body["executedCommand"] == command
                assert body["emittedEvent"] == event
                assert body["currentStatus"] == status
                assert body["policyName"] == policy
                assert body["suggestedNextCommand"] == next_cmd
                assert body["board"]["currentStatus"] == status

    @allure.title("Board: начальное состояние заказа")
    def test_board_initial_state(self, workflow_api, wf_order):
        response = workflow_api.board(wf_order["orderId"])
        assert_status(response, 200)
        body = response.json()
        assert_schema(body, BOARD_SCHEMA)
        assert body["currentStatus"] == "CREATED"
        assert body["nextSuggestedCommand"] == "ReceivePayment"
        assert not any([body["paymentReceived"], body["cookingStarted"],
                        body["courierAssigned"], body["delivered"]])

    @allure.title("Board: флаги прогресса после шага {method}")
    @pytest.mark.parametrize("method", STEP_METHODS)
    def test_board_flags_progress(self, workflow_api, wf_order, method):
        order_id = wf_order["orderId"]
        for m in STEP_METHODS[: STEP_METHODS.index(method) + 1]:
            assert_status(getattr(workflow_api, m)(order_id), 200)

        board = workflow_api.board(order_id).json()

        reached = STEP_METHODS.index(method) + 1
        assert board["paymentReceived"] is (reached >= 1)
        assert board["cookingStarted"] is (reached >= 2)
        assert board["courierAssigned"] is (reached >= 3)
        assert board["delivered"] is (reached >= 4)

    @allure.title("Заказ из workflow API виден в основном API /orders/{id}")
    def test_workflow_order_visible_in_orders_api(self, orders_api, workflow_api, wf_order):
        assert_status(workflow_api.payment_received(wf_order["orderId"]), 200)

        response = orders_api.get(wf_order["orderId"])

        assert_status(response, 200)
        body = response.json()
        assert_schema(body, ORDER_SCHEMA)
        assert body["status"] == "PAID"


@allure.story("Негативные сценарии")
@pytest.mark.negative
class TestWorkflowNegative:
    @allure.title("CreateOrder с невалидными данными -> 400")
    def test_create_invalid(self, workflow_api):
        assert_error(workflow_api.create(payload_with_item(qty=0)), 400, "item.qty")

    @allure.title("CreateOrder с пустым списком позиций -> 400")
    def test_create_without_items(self, workflow_api):
        assert_error(workflow_api.create(valid_order_payload(items=[])), 400, "items must be non-empty")

    @allure.title("Команда {method} для несуществующего заказа -> 404")
    @pytest.mark.parametrize("method", STEP_METHODS)
    def test_step_unknown_order(self, workflow_api, method):
        assert_error(getattr(workflow_api, method)(random_uuid()), 404, "Order not found")

    @allure.title("Команда {method} с некорректным UUID -> 400")
    @pytest.mark.parametrize("method", STEP_METHODS)
    def test_step_invalid_uuid(self, workflow_api, method):
        assert_error(getattr(workflow_api, method)("not-a-uuid"), 400)

    @allure.title("Board для несуществующего заказа -> 404")
    def test_board_unknown_order(self, workflow_api):
        assert_error(workflow_api.board(random_uuid()), 404)

    @allure.title("Board с некорректным UUID -> 400")
    def test_board_invalid_uuid(self, workflow_api):
        assert_error(workflow_api.board("not-a-uuid"), 400)

    @workflow_bug
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Команда {method} вне очереди -> 409 (README: нарушение правила даёт 409), статус не меняется")
    @pytest.mark.parametrize("method", ["start_cooking", "assign_courier", "deliver"])
    def test_out_of_order_command(self, workflow_api, wf_order, method):
        # Заказ в статусе CREATED: пропуск оплаты недопустим
        response = getattr(workflow_api, method)(wf_order["orderId"])

        assert_error(response, 409, "Illegal status transition")
        assert workflow_api.board(wf_order["orderId"]).json()["currentStatus"] == "CREATED"

    @workflow_bug
    @allure.title("Повторная оплата уже оплаченного заказа -> 409")
    def test_repeat_payment(self, workflow_api, wf_order):
        assert_status(workflow_api.payment_received(wf_order["orderId"]), 200)
        assert_error(workflow_api.payment_received(wf_order["orderId"]), 409)

    @workflow_bug
    @allure.title("Команда после завершения доставки -> 409")
    def test_command_after_delivered(self, workflow_api, wf_order):
        for method in STEP_METHODS:
            assert_status(getattr(workflow_api, method)(wf_order["orderId"]), 200)
        assert_error(workflow_api.deliver(wf_order["orderId"]), 409)
