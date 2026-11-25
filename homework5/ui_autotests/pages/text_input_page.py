from selenium.webdriver.common.by import By
from core.base_page import BasePage


class TextInputPage(BasePage):
    PATH = "/textinput"
    INPUT = (By.ID, "newButtonName")
    BUTTON = (By.ID, "updatingButton")

    def set_button_name(self, name: str):
        self.type_text(self.INPUT, name)
        return self  # Fluent Interface

    def click_button(self):
        self.click(self.BUTTON)
        return self

    def get_button_text(self) -> str:
        return self.get_text(self.BUTTON)
