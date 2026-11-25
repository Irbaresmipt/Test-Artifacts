import pytest

from config.settings import settings
from core.driver_factory import DriverFactory
from pages.class_attribute_page import ClassAttributePage
from pages.dynamic_id_page import DynamicIdPage
from pages.text_input_page import TextInputPage


@pytest.fixture
def driver():
    drv = DriverFactory.create(settings.browser, settings.headless)
    yield drv
    drv.quit()


@pytest.fixture
def dynamic_id_page(driver):
    return DynamicIdPage(driver)


@pytest.fixture
def class_attr_page(driver):
    return ClassAttributePage(driver)


@pytest.fixture
def text_input_page(driver):
    return TextInputPage(driver)
