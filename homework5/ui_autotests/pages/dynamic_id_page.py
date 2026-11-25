from selenium.webdriver.common.by import By
from core.base_page import BasePage


class DynamicIdPage(BasePage):
    PATH = "/dynamicid"
    # id у кнопки меняется при каждой загрузке, поэтому ищем по тексту
    BUTTON = (By.XPATH, "//button[text()='Button with Dynamic ID']")

    def click_button(self):
        self.click(self.BUTTON)
        return self

    def get_button_id(self) -> str:
        return self.find(self.BUTTON).get_attribute("id")
