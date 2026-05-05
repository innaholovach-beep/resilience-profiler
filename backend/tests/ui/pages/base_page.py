import os
from selenium.webdriver.support.ui import WebDriverWait

SCREENSHOTS_DIR = "screenshots"

class BasePage:
    """Базовий Page Object клас для всіх сторінок"""
    BASE_URL = "http://127.0.0.1:8000"

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    def open(self, path="/"):
        self.driver.get(self.BASE_URL + path)
        return self

    def screenshot(self, name):
        path = f"{SCREENSHOTS_DIR}/{name}.png"
        self.driver.save_screenshot(path)
        print(f"Screenshot: {path}")
        return path

    def get_title(self):
        return self.driver.title

    def is_element_present(self, by, value):
        return len(self.driver.find_elements(by, value)) > 0
