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
    level_sets,
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
        "first_attempt_threshold": float(mastery.get("first_attempt_threshold", 0.90)),
        "pre_exam_enabled": bool(pre_exam.get("enabled", True)),
        "pre_exam_max_sets": int(pre_exam.get("max_sets", 3)),
    }


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
    level = route_level(level)
    rows = (
        db.query(SetProgress)
        .filter(
            SetProgress.level == level,
            SetProgress.repeat_scheduled_for.isnot(None),
            SetProgress.repeat_scheduled_for <= today,
        )
        .all()
    )
    out: list[dict] = []
    for sp in rows:
        if sp.repeat_completed_at == today:
            continue
        out.append({
            "type": "set",
            "level": level,
            "set_number": sp.set_number,
            "reason": "repeat",
            "estimated_minutes": _set_minutes(level, sp.set_number),
        })
    out.sort(key=lambda a: a["set_number"])
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
            out.append({
                "type": "set",
                "level": level,
                "set_number": set_number,
                "reason": "pre_exam",
                "estimated_minutes": _set_minutes(level, set_number),
            })
    return out


def _set_item(level: str, set_number: int, reason: str, *, lap: int = 0) -> dict:
    item = {
        "type": "set",
        "level": route_level(level),
        "set_number": set_number,
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
    """Keep completion state when the plan is rebuilt (indices shift)."""
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
    minutes = _clamp_minutes(minutes)
    today = date.today()

    if new_session:
        if get_active_plan(db, track):
            raise HTTPException(400, "Termina la sesion activa antes de anadir otra")
        return _create_new_session(db, minutes, track, today)

    if plan_id is not None:
        plan = _get_plan_today(db, plan_id, track)
        if plan.status == "completed":
            raise HTTPException(400, "La sesion ya esta completada")
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
        "config": orientador_config(),
    }


