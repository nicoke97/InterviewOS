from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .content_loader import invalidate_curriculum_cache, load_curriculum
from .models import init_db
from .routes import router

app = FastAPI(title="InterviewOS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.on_event("startup")
def startup():
    init_db()
    invalidate_curriculum_cache()
    load_curriculum()


@app.get("/")
def root():
    return {"app": "InterviewOS", "docs": "/docs"}
