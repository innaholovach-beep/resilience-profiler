"""
ML-сервіс профілювання психологічної резильєнтності.

Субшкали (по 5 питань кожна, оцінки 1-5):
  1. emotional_regulation  — питання 1-5
  2. cognitive_flexibility  — питання 6-10
  3. social_support         — питання 11-15
  4. self_efficacy          — питання 16-20
  5. meaning_making         — питання 21-25

Загальний бал = середнє по всіх субшкалах (1.0 – 5.0)

Типи профілів:
  High      >= 4.0  — висока резильєнтність
  Moderate  >= 2.5  — помірна
  Low       < 2.5   — низька (рекомендується підтримка)
"""

from __future__ import annotations
from typing import Dict
from sqlalchemy.orm import Session
from app.models.models import ResilienceProfile

# Mapping: question_id → subscale
SCALE_QUESTIONS: Dict[str, list[int]] = {
    "emotional_regulation": [1, 2, 3, 4, 5],
    "cognitive_flexibility": [6, 7, 8, 9, 10],
    "social_support":        [11, 12, 13, 14, 15],
    "self_efficacy":         [16, 17, 18, 19, 20],
    "meaning_making":        [21, 22, 23, 24, 25],
}

RECOMMENDATIONS: Dict[str, Dict[str, str]] = {
    "emotional_regulation": {
        "Low":      "Практикуйте щоденну медитацію або техніки дихання (4-7-8, box breathing).",
        "Moderate": "Ведіть щоденник емоцій, щоб краще розуміти свої реакції.",
        "High":     "Ваша емоційна регуляція на високому рівні. Продовжуйте розвивати усвідомленість.",
    },
    "cognitive_flexibility": {
        "Low":      "Спробуйте техніку 'рефреймінгу' — знаходьте альтернативні інтерпретації ситуацій.",
        "Moderate": "Практикуйте brainstorming без критики для розвитку гнучкого мислення.",
        "High":     "Відмінна когнітивна гнучкість! Діліться своїм підходом з оточуючими.",
    },
    "social_support": {
        "Low":      "Знайдіть групу за інтересами або зверніться до психолога для зміцнення зв'язків.",
        "Moderate": "Регулярно виділяйте час для спілкування з близькими людьми.",
        "High":     "Ваша соціальна мережа — ваша сила. Підтримуйте і поглиблюйте ці зв'язки.",
    },
    "self_efficacy": {
        "Low":      "Починайте з маленьких досяжних цілей, щоб накопичити досвід успіху.",
        "Moderate": "Ведіть список своїх досягнень — навіть невеликих. Це зміцнює впевненість.",
        "High":     "Висока самоефективність! Ставте амбітніші цілі і надихайте інших.",
    },
    "meaning_making": {
        "Low":      "Спробуйте практику gratitude journal або поговоріть з психологом про цінності.",
        "Moderate": "Запишіть 3 ключові цінності та як вони відображаються у вашому житті.",
        "High":     "Ви добре знаходите сенс у своєму досвіді. Це основа стійкої резильєнтності.",
    },
}


def _scale_score(answers: Dict[int, int], question_ids: list[int]) -> float:
    scores = [answers[qid] for qid in question_ids if qid in answers]
    return round(sum(scores) / len(scores), 2) if scores else 0.0


def _classify(score: float) -> str:
    if score >= 4.0:
        return "High"
    if score >= 2.5:
        return "Moderate"
    return "Low"


def predict_profile(
    survey_id: int,
    answers: Dict[int, int],
    db: Session,
    user_id: int,
) -> ResilienceProfile:
    scores = {
        scale: _scale_score(answers, qids)
        for scale, qids in SCALE_QUESTIONS.items()
    }
    overall = round(sum(scores.values()) / len(scores), 2)
    profile_type = _classify(overall)

    recs = [
        {
            "scale": scale,
            "level": _classify(score),
            "score": score,
            "recommendation": RECOMMENDATIONS[scale][_classify(score)],
        }
        for scale, score in scores.items()
    ]

    profile = ResilienceProfile(
        user_id=user_id,
        survey_id=survey_id,
        emotional_regulation=scores["emotional_regulation"],
        cognitive_flexibility=scores["cognitive_flexibility"],
        social_support=scores["social_support"],
        self_efficacy=scores["self_efficacy"],
        meaning_making=scores["meaning_making"],
        overall_score=overall,
        profile_type=profile_type,
        recommendations=recs,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
