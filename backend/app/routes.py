from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from .content_i18n import localize_starter_code
from .content_loader import guide_fields, interview_payload, load_curriculum, problem_description, problem_title
from .executor import run_kumon_code, run_leetcode_code
from .kumon_hierarchy import (
    is_valid_route_level,
    language_for_level,
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
from .leetcodes_practice import (
    get_leetcodes_problem_detail,
    leetcodes_roadmap,
    submit_practice,
)
from .leetcodes_orientador import submit_guided_step
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
from .i18n import locale_from_request, t
from .return_exam import (
    get_exam_response as get_return_exam_response,
    get_status as get_return_exam_status,
    submit as submit_return_exam,
)
from .set_engine import (
    build_session,
    build_review_session,
    current_target,
    get_checkpoint,
    get_exam,
    level_roadmap,
    submit_checkpoint,
    submit_exam,
    submit_set,
)
from . import sde_engine

router = APIRouter()


# ---------------------------------------------------------------------------
# request models
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    code: str
    exercise_id: str
    exercise_type: str = "kumon"
    tier: int = 1
    language: str | None = None


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


class LeetcodesPracticeSubmitRequest(BaseModel):
    problem_id: str
    tier: int = 1
    code: str
    plan_id: int | None = None
    assignment_index: int | None = None
    language: str | None = None


class ReturnExamSubmitRequest(BaseModel):
    answers: list[SheetAnswerItem]


class SettingsUpdate(BaseModel):
    focus_mode: bool | None = None
    dev_mode: bool | None = None
    locale: str | None = None


class SdeCardReview(BaseModel):
    results: list[dict]


class SdeSheetSubmit(BaseModel):
    code: str


class SdeVoiceSubmit(BaseModel):
    transcript: str
    algo_id: str
    lang: str


class SdeTheorySubmit(BaseModel):
    answers: list[int]


class SdeOfflineBody(BaseModel):
    kinds: list[str] = []
    section_id: str | None = None
    passed: bool | None = None


class SdeSqlSubmit(BaseModel):
    sql: str


def _require_level(level: str, locale: str = "en") -> str:
    if not is_valid_route_level(level):
        raise HTTPException(404, t("unknown_level", locale, level=level))
    return route_level(level)


# ---------------------------------------------------------------------------
# meta
# ---------------------------------------------------------------------------

@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/curriculum")
def curriculum(request: Request, db: Session = Depends(get_db)):
    c = load_curriculum()
    locale = locale_from_request(request)
    return {
        "kumon_count": len(c.kumon),
        "leetcode_count": len(c.leetcode),
        "leetcodes_count": len(c.leetcodes),
        "interview_count": len(c.interview),
        "levels": levels_for_api("python", locale),
        "odoo_levels": levels_for_api("odoo", locale),
        "csharp_levels": levels_for_api("csharp", locale),
        "unlocks": get_unlock_status(db),
    }


# ---------------------------------------------------------------------------
# roadmap + flexible session
# ---------------------------------------------------------------------------

@router.get("/level/{level}/roadmap")
def roadmap(level: str, request: Request, db: Session = Depends(get_db)):
    locale = locale_from_request(request)
    level = _require_level(level, locale)
    return level_roadmap(db, level, locale=locale)


@router.get("/level/{level}/session")
def session(
    level: str,
    request: Request,
    count: int = 10,
    set_number: int | None = None,
    db: Session = Depends(get_db),
):
    locale = locale_from_request(request)
    level = _require_level(level, locale)
    if set_number is not None:
        return build_review_session(db, level, set_number, count, locale=locale)
    return build_session(db, level, count, locale=locale)


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
def orientador_calculate(req: OrientadorCalculateRequest, request: Request, db: Session = Depends(get_db)):
    locale = locale_from_request(request)
    if req.track != "leetcodes" and get_return_exam_status(db).get("needed"):
        raise HTTPException(400, t("return_exam_required", locale))
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
    data = get_active_plan_response(db, track)
    data["return_exam"] = get_return_exam_status(db)
    return data


@router.get("/orientador/insight")
def orientador_insight(request: Request, track: str = "python", db: Session = Depends(get_db)):
    locale = locale_from_request(request)
    return get_orientador_insight(db, track, locale=locale)


@router.get("/orientador/session/{plan_id}/{index}")
def orientador_session(plan_id: int, index: int, request: Request, db: Session = Depends(get_db)):
    locale = locale_from_request(request)
    return get_assignment_session(db, plan_id, index, locale=locale)


# ---------------------------------------------------------------------------
# LeetCodes interview practice track
# ---------------------------------------------------------------------------

@router.get("/leetcodes/roadmap")
def leetcodes_roadmap_route(db: Session = Depends(get_db)):
    return leetcodes_roadmap(db)


@router.get("/leetcodes/problem/{problem_id}")
def leetcodes_problem(problem_id: str, request: Request, tier: int = 1, language: str | None = None):
    locale = locale_from_request(request)
    detail = get_leetcodes_problem_detail(problem_id, tier, locale=locale, language=language)
    if not detail:
        raise HTTPException(404, t("problem_not_found", locale))
    return detail


@router.post("/leetcodes/practice/submit")
def leetcodes_practice_submit(req: LeetcodesPracticeSubmitRequest, request: Request, db: Session = Depends(get_db)):
    locale = locale_from_request(request)
    if req.plan_id is not None and req.assignment_index is not None:
        return submit_guided_step(
            db, req.plan_id, req.assignment_index, req.tier, req.code,
            language=req.language,
        )
    return submit_practice(db, req.problem_id, req.tier, req.code, locale=locale, language=req.language)


# ---------------------------------------------------------------------------
# checkpoints
# ---------------------------------------------------------------------------

@router.get("/level/{level}/checkpoint/{block}")
def checkpoint(level: str, block: str, request: Request, db: Session = Depends(get_db)):
    locale = locale_from_request(request)
    level = _require_level(level, locale)
    return get_checkpoint(db, level, block, locale=locale)


@router.post("/checkpoint/submit")
def checkpoint_submit(req: CheckpointSubmitRequest, db: Session = Depends(get_db)):
    level = _require_level(req.level)
    return submit_checkpoint(db, level, req.problem_id, req.code)


# ---------------------------------------------------------------------------
# level exam
# ---------------------------------------------------------------------------

@router.get("/level/{level}/exam")
def exam(level: str, request: Request, db: Session = Depends(get_db)):
    locale = locale_from_request(request)
    level = _require_level(level, locale)
    return get_exam(db, level, locale=locale)


@router.post("/exam/submit")
def exam_submit(req: ExamSubmitRequest, db: Session = Depends(get_db)):
    level = _require_level(req.level)
    return submit_exam(db, level, req.exercise_id, req.exercise_type,
                       code=req.code, self_score=req.self_score, answer_text=req.answer_text)


# ---------------------------------------------------------------------------
# problem / question detail (for checkpoint & exam editors)
# ---------------------------------------------------------------------------

@router.get("/problem/{problem_id}")
def get_problem(problem_id: str, request: Request, tier: int = 1, language: str | None = None, db: Session = Depends(get_db)):
    locale = locale_from_request(request)
    c = load_curriculum()
    if problem_id in c.leetcodes:
        detail = get_leetcodes_problem_detail(problem_id, tier, locale=locale, language=language)
        if detail:
            return detail
    p = c.leetcode.get(problem_id)
    if not p:
        raise HTTPException(404, t("problem_not_found", locale))
    tier_data = p.tiers.get(tier, {}) or p.tiers.get(1, {})
    guide = guide_fields(p, tier_data, tier, locale)
    explain_checklist = guide.pop("explain_checklist", tier_data.get("explain_checklist", []))
    narration_prompts = guide.pop("narration_prompts", tier_data.get("narration_prompts", []))
    return {
        "id": p.id, "title": problem_title(p, locale, p.title), "description": problem_description(p, locale),
        "tier": tier, "fn_name": p.fn_name,
        "language": language_for_level(p.level),
        "starter_code": localize_starter_code(tier_data.get("starter_code", ""), locale),
        "explain_checklist": explain_checklist,
        "narration_prompts": narration_prompts,
        "test_cases_preview": p.test_cases[:2],
        **guide,
    }


@router.get("/question/{question_id}")
def get_question(question_id: str, request: Request):
    locale = locale_from_request(request)
    c = load_curriculum()
    q = c.interview.get(question_id)
    if not q:
        raise HTTPException(404, t("question_not_found", locale))
    return interview_payload(q, locale)


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
        return run_kumon_code(req.code, d.validation, language=language_for_level(d.level))
    if req.exercise_type == "leetcode":
        p = c.leetcodes.get(req.exercise_id) or c.leetcode.get(req.exercise_id)
        if not p:
            raise HTTPException(404)
        from .leetcodes_csharp import csharp_spec, normalize_exec_language
        if p.track == "leetcodes":
            lang = normalize_exec_language(req.language)
            fn_name = p.fn_name
            if lang == "csharp":
                spec = csharp_spec(p.id, req.tier)
                if spec:
                    fn_name = spec["fn_name"]
                else:
                    lang = "python"
            return run_leetcode_code(req.code, p.test_cases, fn_name, language=lang)
        return run_leetcode_code(req.code, p.test_cases, p.fn_name, language=language_for_level(p.level))
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
def stats(request: Request, db: Session = Depends(get_db)):
    locale = locale_from_request(request)
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
        "block_accuracy": get_block_accuracy(db, progress_map, locale=locale),
        "today_activity": get_today_activity(db),
        "total_attempts": total_attempts,
        "pass_rate": round(passed_attempts / total_attempts * 100, 1) if total_attempts else 0,
        "day_number": distinct_days,
        "unlocks": get_unlock_status(db, progress_map),
        "return_exam": get_return_exam_status(db),
    }


