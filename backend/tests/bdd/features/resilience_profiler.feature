Feature: Resilience Profiler Web Application
  As a user of Resilience Profiler
  I want to access the application pages
  So that I can take the resilience survey and view my profile

  Background:
    Given the browser is open at "http://127.0.0.1:8000"

  Scenario: Home page is accessible
    When I open the home page
    Then the page title should be "Resilience Profiler"
    And the element with id "page-home" should be present

  Scenario: Registration section is present on home page
    When I open the home page
    Then the element with id "page-register" should be present

  Scenario: Login section is present on home page
    When I open the home page
    Then the element with id "page-login" should be present

  Scenario: Survey section is present on home page
    When I open the home page
    Then the element with id "page-survey" should be present

  Scenario: Results section is present on home page
    When I open the home page
    Then the element with id "page-results" should be present
