from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from .content_loader import load_curriculum
from .executor import run_kumon_code, run_leetcode_code
from .kumon_hierarchy import (
    is_valid_route_level,
    levels_for_api,
    route_level,
)
from .models import (
    AppSettings,
    Attempt,
    Session as StudySession,
    Streak,
    get_db,
)
from .progress import (
    get_block_accuracy,
    get_effective_streak,
    get_month_calendar,
    get_today_activity,
    get_unlock_status,
    load_set_progress_map,
)
from .orientador import (
    calculate_session,
    get_active_plan_response,
    get_assignment_session,
    get_orientador_insight,
    get_next_assignment,
    mark_assignment_done,
    plan_to_dict,
    validate_assignment,
)
from .set_engine import (
    build_session,
    current_target,
    get_checkpoint,
    get_exam,
    level_roadmap,
    submit_checkpoint,
    submit_exam,
    submit_set,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# request models
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    code: str
    exercise_id: str
    exercise_type: str = "kumon"
    tier: int = 1


class SheetAnswerItem(BaseModel):
    exercise_id: str
    code: str


class SetSubmitRequest(BaseModel):
    level: str
    set_number: int
    answers: list[SheetAnswerItem]
    time_ms: int = 0
    plan_id: int | None = None
    assignment_index: int | None = None


class OrientadorCalculateRequest(BaseModel):
    minutes: int
    track: str = "python"
    plan_id: int | None = None
    new_session: bool = False


class CheckpointSubmitRequest(BaseModel):
    level: str
    problem_id: str
    code: str


class ExamSubmitRequest(BaseModel):
    level: str
    exercise_id: str
    exercise_type: str = "leetcode"
    code: str = ""
    self_score: int | None = None
    answer_text: str | None = None


class SessionStartRequest(BaseModel):
    slot: str = "study"


class SessionEndRequest(BaseModel):
    session_id: int
    duration_seconds: int


class SettingsUpdate(BaseModel):
    focus_mode: bool | None = None
    dev_mode: bool | None = None


def _require_level(level: str) -> str:
    if not is_valid_route_level(level):
        raise HTTPException(404, f"Nivel desconocido: {level}")
    return route_level(level)


# ---------------------------------------------------------------------------
# meta
# ---------------------------------------------------------------------------

@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/curriculum")
def curriculum(db: Session = Depends(get_db)):
    c = load_curriculum()
    return {
        "kumon_count": len(c.kumon),
        "leetcode_count": len(c.leetcode),
        "interview_count": len(c.interview),
        "levels": levels_for_api("python"),
        "odoo_levels": levels_for_api("odoo"),
        "unlocks": get_unlock_status(db),
    }


# ---------------------------------------------------------------------------
# roadmap + flexible session
# ---------------------------------------------------------------------------

@router.get("/level/{level}/roadmap")
def roadmap(level: str, db: Session = Depends(get_db)):
    level = _require_level(level)
    return level_roadmap(db, level)


@router.get("/level/{level}/session")
def session(level: str, count: int = 10, db: Session = Depends(get_db)):
    level = _require_level(level)
    return build_session(db, level, count)


@router.post("/set/submit")
def set_submit(req: SetSubmitRequest, db: Session = Depends(get_db)):
    level = _require_level(req.level)
    is_repeat = False
    if req.plan_id is not None and req.assignment_index is not None:
        va = validate_assignment(
            db, req.plan_id, req.assignment_index,
            assignment_type="set", level=level, set_number=req.set_number,
        )
        is_repeat = va.get("assignment", {}).get("reason") == "repeat"
    result = submit_set(
        db, level, req.set_number, req.answers, req.time_ms, is_repeat=is_repeat,
    )
    if req.plan_id is not None and req.assignment_index is not None:
        if result.get("mastered") or result.get("outcome") in ("mastered", "too_slow"):
            mark_assignment_done(db, req.plan_id, req.assignment_index)
            nxt = get_next_assignment(db, req.plan_id)
            if nxt:
                result["next_assignment"] = nxt
            else:
                result["session_complete"] = True
    return result


# ---------------------------------------------------------------------------
# orientador
# ---------------------------------------------------------------------------

@router.post("/orientador/calculate")
def orientador_calculate(req: OrientadorCalculateRequest, db: Session = Depends(get_db)):
    plan = calculate_session(
        db,
        req.minutes,
        req.track,
        plan_id=req.plan_id,
        new_session=req.new_session,
    )
    return plan_to_dict(plan)


@router.get("/orientador/active")
def orientador_active(track: str = "python", db: Session = Depends(get_db)):
    return get_active_plan_response(db, track)


@router.get("/orientador/insight")
def orientador_insight(track: str = "python", db: Session = Depends(get_db)):
    return get_orientador_insight(db, track)


@router.get("/orientador/session/{plan_id}/{index}")
def orientador_session(plan_id: int, index: int, db: Session = Depends(get_db)):
    return get_assignment_session(db, plan_id, index)


# ---------------------------------------------------------------------------
# checkpoints
# ---------------------------------------------------------------------------

@router.get("/level/{level}/checkpoint/{block}")
def checkpoint(level: str, block: str, db: Session = Depends(get_db)):
    level = _require_level(level)
    return get_checkpoint(db, level, block)


@router.post("/checkpoint/submit")
def checkpoint_submit(req: CheckpointSubmitRequest, db: Session = Depends(get_db)):
    level = _require_level(req.level)
    return submit_checkpoint(db, level, req.problem_id, req.code)


# ---------------------------------------------------------------------------
# level exam
# ---------------------------------------------------------------------------

@router.get("/level/{level}/exam")
def exam(level: str, db: Session = Depends(get_db)):
    level = _require_level(level)
    return get_exam(db, level)


@router.post("/exam/submit")
def exam_submit(req: ExamSubmitRequest, db: Session = Depends(get_db)):
    level = _require_level(req.level)
    return submit_exam(db, level, req.exercise_id, req.exercise_type,
                       code=req.code, self_score=req.self_score, answer_text=req.answer_text)


# ---------------------------------------------------------------------------
# problem / question detail (for checkpoint & exam editors)
# ---------------------------------------------------------------------------

@router.get("/problem/{problem_id}")
def get_problem(problem_id: str, tier: int = 1, db: Session = Depends(get_db)):
    c = load_curriculum()
    p = c.leetcode.get(problem_id)
    if not p:
        raise HTTPException(404, "Problema no encontrado")
    tier_data = p.tiers.get(tier, {}) or p.tiers.get(1, {})
    return {
        "id": p.id, "title": p.title, "description": p.description,
        "tier": tier, "fn_name": p.fn_name,
        "starter_code": tier_data.get("starter_code", ""),
        "explain_checklist": tier_data.get("explain_checklist", []),
        "narration_prompts": tier_data.get("narration_prompts", []),
        "hints_allowed": tier_data.get("hints_allowed", tier < 3),
        "test_cases_preview": p.test_cases[:2],
    }


@router.get("/question/{question_id}")
def get_question(question_id: str):
    c = load_curriculum()
    q = c.interview.get(question_id)
    if not q:
        raise HTTPException(404, "Pregunta no encontrada")
    return {
        "id": q.id, "category": q.category, "question": q.question,
        "type": q.question_type, "rubric": q.rubric, "sample_answer": q.sample_answer,
    }


# ---------------------------------------------------------------------------
# run (editor "Run" button)
# ---------------------------------------------------------------------------

@router.post("/run")
def run_code(req: RunRequest):
    c = load_curriculum()
    if req.exercise_type == "kumon":
        d = c.kumon.get(req.exercise_id)
        if not d:
            raise HTTPException(404)
        return run_kumon_code(req.code, d.validation)
    if req.exercise_type == "leetcode":
        p = c.leetcode.get(req.exercise_id)
        if not p:
            raise HTTPException(404)
        return run_leetcode_code(req.code, p.test_cases, p.fn_name)
    raise HTTPException(400, "Tipo de ejercicio desconocido")


# ---------------------------------------------------------------------------
# session timer
# ---------------------------------------------------------------------------

@router.post("/session/start")
def session_start(req: SessionStartRequest, db: Session = Depends(get_db)):
    s = StudySession(date=date.today(), slot=req.slot, duration_seconds=0)
    db.add(s)
    db.commit()
    return {"session_id": s.id}


@router.post("/session/end")
def session_end(req: SessionEndRequest, db: Session = Depends(get_db)):
    s = db.query(StudySession).filter_by(id=req.session_id).first()
    if s:
        s.duration_seconds = req.duration_seconds
        db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# calendar + stats
# ---------------------------------------------------------------------------

@router.get("/calendar")
def calendar_month(year: int | None = None, month: int | None = None, db: Session = Depends(get_db)):
    today = date.today()
    y = year if year is not None else today.year
    m = month if month is not None else today.month
    if not 1 <= m <= 12:
        raise HTTPException(400, "month must be 1-12")
    return get_month_calendar(db, y, m)


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    streak = db.query(Streak).first()
    today = date.today()
    thirty_ago = today - timedelta(days=30)

    daily_minutes = (
        db.query(StudySession.date, func.sum(StudySession.duration_seconds))
        .filter(StudySession.date >= thirty_ago)
        .group_by(StudySession.date)
        .all()
    )
    minutes_chart = [{"date": str(d), "minutes": round(s / 60, 1)} for d, s in daily_minutes]

    total_attempts = db.query(Attempt).count()
    passed_attempts = db.query(Attempt).filter_by(passed=True).count()

    distinct_days = db.query(func.count(func.distinct(Attempt.attempt_date))).scalar() or 0

    progress_map = load_set_progress_map(db)

    return {
        "streak": get_effective_streak(db, streak),
        "minutes_chart": minutes_chart,
        "block_accuracy": get_block_accuracy(db, progress_map),
        "today_activity": get_today_activity(db),
        "total_attempts": total_attempts,
        "pass_rate": round(passed_attempts / total_attempts * 100, 1) if total_attempts else 0,
        "day_number": distinct_days,
        "unlocks": get_unlock_status(db, progress_map),
    }


# ---------------------------------------------------------------------------
# settings
# ---------------------------------------------------------------------------

def _bool_setting(db: Session, key: str, default: bool = False) -> bool:
    s = db.query(AppSettings).filter_by(key=key).first()
    return s.value == "true" if s else default


def _set_bool_setting(db: Session, key: str, value: bool) -> None:
    s = db.query(AppSettings).filter_by(key=key).first()
    if not s:
        s = AppSettings(key=key, value="false")
        db.add(s)
    s.value = "true" if value else "false"


@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    return {
        "focus_mode": _bool_setting(db, "focus_mode"),
        "dev_mode": _bool_setting(db, "dev_mode"),
    }


@router.post("/settings")
def update_settings(req: SettingsUpdate, db: Session = Depends(get_db)):
    changed = False
    if req.focus_mode is not None:
        _set_bool_setting(db, "focus_mode", req.focus_mode)
        changed = True
    if req.dev_mode is not None:
        _set_bool_setting(db, "dev_mode", req.dev_mode)
        changed = True
    if changed:
        db.commit()
    return get_settings(db)


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------

@router.get("/export")
def export_progress(db: Session = Depends(get_db)):
    attempts = db.query(Attempt).all()
    return {
        "exported_at": datetime.utcnow().isoformat(),
        "attempts": [
            {"exercise_id": a.exercise_id, "type": a.exercise_type, "passed": a.passed,
             "time_ms": a.time_ms, "date": str(a.attempt_date)}
            for a in attempts
        ],
        "unlocks": get_unlock_status(db),
    }
