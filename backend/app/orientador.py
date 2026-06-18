"""Orientador Kumon — daily session planner with spaced repetition."""
from __future__ import annotations

from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .content_loader import get_set_pages, load_curriculum
from .kumon_hierarchy import (
    block_instruction,
    block_title,
    display_set_number,
    level_sets,
    level_track,
    list_route_levels,
    normalize_level,
    route_level,
    set_standard_seconds,
    set_title,
)
from .models import DailyPlan, SetProgress
from .progress import get_active_level
from .set_engine import (
    _exam_available,
    _page_payload,
    _set_prog,
    block_letter_for_set_num,
    current_target,
    dev_mode_enabled,
    get_checkpoint,
    get_exam,
    set_mastered,
)


def _progression() -> dict:
    return load_curriculum().progression or {}


def orientador_config() -> dict:
    prog = _progression()
    orientador = prog.get("orientador") or {}
    pre_exam = prog.get("pre_exam") or {}
    mastery = prog.get("mastery") or {}
    return {
        "minute_presets": orientador.get("minute_presets", [20, 30, 40, 60]),
        "min_minutes": int(orientador.get("min_minutes", 15)),
        "max_minutes": int(orientador.get("max_minutes", 90)),
        "default_minutes": int(orientador.get("default_minutes", 15)),
        "first_attempt_threshold": float(mastery.get("first_attempt_threshold", 0.90)),
        "pre_exam_enabled": bool(pre_exam.get("enabled", True)),
        "pre_exam_max_sets": int(pre_exam.get("max_sets", 3)),
    }


def orientador_config_for(track: str = "python") -> dict:
    if track == "leetcodes":
        cfg = load_curriculum().leetcodes_schedule.orientador or {}
        return {
            "minute_presets": cfg.get("minute_presets", [45, 60, 90]),
            "min_minutes": int(cfg.get("min_minutes", 30)),
            "max_minutes": int(cfg.get("max_minutes", 90)),
            "default_minutes": int(cfg.get("default_minutes", 60)),
            "hint_lock_minutes": int(cfg.get("hint_lock_minutes", 25)),
            "focus_topics": cfg.get("focus_topics") or ["arrays_hashing", "two_pointers"],
            "max_problems_per_session": int(cfg.get("max_problems_per_session", 1)),
        }
    return orientador_config()


def _clamp_minutes(minutes: int) -> int:
    cfg = orientador_config()
    return max(cfg["min_minutes"], min(cfg["max_minutes"], minutes))


def _assignment_key(a: dict) -> str:
    if a.get("type") == "set":
        return f"set:{a['level']}:{a['set_number']}"
    if a.get("type") == "checkpoint":
        return f"checkpoint:{a['level']}:{a['block']}"
    if a.get("type") == "exam":
        return f"exam:{a['level']}"
    return str(a)


def _set_minutes(level: str, set_number: int) -> float:
    return set_standard_seconds(level, set_number) / 60.0


def _assignment_identity(a: dict) -> str:
    return f"{_assignment_key(a)}:{a.get('reason', '')}:{a.get('lap', 0)}"


def _plan_estimated_minutes(assignments: list[dict]) -> float:
    return sum(float(a.get("estimated_minutes", 0)) for a in assignments)


def get_today_plans(db: Session, track: str = "python") -> list[DailyPlan]:
    return (
        db.query(DailyPlan)
        .filter_by(date=date.today(), track=track or "python")
        .order_by(DailyPlan.session_number.asc(), DailyPlan.id.asc())
        .all()
    )


def _next_session_number(db: Session, today: date, track: str) -> int:
    max_n = (
        db.query(func.max(DailyPlan.session_number))
        .filter_by(date=today, track=track)
        .scalar()
    )
    return int(max_n or 0) + 1


def _today_plan_keys(db: Session, track: str, today: date) -> set[str]:
    keys: set[str] = set()
    for plan in db.query(DailyPlan).filter_by(date=today, track=track):
        for assignment in plan.assignments or []:
            keys.add(_assignment_key(assignment))
    return keys


def _get_plan_today(db: Session, plan_id: int, track: str) -> DailyPlan:
    plan = db.query(DailyPlan).filter_by(id=plan_id).first()
    if not plan or plan.date != date.today() or plan.track != track:
        raise HTTPException(404, "Sesion no encontrada para hoy")
    return plan


