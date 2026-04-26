"""
Компонентні тести RAG API ендпоінту.
Мокають rag_service.ask — не потребують ChromaDB чи LLM.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_db
from app.models.models import Base

TEST_DB_URL = "sqlite:///./test_rag.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

MOCK_RAG_RESULT = {
    "answer":      "Ось персоналізована відповідь про резильєнтність.",
    "sources":     [{"source": "basics.txt", "distance": 0.12}],
    "chunks_used": 1,
}


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def auth_headers():
    resp = client.post("/api/auth/register", json={
        "email": "ragtest@example.com",
        "password": "Pass123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def profile_id(auth_headers):
    answers = {"answers": {str(i): 4 for i in range(1, 26)}}
    resp = client.post("/api/survey/submit", json=answers, headers=auth_headers)
    return resp.json()["profile_id"]


class TestRagEndpoint:
    @patch("app.api.rag.rag_service.ask", return_value=MOCK_RAG_RESULT)
    def test_ask_success(self, mock_ask, auth_headers, profile_id):
        resp = client.post("/api/rag/ask", json={
            "question":   "Як покращити емоційну регуляцію?",
            "profile_id": profile_id,
        }, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert "answer"      in data
        assert "sources"     in data
        assert "chunks_used" in data
        assert data["answer"] == MOCK_RAG_RESULT["answer"]

    def test_ask_requires_auth(self, profile_id):
        resp = client.post("/api/rag/ask", json={
            "question": "Запит?", "profile_id": profile_id,
        })
        assert resp.status_code == 403

    def test_ask_wrong_profile_id(self, auth_headers):
        resp = client.post("/api/rag/ask", json={
            "question": "Запит?", "profile_id": 99999,
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_ask_too_short_question(self, auth_headers, profile_id):
        resp = client.post("/api/rag/ask", json={
            "question": "Hi", "profile_id": profile_id,
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_rag_status_endpoint(self):
        resp = client.get("/api/rag/status")
        assert resp.status_code == 200
        assert "indexed_chunks" in resp.json()
        assert "status"         in resp.json()

    @patch("app.api.rag.rag_service.ask", return_value=MOCK_RAG_RESULT)
    def test_ask_calls_rag_service_with_correct_profile(self, mock_ask, auth_headers, profile_id):
        client.post("/api/rag/ask", json={
            "question":   "Запит про самоефективність?",
            "profile_id": profile_id,
        }, headers=auth_headers)

        call_kwargs = mock_ask.call_args
        profile_arg = call_kwargs[1].get("profile") or call_kwargs[0][1]
        assert "overall_score" in profile_arg
        assert "dimensions"    in profile_arg
        assert len(profile_arg["dimensions"]) == 5
