from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    surveys = relationship("SurveyResponse", back_populates="user")
    profiles = relationship("ResilienceProfile", back_populates="user")


class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    answers = Column(JSON, nullable=False)   # {question_id: score (1-5)}
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="surveys")
    profile = relationship("ResilienceProfile", back_populates="survey", uselist=False)


class ResilienceProfile(Base):
    __tablename__ = "resilience_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    survey_id = Column(Integer, ForeignKey("survey_responses.id"), nullable=False)

    # П'ять вимірів психологічної резильєнтності
    emotional_regulation = Column(Float, nullable=False)   # Емоційна регуляція
    cognitive_flexibility = Column(Float, nullable=False)  # Когнітивна гнучкість
    social_support        = Column(Float, nullable=False)  # Соціальна підтримка
    self_efficacy         = Column(Float, nullable=False)  # Самоефективність
    meaning_making        = Column(Float, nullable=False)  # Осмислення досвіду

    overall_score = Column(Float, nullable=False)
    profile_type  = Column(String, nullable=False)  # e.g. "High", "Moderate", "Low"
    recommendations = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user   = relationship("User", back_populates="profiles")
    survey = relationship("SurveyResponse", back_populates="profile")
