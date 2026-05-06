from behave import given, when, then
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


@given('the browser is open at "{url}"')
def step_browser_open(context, url):
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    context.driver = webdriver.Chrome(service=service, options=options)
    context.driver.maximize_window()
    context.base_url = url


@when('I open the home page')
def step_open_home(context):
    context.driver.get(context.base_url)
    context.driver.save_screenshot("screenshots/step_home_opened.png")


@then('the page title should be "{title}"')
def step_check_title(context, title):
    actual = context.driver.title
    context.driver.save_screenshot("screenshots/step_title_check.png")
    assert actual == title, f"Expected '{title}', got '{actual}'"


@then('the element with id "{element_id}" should be present')
def step_element_present(context, element_id):
    elements = context.driver.find_elements(By.ID, element_id)
    context.driver.save_screenshot(f"screenshots/step_{element_id}_check.png")
    assert len(elements) > 0, f"Element with id='{element_id}' not found"