def get_active_plan(db: Session, track: str = "python") -> DailyPlan | None:
    d = date.today()
    return (
        db.query(DailyPlan)
        .filter_by(date=d, track=track, status="active")
        .order_by(DailyPlan.calculated_at.desc())
        .first()
    )


def _due_repeats(db: Session, level: str, today: date) -> list[dict]:
    """Due repeats for the whole track so a failed return-exam set in a
    previous level still comes first in today's plan."""
    levels = list_route_levels(level_track(level))
    rows = (
        db.query(SetProgress)
        .filter(
            SetProgress.level.in_(levels),
            SetProgress.repeat_scheduled_for.isnot(None),
            SetProgress.repeat_scheduled_for <= today,
        )
        .all()
    )
    out: list[dict] = []
    for sp in rows:
        if sp.repeat_completed_at == today:
            continue
        item = _set_item(sp.level, sp.set_number, "repeat")
        if "return_exam" in (sp.failure_flags or []):
            item["from_return_exam"] = True
        out.append(item)
    out.sort(key=lambda a: (a["level"], a["set_number"]))
    return out


def _pre_exam_sets(db: Session, level: str) -> list[dict]:
    cfg = orientador_config()
    if not cfg["pre_exam_enabled"]:
        return []
    if not _exam_available(db, level):
        return []

    level = route_level(level)
    candidates: list[tuple[int, SetProgress]] = []
    for s in level_sets(level):
        sp = _set_prog(db, level, s.set_number, create=False)
        if not sp:
            continue
        if sp.solid_mastery:
            continue
        if sp.failure_flags or (
            sp.first_attempt_accuracy is not None
            and sp.first_attempt_accuracy < cfg["first_attempt_threshold"]
        ):
            candidates.append((s.set_number, sp))

    candidates.sort(key=lambda x: x[0])
    out: list[dict] = []
    for set_number, _sp in candidates[: cfg["pre_exam_max_sets"]]:
        if set_mastered(db, level, set_number):
            out.append(_set_item(level, set_number, "pre_exam"))
    return out


def _set_item(level: str, set_number: int, reason: str, *, lap: int = 0) -> dict:
    item = {
        "type": "set",
        "level": route_level(level),
        "set_number": set_number,
        "display_set_number": display_set_number(level, set_number),
        "reason": reason,
        "estimated_minutes": _set_minutes(level, set_number),
    }
    if lap:
        item["lap"] = lap
    return item


def _repaso_sets(db: Session, level: str, exclude_keys: set[str]) -> list[dict]:
    """Mastered sets worth revisiting (non-solid first, then recent solid)."""
    level = route_level(level)
    out: list[dict] = []
    seen: set[str] = set()

    for s in level_sets(level):
        sn = s.set_number
        key = _assignment_key(_set_item(level, sn, "repaso"))
        if key in exclude_keys or key in seen:
            continue
        if not set_mastered(db, level, sn):
            continue
        sp = _set_prog(db, level, sn, create=False)
        if sp and sp.solid_mastery:
            continue
        seen.add(key)
        out.append(_set_item(level, sn, "repaso"))

    for s in reversed(level_sets(level)):
        sn = s.set_number
        key = _assignment_key(_set_item(level, sn, "repaso"))
        if key in exclude_keys or key in seen:
            continue
        if not set_mastered(db, level, sn):
            continue
        sp = _set_prog(db, level, sn, create=False)
        if not sp or not sp.solid_mastery:
            continue
        seen.add(key)
        out.append(_set_item(level, sn, "repaso"))

    return out


def _new_set_candidates(db: Session, level: str) -> list[dict]:
    level = route_level(level)
    target = current_target(db, level)
    out: list[dict] = []
    if target.get("type") == "set":
        sn = target["set_number"]
        if not set_mastered(db, level, sn):
            out.append(_set_item(level, sn, "new"))
    elif target.get("type") == "checkpoint":
        out.append({
            "type": "checkpoint",
            "level": level,
            "block": target["block"],
            "reason": "checkpoint",
            "estimated_minutes": 30.0,
        })
    elif target.get("type") == "exam":
        out.append({
            "type": "exam",
            "level": level,
            "reason": "exam",
            "estimated_minutes": 45.0,
        })
    return out


