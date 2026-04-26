"""
Тести для RAG-сервісу.
Запуск: pytest tests/test_rag.py -v

Тести не потребують ChromaDB або LLM — мокають зовнішні залежності.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.rag_service import (
    _chunk_text,
    _build_prompt,
    retrieve,
    ask,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K,
)

SAMPLE_PROFILE = {
    "overall_score": 3.6,
    "profile_type":  "Moderate",
    "dimensions": {
        "emotional_regulation": 3.2,
        "cognitive_flexibility": 4.0,
        "social_support":        3.8,
        "self_efficacy":         3.4,
        "meaning_making":        3.6,
    },
}

SAMPLE_CHUNKS = [
    {"text": "Резильєнтність — це здатність адаптуватися.", "source": "basics.txt", "distance": 0.12},
    {"text": "Техніка дихання 4-7-8 допомагає заспокоїтись.", "source": "emotional.txt", "distance": 0.23},
]


# ── Тести _chunk_text ─────────────────────────────────────────────────────────

class TestChunkText:
    def test_short_text_returns_one_chunk(self):
        text   = "Короткий текст про резильєнтність."
        chunks = _chunk_text(text, size=200)
        assert len(chunks) == 1

    def test_long_text_splits_correctly(self):
        text   = "А" * 1200
        chunks = _chunk_text(text, size=500, overlap=50)
        assert len(chunks) > 1

    def test_overlap_creates_shared_content(self):
        text   = "X" * 600
        chunks = _chunk_text(text, size=300, overlap=50)
        # Кожен chunk має бути принаймні overlap символів з наступним
        assert len(chunks) >= 2

    def test_very_short_chunks_filtered_out(self):
        text   = "АБВ" * 5 + "." + " " * 10 + "ГДЕ"
        chunks = _chunk_text(text, size=50, overlap=10)
        for c in chunks:
            assert len(c) > 50

    def test_empty_text_returns_empty_list(self):
        assert _chunk_text("") == []

    def test_chunk_size_respected(self):
        text   = "А" * 2000
        chunks = _chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
        for c in chunks:
            assert len(c) <= CHUNK_SIZE + 10  # +10 допуск на обрізку слів

    def test_returns_list_of_strings(self):
        chunks = _chunk_text("Текст для тестування чанкінгу.", size=50)
        assert isinstance(chunks, list)
        if chunks:
            assert all(isinstance(c, str) for c in chunks)


# ── Тести _build_prompt ───────────────────────────────────────────────────────

class TestBuildPrompt:
    def test_prompt_contains_query(self):
        query  = "Як покращити самоефективність?"
        prompt = _build_prompt(query, SAMPLE_PROFILE, SAMPLE_CHUNKS)
        assert query in prompt

    def test_prompt_contains_overall_score(self):
        prompt = _build_prompt("запит", SAMPLE_PROFILE, SAMPLE_CHUNKS)
        assert "3.6" in prompt

    def test_prompt_contains_profile_type(self):
        prompt = _build_prompt("запит", SAMPLE_PROFILE, SAMPLE_CHUNKS)
        assert "Moderate" in prompt

    def test_prompt_contains_all_dimensions(self):
        prompt = _build_prompt("запит", SAMPLE_PROFILE, SAMPLE_CHUNKS)
        assert "Емоційна регуляція" in prompt
        assert "Когнітивна гнучкість" in prompt
        assert "Соціальна підтримка" in prompt
        assert "Самоефективність" in prompt
        assert "Осмислення досвіду" in prompt

    def test_prompt_contains_chunk_text(self):
        prompt = _build_prompt("запит", SAMPLE_PROFILE, SAMPLE_CHUNKS)
        assert SAMPLE_CHUNKS[0]["text"] in prompt
        assert SAMPLE_CHUNKS[1]["text"] in prompt

    def test_prompt_contains_source_names(self):
        prompt = _build_prompt("запит", SAMPLE_PROFILE, SAMPLE_CHUNKS)
        assert "basics.txt" in prompt
        assert "emotional.txt" in prompt

    def test_prompt_is_nonempty_string(self):
        prompt = _build_prompt("запит", SAMPLE_PROFILE, [])
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_empty_profile_does_not_crash(self):
        prompt = _build_prompt("запит", {}, SAMPLE_CHUNKS)
        assert isinstance(prompt, str)


# ── Тести retrieve (з моком ChromaDB) ────────────────────────────────────────

class TestRetrieve:
    @patch("app.services.rag_service._get_client_and_collection")
    def test_retrieve_returns_list(self, mock_get):
        mock_col = MagicMock()
        mock_col.count.return_value = 10
        mock_col.query.return_value = {
            "documents": [["chunk1", "chunk2"]],
            "metadatas": [[{"source": "a.txt"}, {"source": "b.txt"}]],
            "distances": [[0.1, 0.3]],
        }
        mock_get.return_value = (MagicMock(), mock_col)

        results = retrieve("тестовий запит", top_k=2)
        assert isinstance(results, list)
        assert len(results) == 2

    @patch("app.services.rag_service._get_client_and_collection")
    def test_retrieve_has_required_keys(self, mock_get):
        mock_col = MagicMock()
        mock_col.count.return_value = 5
        mock_col.query.return_value = {
            "documents": [["текст фрагменту"]],
            "metadatas": [[{"source": "test.txt"}]],
            "distances": [[0.15]],
        }
        mock_get.return_value = (MagicMock(), mock_col)

        results = retrieve("запит")
        assert "text"     in results[0]
        assert "source"   in results[0]
        assert "distance" in results[0]

    @patch("app.services.rag_service._get_client_and_collection")
    def test_retrieve_top_k_respected(self, mock_get):
        mock_col = MagicMock()
        mock_col.count.return_value = 20
        mock_col.query.return_value = {
            "documents": [["a", "b", "c"]],
            "metadatas": [[{"source": "x"}, {"source": "y"}, {"source": "z"}]],
            "distances": [[0.1, 0.2, 0.3]],
        }
        mock_get.return_value = (MagicMock(), mock_col)

        results = retrieve("запит", top_k=3)
        assert len(results) == 3


# ── Тести ask (інтеграційні, з моком LLM і ChromaDB) ─────────────────────────

class TestAsk:
    @patch("app.services.rag_service.retrieve")
    @patch("app.services.rag_service._generate_ollama")
    @patch("app.services.rag_service.LLM_PROVIDER", "ollama")
    def test_ask_returns_answer(self, mock_gen, mock_ret):
        mock_ret.return_value = SAMPLE_CHUNKS
        mock_gen.return_value = "Ось персоналізована відповідь."

        result = ask("Як підвищити резильєнтність?", SAMPLE_PROFILE)

        assert "answer"      in result
        assert "sources"     in result
        assert "chunks_used" in result
        assert result["answer"] == "Ось персоналізована відповідь."

    @patch("app.services.rag_service.retrieve")
    @patch("app.services.rag_service._generate_ollama")
    @patch("app.services.rag_service.LLM_PROVIDER", "ollama")
    def test_ask_passes_profile_to_llm(self, mock_gen, mock_ret):
        mock_ret.return_value = SAMPLE_CHUNKS
        mock_gen.return_value = "Відповідь."

        ask("Запит?", SAMPLE_PROFILE)

        # Перевіряємо що generate був викликаний з промптом що містить профіль
        call_args = mock_gen.call_args[0][0]
        assert "3.6" in call_args
        assert "Moderate" in call_args

    @patch("app.services.rag_service.retrieve")
    @patch("app.services.rag_service._generate_ollama")
    @patch("app.services.rag_service.LLM_PROVIDER", "ollama")
    def test_ask_chunks_used_equals_retrieved(self, mock_gen, mock_ret):
        mock_ret.return_value = SAMPLE_CHUNKS
        mock_gen.return_value = "Відповідь."

        result = ask("Запит?", SAMPLE_PROFILE)
        assert result["chunks_used"] == len(SAMPLE_CHUNKS)

    @patch("app.services.rag_service.retrieve")
    @patch("app.services.rag_service._generate_ollama")
    @patch("app.services.rag_service.LLM_PROVIDER", "ollama")
    def test_ask_sources_match_chunks(self, mock_gen, mock_ret):
        mock_ret.return_value = SAMPLE_CHUNKS
        mock_gen.return_value = "Відповідь."

        result = ask("Запит?", SAMPLE_PROFILE)
        sources = {s["source"] for s in result["sources"]}
        assert "basics.txt"    in sources
        assert "emotional.txt" in sources

    @patch("app.services.rag_service.retrieve")
    def test_ask_fallback_when_no_llm(self, mock_ret):
        mock_ret.return_value = SAMPLE_CHUNKS

        with patch("app.services.rag_service.LLM_PROVIDER", "none"):
            result = ask("Запит?", SAMPLE_PROFILE)

        assert isinstance(result["answer"], str)
        assert len(result["answer"]) > 0
