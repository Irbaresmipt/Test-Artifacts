"""Конфигурация тестов. Всё переопределяется через переменные окружения."""
import os

BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8080").rstrip("/")
REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT", "10"))
