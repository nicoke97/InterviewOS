"""Return exam — retention check after several days away.

If the learner comes back after `inactivity_days` (default 3), they take a
short quiz of 2–3 exercises from mastered sets. Each failed exercise schedules
that set as a full repeat. Previously completed levels stay unlocked.
"""
from __future__ import annotations

import random
from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .content_loader import get_set_pages, load_curriculum, page_payload
from .executor import run_kumon_code
from .kumon_hierarchy import (
    display_set_number,
    is_extra_set,
    language_for_level,
    level_track,
    list_route_levels,
    route_level,
    set_title,
)
from .models import Attempt, ReturnExam, SetProgress, Streak


def return_exam_config() -> dict:
    try:
        cfg = (load_curriculum().progression or {}).get("return_exam") or {}
    except Exception:
        cfg = {}
    return {
        "enabled": bool(cfg.get("enabled", True)),
        "inactivity_days": int(cfg.get("inactivity_days", 3)),
        "min_exercises": int(cfg.get("min_exercises", 2)),
        "max_exercises": int(cfg.get("max_exercises", 3)),
    }


def last_activity_date(db: Session) -> date | None:
    last_attempt = db.query(func.max(Attempt.attempt_date)).scalar()
    streak = db.query(Streak).first()
    dates = [d for d in (last_attempt, streak.last_active_date if streak else None) if d]
    return max(dates) if dates else None


def inactivity_gap_days(db: Session) -> int:
    last = last_activity_date(db)
    if not last:
        return 0
    return max(0, (date.today() - last).days)


def _track_levels(track: str = "python") -> set[str]:
    return set(list_route_levels(track))


def _mastered_core_sets(db: Session, track: str = "python") -> list[SetProgress]:
    levels = _track_levels(track)
    rows = (
        db.query(SetProgress)
        .filter(SetProgress.status == "mastered")
        .order_by(SetProgress.mastered_at.asc())
        .all()
    )
    out: list[SetProgress] = []
    for sp in rows:
        lvl = route_level(sp.level)
        if lvl not in levels:
            continue
        if is_extra_set(lvl, sp.set_number):
            continue
        out.append(sp)
    return out


def get_pending(db: Session) -> ReturnExam | None:
    return (
        db.query(ReturnExam)
        .filter_by(status="pending")
        .order_by(ReturnExam.id.desc())
        .first()
    )


def _should_create(db: Session, track: str = "python") -> bool:
    cfg = return_exam_config()
    if not cfg["enabled"]:
        return False
    if get_pending(db):
        return False
    last = last_activity_date(db)
    if not last:
        return False
    if (date.today() - last).days < cfg["inactivity_days"]:
        return False
    if not _mastered_core_sets(db, track):
        return False
    return True


def get_status(db: Session, track: str = "python") -> dict:
    cfg = return_exam_config()
    pending = get_pending(db)
    last = last_activity_date(db)
    gap = inactivity_gap_days(db)
    needed = bool(pending) or _should_create(db, track)
    return {
        "needed": needed,
        "status": pending.status if pending else ("eligible" if needed else "none"),
        "exam_id": pending.id if pending else None,
        "inactivity_days": gap,
        "threshold_days": cfg["inactivity_days"],
        "last_active_date": str(last) if last else None,
        "exercise_count": len(pending.items or []) if pending else 0,
    }


def _item_from_page(page, level: str, set_number: int) -> dict:
    level = route_level(level)
    return {
        "exercise_id": page.id,
        "level": level,
        "set_number": set_number,
        "display_set_number": display_set_number(level, set_number),
    }


def _select_items(db: Session, track: str = "python") -> list[dict]:
    cfg = return_exam_config()
    min_n = max(1, cfg["min_exercises"])
    max_n = max(min_n, cfg["max_exercises"])
    rows = _mastered_core_sets(db, track)
    if not rows:
        return []

    curriculum = load_curriculum()
    by_level: dict[str, list[SetProgress]] = {}
    for sp in rows:
        by_level.setdefault(route_level(sp.level), []).append(sp)

    level_order = sorted(
        by_level.keys(),
        key=lambda lv: by_level[lv][0].mastered_at or datetime.max,
    )
    picked: list[SetProgress] = []
    index = {lv: 0 for lv in level_order}
    while len(picked) < max_n and any(index[lv] < len(by_level[lv]) for lv in level_order):
        for lv in level_order:
            i = index[lv]
            if i < len(by_level[lv]):
                picked.append(by_level[lv][i])
                index[lv] += 1
            if len(picked) >= max_n:
                break

    rng = random.Random()
    items: list[dict] = []

    if len(picked) == 1:
        sp = picked[0]
        pages = get_set_pages(curriculum, sp.level, sp.set_number)
        if not pages:
            return []
        n = min(max_n, max(min_n, 2), len(pages))
        for page in rng.sample(pages, n):
            items.append(_item_from_page(page, sp.level, sp.set_number))
        return items

    n = max(min_n, min(max_n, len(picked)))
    for sp in picked[:n]:
        pages = get_set_pages(curriculum, sp.level, sp.set_number)
        if not pages:
            continue
        items.append(_item_from_page(rng.choice(pages), sp.level, sp.set_number))
    return items


