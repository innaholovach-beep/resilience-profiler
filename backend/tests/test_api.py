"""
ЛАБА 5 — Компонентні тести API (тести ендпоінтів).

Запуск:  pytest tests/test_api.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db
from app.models.models import Base

# ── Тестова БД (SQLite в пам'яті) ────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

Base.metadata.create_all(bind=engine)
client = TestClient(app)


# ── Фікстури ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def registered_user():
    resp = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "Password123",
        "full_name": "Тест Юзер",
    })
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def auth_headers(registered_user):
    token = registered_user["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def full_answers():
    return {"answers": {str(i): 4 for i in range(1, 26)}}


# ── Тести health ──────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ── Тести аутентифікації ──────────────────────────────────────────────────────

class TestAuth:
    def test_register_success(self):
        resp = client.post("/api/auth/register", json={
            "email": "new@example.com",
            "password": "Pass123",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["email"] == "new@example.com"

    def test_register_duplicate_email(self, registered_user):
        resp = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "AnotherPass",
        })
        assert resp.status_code == 400

    def test_login_success(self, registered_user):
        resp = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "Password123",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, registered_user):
        resp = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpass",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self):
        resp = client.post("/api/auth/login", json={
            "email": "nobody@example.com",
            "password": "anything",
        })
        assert resp.status_code == 401


# ── Тести анкети ──────────────────────────────────────────────────────────────

class TestSurvey:
    def test_get_questions_returns_25(self):
        resp = client.get("/api/survey/questions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 25
        assert len(data["questions"]) == 25

    def test_questions_have_required_fields(self):
        resp = client.get("/api/survey/questions")
        for q in resp.json()["questions"]:
            assert "id" in q
            assert "text" in q
            assert "scale" in q

    def test_submit_requires_auth(self, full_answers):
        resp = client.post("/api/survey/submit", json=full_answers)
        assert resp.status_code == 403

    def test_submit_success(self, auth_headers, full_answers):
        resp = client.post("/api/survey/submit", json=full_answers, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert "survey_id" in data
        assert "profile_id" in data

    def test_submit_missing_answers_fails(self, auth_headers):
        resp = client.post(
            "/api/survey/submit",
            json={"answers": {"1": 3}},  # тільки одна відповідь
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_submit_invalid_score_fails(self, auth_headers):
        bad = {"answers": {str(i): 6 for i in range(1, 26)}}  # 6 не валідне
        resp = client.post("/api/survey/submit", json=bad, headers=auth_headers)
        assert resp.status_code == 422


# ── Тести профілю ─────────────────────────────────────────────────────────────

class TestProfile:
    def test_get_profile_after_survey(self, auth_headers, full_answers):
        submit_resp = client.post(
            "/api/survey/submit", json=full_answers, headers=auth_headers
        )
        profile_id = submit_resp.json()["profile_id"]

        resp = client.get(f"/api/profile/{profile_id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "overall_score" in data
        assert "profile_type" in data
        assert "dimensions" in data
        assert len(data["dimensions"]) == 5
        assert "recommendations" in data

    def test_profile_type_is_high_for_all_5s(self, auth_headers):
        answers = {"answers": {str(i): 5 for i in range(1, 26)}}
        resp = client.post("/api/survey/submit", json=answers, headers=auth_headers)
        profile_id = resp.json()["profile_id"]

        profile = client.get(f"/api/profile/{profile_id}", headers=auth_headers).json()
        assert profile["profile_type"] == "High"
        assert profile["overall_score"] == 5.0

    def test_profile_type_is_low_for_all_1s(self, auth_headers):
        answers = {"answers": {str(i): 1 for i in range(1, 26)}}
        resp = client.post("/api/survey/submit", json=answers, headers=auth_headers)
        profile_id = resp.json()["profile_id"]

        profile = client.get(f"/api/profile/{profile_id}", headers=auth_headers).json()
        assert profile["profile_type"] == "Low"
        assert profile["overall_score"] == 1.0

    def test_get_my_profiles_returns_list(self, auth_headers, full_answers):
        client.post("/api/survey/submit", json=full_answers, headers=auth_headers)
        client.post("/api/survey/submit", json=full_answers, headers=auth_headers)

        resp = client.get("/api/profile/my/all", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_cannot_access_other_users_profile(self, auth_headers, full_answers):
        submit_resp = client.post(
            "/api/survey/submit", json=full_answers, headers=auth_headers
        )
        profile_id = submit_resp.json()["profile_id"]

        other = client.post("/api/auth/register", json={
            "email": "other@example.com", "password": "OtherPass123"
        }).json()
        other_headers = {"Authorization": f"Bearer {other['access_token']}"}

        resp = client.get(f"/api/profile/{profile_id}", headers=other_headers)
        assert resp.status_code == 404
