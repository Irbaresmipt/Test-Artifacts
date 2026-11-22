"""Клиент для /orders (основной REST API)."""
from typing import Any, Optional

import requests

from api.base_client import BaseClient


class OrdersClient(BaseClient):
    def create(self, payload: Any) -> requests.Response:
        return self.request("POST", "/orders", json=payload)

    def get(self, order_id: str) -> requests.Response:
        return self.request("GET", f"/orders/{order_id}")

    def list(self) -> requests.Response:
        return self.request("GET", "/orders")

    def change_status(self, order_id: str, status: Any) -> requests.Response:
        return self.request("PATCH", f"/orders/{order_id}/status", json={"status": status})

    def cancel(self, order_id: str, reason: Optional[str]) -> requests.Response:
        params = None if reason is None else {"reason": reason}
        return self.request("DELETE", f"/orders/{order_id}", params=params)

    def remove(self, order_id: str, reason: Optional[str]) -> requests.Response:
        params = None if reason is None else {"reason": reason}
        return self.request("DELETE", f"/orders/{order_id}/remove", params=params)

    def api_docs(self) -> requests.Response:
        return self.request("GET", "/v3/api-docs")

    def swagger_ui(self) -> requests.Response:
        return self.request("GET", "/swagger-ui/index.html")
