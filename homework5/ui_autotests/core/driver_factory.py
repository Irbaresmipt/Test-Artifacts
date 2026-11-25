"""Factory Method / Simple Factory: создание WebDriver по имени браузера."""
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver


class DriverFactory:
    @staticmethod
    def _chrome(headless: bool) -> WebDriver:
        opts = webdriver.ChromeOptions()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-features=HttpsUpgrades,HttpsFirstBalancedModeAutoEnable")
        opts.add_experimental_option("prefs", {"https_first_balanced_mode_enabled": False})
        return webdriver.Chrome(options=opts)

    @staticmethod
    def _firefox(headless: bool) -> WebDriver:
        opts = webdriver.FirefoxOptions()
        if headless:
            opts.add_argument("-headless")
        return webdriver.Firefox(options=opts)

    _builders = {"chrome": _chrome.__func__, "firefox": _firefox.__func__}

    @classmethod
    def create(cls, browser: str, headless: bool = True) -> WebDriver:
        try:
            builder = cls._builders[browser.lower()]
        except KeyError:
            raise ValueError(f"Неподдерживаемый браузер: {browser}")
        return builder(headless)
