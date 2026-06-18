from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import ALLOWED_ORIGINS, IS_PRODUCTION, SERVE_STATIC, STATIC_DIR
from .content_loader import invalidate_curriculum_cache, load_curriculum
from .models import AppSettings, SessionLocal, init_db
from .routes import router

app = FastAPI(title="Codenda API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


def _disable_dev_mode_in_production() -> None:
    if not IS_PRODUCTION:
        return
    db = SessionLocal()
    try:
        setting = db.query(AppSettings).filter_by(key="dev_mode").first()
        if setting and setting.value == "true":
            setting.value = "false"
            db.commit()
    finally:
        db.close()


def _mount_static_files() -> None:
    if not SERVE_STATIC or not STATIC_DIR.is_dir():
        return

    assets_dir = STATIC_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        if full_path.startswith("api/") or full_path in {"docs", "openapi.json", "redoc"}:
            raise HTTPException(status_code=404, detail="Not found")
        candidate = STATIC_DIR / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        index = STATIC_DIR / "index.html"
        if index.is_file():
            return FileResponse(index)
        raise HTTPException(status_code=404, detail="Not found")


@app.on_event("startup")
def startup():
    init_db()
    _disable_dev_mode_in_production()
    invalidate_curriculum_cache()
    load_curriculum()
    _mount_static_files()


@app.get("/")
def root():
    if SERVE_STATIC and (STATIC_DIR / "index.html").is_file():
        return FileResponse(STATIC_DIR / "index.html")
    return {"app": "Codenda", "docs": "/docs"}
