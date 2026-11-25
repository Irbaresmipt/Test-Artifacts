from selenium.webdriver.common.by import By
from core.base_page import BasePage


class ClassAttributePage(BasePage):
    PATH = "/classattr"
    # contains(@class,'btn-primary') нашёл бы и btn-primary-xxx, поэтому проверяем целый класс
    PRIMARY_BUTTON = (
        By.XPATH,
        "//button[contains(concat(' ', normalize-space(@class), ' '), ' btn-primary ')]",
    )

    def click_primary_button(self):
        self.click(self.PRIMARY_BUTTON)
        return self

    def accept_alert_text(self) -> str:
        return self.accept_alert()