def get_active_plan_response(db: Session, track: str = "python") -> dict:
    track = track or "python"
    sessions = [plan_to_dict(p) for p in get_today_plans(db, track)]
    active = get_active_plan(db, track)
    base: dict = {
        "sessions": sessions,
        "active_plan_id": active.id if active else None,
        "config": orientador_config(),
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


def _explain_assignment(db: Session, assignment: dict, today: date) -> dict:
    reason = assignment.get("reason", "")
    atype = assignment.get("type", "")
    level = route_level(assignment.get("level", "a"))
    cfg = orientador_config()
    threshold = cfg["first_attempt_threshold"]

    if atype == "set":
        sn = assignment.get("set_number", 0)
        detail = _set_progress_detail(db, level, sn) or {}
        flags = detail.get("failure_flags") or []
        acc = detail.get("first_attempt_accuracy")
        acc_pct = round(acc * 100) if acc is not None else None

        if reason == "repeat":
            parts = [f"Repeticion programada para hoy ({detail.get('repeat_scheduled_for')})."]
            if "too_slow" in flags:
                parts.append("En el primer intento completo superaste el tiempo estandar del set.")
            if "low_accuracy" in flags:
                parts.append(
                    f"En el primer intento completo tu precision fue {acc_pct}% "
                    f"(umbral {round(threshold * 100)}%)."
                )
            if not flags:
                parts.append("Necesitas consolidar este set antes de seguir avanzando.")
            summary = " ".join(parts)
        elif reason == "pre_exam":
            summary = (
                "Repaso obligatorio antes del examen de nivel: este set ya lo dominaste "
                "pero no alcanzo dominio solido"
            )
            if acc_pct is not None:
                summary += f" (primer intento {acc_pct}%)."
            else:
                summary += "."
        elif reason == "repaso":
            if detail.get("solid_mastery"):
                summary = (
                    "Set dominado con buen desempeno. Se incluye como repaso para mantener "
                    "velocidad y precision."
                )
            else:
                summary = (
                    "Set dominado pero con historial de fallas o precision baja. "
                    "Conviene repasarlo antes de avanzar."
                )
                if acc_pct is not None:
                    summary += f" Primer intento: {acc_pct}%."
        elif reason == "repaso_extra":
            lap = assignment.get("lap", 1)
            summary = (
                f"Repaso adicional (vuelta {lap}) para aprovechar el tiempo libre de tu sesion. "
                "Mismo contenido ya dominado — refuerza memoria y velocidad."
            )
        elif reason == "new":
            summary = (
                "Es tu set actual en el nivel: el siguiente paso del camino que aun no has "
                "dominado por completo."
            )
        else:
            summary = "Actividad de set incluida en tu plan de hoy."

        return {
            "title": f"Set {sn} · Nivel {level.upper()}",
            "reason": reason,
            "summary": summary,
            "set_progress": detail,
        }

    if atype == "checkpoint":
        block = assignment.get("block", "")
        return {
            "title": f"Checkpoint Bloque {block} · Nivel {level.upper()}",
            "reason": reason,
            "summary": (
                "Completaste las paginas del bloque pero falta el checkpoint de LeetCode "
                "para desbloquear el siguiente bloque."
            ),
            "set_progress": None,
        }

    if atype == "exam":
        return {
            "title": f"Examen · Nivel {level.upper()}",
            "reason": reason,
            "summary": "Dominaste los 20 sets del nivel. Falta el examen de conclusion para pasar al siguiente nivel.",
            "set_progress": None,
        }

    return {"title": "Actividad", "reason": reason, "summary": "", "set_progress": None}


def get_orientador_insight(db: Session, track: str = "python") -> dict:
    today = date.today()
    active_level = get_active_level(db, track)
    cfg = orientador_config()
    plan = get_active_plan(db, track)

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
                "title": s.title,
                **detail,
            })

    priority_rules = [
        {
            "order": 1,
            "id": "repeat",
            "label": "Repeticiones vencidas",
            "description": (
                "Sets con repeticion programada para hoy (fallaste tiempo o precision "
                f"< {round(cfg['first_attempt_threshold'] * 100)}% en el primer intento)."
            ),
        },
        {
            "order": 2,
            "id": "pre_exam",
            "label": "Repaso pre-examen",
            "description": "Sets dominados pero no solidos, cuando el examen de nivel esta disponible.",
        },
        {
            "order": 3,
            "id": "new",
            "label": "Set nuevo",
            "description": "El siguiente set que aun no dominas en tu nivel activo.",
        },
        {
            "order": 4,
            "id": "repaso",
            "label": "Repaso de sets dominados",
            "description": "Sets ya aprobados que conviene mantener frescos.",
        },
        {
            "order": 5,
            "id": "repaso_extra",
            "label": "Repaso adicional",
            "description": "Si sobra tiempo en tu presupuesto, se repiten sets de repaso para llenar la sesion.",
        },
    ]

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
                "explain": _explain_assignment(db, a, today),
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
        raise HTTPException(403, "Tipo de asignacion no coincide con el plan")
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


def get_assignment_session(db: Session, plan_id: int, index: int) -> dict:
    plan = db.query(DailyPlan).filter_by(id=plan_id).first()
    if not plan:
        raise HTTPException(404, "Plan no encontrado")
    assignments = plan.assignments or []
    if index < 0 or index >= len(assignments):
        raise HTTPException(404, "Asignacion no encontrada")

    assignment = assignments[index]
    atype = assignment.get("type")
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
            "set_title": s_def.title if s_def else set_title(level, set_number),
            "block": block_letter,
            "block_title": block_title(bid),
            "instruction": block_instruction(bid),
            "standard_seconds": set_standard_seconds(level, set_number),
            "status": sp.status,
            "attempts": sp.attempts,
            "completed": len(done),
            "total": len(pages),
            "accumulated_time_ms": sp.accumulated_time_ms,
            "page_range": f"{pages[0].page}-{pages[-1].page}" if pages else "",
            "drills": [_page_payload(p) for p in pages],
        }

    if atype == "checkpoint":
        block = assignment["block"].upper()
        cp = get_checkpoint(db, level, block)
        return {**base, "type": "checkpoint", "level": level, "checkpoint": cp}

    if atype == "exam":
        exam = get_exam(db, level)
        return {**base, "type": "exam", "level": level, "exam": exam}

    raise HTTPException(400, "Tipo de asignacion desconocido")
