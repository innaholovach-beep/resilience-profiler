from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from app.api import auth, survey, profile, rag
from app.core.database import init_db

app = FastAPI(
    title="Resilience Profiler",
    description="Система профілювання психологічної резильєнтності",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,    prefix="/api/auth",    tags=["auth"])
app.include_router(survey.router,  prefix="/api/survey",  tags=["survey"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(rag.router,     prefix="/api/rag",     tags=["rag"])


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "service": "Resilience Profiler"}


@app.get("/", response_class=HTMLResponse)
def frontend():
    html_path = Path(__file__).parent.parent.parent / "frontend" / "templates" / "index.html"
    return html_path.read_text(encoding="utf-8")