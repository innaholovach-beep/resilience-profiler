*** Settings ***
Library           SeleniumLibrary
Suite Setup       Open Browser    http://127.0.0.1:8000    chrome
Suite Teardown    Close Browser

*** Variables ***
${BASE_URL}       http://127.0.0.1:8000

*** Test Cases ***
TC-01 Home Page Is Accessible
    [Documentation]    Перевірити що головна сторінка відкривається
    Go To    ${BASE_URL}
    Page Should Contain Element    id=page-home
    Title Should Be    Resilience Profiler

TC-02 Registration Page Elements Present
    [Documentation]    Перевірити наявність елементів сторінки реєстрації
    Go To    ${BASE_URL}
    Page Should Contain Element    id=page-register

TC-03 Login Page Elements Present
    [Documentation]    Перевірити наявність елементів сторінки входу
    Go To    ${BASE_URL}
    Page Should Contain Element    id=page-login

TC-04 Survey Page Elements Present
    [Documentation]    Перевірити наявність елементів сторінки анкети
    Go To    ${BASE_URL}
    Page Should Contain Element    id=page-survey

TC-05 Results Page Elements Present
    [Documentation]    Перевірити наявність елементів сторінки результатів
    Go To    ${BASE_URL}
    Page Should Contain Element    id=page-results
