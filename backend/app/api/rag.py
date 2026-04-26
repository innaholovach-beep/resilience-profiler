"""
ЛАБА — RAG ендпоінт.

POST /api/rag/ask
  Приймає запит користувача + profile_id,
  виконує retrieval + generation,
  повертає персоналізовану відповідь.

GET /api/rag/status
  Перевіряє стан бази знань (кількість документів).

POST /api/rag/index
  (адмін) Переіндексує базу знань.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import ResilienceProfile
from app.api.deps import get_current_user_id
from app.services import rag_service

router = APIRouter()


# ── Схеми ─────────────────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str = Field(
        min_length=5,
        max_length=500,
        description="Запит користувача",
        example="Як мені покращити емоційну регуляцію?",
    )
    profile_id: int = Field(description="ID профілю резильєнтності")


class AskResponse(BaseModel):
    answer:      str
    sources:     list[dict]
    chunks_used: int


# ── Ендпоінти ─────────────────────────────────────────────────────────────────

@router.post("/ask", response_model=AskResponse)
def ask(
    data: AskRequest,
    db:      Session = Depends(get_db),
    user_id: int     = Depends(get_current_user_id),
):
    # Завантажуємо профіль і перевіряємо права доступу
    profile_orm = db.query(ResilienceProfile).filter(
        ResilienceProfile.id      == data.profile_id,
        ResilienceProfile.user_id == user_id,
    ).first()

    if not profile_orm:
        raise HTTPException(status_code=404, detail="Профіль не знайдено")

    # Формуємо словник профілю для RAG
    profile = {
        "overall_score": profile_orm.overall_score,
        "profile_type":  profile_orm.profile_type,
        "dimensions": {
            "emotional_regulation": profile_orm.emotional_regulation,
            "cognitive_flexibility": profile_orm.cognitive_flexibility,
            "social_support":        profile_orm.social_support,
            "self_efficacy":         profile_orm.self_efficacy,
            "meaning_making":        profile_orm.meaning_making,
        },
    }

    result = rag_service.ask(query=data.question, profile=profile)
    return AskResponse(**result)


@router.get("/status")
def status():
    try:
        _, collection = rag_service._get_client_and_collection()
        count = collection.count()
        return {
            "indexed_chunks": count,
            "status": "ready" if count > 0 else "empty",
            "knowledge_base_dir": str(rag_service.KNOWLEDGE_BASE_DIR),
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.post("/index", status_code=200)
def reindex():
    count = rag_service.index_knowledge_base(force=True)
    return {"indexed_chunks": count, "status": "done"}
