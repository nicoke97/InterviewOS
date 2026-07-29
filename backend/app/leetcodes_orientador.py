"""Orientador for LeetCodes interview practice track."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .content_loader import load_curriculum, problem_description
from .i18n import DEFAULT, tier_label
from .leetcodes_practice import (
    LEETCODES_TRACK,
    build_tier_steps,
    estimate_problem_minutes,
    ordered_leetcodes_problems,
    submit_practice,
)
from .models import Attempt, DailyPlan, LeetCodeProgress
from .orientador import (
    _get_plan_today,
    _next_session_number,
    _plan_estimated_minutes,
    _remap_completed_indices,
    _today_plan_keys,
    get_active_plan,
    get_today_plans,
    mark_assignment_done,
    plan_to_dict,
)

TRACK = LEETCODES_TRACK


def _cfg() -> dict:
    return load_curriculum().leetcodes_schedule.orientador or {}


def _clamp_session_minutes(minutes: int) -> int:
    cfg = _cfg()
    lo = int(cfg.get("min_minutes", 30))
    hi = int(cfg.get("max_minutes", 90))
    return max(lo, min(hi, minutes))


def _focus_topics() -> list[str]:
    topics = _cfg().get("focus_topics") or ["arrays_hashing", "two_pointers"]
    return [str(t) for t in topics]


def _focus_complete(progress: dict[str, LeetCodeProgress]) -> bool:
    for p in ordered_leetcodes_problems():
        if p.topic not in _focus_topics():
            continue
        if (p.difficulty or "").lower() == "hard":
            continue
        prog = progress.get(p.id)
        if not prog or not prog.solid_mastery:
            return False
    return True


def _steps_per_problem() -> int:
    return max(1, int(_cfg().get("steps_per_problem", 1)))


def _allows_new_problem(p, progress: dict[str, LeetCodeProgress], focus_done: bool) -> bool:
    difficulty = (p.difficulty or "").lower()
    skip_hard = bool(_cfg().get("skip_hard_until_focus_done", True))
    if skip_hard and difficulty == "hard" and not focus_done:
        return False
    if not focus_done and p.topic not in _focus_topics():
        return False
    return True


def _progress_map(db: Session) -> dict[str, LeetCodeProgress]:
    rows = db.query(LeetCodeProgress).filter_by(track=TRACK).all()
    return {r.problem_id: r for r in rows}


def _recent_fail_tier(db: Session, problem_id: str) -> int | None:
    row = (
        db.query(Attempt)
        .filter_by(exercise_id=problem_id, exercise_type="leetcode", passed=False)
        .order_by(Attempt.created_at.desc())
        .first()
    )
    return row.tier if row else None


def _assignment_key(a: dict) -> str:
    return f"lc:{a.get('problem_id', '')}"


def _problem_item(problem_id: str, reason: str, steps: list[int]) -> dict:
    curriculum = load_curriculum()
    p = curriculum.leetcodes.get(problem_id)
    return {
        "type": "leetcode_practice",
        "problem_id": problem_id,
        "title": p.title if p else problem_id,
        "topic": p.topic if p else "",
        "leetcode_ref": p.leetcode_ref if p else 0,
        "reason": reason,
        "steps": [{"tier": t, "label": tier_label(t, DEFAULT)} for t in steps],
        "estimated_minutes": estimate_problem_minutes(steps),
    }


def _due_repeats(db: Session, progress: dict[str, LeetCodeProgress]) -> list[dict]:
    out = []
    for p in ordered_leetcodes_problems():
        prog = progress.get(p.id)
        if not prog or prog.solid_mastery:
            continue
        if prog.tier_passed >= 3:
            continue
        fail = _recent_fail_tier(db, p.id)
        if fail or (prog.attempts and prog.attempts > 0 and prog.tier_passed < 3):
            steps = build_tier_steps(prog.tier_passed, False, fail, _steps_per_problem())
            out.append(_problem_item(p.id, "repeat", steps))
    return out


def _new_problems(db: Session, progress: dict[str, LeetCodeProgress]) -> list[dict]:
    focus_done = _focus_complete(progress)
    out = []
    for p in ordered_leetcodes_problems():
        if not _allows_new_problem(p, progress, focus_done):
            continue
        prog = progress.get(p.id)
        if prog and (prog.tier_passed > 0 or prog.attempts > 0):
            continue
        steps = build_tier_steps(0, False, None, _steps_per_problem())
        out.append(_problem_item(p.id, "new", steps))
        break
    return out


def _repaso_problems(db: Session, progress: dict[str, LeetCodeProgress]) -> list[dict]:
    repaso_days = int(_cfg().get("repaso_days", 7))
    cutoff = date.today() - timedelta(days=repaso_days)
    out = []
    for p in ordered_leetcodes_problems():
        prog = progress.get(p.id)
        if not prog or not prog.solid_mastery:
            continue
        if prog.last_practiced_at and prog.last_practiced_at.date() >= cutoff:
            continue
        out.append(_problem_item(p.id, "repaso", [3]))
    return out


def _merge_candidates(db: Session, exclude_keys: set[str]) -> list[dict]:
    progress = _progress_map(db)
    merged: list[dict] = []
    seen: set[str] = set()

    def add(items: list[dict]) -> None:
        for item in items:
            key = _assignment_key(item)
            if key in exclude_keys or key in seen:
                continue
            seen.add(key)
            merged.append(item)

    add(_due_repeats(db, progress))
    add(_new_problems(db, progress))
    add(_repaso_problems(db, progress))

    if not merged:
        for p in ordered_leetcodes_problems():
            prog = progress.get(p.id)
            if prog and prog.solid_mastery:
                item = _problem_item(p.id, "repaso_extra", [3])
                key = _assignment_key(item)
                if key not in exclude_keys:
                    merged.append(item)
                    break
    return merged


def _pack_assignments(candidates: list[dict], budget: float) -> list[dict]:
    max_problems = int(_cfg().get("max_problems_per_session", 1))
    out: list[dict] = []
    used = 0.0
    for item in candidates:
        if len(out) >= max_problems:
            break
        est = float(item.get("estimated_minutes", 10))
        if out and used + est > budget:
            break
        if not out and est > budget:
            # shrink steps for single problem
            steps = [s["tier"] for s in item.get("steps", [])]
            while len(steps) > 1 and estimate_problem_minutes(steps) > budget:
                steps = steps[:-1]
            item = {**item, "steps": [{"tier": t, "label": tier_label(t, DEFAULT)} for t in steps],
                    "estimated_minutes": estimate_problem_minutes(steps)}
            est = item["estimated_minutes"]
        if est <= budget - used or not out:
            out.append(item)
            used += est
    return out


def calculate_leetcodes_session(
    db: Session,
    minutes: int,
    plan_id: int | None = None,
    new_session: bool = False,
) -> DailyPlan:
    minutes = _clamp_session_minutes(minutes)
    today = date.today()

    if new_session and not plan_id:
        if get_active_plan(db, TRACK):
            raise HTTPException(400, "Ya hay una sesion LeetCodes activa hoy")
        return _create_plan(db, minutes, today)

    if plan_id is not None:
        plan = _get_plan_today(db, plan_id, TRACK)
        if new_session:
            return _create_plan(db, minutes, today)
        return _adjust_plan(db, plan, minutes)

    existing = get_active_plan(db, TRACK)
    if existing:
        return _adjust_plan(db, existing, minutes)
    return _create_plan(db, minutes, today)


def _create_plan(db: Session, minutes: int, today: date) -> DailyPlan:
    exclude = _today_plan_keys(db, TRACK, today)
    candidates = _merge_candidates(db, exclude)
    assignments = _pack_assignments(candidates, float(minutes))
    plan = DailyPlan(
        date=today,
        track=TRACK,
        session_number=_next_session_number(db, today, TRACK),
        minutes_budget=minutes,
        assignments=assignments,
        completed_indices=[],
        status="active" if assignments else "completed",
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def _trim_to_max_problems(assignments: list[dict], completed: list[int]) -> tuple[list[dict], list[int]]:
    max_problems = int(_cfg().get("max_problems_per_session", 1))
    if len(assignments) <= max_problems:
        return assignments, completed
    completed_set = set(completed)
    keep: list[int] = [i for i, _ in enumerate(assignments) if i in completed_set]
    for i in range(len(assignments)):
        if i not in keep:
            keep.append(i)
        if len(keep) >= max_problems:
            break
    keep = sorted(keep[:max_problems])
    remap = {old: new for new, old in enumerate(keep)}
    return [assignments[i] for i in keep], sorted(remap[i] for i in completed if i in remap)


def _adjust_plan(db: Session, plan: DailyPlan, new_minutes: int) -> DailyPlan:
    old_assignments, old_completed = _trim_to_max_problems(
        list(plan.assignments or []),
        list(plan.completed_indices or []),
    )
    old_minutes = plan.minutes_budget or new_minutes
    delta = float(new_minutes) - float(old_minutes)

    if delta > 0:
        max_problems = int(_cfg().get("max_problems_per_session", 1))
        remaining = max(0, max_problems - len(old_assignments))
        extra: list[dict] = []
        if remaining:
            exclude = _today_plan_keys(db, TRACK, plan.date)
            for a in old_assignments:
                exclude.add(_assignment_key(a))
            extra = _pack_assignments(_merge_candidates(db, exclude), delta)[:remaining]
        new_assignments = old_assignments + extra
    else:
        new_assignments = old_assignments

    plan.minutes_budget = new_minutes
    plan.assignments = new_assignments
    plan.completed_indices = _remap_completed_indices(old_assignments, new_assignments, old_completed)
    if len(plan.completed_indices or []) >= len(new_assignments):
        plan.status = "completed"
    else:
        plan.status = "active"
    db.commit()
    db.refresh(plan)
    return plan


def get_leetcodes_assignment_session(db: Session, plan_id: int, index: int, *, locale: str = "en") -> dict:
    plan = db.query(DailyPlan).filter_by(id=plan_id).first()
    if not plan or plan.track != TRACK:
        raise HTTPException(404, "Plan LeetCodes no encontrado")
    assignments = plan.assignments or []
    if index < 0 or index >= len(assignments):
        raise HTTPException(404, "Asignacion no encontrada")

    assignment = assignments[index]
    problem_id = assignment["problem_id"]
    steps = assignment.get("steps", [])
    completed_steps = assignment.get("completed_steps", [])

    step_index = len(completed_steps)
    current_step = steps[step_index] if step_index < len(steps) else None

    curriculum = load_curriculum()
    p = curriculum.leetcodes.get(problem_id)
    prog = db.query(LeetCodeProgress).filter_by(problem_id=problem_id, track=TRACK).first()

    return {
        "type": "leetcode_practice",
        "plan_id": plan.id,
        "assignment_index": index,
        "assignment": {**assignment, "index": index},
        "problem_id": problem_id,
        "title": p.title if p else problem_id,
        "description": problem_description(p, locale) if p else "",
        "topic": p.topic if p else "",
        "leetcode_ref": p.leetcode_ref if p else 0,
        "tier_passed": prog.tier_passed if prog else 0,
        "solid_mastery": bool(prog and prog.solid_mastery),
        "steps": steps,
        "step_index": step_index,
        "total_steps": len(steps),
        "current_step": current_step,
        "current_tier": current_step["tier"] if current_step else 1,
        "hint_lock_minutes": int(_cfg().get("hint_lock_minutes", 25)),
        "explain": {
            "summary": _explain_assignment(assignment, locale),
            "reason": assignment.get("reason", ""),
        },
    }


def _explain_assignment(assignment: dict, locale: str = "en") -> str:
    reason = assignment.get("reason", "new")
    if locale == "es":
        labels = {
            "new": "Nuevo problema en la secuencia de entrevista.",
            "repeat": "Repeticion para consolidar antes de subir de tier.",
            "repaso": "Repaso de memoria — resolver de nuevo sin hints.",
            "repaso_extra": "Repaso adicional del catalogo.",
        }
        return labels.get(reason, "Practica LeetCode guiada.")
    labels = {
        "new": "New problem in the interview sequence.",
        "repeat": "Repeat to consolidate before advancing tier.",
        "repaso": "Memory review — solve again without hints.",
        "repaso_extra": "Extra catalog review.",
    }
    return labels.get(reason, "Guided LeetCode practice.")


def submit_guided_step(
    db: Session,
    plan_id: int,
    index: int,
    tier: int,
    code: str,
    language: str | None = None,
) -> dict:
    plan = db.query(DailyPlan).filter_by(id=plan_id).first()
    if not plan or plan.track != TRACK:
        raise HTTPException(404, "Plan no encontrado")
    assignments = list(plan.assignments or [])
    if index < 0 or index >= len(assignments):
        raise HTTPException(404, "Asignacion no encontrada")

    assignment = dict(assignments[index])
    steps = assignment.get("steps", [])
    completed = list(assignment.get("completed_steps", []))
    step_index = len(completed)
    if step_index >= len(steps):
        raise HTTPException(400, "Asignacion ya completada")

    expected_tier = steps[step_index]["tier"]
    if tier != expected_tier:
        tier = expected_tier

    result = submit_practice(db, assignment["problem_id"], tier, code, language=language)
    if result.get("passed"):
        completed.append(step_index)
        assignment["completed_steps"] = completed
        assignments[index] = assignment
        plan.assignments = assignments

        if len(completed) >= len(steps):
            completed_indices = list(plan.completed_indices or [])
            if index not in completed_indices:
                completed_indices.append(index)
                plan.completed_indices = sorted(completed_indices)
            if len(completed_indices) >= len(assignments):
                plan.status = "completed"
        db.commit()

    from .orientador import get_next_assignment
    nxt = get_next_assignment(db, plan_id)
    result["step_complete"] = result.get("passed", False)
    result["assignment_complete"] = len(completed) >= len(steps)
    result["next_assignment"] = nxt
    result["session_complete"] = plan.status == "completed"
    return result


def get_leetcodes_orientador_insight(db: Session, locale: str = "en") -> dict:
    from .leetcodes_practice import leetcodes_roadmap
    from .orientador_i18n import leetcodes_priority_rules

    today = date.today()
    plan = get_active_plan(db, TRACK)
    roadmap = leetcodes_roadmap(db)
    cfg = _cfg()

    priority_rules = leetcodes_priority_rules(locale)

    problem_history = []
    for topic in roadmap.get("topics", []):
        for p in topic.get("problems", []):
            if p.get("tier_passed", 0) > 0 or p.get("attempts", 0) > 0:
                problem_history.append(p)

    result = {
        "date": str(today),
        "active_level": "lc",
        "track": TRACK,
        "config": cfg,
        "priority_rules": priority_rules,
        "set_history": problem_history,
        "problem_history": problem_history,
        "roadmap_summary": {
            "total": roadmap.get("total", 0),
            "mastered_count": roadmap.get("mastered_count", 0),
            "started_count": roadmap.get("started_count", 0),
        },
        "plan": None,
    }
    if plan:
        plan_dict = plan_to_dict(plan)
        explained = []
        for a in plan_dict.get("assignments") or []:
            explained.append({
                **a,
                "explain": {
                    "title": a.get("title") or a.get("problem_id") or "",
                    "reason": a.get("reason", ""),
                    "summary": _explain_assignment(a, locale),
                    "set_progress": None,
                },
            })
        plan_dict["assignments"] = explained
        result["plan"] = plan_dict
    return result
