"""Клиент для /seminar/workflow/orders (Event Storming demo API)."""
from typing import Any

import requests

from api.base_client import BaseClient

_BASE = "/seminar/workflow/orders"


class WorkflowClient(BaseClient):
    def create(self, payload: Any) -> requests.Response:
        return self.request("POST", _BASE, json=payload)

    def payment_received(self, order_id: str) -> requests.Response:
        return self.request("POST", f"{_BASE}/{order_id}/payment-received")

    def start_cooking(self, order_id: str) -> requests.Response:
        return self.request("POST", f"{_BASE}/{order_id}/start-cooking")

    def assign_courier(self, order_id: str) -> requests.Response:
        return self.request("POST", f"{_BASE}/{order_id}/assign-courier")

    def deliver(self, order_id: str) -> requests.Response:
        return self.request("POST", f"{_BASE}/{order_id}/deliver")

    def board(self, order_id: str) -> requests.Response:
        return self.request("GET", f"{_BASE}/{order_id}/board")