def _merge_candidates(
    db: Session,
    level: str,
    today: date,
    exclude_keys: set[str],
) -> list[dict]:
    seen: set[str] = set()
    ordered: list[dict] = []
    for group in (
        _due_repeats(db, level, today),
        _pre_exam_sets(db, level),
        _new_set_candidates(db, level),
        _repaso_sets(db, level, exclude_keys),
    ):
        for item in group:
            key = _assignment_key(item)
            if key in seen or key in exclude_keys:
                continue
            seen.add(key)
            ordered.append(item)
    return ordered


def _min_activity_minutes() -> float:
    try:
        orientador = (_progression().get("orientador") or {})
        return float(orientador.get("min_activity_minutes", 5))
    except Exception:
        return 5.0


def _pack_assignments(candidates: list[dict], budget_minutes: float) -> list[dict]:
    """Fill the session budget with as many activities as fit."""
    if not candidates:
        return []

    min_slot = _min_activity_minutes()
    assignments: list[dict] = []
    budget = float(budget_minutes)

    for item in candidates:
        est = float(item.get("estimated_minutes", 15))
        if est <= budget or not assignments:
            assignments.append(item)
            budget -= est
        if budget < min_slot:
            return assignments

    repaso_pool = [
        c for c in candidates
        if c.get("type") == "set" and c.get("reason") in ("repaso", "pre_exam", "repeat")
    ]
    if not repaso_pool:
        repaso_pool = [c for c in candidates if c.get("type") == "set"]

    lap = 1
    while budget >= min_slot and repaso_pool and lap <= 8:
        for item in repaso_pool:
            est = float(item.get("estimated_minutes", 15))
            if est > budget:
                continue
            assignments.append({**item, "reason": "repaso_extra", "lap": lap})
            budget -= est
            if budget < min_slot:
                return assignments
        lap += 1

    return assignments


def _assignments_match(a: dict, b: dict) -> bool:
    if a.get("type") != b.get("type"):
        return False
    if _assignment_key(a) != _assignment_key(b):
        return False
    return a.get("reason") == b.get("reason") and a.get("lap", 0) == b.get("lap", 0)


def _remap_completed_indices(old_assignments: list[dict], new_assignments: list[dict], old_completed: list[int]) -> list[int]:
    """Keep completion state when the plan is rebuilt (índices shift)."""
    done_items: list[dict] = []
    for idx in sorted(old_completed):
        if 0 <= idx < len(old_assignments):
            done_items.append(old_assignments[idx])
    matched: list[int] = []
    used: set[int] = set()
    for done in done_items:
        for i, item in enumerate(new_assignments):
            if i in used:
                continue
            if _assignments_match(done, item):
                matched.append(i)
                used.add(i)
                break
    return sorted(matched)


def _pack_extension(
    existing_assignments: list[dict],
    db: Session,
    track: str,
    delta_minutes: float,
) -> list[dict]:
    """Append activities that fit in extra minutes budget."""
    if delta_minutes <= 0:
        return []

    today = date.today()
    level = get_active_level(db, track)
    exclude_keys = _today_plan_keys(db, track, today)
    candidates = _merge_candidates(db, level, today, exclude_keys)
    extra = _pack_assignments(candidates, delta_minutes)
    used = sum(float(a.get("estimated_minutes", 0)) for a in extra)
    budget = delta_minutes - used
    min_slot = _min_activity_minutes()

    if budget < min_slot:
        return extra

    repaso_pool = [a for a in existing_assignments if a.get("type") == "set"]
    if not repaso_pool:
        repaso_pool = [c for c in candidates if c.get("type") == "set"]
    max_lap = max((int(a.get("lap", 0)) for a in existing_assignments), default=0)
    lap = max_lap + 1
    while budget >= min_slot and repaso_pool and lap <= 8:
        for item in repaso_pool:
            est = float(item.get("estimated_minutes", 15))
            if est > budget:
                continue
            extra.append({**item, "reason": "repaso_extra", "lap": lap})
            budget -= est
            if budget < min_slot:
                return extra
        lap += 1
    return extra


