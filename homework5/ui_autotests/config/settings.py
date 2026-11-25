"""Singleton: единая точка конфигурации (значения можно переопределить через env)."""
import os


class Settings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            inst = super().__new__(cls)
            inst.base_url = os.getenv("BASE_URL", "http://www.uitestingplayground.com")
            inst.browser = os.getenv("BROWSER", "chrome")
            inst.headless = os.getenv("HEADLESS", "true").lower() == "true"
            inst.timeout = int(os.getenv("TIMEOUT", "10"))
            cls._instance = inst
        return cls._instance


settings = Settings()
