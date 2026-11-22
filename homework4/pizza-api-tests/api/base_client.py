"""Базовый HTTP-клиент: единая точка отправки запросов + вложения для Allure."""
import json
from typing import Any

import allure
import requests

from config import settings


class BaseClient:
    def __init__(self, base_url: str = settings.BASE_URL, timeout: float = settings.REQUEST_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()

    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.timeout)
        with allure.step(f"{method} {path}"):
            self._attach_request(method, url, kwargs)
            response = self.session.request(method, url, **kwargs)
            self._attach_response(response)
        return response

    @staticmethod
    def _attach_request(method: str, url: str, kwargs: dict) -> None:
        details = {"method": method, "url": url}
        if kwargs.get("params"):
            details["params"] = kwargs["params"]
        if "json" in kwargs:
            details["json"] = kwargs["json"]
        allure.attach(
            json.dumps(details, ensure_ascii=False, indent=2, default=str),
            name="Request",
            attachment_type=allure.attachment_type.JSON,
        )

    @staticmethod
    def _attach_response(response: requests.Response) -> None:
        try:
            body = json.dumps(response.json(), ensure_ascii=False, indent=2)
        except ValueError:
            body = response.text or "<empty body>"
        allure.attach(
            f"HTTP {response.status_code}\n\n{body}",
            name="Response",
            attachment_type=allure.attachment_type.TEXT,
        )
