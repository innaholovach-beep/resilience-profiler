from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import ResilienceProfile
from app.api.deps import get_current_user_id

router = APIRouter()


@router.get("/{profile_id}")
def get_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    profile = db.query(ResilienceProfile).filter(
        ResilienceProfile.id == profile_id,
        ResilienceProfile.user_id == user_id,
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Профіль не знайдено")

    return {
        "id": profile.id,
        "overall_score": profile.overall_score,
        "profile_type": profile.profile_type,
        "dimensions": {
            "emotional_regulation": profile.emotional_regulation,
            "cognitive_flexibility": profile.cognitive_flexibility,
            "social_support": profile.social_support,
            "self_efficacy": profile.self_efficacy,
            "meaning_making": profile.meaning_making,
        },
        "recommendations": profile.recommendations,
        "created_at": profile.created_at.isoformat(),
    }


@router.get("/my/all")
def get_my_profiles(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    profiles = db.query(ResilienceProfile).filter(
        ResilienceProfile.user_id == user_id
    ).order_by(ResilienceProfile.created_at.desc()).all()

    return [
        {
            "id": p.id,
            "overall_score": p.overall_score,
            "profile_type": p.profile_type,
            "created_at": p.created_at.isoformat(),
        }
        for p in profiles
    ]
