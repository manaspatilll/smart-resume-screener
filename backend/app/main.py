from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, reset_db
from app.routers import jobs, resumes, screening

app = FastAPI(
    title="Smart Resume Screener API",
    description="Extracts structured data from resumes/JDs and computes LLM-based match scores.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(resumes.router)
app.include_router(screening.router)


@app.on_event("startup")
def on_startup():
    reset_db()
    init_db()


@app.get("/")
def health_check():
    return {"status": "ok", "service": "smart-resume-screener"}