def get_or_create(db: Session, track: str = "python") -> ReturnExam | None:
    pending = get_pending(db)
    if pending:
        return pending
    if not _should_create(db, track):
        return None
    items = _select_items(db, track)
    if len(items) < 1:
        return None
    last = last_activity_date(db)
    exam = ReturnExam(
        last_active_date=last,
        inactivity_days=inactivity_gap_days(db),
        status="pending",
        items=items,
        failed_sets=[],
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam


def _session_payload(exam: ReturnExam, locale: str = "en") -> dict:
    curriculum = load_curriculum()
    drills = []
    items = []
    for raw in exam.items or []:
        page = curriculum.kumon.get(raw["exercise_id"])
        if not page:
            continue
        level = route_level(raw.get("level") or page.level)
        set_number = int(raw.get("set_number") or page.set)
        payload = page_payload(page, locale)
        payload["set_title"] = set_title(level, set_number, locale)
        payload["display_set_number"] = display_set_number(level, set_number)
        drills.append(payload)
        items.append({
            **raw,
            "level": level,
            "set_number": set_number,
            "display_set_number": display_set_number(level, set_number),
            "set_title": set_title(level, set_number, locale),
        })
    return {
        "id": exam.id,
        "status": exam.status,
        "inactivity_days": exam.inactivity_days,
        "last_active_date": str(exam.last_active_date) if exam.last_active_date else None,
        "drills": drills,
        "items": items,
        "results": exam.results,
        "failed_sets": exam.failed_sets or [],
        "completed_at": exam.completed_at.isoformat() if exam.completed_at else None,
    }


def get_exam_response(db: Session, locale: str = "en", *, create: bool = True, track: str = "python") -> dict:
    exam = get_or_create(db, track) if create else get_pending(db)
    status = get_status(db, track)
    if not exam:
        return {**status, "needed": False, "exam": None}
    return {**status, "needed": True, "exam": _session_payload(exam, locale)}


def schedule_full_set_repeat(db: Session, level: str, set_number: int) -> None:
    from .set_engine import _set_prog

    level = route_level(level)
    sp = _set_prog(db, level, set_number, create=True)
    sp.completed_pages = []
    sp.accumulated_time_ms = 0
    sp.errors = 0
    sp.status = "repeating"
    sp.solid_mastery = False
    sp.repeat_scheduled_for = date.today()
    flags = list(sp.failure_flags or [])
    if "return_exam" not in flags:
        flags.append("return_exam")
    sp.failure_flags = flags
    if not sp.track:
        sp.track = level_track(level)
    db.commit()


def submit(db: Session, answers: list, locale: str = "en") -> dict:
    from .i18n import t

    exam = get_pending(db)
    if not exam:
        raise HTTPException(400, t("return_exam_not_pending", locale))

    curriculum = load_curriculum()
    today = date.today()
    items = list(exam.items or [])
    answer_map = {a.exercise_id: (a.code or "") for a in answers}

    missing = [it["exercise_id"] for it in items if not (answer_map.get(it["exercise_id"]) or "").strip()]
    if missing:
        raise HTTPException(400, t("return_exam_incomplete", locale))

    results: dict[str, dict] = {}
    failed_keys: list[tuple[str, int]] = []

    for it in items:
        eid = it["exercise_id"]
        page = curriculum.kumon.get(eid)
        if not page:
            results[eid] = {"passed": False, "error": "Ejercicio no encontrado"}
            failed_keys.append((route_level(it.get("level") or ""), int(it.get("set_number") or 0)))
            continue
        res = run_kumon_code(answer_map[eid], page.validation, language=language_for_level(page.level))
        passed = bool(res.get("passed", False))
        results[eid] = {
            "passed": passed,
            "error": res.get("error"),
            "expected": res.get("expected"),
            "stdout": res.get("stdout"),
        }
        db.add(Attempt(
            exercise_id=eid,
            exercise_type="kumon",
            tier=0,
            hints_used=0,
            passed=passed,
            time_ms=0,
            code_snapshot=answer_map[eid],
            attempt_date=today,
        ))
        if not passed:
            failed_keys.append((
                route_level(it.get("level") or page.level),
                int(it.get("set_number") or page.set),
            ))

    unique_failed: list[dict] = []
    seen: set[tuple[str, int]] = set()
    for level, set_number in failed_keys:
        if not level or not set_number or (level, set_number) in seen:
            continue
        seen.add((level, set_number))
        unique_failed.append({
            "level": level,
            "set_number": set_number,
            "display_set_number": display_set_number(level, set_number),
            "set_title": set_title(level, set_number, locale),
        })
        schedule_full_set_repeat(db, level, set_number)

    exam.results = results
    exam.failed_sets = unique_failed
    exam.status = "completed"
    exam.completed_at = datetime.utcnow()
    db.commit()

    from .set_engine import update_streak
    update_streak(db)

    passed_count = sum(1 for r in results.values() if r.get("passed"))
    return {
        **get_status(db),
        "needed": False,
        "exam": _session_payload(exam, locale),
        "results": results,
        "passed_count": passed_count,
        "total": len(items),
        "passed": passed_count == len(items) and len(items) > 0,
        "failed_sets": unique_failed,
    }
