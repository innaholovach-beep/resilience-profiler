"""
ЛАБА 4 — Unit-тести для ML-сервісу та бізнес-логіки.

Запуск:  pytest tests/ -v --cov=app --cov-report=term-missing
"""
import pytest
from app.services.ml_service import _scale_score, _classify, SCALE_QUESTIONS


# ── Тести функції _scale_score ────────────────────────────────────────────────

class TestScaleScore:
    def test_all_max_scores(self):
        answers = {qid: 5 for qid in range(1, 26)}
        score = _scale_score(answers, SCALE_QUESTIONS["emotional_regulation"])
        assert score == 5.0

    def test_all_min_scores(self):
        answers = {qid: 1 for qid in range(1, 26)}
        score = _scale_score(answers, SCALE_QUESTIONS["self_efficacy"])
        assert score == 1.0

    def test_mixed_scores(self):
        answers = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}
        score = _scale_score(answers, [1, 2, 3, 4, 5])
        assert score == 3.0

    def test_empty_answers_returns_zero(self):
        score = _scale_score({}, [1, 2, 3])
        assert score == 0.0

    def test_result_is_rounded_to_2_decimals(self):
        answers = {1: 1, 2: 2, 3: 2}
        score = _scale_score(answers, [1, 2, 3])
        assert score == round(score, 2)

    def test_all_subscales_have_5_questions(self):
        for scale, qids in SCALE_QUESTIONS.items():
            assert len(qids) == 5, f"{scale} має {len(qids)} питань, очікується 5"

    def test_all_question_ids_unique(self):
        all_ids = [qid for qids in SCALE_QUESTIONS.values() for qid in qids]
        assert len(all_ids) == len(set(all_ids)), "Є дублікати ID питань"

    def test_question_ids_range_1_to_25(self):
        all_ids = sorted(qid for qids in SCALE_QUESTIONS.values() for qid in qids)
        assert all_ids == list(range(1, 26))


# ── Тести функції _classify ───────────────────────────────────────────────────

class TestClassify:
    def test_high_threshold(self):
        assert _classify(4.0) == "High"
        assert _classify(5.0) == "High"
        assert _classify(4.5) == "High"

    def test_moderate_threshold(self):
        assert _classify(2.5) == "Moderate"
        assert _classify(3.0) == "Moderate"
        assert _classify(3.99) == "Moderate"

    def test_low_threshold(self):
        assert _classify(1.0) == "Low"
        assert _classify(2.49) == "Low"
        assert _classify(2.0) == "Low"

    def test_boundary_4_0_is_high(self):
        assert _classify(4.0) == "High"

    def test_boundary_2_5_is_moderate(self):
        assert _classify(2.5) == "Moderate"

    def test_boundary_just_below_2_5_is_low(self):
        assert _classify(2.49) == "Low"

    def test_returns_string(self):
        result = _classify(3.5)
        assert isinstance(result, str)

    @pytest.mark.parametrize("score,expected", [
        (1.0, "Low"),
        (2.0, "Low"),
        (2.5, "Moderate"),
        (3.5, "Moderate"),
        (4.0, "High"),
        (5.0, "High"),
    ])
    def test_parametrized_classification(self, score, expected):
        assert _classify(score) == expected


# ── Тести інтеграції scale_score + classify ───────────────────────────────────

class TestScoreAndClassifyIntegration:
    def test_high_answers_give_high_profile(self):
        answers = {qid: 5 for qid in range(1, 26)}
        for scale, qids in SCALE_QUESTIONS.items():
            score = _scale_score(answers, qids)
            assert _classify(score) == "High"

    def test_low_answers_give_low_profile(self):
        answers = {qid: 1 for qid in range(1, 26)}
        for scale, qids in SCALE_QUESTIONS.items():
            score = _scale_score(answers, qids)
            assert _classify(score) == "Low"
