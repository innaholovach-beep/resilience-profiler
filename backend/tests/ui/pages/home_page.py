from selenium.webdriver.common.by import By
from .base_page import BasePage

class HomePage(BasePage):
    """Page Object для головної сторінки"""

    PAGE_HOME    = (By.ID, "page-home")
    PAGE_REGISTER = (By.ID, "page-register")
    PAGE_LOGIN   = (By.ID, "page-login")
    PAGE_SURVEY  = (By.ID, "page-survey")
    PAGE_RESULTS = (By.ID, "page-results")

    def open_home(self):
        self.open("/")
        self.screenshot("01_home_page_opened")
        return self

    def is_home_page_loaded(self):
        result = self.is_element_present(*self.PAGE_HOME)
        self.screenshot("02_home_page_loaded_check")
        return result

    def has_registration_section(self):
        result = self.is_element_present(*self.PAGE_REGISTER)
        self.screenshot("03_register_section_check")
        return result

    def has_login_section(self):
        result = self.is_element_present(*self.PAGE_LOGIN)
        self.screenshot("04_login_section_check")
        return result

    def has_survey_section(self):
        result = self.is_element_present(*self.PAGE_SURVEY)
        self.screenshot("05_survey_section_check")
        return result

    def has_results_section(self):
        result = self.is_element_present(*self.PAGE_RESULTS)
        self.screenshot("06_results_section_check")
        return result

    def get_page_title(self):
        title = self.get_title()
        self.screenshot("07_page_title_check")
        return title
