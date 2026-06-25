from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from .content_loader import load_curriculum
from .executor import run_kumon_code, run_leetcode_code
from .models import (
    AppSettings,
    Attempt,
    DailySheet,
    DrillMastery,
    InterviewProgress,
    LeetCodeProgress,
    Session as StudySession,
    Streak,
    StudyDay,
    get_db,
    init_db,
)
from .progress import get_unlock_status, interview_unlocked, leetcode_unlocked, update_streak
from .sheet_composer import advance_study_day, build_sheet, update_drill_mastery

router = APIRouter()


class RunRequest(BaseModel):
    code: str
    exercise_id: str
    exercise_type: str = "kumon"
    tier: int = 1


class SubmitRequest(BaseModel):
    code: str
    exercise_id: str
    exercise_type: str = "kumon"
    tier: int = 1
    hints_used: int = 0
    time_ms: int = 0
    self_score: int | None = None
    answer_text: str | None = None


class SessionStartRequest(BaseModel):
    slot: str


class SessionEndRequest(BaseModel):
    session_id: int
    duration_seconds: int


class SettingsUpdate(BaseModel):
    focus_mode: bool | None = None


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/curriculum")
def curriculum(db: Session = Depends(get_db)):
    c = load_curriculum()
    unlocks = get_unlock_status(db)
    return {
        "kumon_count": len(c.kumon),
        "leetcode_count": len(c.leetcode),
        "interview_count": len(c.interview),
        "blocks": c.blocks,
        "unlocks": unlocks,
    }


@router.get("/sheet/today")
def sheet_today(slot: str = "morning", db: Session = Depends(get_db)):
    sheet = build_sheet(db, slot)
    curriculum = load_curriculum()
    drills = []
    for did in sheet.drill_ids:
        d = curriculum.kumon.get(did)
        if d:
            drills.append({
                "id": d.id,
                "block": d.block,
                "order": d.order,
                "scaffolding": d.scaffolding,
                "prompt": d.prompt,
                "starter_code": d.starter_code,
                "hints": d.hints,
                "csharp_note": d.csharp_note,
                "completed": did in (sheet.completed_ids or []),
            })
    study_day = db.query(StudyDay).filter_by(date=date.today()).first()
    return {
        "sheet_id": sheet.id,
        "slot": sheet.slot,
        "rule": sheet.generated_by_rule,
        "current_index": sheet.current_index,
        "drills": drills,
        "day_number": study_day.day_number if study_day else 1,
        "active_block": study_day.active_block if study_day else "a1-variables",
    }


@router.get("/kumon/{drill_id}")
def get_kumon(drill_id: str):
    c = load_curriculum()
    d = c.kumon.get(drill_id)
    if not d:
        raise HTTPException(404, "Drill not found")
    return {
        "id": d.id, "block": d.block, "order": d.order,
        "scaffolding": d.scaffolding, "prompt": d.prompt,
        "starter_code": d.starter_code, "hints": d.hints,
        "csharp_note": d.csharp_note,
    }


@router.get("/leetcode")
def list_leetcode(level: str = "a", db: Session = Depends(get_db)):
    if not leetcode_unlocked(db, level):
        return {"unlocked": False, "problems": []}
    c = load_curriculum()
    problems = []
    for p in c.leetcode.values():
        if p.level != level:
            continue
        prog = db.query(LeetCodeProgress).filter_by(problem_id=p.id).first()
        problems.append({
            "id": p.id, "title": p.title, "tier_passed": prog.tier_passed if prog else 0,
        })
    return {"unlocked": True, "problems": problems}