# ---------------------------------------------------------------------------
# return exam (after inactivity)
# ---------------------------------------------------------------------------

@router.get("/return-exam/status")
def return_exam_status(db: Session = Depends(get_db)):
    return get_return_exam_status(db)


@router.get("/return-exam")
def return_exam_get(request: Request, db: Session = Depends(get_db)):
    locale = locale_from_request(request)
    return get_return_exam_response(db, locale=locale, create=True)


@router.post("/return-exam/submit")
def return_exam_submit(req: ReturnExamSubmitRequest, request: Request, db: Session = Depends(get_db)):
    locale = locale_from_request(request)
    return submit_return_exam(db, req.answers, locale=locale)


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


def _str_setting(db: Session, key: str, default: str = "en") -> str:
    s = db.query(AppSettings).filter_by(key=key).first()
    return s.value if s else default


def _set_str_setting(db: Session, key: str, value: str) -> None:
    s = db.query(AppSettings).filter_by(key=key).first()
    if not s:
        s = AppSettings(key=key, value=value)
        db.add(s)
    s.value = value


@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    return {
        "focus_mode": _bool_setting(db, "focus_mode"),
        "dev_mode": _bool_setting(db, "dev_mode"),
        "locale": _str_setting(db, "locale", "en"),
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
    if req.locale is not None and req.locale in ("en", "es"):
        _set_str_setting(db, "locale", req.locale)
        changed = True
    if changed:
        db.commit()
    return get_settings(db)


@router.get("/sde/today")
def sde_today(request: Request, db: Session = Depends(get_db)):
    return sde_engine.ensure_today(db, locale_from_request(request))


@router.post("/sde/cards/review")
def sde_cards_review(req: SdeCardReview, db: Session = Depends(get_db)):
    return sde_engine.review_cards(db, req.results)


@router.get("/sde/section/{section_id}")
def sde_section(section_id: str, request: Request):
    sec = sde_engine.get_section(section_id, locale_from_request(request))
    if not sec:
        raise HTTPException(404, "section not found")
    return sec


@router.post("/sde/section/{section_id}/quiz")
def sde_section_quiz(section_id: str, req: SdeTheorySubmit, request: Request, db: Session = Depends(get_db)):
    return sde_engine.submit_theory(db, section_id, req.answers, locale_from_request(request))


@router.get("/sde/algo/{algo_id}/{lang}/{sheet_id}")
def sde_sheet(algo_id: str, lang: str, sheet_id: str, request: Request):
    payload = sde_engine.get_sheet_payload(algo_id, lang, sheet_id, locale_from_request(request))
    if not payload:
        raise HTTPException(404, "sheet not found")
    return payload


@router.post("/sde/algo/{algo_id}/{lang}/{sheet_id}/submit")
def sde_sheet_submit(algo_id: str, lang: str, sheet_id: str, req: SdeSheetSubmit, db: Session = Depends(get_db)):
    return sde_engine.submit_sheet(db, algo_id, lang, sheet_id, req.code)


@router.post("/sde/voice")
def sde_voice(req: SdeVoiceSubmit, db: Session = Depends(get_db)):
    return sde_engine.submit_voice(db, req.algo_id, req.lang, req.transcript)


@router.post("/sde/offline")
def sde_offline(req: SdeOfflineBody, db: Session = Depends(get_db)):
    if req.passed is not None:
        return sde_engine.verify_offline(db, req.passed)
    return sde_engine.log_offline(db, req.kinds, req.section_id)


@router.get("/sde/travel-pack")
def sde_pack(request: Request, db: Session = Depends(get_db)):
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(sde_engine.travel_pack(db, locale_from_request(request)), media_type="text/markdown")


@router.post("/sde/sql/{drill_id}")
def sde_sql(drill_id: str, req: SdeSqlSubmit, db: Session = Depends(get_db)):
    return sde_engine.submit_sql(db, drill_id, req.sql)


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
