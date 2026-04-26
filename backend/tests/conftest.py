import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth_headers(client):
    """Авторизований клієнт з JWT токеном"""
    # Реєстрація тестового користувача
    client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123",
        "full_name": "Test User"
    })
    # Логін
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "TestPass123"
    })
    token = response.json().get("access_token", "")
    return {"Authorization": f"Bearer {token}"}


import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
