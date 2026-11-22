"""Переиспользуемые проверки ответов."""
from typing import Optional

import allure
import requests
from jsonschema import Draft7Validator

from schemas.order_schemas import ERROR_SCHEMA


def assert_status(response: requests.Response, expected: int) -> None:
    with allure.step(f"Проверить статус-код: ожидается {expected}"):
        assert response.status_code == expected, (
            f"Ожидался HTTP {expected}, получен {response.status_code}. Тело: {response.text[:500]}"
        )


def assert_schema(instance, schema: dict) -> None:
    with allure.step("Проверить структуру ответа по JSON-схеме"):
        errors = sorted(Draft7Validator(schema).iter_errors(instance), key=lambda e: list(map(str, e.path)))
        assert not errors, "Нарушение схемы:\n" + "\n".join(
            f"  {'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors
        )


def assert_error(response: requests.Response, status: int, message_contains: Optional[str] = None) -> None:
    """Проверяет статус, формат ApiError и (опционально) фрагмент сообщения."""
    assert_status(response, status)
    body = response.json()
    assert_schema(body, ERROR_SCHEMA)
    with allure.step("Проверить содержимое ошибки"):
        assert body["status"] == status
        if message_contains:
            assert message_contains in body["message"], (
                f"'{message_contains}' не найдено в '{body['message']}'"
            )
