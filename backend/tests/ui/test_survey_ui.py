"""
ЛАБА 8 — Selenium WebDriver з паттерном Page Object.

Запуск:
  pip install selenium pytest
  pytest tests/ui/test_survey_ui.py -v

Потрібно мати ChromeDriver у PATH або встановити:
  pip install webdriver-manager
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


BASE_URL = "http://localhost:8000"


# ── Page Objects ──────────────────────────────────────────────────────────────

class BasePage:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.wait   = WebDriverWait(driver, 10)

    def find(self, by, selector):
        return self.wait.until(EC.presence_of_element_located((by, selector)))

    def click(self, by, selector):
        self.wait.until(EC.element_to_be_clickable((by, selector))).click()

    def type(self, by, selector, text):
        el = self.find(by, selector)
        el.clear()
        el.send_keys(text)


class HomePage(BasePage):
    URL = BASE_URL

    def open(self):
        self.driver.get(self.URL)
        return self

    def go_to_register(self):
        self.click(By.ID, "btn-nav-register")
        return RegisterPage(self.driver)

    def go_to_login(self):
        self.click(By.ID, "btn-nav-login")
        return LoginPage(self.driver)

    def is_visible(self):
        return self.find(By.CSS_SELECTOR, "#page-home.active") is not None


class RegisterPage(BasePage):
    def fill_and_submit(self, name: str, email: str, password: str):
        self.type(By.ID, "reg-name",  name)
        self.type(By.ID, "reg-email", email)
        self.type(By.ID, "reg-pass",  password)
        self.click(By.CSS_SELECTOR, "#page-register .btn-primary")
        return SurveyPage(self.driver)

    def get_error(self) -> str:
        el = self.find(By.ID, "reg-error")
        return el.text if el.is_displayed() else ""


class LoginPage(BasePage):
    def fill_and_submit(self, email: str, password: str):
        self.type(By.ID, "login-email", email)
        self.type(By.ID, "login-pass",  password)
        self.click(By.CSS_SELECTOR, "#page-login .btn-primary")
        return SurveyPage(self.driver)

    def get_error(self) -> str:
        el = self.find(By.ID, "login-error")
        return el.text if el.is_displayed() else ""


class SurveyPage(BasePage):
    def wait_for_questions(self):
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".question")
        ))
        return self

    def answer_all(self, score: int = 4):
        """Відповісти на всі питання заданим балом."""
        for q_num in range(1, 26):
            radio = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, f'input[name="q{q_num}"][value="{score}"]')
            ))
            self.driver.execute_script("arguments[0].click();", radio)
        return self

    def submit(self):
        self.click(By.CSS_SELECTOR, "#page-survey .btn-primary")
        return ResultsPage(self.driver)

    def get_progress_pct(self) -> str:
        bar = self.find(By.ID, "progress")
        return bar.get_attribute("style")


class ResultsPage(BasePage):
    def wait_for_results(self):
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#page-results.active")
        ))
        return self

    def get_overall_score(self) -> str:
        return self.find(By.ID, "res-score").text

    def get_profile_type(self) -> str:
        return self.find(By.ID, "res-type").text

    def get_recommendations_count(self) -> int:
        recs = self.driver.find_elements(By.CSS_SELECTOR, ".rec-item")
        return len(recs)

    def get_dimensions_count(self) -> int:
        dims = self.driver.find_elements(By.CSS_SELECTOR, ".dim-card")
        return len(dims)


# ── Test fixtures ─────────────────────────────────────────────────────────────

import pytest

@pytest.fixture(scope="session")
def driver():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    drv = webdriver.Chrome(options=opts)
    drv.set_window_size(1280, 900)
    yield drv
    drv.quit()


@pytest.fixture
def home(driver):
    return HomePage(driver).open()


# ── UI Tests ──────────────────────────────────────────────────────────────────

class TestRegistration:
    def test_register_page_opens(self, home):
        reg_page = home.go_to_register()
        assert reg_page is not None

    def test_successful_registration_leads_to_survey(self, home):
        reg = home.go_to_register()
        survey = reg.fill_and_submit(
            "Test User", "uitest@example.com", "Pass123"
        )
        survey.wait_for_questions()
        assert len(survey.driver.find_elements(By.CSS_SELECTOR, ".question")) == 25


class TestLogin:
    def test_wrong_password_shows_error(self, home):
        login = home.go_to_login()
        login.fill_and_submit("nobody@example.com", "wrongpass")
        error = login.get_error()
        assert error != ""


class TestSurveyFlow:
    def test_all_questions_rendered(self, home):
        reg   = home.go_to_register()
        survey = reg.fill_and_submit("Survey User", "survey@example.com", "Pass123")
        survey.wait_for_questions()
        questions = survey.driver.find_elements(By.CSS_SELECTOR, ".question")
        assert len(questions) == 25

    def test_progress_updates_on_answer(self, home):
        reg    = home.go_to_register()
        survey = reg.fill_and_submit("Prog User", "prog@example.com", "Pass123")
        survey.wait_for_questions()
        before = survey.get_progress_pct()
        survey.driver.execute_script(
            'document.querySelector(\'input[name="q1"][value="3"]\').click()'
        )
        after = survey.get_progress_pct()
        assert before != after

    def test_complete_survey_shows_results(self, home):
        reg     = home.go_to_register()
        survey  = reg.fill_and_submit("Full User", "full@example.com", "Pass123")
        survey.wait_for_questions().answer_all(score=4)
        results = survey.submit()
        results.wait_for_results()
        assert results.get_overall_score() != "—"
        assert results.get_dimensions_count() == 5
        assert results.get_recommendations_count() == 5