@router.get("/leetcode/{problem_id}")
def get_leetcode(problem_id: str, tier: int = 1, db: Session = Depends(get_db)):
    c = load_curriculum()
    p = c.leetcode.get(problem_id)
    if not p:
        raise HTTPException(404, "Problem not found")
    if not leetcode_unlocked(db, p.level):
        raise HTTPException(403, "LeetCode not unlocked for this level")
    tier_data = p.tiers.get(tier, {})
    return {
        "id": p.id, "title": p.title, "description": p.description,
        "tier": tier, "fn_name": p.fn_name,
        "starter_code": tier_data.get("starter_code", ""),
        "explain_checklist": tier_data.get("explain_checklist", []),
        "narration_prompts": tier_data.get("narration_prompts", []),
        "hints_allowed": tier_data.get("hints_allowed", tier < 3),
        "test_cases_preview": p.test_cases[:2],
    }


@router.get("/interview")
def list_interview(level: str = "a", category: str | None = None, db: Session = Depends(get_db)):
    if not interview_unlocked(db, level):
        return {"unlocked": False, "questions": []}
    c = load_curriculum()
    questions = []
    for q in c.interview.values():
        if q.level != level:
            continue
        if category and q.category != category:
            continue
        prog = db.query(InterviewProgress).filter_by(question_id=q.id).first()
        questions.append({
            "id": q.id, "category": q.category, "question": q.question,
            "completed": prog.completed if prog else False,
        })
    return {"unlocked": True, "questions": questions}


@router.get("/interview/{question_id}")
def get_interview(question_id: str, db: Session = Depends(get_db)):
    c = load_curriculum()
    q = c.interview.get(question_id)
    if not q:
        raise HTTPException(404, "Question not found")
    if not interview_unlocked(db, q.level):
        raise HTTPException(403, "Interview not unlocked")
    return {
        "id": q.id, "category": q.category, "question": q.question,
        "type": q.question_type,
    }


@router.get("/interview/{question_id}/answer")
def get_interview_answer(question_id: str, db: Session = Depends(get_db)):
    c = load_curriculum()
    q = c.interview.get(question_id)
    if not q:
        raise HTTPException(404)
    return {"rubric": q.rubric, "sample_answer": q.sample_answer}


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
    raise HTTPException(400, "Unknown exercise type")


@router.post("/submit")
def submit(req: SubmitRequest, db: Session = Depends(get_db)):
    c = load_curriculum()
    today = date.today()
    passed = False
    result = {}

    if req.exercise_type == "kumon":
        d = c.kumon.get(req.exercise_id)
        if not d:
            raise HTTPException(404)
        result = run_kumon_code(req.code, d.validation)
        passed = result.get("passed", False)
        update_drill_mastery(db, d.id, d.block, passed, req.hints_used)

        sheet = db.query(DailySheet).filter_by(date=today, slot="morning").first()
        for slot in ("morning", "evening"):
            sheet = db.query(DailySheet).filter_by(date=today, slot=slot).first()
            if sheet and req.exercise_id in (sheet.drill_ids or []):
                completed = list(sheet.completed_ids or [])
                if passed and req.exercise_id not in completed:
                    completed.append(req.exercise_id)
                    sheet.completed_ids = completed
                    sheet.current_index = min(sheet.current_index + 1, len(sheet.drill_ids))
                db.commit()

    elif req.exercise_type == "leetcode":
        p = c.leetcode.get(req.exercise_id)
        if not p:
            raise HTTPException(404)
        result = run_leetcode_code(req.code, p.test_cases, p.fn_name)
        passed = result.get("passed", False)
        if passed:
            prog = db.query(LeetCodeProgress).filter_by(problem_id=p.id).first()
            if not prog:
                prog = LeetCodeProgress(problem_id=p.id, level=p.level, tier_passed=req.tier)
                db.add(prog)
            else:
                prog.tier_passed = max(prog.tier_passed, req.tier)
            db.commit()

    elif req.exercise_type == "interview":
        q = c.interview.get(req.exercise_id)
        if not q:
            raise HTTPException(404)
        passed = True
        prog = db.query(InterviewProgress).filter_by(question_id=q.id).first()
        if not prog:
            prog = InterviewProgress(question_id=q.id, level=q.level, category=q.category)
            db.add(prog)
        prog.self_score = req.self_score or 0
        prog.completed = True
        db.commit()
        result = {"passed": True}

    attempt = Attempt(
        exercise_id=req.exercise_id,
        exercise_type=req.exercise_type,
        tier=req.tier,
        hints_used=req.hints_used,
        passed=passed,
        time_ms=req.time_ms,
        code_snapshot=req.code,
        self_score=req.self_score,
        attempt_date=today,
    )
    db.add(attempt)
    update_streak(db)
    db.commit()

    return {"passed": passed, "result": result}


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

    attempts_by_block = {}
    for m in db.query(DrillMastery).all():
        total = m.times_passed + (0 if m.status != "shaky" else 1)
        if m.block_id not in attempts_by_block:
            attempts_by_block[m.block_id] = {"passed": 0, "total": 20}
        attempts_by_block[m.block_id]["passed"] = m.times_passed

    accuracy = []
    for block_id, data in attempts_by_block.items():
        accuracy.append({"block": block_id, "accuracy": min(100, round(data["passed"] / 20 * 100))})

    total_attempts = db.query(Attempt).count()
    passed_attempts = db.query(Attempt).filter_by(passed=True).count()

    study_day = db.query(StudyDay).filter_by(date=today).first()

    return {
        "streak": {
            "current": streak.current_streak if streak else 0,
            "best": streak.best_streak if streak else 0,
        },
        "minutes_chart": minutes_chart,
        "block_accuracy": accuracy,
        "total_attempts": total_attempts,
        "pass_rate": round(passed_attempts / total_attempts * 100, 1) if total_attempts else 0,
        "day_number": study_day.day_number if study_day else 1,
        "unlocks": get_unlock_status(db),
    }


