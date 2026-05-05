"""
Selenium WebDriver тести для проєкту Resilience Profiler
Патерн: Page Object
"""
import pytest
from pages.home_page import HomePage


class TestHomePage:
    """TC-01: Перевірка головної сторінки"""
    
    def test_home_page_title(self, driver):
        """TC-01: Заголовок сторінки має бути 'Resilience Profiler'"""
        page = HomePage(driver)
        page.open_home()
        title = page.get_page_title()
        assert title == "Resilience Profiler", f"Expected 'Resilience Profiler', got '{title}'"
    
    def test_home_page_element_present(self, driver):
        """TC-01: Елемент id=page-home присутній на сторінці"""
        page = HomePage(driver)
        page.open_home()
        assert page.is_home_page_loaded(), "id=page-home not found on page"


class TestRegistrationPage:
    """TC-02: Перевірка сторінки реєстрації"""
    
    def test_register_section_exists(self, driver):
        """TC-02: Секція реєстрації присутня в DOM"""
        page = HomePage(driver)
        page.open_home()
        assert page.has_registration_section(), "id=page-register not found"


class TestLoginPage:
    """TC-03: Перевірка сторінки авторизації"""
    
    def test_login_section_exists(self, driver):
        """TC-03: Секція логіну присутня в DOM"""
        page = HomePage(driver)
        page.open_home()
        assert page.has_login_section(), "id=page-login not found"


class TestSurveyPage:
    """TC-04: Перевірка сторінки анкети"""
    
    def test_survey_section_exists(self, driver):
        """TC-04: Секція анкети присутня в DOM"""
        page = HomePage(driver)
        page.open_home()
        assert page.has_survey_section(), "id=page-survey not found"


class TestResultsPage:
    """TC-05: Перевірка сторінки результатів"""
    
    def test_results_section_exists(self, driver):
        """TC-05: Секція результатів присутня в DOM"""
        page = HomePage(driver)
        page.open_home()
        assert page.has_results_section(), "id=page-results not found"
