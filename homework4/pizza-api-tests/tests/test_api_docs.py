"""Smoke-проверки доступности приложения: OpenAPI и Swagger UI."""
import allure
import pytest

from api.assertions import assert_status

pytestmark = [allure.epic("Pizza Delivery API"), allure.feature("Документация API"), pytest.mark.smoke]

@allure.severity(allure.severity_level.BLOCKER)
@allure.title("OpenAPI JSON доступен и описывает основные эндпоинты")
def test_openapi_available(orders_api):
    response = orders_api.api_docs()
    assert_status(response, 200)
    paths = response.json()["paths"]
    for expected in ("/orders", "/orders/{id}/status", "/seminar/workflow/orders"):
        assert expected in paths, f"{expected} отсутствует в OpenAPI"


@allure.title("Swagger UI доступен")
def test_swagger_ui_available(orders_api):
    assert_status(orders_api.swagger_ui(), 200)
