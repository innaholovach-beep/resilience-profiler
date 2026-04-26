from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict
from app.core.database import get_db
from app.models.models import SurveyResponse
from app.services.ml_service import predict_profile
from app.api.deps import get_current_user_id

router = APIRouter()

# 25 питань — 5 субшкал по 5 питань кожна
QUESTIONS = [
    # Субшкала 1: Емоційна регуляція (питання 1-5)
    {"id": 1,  "scale": "emotional_regulation", "text": "Я можу заспокоїти себе, коли відчуваю сильне хвилювання"},
    {"id": 2,  "scale": "emotional_regulation", "text": "Після стресової події я швидко повертаюсь до звичного стану"},
    {"id": 3,  "scale": "emotional_regulation", "text": "Я розумію свої емоції і причини їх виникнення"},
    {"id": 4,  "scale": "emotional_regulation", "text": "Негативні емоції не заважають мені виконувати щоденні справи"},
    {"id": 5,  "scale": "emotional_regulation", "text": "Я можу контролювати свою реакцію на стресові ситуації"},
    # Субшкала 2: Когнітивна гнучкість (питання 6-10)
    {"id": 6,  "scale": "cognitive_flexibility", "text": "Коли одне рішення не спрацьовує, я легко знаходжу інше"},
    {"id": 7,  "scale": "cognitive_flexibility", "text": "Я можу подивитись на проблему з різних точок зору"},
    {"id": 8,  "scale": "cognitive_flexibility", "text": "Зміни у планах не викликають у мене сильного дискомфорту"},
    {"id": 9,  "scale": "cognitive_flexibility", "text": "У складних ситуаціях я шукаю нові підходи"},
    {"id": 10, "scale": "cognitive_flexibility", "text": "Я можу переосмислити невдачу як можливість для зростання"},
    # Субшкала 3: Соціальна підтримка (питання 11-15)
    {"id": 11, "scale": "social_support", "text": "У мене є люди, до яких я можу звернутись у важку хвилину"},
    {"id": 12, "scale": "social_support", "text": "Я не соромлюсь просити допомоги, коли вона мені потрібна"},
    {"id": 13, "scale": "social_support", "text": "Мої близькі розуміють і підтримують мене"},
    {"id": 14, "scale": "social_support", "text": "Я відчуваю себе частиною спільноти"},
    {"id": 15, "scale": "social_support", "text": "Спілкування з іншими допомагає мені справлятись зі стресом"},
    # Субшкала 4: Самоефективність (питання 16-20)
    {"id": 16, "scale": "self_efficacy", "text": "Я вірю, що здатний(а) впоратись із більшістю проблем"},
    {"id": 17, "scale": "self_efficacy", "text": "Навіть у складних ситуаціях я не здаюсь"},
    {"id": 18, "scale": "self_efficacy", "text": "Мені вдавалось долати серйозні труднощі в минулому"},
    {"id": 19, "scale": "self_efficacy", "text": "Я довіряю своїм здібностям вирішувати проблеми"},
    {"id": 20, "scale": "self_efficacy", "text": "Невдача не змушує мене відмовитись від своїх цілей"},
    # Субшкала 5: Осмислення досвіду (питання 21-25)
    {"id": 21, "scale": "meaning_making", "text": "Я знаходжу сенс навіть у складних подіях свого життя"},
    {"id": 22, "scale": "meaning_making", "text": "Мої труднощі зробили мене сильнішим(ою)"},
    {"id": 23, "scale": "meaning_making", "text": "У мене є чіткі цінності, які допомагають рухатись вперед"},
    {"id": 24, "scale": "meaning_making", "text": "Я можу знайти позитивне навіть у поганих ситуаціях"},
    {"id": 25, "scale": "meaning_making", "text": "Мій досвід (у т.ч. негативний) має для мене значення"},
]


class SurveySubmit(BaseModel):
    answers: Dict[int, int] = Field(
        description="Ключ — ID питання (1-25), значення — оцінка (1-5)",
        example={1: 4, 2: 3}
    )

    def validate_answers(self):
        expected = {q["id"] for q in QUESTIONS}
        given = set(self.answers.keys())
        if given != expected:
            missing = expected - given
            raise ValueError(f"Відсутні відповіді на питання: {sorted(missing)}")
        for qid, score in self.answers.items():
            if score not in range(1, 6):
                raise ValueError(f"Питання {qid}: оцінка має бути від 1 до 5")


@router.get("/questions")
def get_questions():
    return {"questions": QUESTIONS, "total": len(QUESTIONS)}


@router.post("/submit", status_code=201)
def submit_survey(
    data: SurveySubmit,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    try:
        data.validate_answers()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    survey = SurveyResponse(user_id=user_id, answers=data.answers)
    db.add(survey)
    db.commit()
    db.refresh(survey)

    profile = predict_profile(survey_id=survey.id, answers=data.answers, db=db, user_id=user_id)
    return {
        "survey_id": survey.id,
        "profile_id": profile.id,
        "message": "Анкету успішно збережено та оброблено",
    }