@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    focus = db.query(AppSettings).filter_by(key="focus_mode").first()
    return {"focus_mode": focus.value == "true" if focus else False}


@router.post("/settings")
def update_settings(req: SettingsUpdate, db: Session = Depends(get_db)):
    if req.focus_mode is not None:
        s = db.query(AppSettings).filter_by(key="focus_mode").first()
        if not s:
            s = AppSettings(key="focus_mode", value="false")
            db.add(s)
        s.value = "true" if req.focus_mode else "false"
        db.commit()
    return get_settings(db)


@router.post("/study/advance-day")
def study_advance(db: Session = Depends(get_db)):
    advance_study_day(db)
    sd = db.query(StudyDay).filter_by(date=date.today()).first()
    return {"day_number": sd.day_number if sd else 1, "active_block": sd.active_block if sd else "a1-variables"}


@router.get("/export")
def export_progress(db: Session = Depends(get_db)):
    attempts = db.query(Attempt).all()
    mastery = db.query(DrillMastery).all()
    return {
        "exported_at": datetime.utcnow().isoformat(),
        "attempts": [
            {"exercise_id": a.exercise_id, "type": a.exercise_type, "passed": a.passed,
             "time_ms": a.time_ms, "date": str(a.attempt_date)}
            for a in attempts
        ],
        "mastery": [
            {"drill_id": m.drill_id, "status": m.status, "times_passed": m.times_passed}
            for m in mastery
        ],
        "unlocks": get_unlock_status(db),
    }


@router.post("/mock/start")
def mock_start(level: str = "a", db: Session = Depends(get_db)):
    c = load_curriculum()
    if not leetcode_unlocked(db, level):
        raise HTTPException(403, "Complete Kumon blocks first")
    problems = [p for p in c.leetcode.values() if p.level == level]
    import random
    p = random.choice(problems) if problems else None
    if not p:
        raise HTTPException(404)
    return {
        "mode": "mock",
        "problem_id": p.id,
        "title": p.title,
        "description": p.description,
        "tier": 3,
        "time_limit_minutes": 25,
        "starter_code": p.tiers.get(3, {}).get("starter_code", "def solution():\n    pass"),
    }
