# Resilience Profiler

> Система профілювання психологічної резильєнтності  
> Навчальний проєкт з предмету «Автоматизація тестування програмного забезпечення»  
> Також є основою магістерської роботи

---

## Швидкий старт

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Відкрий: http://localhost:8000/docs  (автодокументація Swagger)

### Запуск тестів

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing
```

### Docker

```bash
docker build -t resilience-profiler ./backend
docker run -p 8000:8000 resilience-profiler
```

---

## Архітектура

```
resilience-profiler/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── api/
│   │   │   ├── auth.py          # POST /api/auth/register|login
│   │   │   ├── survey.py        # GET /api/survey/questions, POST /api/survey/submit
│   │   │   ├── profile.py       # GET /api/profile/{id}
│   │   │   └── deps.py          # JWT dependency
│   │   ├── core/
│   │   │   └── database.py      # SQLAlchemy setup
│   │   ├── models/
│   │   │   └── models.py        # User, SurveyResponse, ResilienceProfile
│   │   └── services/
│   │       ├── auth_service.py  # bcrypt + JWT
│   │       └── ml_service.py    # Логіка профілювання (5 вимірів)
│   ├── tests/
│   │   ├── test_ml_service.py   # Unit-тести (Лаба 4)
│   │   └── test_api.py          # Компонентні тести (Лаба 5)
│   ├── requirements.txt
│   └── Dockerfile
└── .github/
    └── workflows/
        └── ci.yml               # GitHub Actions (Лаби 2-3)
```

---

## П'ять вимірів резильєнтності

| Вимір | Питання | Опис |
|-------|---------|------|
| Емоційна регуляція | 1–5 | Здатність керувати емоціями |
| Когнітивна гнучкість | 6–10 | Адаптивність мислення |
| Соціальна підтримка | 11–15 | Якість соціальних зв'язків |
| Самоефективність | 16–20 | Впевненість у власних силах |
| Осмислення досвіду | 21–25 | Здатність знаходити сенс |

Профілі: **High** (≥4.0) · **Moderate** (2.5–3.99) · **Low** (<2.5)

---

## Дорожня карта лаб

| Лаба | Що робимо | Файли/інструменти |
|------|-----------|-------------------|
| **1** | Базовий веб-проєкт за вимогами | `backend/`, `Dockerfile` |
| **2** | Git flow: гілки, PR, захист main | `.github/` |
| **3** | CI/CD: автозапуск тестів | `ci.yml` |
| **4** | Unit-тести ML-логіки | `tests/test_ml_service.py` |
| **5** | Компонентні тести API | `tests/test_api.py` |
| **6** | Selenium record&play анкети | `tests/ui/selenium_record/` |
| **7** | Keyword-driven / Katalone | `tests/ui/keyword/` |
| **8** | Selenium Page Object | `tests/ui/page_objects/` |
| **9** | BDD / Cucumber сценарії | `tests/bdd/features/` |
| **10** | Load testing JMeter | `tests/performance/load/` |
| **11** | Stress testing | `tests/performance/stress/` |
| **12** | SAST аналіз | `tests/security/sast/` |
| **13** | DAST / ZAP | `tests/security/dast/` |
| **14** | API testing Postman | `tests/api/postman_collection.json` |

---

## API ендпоінти

### Auth
- `POST /api/auth/register` — реєстрація
- `POST /api/auth/login` — логін → JWT токен

### Survey
- `GET /api/survey/questions` — 25 питань (5 субшкал)
- `POST /api/survey/submit` — відправити відповіді (потребує JWT)

### Profile
- `GET /api/profile/{id}` — отримати профіль (потребує JWT)
- `GET /api/profile/my/all` — всі профілі поточного юзера

---

## Вимоги (накопичуються з кожною лабою)

### Лаба 1 (Блок 1)
- [x] Реєстрація та авторизація користувача
- [x] Анкета з 25 питаннями по 5 субшкалах
- [x] ML-сервіс: розрахунок профілю резильєнтності
- [x] REST API (FastAPI + Swagger документація)
- [x] База даних (SQLite → легко мігрувати на PostgreSQL)
- [x] Докер-контейнеризація

### Лаба 2-3 (Блок 2) — додати сюди
- [ ] Git branching strategy (feature/hotfix/release)
- [ ] GitHub Actions CI pipeline
- [ ] Автоматична збірка Docker-образу

### Лаба 4-5 (Блок 3) — вже є
- [x] Unit-тести `test_ml_service.py` (покриття ML-логіки)
- [x] Компонентні тести `test_api.py` (всі ендпоінти)
- [x] Coverage ≥ 80%
