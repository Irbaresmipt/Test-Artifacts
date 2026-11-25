"""Базовый Page Object: общие действия и явные ожидания (инкапсуляция Selenium)."""
import logging
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.settings import settings

log = logging.getLogger(__name__)


class BasePage:
    PATH = ""  # переопределяется в наследниках

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.wait = WebDriverWait(driver, settings.timeout)

    def open(self):
        url = f"{settings.base_url}{self.PATH}"
        log.info("Открываем %s", url)
        self.driver.get(url)
        return self

    def find(self, locator) -> WebElement:
        return self.wait.until(EC.visibility_of_element_located(locator))

    def click(self, locator):
        log.info("Клик по %s", locator)
        self.wait.until(EC.element_to_be_clickable(locator)).click()

    def type_text(self, locator, text: str):
        log.info("Ввод '%s' в %s", text, locator)
        el = self.find(locator)
        el.clear()
        el.send_keys(text)

    def get_text(self, locator) -> str:
        return self.find(locator).text

    def accept_alert(self) -> str:
        alert = self.wait.until(EC.alert_is_present())
        text = alert.text
        alert.accept()
        return text