def _create_new_session(db: Session, minutes: int, track: str, today: date) -> DailyPlan:
    level = get_active_level(db, track)
    exclude_keys = _today_plan_keys(db, track, today)
    candidates = _merge_candidates(db, level, today, exclude_keys)
    assignments = _pack_assignments(candidates, float(minutes))
    plan = DailyPlan(
        date=today,
        track=track,
        session_number=_next_session_number(db, today, track),
        minutes_budget=minutes,
        assignments=assignments,
        completed_indices=[],
        status="active" if assignments else "completed",
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def _adjust_session_minutes(db: Session, plan: DailyPlan, new_minutes: int, track: str) -> DailyPlan:
    old_minutes = plan.minutes_budget
    old_assignments = list(plan.assignments or [])
    old_completed = list(plan.completed_indices or [])
    old_estimated = _plan_estimated_minutes(old_assignments)

    if new_minutes == old_minutes:
        return plan

    if new_minutes > old_minutes:
        delta = new_minutes - old_minutes
        extra = _pack_extension(old_assignments, db, track, float(delta))
        plan.assignments = old_assignments + extra
        plan.minutes_budget = new_minutes
    elif old_estimated > new_minutes:
        plan.minutes_budget = new_minutes
    else:
        level = get_active_level(db, track)
        today = date.today()
        exclude_keys: set[str] = set()
        for idx in old_completed:
            if 0 <= idx < len(old_assignments):
                exclude_keys.add(_assignment_key(old_assignments[idx]))
        candidates = _merge_candidates(db, level, today, exclude_keys)
        assignments = _pack_assignments(candidates, float(new_minutes))
        plan.assignments = assignments
        plan.completed_indices = _remap_completed_indices(
            old_assignments, assignments, old_completed,
        )
        plan.minutes_budget = new_minutes

    plan.calculated_at = datetime.utcnow()
    completed = set(plan.completed_indices or [])
    plan.status = (
        "completed"
        if plan.assignments and len(completed) >= len(plan.assignments)
        else "active"
    )
    db.commit()
    db.refresh(plan)
    return plan


def calculate_session(
    db: Session,
    minutes: int,
    track: str = "python",
    *,
    plan_id: int | None = None,
    new_session: bool = False,
) -> DailyPlan:
    track = track or "python"
    if track == "leetcodes":
        from .leetcodes_orientador import calculate_leetcodes_session
        return calculate_leetcodes_session(db, minutes, plan_id=plan_id, new_session=new_session)

    minutes = _clamp_minutes(minutes)
    today = date.today()

    if new_session:
        if get_active_plan(db, track):
            raise HTTPException(400, "Termina la sesión activa antes de añadir otra")
        return _create_new_session(db, minutes, track, today)

    if plan_id is not None:
        plan = _get_plan_today(db, plan_id, track)
        if plan.status == "completed":
            raise HTTPException(400, "La sesión ya está completada")
        return _adjust_session_minutes(db, plan, minutes, track)

    existing = get_active_plan(db, track)
    if existing:
        return _adjust_session_minutes(db, existing, minutes, track)

    return _create_new_session(db, minutes, track, today)


def build_session_plan(db: Session, minutes: int, track: str = "python") -> DailyPlan:
    return calculate_session(db, minutes, track)


def plan_to_dict(plan: DailyPlan) -> dict:
    assignments = []
    completed = set(plan.completed_indices or [])
    for i, a in enumerate(plan.assignments or []):
        assignments.append({**a, "index": i, "completed": i in completed})
    total_min = _plan_estimated_minutes(plan.assignments or [])
    return {
        "id": plan.id,
        "date": str(plan.date),
        "track": plan.track,
        "session_number": plan.session_number,
        "status": plan.status,
        "minutes_budget": plan.minutes_budget,
        "assignments": assignments,
        "completed_count": len(completed),
        "total_count": len(plan.assignments or []),
        "estimated_minutes": round(total_min, 1),
        "calculated_at": plan.calculated_at.isoformat() if plan.calculated_at else None,
        "config": orientador_config_for(plan.track),
    }


def get_active_plan_response(db: Session, track: str = "python") -> dict:
    track = track or "python"
    sessions = [plan_to_dict(p) for p in get_today_plans(db, track)]
    active = get_active_plan(db, track)
    base: dict = {
        "sessions": sessions,
        "active_plan_id": active.id if active else None,
        "config": orientador_config_for(track),
        "active": active is not None,
    }
    if active:
        base.update(plan_to_dict(active))
    return base


def _set_progress_detail(db: Session, level: str, set_number: int) -> dict | None:
    sp = _set_prog(db, level, set_number, create=False)
    if not sp:
        return None
    return {
        "status": sp.status,
        "attempts": sp.attempts,
        "solid_mastery": bool(sp.solid_mastery),
        "first_attempt_accuracy": sp.first_attempt_accuracy,
        "failure_flags": list(sp.failure_flags or []),
        "repeat_scheduled_for": str(sp.repeat_scheduled_for) if sp.repeat_scheduled_for else None,
        "repeat_completed_at": str(sp.repeat_completed_at) if sp.repeat_completed_at else None,
        "best_time_ms": sp.best_time_ms,
        "mastered_at": sp.mastered_at.isoformat() if sp.mastered_at else None,
    }


def _explain_assignment(db: Session, assignment: dict, today: date, locale: str = "en") -> dict:
    from .orientador_i18n import (
        assignment_title,
        explain_checkpoint_summary,
        explain_exam_summary,
        explain_set_summary,
    )

    reason = assignment.get("reason", "")
    atype = assignment.get("type", "")
    level = route_level(assignment.get("level", "a"))
    cfg = orientador_config()
    threshold = cfg["first_attempt_threshold"]

    if atype == "set":
        sn = assignment.get("set_number", 0)
        detail = _set_progress_detail(db, level, sn) or {}
        summary = explain_set_summary(
            reason,
            detail,
            threshold,
            lap=assignment.get("lap", 1),
            locale=locale,
        )
        return {
            "title": assignment_title(assignment, locale),
            "reason": reason,
            "summary": summary,
            "set_progress": detail,
        }

    if atype == "checkpoint":
        return {
            "title": assignment_title(assignment, locale),
            "reason": reason,
            "summary": explain_checkpoint_summary(locale),
            "set_progress": None,
        }

    if atype == "exam":
        return {
            "title": assignment_title(assignment, locale),
            "reason": reason,
            "summary": explain_exam_summary(locale),
            "set_progress": None,
        }

    return {
        "title": assignment_title(assignment, locale),
        "reason": reason,
        "summary": "",
        "set_progress": None,
    }


def get_orientador_insight(db: Session, track: str = "python", locale: str = "en") -> dict:
    track = track or "python"
    if track == "leetcodes":
        from .leetcodes_orientador import get_leetcodes_orientador_insight
        return get_leetcodes_orientador_insight(db, locale=locale)

    today = date.today()
    active_level = get_active_level(db, track)
    cfg = orientador_config()
    plan = get_active_plan(db, track)

    from .orientador_i18n import python_priority_rules

    set_history: list[dict] = []
    for s in level_sets(active_level):
        detail = _set_progress_detail(db, active_level, s.set_number)
        if not detail:
            continue
        if (
            detail["status"] == "mastered"
            or detail["attempts"] > 0
            or detail["failure_flags"]
            or detail["repeat_scheduled_for"]
        ):
            set_history.append({
                "level": active_level,
                "set_number": s.set_number,
                "display_set_number": display_set_number(active_level, s.set_number),
                "title": set_title(active_level, s.set_number, locale),
                **detail,
            })

    priority_rules = python_priority_rules(round(cfg["first_attempt_threshold"] * 100), locale)

    result: dict = {
        "date": str(today),
        "active_level": active_level,
        "config": cfg,
        "priority_rules": priority_rules,
        "set_history": set_history,
        "plan": None,
    }

    if plan:
        plan_dict = plan_to_dict(plan)
        explained = []
        for a in plan_dict["assignments"]:
            explained.append({
                **a,
                "explain": _explain_assignment(db, a, today, locale=locale),
            })
        result["plan"] = {**plan_dict, "assignments": explained}

    return result


def prepare_set_repeat(db: Session, level: str, set_number: int) -> None:
    sp = _set_prog(db, level, set_number, create=True)
    sp.completed_pages = []
    sp.accumulated_time_ms = 0
    sp.errors = 0
    sp.status = "current"
    db.commit()


def validate_assignment(
    db: Session,
    plan_id: int,
    index: int,
    *,
    assignment_type: str,
    level: str,
    set_number: int | None = None,
    block: str | None = None,
) -> dict:
    if dev_mode_enabled(db):
        return {"valid": True, "reason": "dev_mode"}

    plan = db.query(DailyPlan).filter_by(id=plan_id).first()
    if not plan or plan.date != date.today() or plan.status != "active":
        raise HTTPException(403, "No hay plan activo para hoy")

    assignments = plan.assignments or []
    if index < 0 or index >= len(assignments):
        raise HTTPException(404, "Asignacion no encontrada en el plan")

    expected = assignments[index]
    if expected.get("type") != assignment_type:
        raise HTTPException(403, "Tipo de asignación no coincide con el plan")
    if route_level(expected.get("level", "")) != route_level(level):
        raise HTTPException(403, "Nivel no coincide con el plan")

    if assignment_type == "set" and expected.get("set_number") != set_number:
        raise HTTPException(403, "Set no coincide con el plan")
    if assignment_type == "checkpoint" and expected.get("block", "").upper() != (block or "").upper():
        raise HTTPException(403, "Checkpoint no coincide con el plan")

    return {"valid": True, "assignment": expected}


def mark_assignment_done(db: Session, plan_id: int, index: int) -> None:
    plan = db.query(DailyPlan).filter_by(id=plan_id).first()
    if not plan:
        return
    completed = list(plan.completed_indices or [])
    if index not in completed:
        completed.append(index)
        plan.completed_indices = sorted(completed)
    if len(completed) >= len(plan.assignments or []):
        plan.status = "completed"
    else:
        plan.status = "active"
    db.commit()


def get_next_assignment(db: Session, plan_id: int) -> dict | None:
    plan = db.query(DailyPlan).filter_by(id=plan_id).first()
    if not plan or plan.date != date.today():
        return None
    completed = set(plan.completed_indices or [])
    for i, assignment in enumerate(plan.assignments or []):
        if i in completed:
            continue
        return {
            "plan_id": plan.id,
            "index": i,
            "assignment": {**assignment, "index": i},
        }
    return None


def get_assignment_session(db: Session, plan_id: int, index: int, *, locale: str = "en") -> dict:
    plan = db.query(DailyPlan).filter_by(id=plan_id).first()
    if not plan:
        raise HTTPException(404, "Plan no encontrado")
    assignments = plan.assignments or []
    if index < 0 or index >= len(assignments):
        raise HTTPException(404, "Asignacion no encontrada")

    assignment = assignments[index]
    atype = assignment.get("type")

    if atype == "leetcode_practice":
        from .leetcodes_orientador import get_leetcodes_assignment_session
        return get_leetcodes_assignment_session(db, plan_id, index, locale=locale)

    level = route_level(assignment["level"])

    base = {
        "plan_id": plan.id,
        "assignment_index": index,
        "assignment": {**assignment, "index": index},
    }

    if atype == "set":
        set_number = assignment["set_number"]
        reason = assignment.get("reason", "new")
        if reason in ("repeat", "pre_exam"):
            prepare_set_repeat(db, level, set_number)

        sp = _set_prog(db, level, set_number, create=True)
        curriculum = load_curriculum()
        pages = get_set_pages(curriculum, level, set_number)
        done = set(sp.completed_pages or [])

        s_def = next((s for s in level_sets(level) if s.set_number == set_number), None)
        block_letter = block_letter_for_set_num(level, set_number)
        bid = f"{normalize_level(level)}.{block_letter}"
        return {
            **base,
            "type": "set",
            "level": level,
            "set_number": set_number,
            "display_set_number": display_set_number(level, set_number),
            "set_title": set_title(level, set_number, locale),
            "block": block_letter,
            "block_title": block_title(bid, locale),
            "instruction": block_instruction(bid, locale),
            "standard_seconds": set_standard_seconds(level, set_number),
            "status": sp.status,
            "attempts": sp.attempts,
            "completed": len(done),
            "total": len(pages),
            "accumulated_time_ms": sp.accumulated_time_ms,
            "page_range": f"{pages[0].page}-{pages[-1].page}" if pages else "",
            "drills": [_page_payload(p, locale) for p in pages],
            "failure_flags": list(sp.failure_flags or []),
            "first_attempt_accuracy": sp.first_attempt_accuracy,
            "explain": _explain_assignment(db, assignment, date.today(), locale=locale),
        }

    if atype == "checkpoint":
        block = assignment["block"].upper()
        cp = get_checkpoint(db, level, block, locale=locale)
        return {**base, "type": "checkpoint", "level": level, "checkpoint": cp}

    if atype == "exam":
        exam = get_exam(db, level, locale=locale)
        return {**base, "type": "exam", "level": level, "exam": exam}

    raise HTTPException(400, "Tipo de asignación desconocido")
