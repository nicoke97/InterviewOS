"""LeetCodes interview practice track — roadmap and free practice."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.orm import Session

from .content_i18n import localize_starter_code
from .content_loader import guide_fields, load_curriculum, problem_description
from .executor import run_leetcode_code
from .leetcodes_csharp import csharp_spec, normalize_exec_language
from .models import Attempt, LeetCodeProgress

from .i18n import tier_label as i18n_tier_label

LEETCODES_TRACK = "leetcodes"


def _orientador_cfg() -> dict:
    return load_curriculum().leetcodes_schedule.orientador or {}


def _problem_progress(db: Session, problem_id: str) -> LeetCodeProgress | None:
    return (
        db.query(LeetCodeProgress)
        .filter_by(problem_id=problem_id, track=LEETCODES_TRACK)
        .first()
    )


def _get_or_create_progress(db: Session, problem_id: str) -> LeetCodeProgress:
    prog = _problem_progress(db, problem_id)
    if prog:
        return prog
    curriculum = load_curriculum()
    p = curriculum.leetcodes.get(problem_id)
    prog = LeetCodeProgress(
        problem_id=problem_id,
        level="lc",
        track=LEETCODES_TRACK,
        topic=p.topic if p else "",
        global_order=p.global_order if p else 0,
    )
    db.add(prog)
    db.flush()
    return prog


def _problem_payload(db: Session, p) -> dict:
    prog = _problem_progress(db, p.id)
    tier_passed = prog.tier_passed if prog else 0
    return {
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "topic": p.topic,
        "difficulty": p.difficulty,
        "global_order": p.global_order,
        "leetcode_ref": p.leetcode_ref,
        "tier_passed": tier_passed,
        "solid_mastery": bool(prog and prog.solid_mastery),
        "attempts": prog.attempts if prog else 0,
        "current_tier": min(3, tier_passed + 1) if not (prog and prog.solid_mastery) else 3,
        "last_practiced_at": prog.last_practiced_at.isoformat() if prog and prog.last_practiced_at else None,
    }


def leetcodes_roadmap(db: Session) -> dict:
    curriculum = load_curriculum()
    schedule = curriculum.leetcodes_schedule
    topics_out = []
    total = 0
    mastered = 0
    started = 0

    for topic in schedule.topics:
        problems = []
        for pid in topic.get("problems", []):
            p = curriculum.leetcodes.get(pid)
            if not p:
                continue
            item = _problem_payload(db, p)
            problems.append(item)
            total += 1
            if item["solid_mastery"]:
                mastered += 1
            if item["tier_passed"] > 0:
                started += 1
        topics_out.append({
            "id": topic.get("id", ""),
            "title": topic.get("title", ""),
            "problems": problems,
        })

    return {
        "track": LEETCODES_TRACK,
        "topics": topics_out,
        "total": total,
        "mastered_count": mastered,
        "started_count": started,
        "orientador_config": _orientador_cfg(),
    }


def _language_fields(p, tier_data: dict, tier: int, language: str | None, locale: str) -> tuple[str, str, str, str]:
    lang = normalize_exec_language(language)
    if lang == "csharp":
        spec = csharp_spec(p.id, tier)
        if spec:
            return lang, spec["fn_name"], spec["starter_code"], spec["solution_code"]
        lang = "python"
    starter = localize_starter_code(tier_data.get("starter_code", ""), locale)
    return lang, p.fn_name, starter, p.solution_code


def get_leetcodes_problem_detail(
    problem_id: str,
    tier: int = 1,
    *,
    locale: str = "en",
    language: str | None = None,
) -> dict:
    curriculum = load_curriculum()
    p = curriculum.leetcodes.get(problem_id)
    if not p:
        return {}
    tier_data = p.tiers.get(tier, {}) or p.tiers.get(1, {})
    guide = guide_fields(p, tier_data, tier, locale)
    explain_checklist = guide.pop("explain_checklist", tier_data.get("explain_checklist", []))
    narration_prompts = guide.pop("narration_prompts", tier_data.get("narration_prompts", []))
    lang, fn_name, starter, solution = _language_fields(p, tier_data, tier, language, locale)
    if guide.get("solution_code"):
        guide["solution_code"] = solution
    return {
        "id": p.id,
        "title": p.title,
        "description": problem_description(p, locale),
        "tier": tier,
        "tier_label": i18n_tier_label(tier, locale),
        "fn_name": fn_name,
        "language": lang,
        "topic": p.topic,
        "difficulty": p.difficulty,
        "leetcode_ref": p.leetcode_ref,
        "starter_code": starter,
        "explain_checklist": explain_checklist,
        "narration_prompts": narration_prompts,
        "test_cases_preview": p.test_cases[:2],
        **guide,
    }


def submit_practice(
    db: Session,
    problem_id: str,
    tier: int,
    code: str,
    *,
    locale: str = "en",
    language: str | None = None,
) -> dict:
    curriculum = load_curriculum()
    p = curriculum.leetcodes.get(problem_id)
    if not p:
        return {"passed": False, "error": "Problema no encontrado"}

    tier = max(1, min(3, tier))
    lang = normalize_exec_language(language)
    fn_name = p.fn_name
    if lang == "csharp":
        spec = csharp_spec(p.id, tier)
        if spec:
            fn_name = spec["fn_name"]
        else:
            lang = "python"
    res = run_leetcode_code(code, p.test_cases, fn_name, language=lang)
    passed = bool(res.get("passed"))

    prog = _get_or_create_progress(db, problem_id)
    prog.attempts = (prog.attempts or 0) + 1
    prog.last_practiced_at = datetime.utcnow()
    if passed:
        prog.tier_passed = max(prog.tier_passed or 0, tier)
        if tier >= 3:
            prog.solid_mastery = True

    today = date.today()
    db.add(Attempt(
        exercise_id=problem_id,
        exercise_type="leetcode",
        tier=tier,
        hints_used=0,
        passed=passed,
        code_snapshot=code,
        attempt_date=today,
    ))
    db.commit()

    next_tier = None
    if passed:
        if tier < 3:
            next_tier = tier + 1
        elif not prog.solid_mastery:
            next_tier = 3

    return {
        "passed": passed,
        "tier_passed": prog.tier_passed,
        "solid_mastery": prog.solid_mastery,
        "attempts": prog.attempts,
        "next_tier_suggestion": next_tier,
        "tier_label": i18n_tier_label(tier, locale),
        "result": res,
    }


def ordered_leetcodes_problems() -> list:
    curriculum = load_curriculum()
    return sorted(curriculum.leetcodes.values(), key=lambda p: p.global_order)


def build_tier_steps(tier_passed: int, solid_mastery: bool, recent_fail_tier: int | None, budget_steps: int) -> list[int]:
    """Build tier attempt sequence for orientador assignment."""
    if solid_mastery:
        steps = [3]
    elif tier_passed <= 0:
        if recent_fail_tier == 1:
            steps = [1, 1, 2, 3]
        else:
            steps = [1, 2, 3]
    elif tier_passed == 1:
        steps = [2, 3]
    elif tier_passed == 2:
        steps = [3]
    else:
        steps = [1, 2, 3]
    return steps[: max(1, budget_steps)]


def estimate_problem_minutes(steps: list[int]) -> float:
    cfg = _orientador_cfg()
    base = float(cfg.get("minutes_per_problem_base", 3))
    per_tier = float(cfg.get("minutes_per_tier_attempt", 5))
    return base + len(steps) * per_tier
