"""Kumon set-based mastery engine.

Replaces the old calendar/7-day-phase model. Progression is by *domain*:

- A level has 20 sets of 10 pages, grouped into 4 blocks of 50 pages.
- You advance to the next set only when you complete all 10 pages of the
  current set (self-correction allowed) AND your accumulated time is within
  the set's standard time. Otherwise the set "repeats" (page progress resets).
- After every block (50 pages) there is a LeetCode checkpoint that must be
  passed to unlock the next block.
- At page 200 there is a level completion exam (LeetCode + interview). Passing
  it unlocks the next level.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from .content_loader import (
    Curriculum,
    get_set_pages,
    interview_payload,
    load_curriculum,
    page_payload,
    problem_description,
    problem_title,
)
from .executor import run_kumon_code, run_leetcode_code
from .kumon_hierarchy import (
    block_instruction,
    block_title,
    checkpoint_for_block,
    core_level_sets,
    get_block_def,
    is_extra_block,
    is_extra_set,
    language_for_level,
    level_checkpoints,
    level_exam,
    level_sets,
    level_track,
    list_route_levels,
    normalize_level,
    route_level,
    display_set_number,
    set_count,
    set_standard_seconds,
    set_title,
)
from .models import (
    AppSettings,
    Attempt,
    CheckpointProgress,
    DrillMastery,
    InterviewProgress,
    LeetCodeProgress,
    LevelExamProgress,
    SetProgress,
)

BLOCK_LETTERS = ["A", "B", "C", "D"]
SETS_PER_BLOCK = 5


def _time_tolerance() -> float:
    try:
        prog = load_curriculum().progression or {}
        return float((prog.get("mastery") or {}).get("time_tolerance", 1.0))
    except Exception:
        return 1.0


def _first_attempt_threshold() -> float:
    try:
        prog = load_curriculum().progression or {}
        return float((prog.get("mastery") or {}).get("first_attempt_threshold", 0.90))
    except Exception:
        return 0.90


def _spaced_repeat_days() -> int:
    try:
        prog = load_curriculum().progression or {}
        orientador = prog.get("orientador") or {}
        repeat = prog.get("repeat") or {}
        return int(orientador.get("spaced_repeat_days") or repeat.get("spaced_repeat_days") or 1)
    except Exception:
        return 1


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def dev_mode_enabled(db: Session) -> bool:
    s = db.query(AppSettings).filter_by(key="dev_mode").first()
    return s.value == "true" if s else False


def _level_block_letters(level: str) -> list[str]:
    seen: list[str] = []
    for s in level_sets(level):
        if s.block_letter not in seen:
            seen.append(s.block_letter)
    return seen


def _block_of_set(level: str, set_number: int) -> str:
    from .kumon_hierarchy import get_set_def
    sd = get_set_def(level, set_number)
    return sd.block_letter if sd else "A"


def _first_set_of_block(level: str, block_letter: str) -> int | None:
    nums = [s.set_number for s in level_sets(level) if s.block_letter == block_letter]
    return min(nums) if nums else None


def block_letter_for_set_num(level: str, set_number: int) -> str:
    return _block_of_set(level, set_number)


def _set_prog(db: Session, level: str, set_number: int, create: bool = True) -> SetProgress | None:
    level = route_level(level)
    sp = db.query(SetProgress).filter_by(level=level, set_number=set_number).first()
    if not sp and create:
        sp = SetProgress(
            track=level_track(level),
            level=level,
            set_number=set_number,
            status="current",
            completed_pages=[],
        )
        db.add(sp)
        db.commit()
        db.refresh(sp)
    return sp


def _checkpoint_prog(db: Session, level: str, block_letter: str, create: bool = True) -> CheckpointProgress | None:
    level = route_level(level)
    cp = db.query(CheckpointProgress).filter_by(level=level, block_letter=block_letter).first()
    if not cp and create:
        cp = CheckpointProgress(level=level, block_letter=block_letter, passed=False)
        db.add(cp)
        db.commit()
        db.refresh(cp)
    return cp


def _exam_prog(db: Session, level: str, create: bool = True) -> LevelExamProgress | None:
    level = route_level(level)
    ep = db.query(LevelExamProgress).filter_by(level=level).first()
    if not ep and create:
        ep = LevelExamProgress(level=level, passed=False)
        db.add(ep)
        db.commit()
        db.refresh(ep)
    return ep


def set_mastered(db: Session, level: str, set_number: int) -> bool:
    sp = _set_prog(db, level, set_number, create=False)
    return bool(sp and sp.status == "mastered")


def set_unlocks_progress(db: Session, level: str, set_number: int) -> bool:
    """True if the set still counts toward unlocking later levels.

    A return-exam remaster temporarily sets status to repeating, but the
    learner already passed this set once (`mastered_at`), so later levels
    must stay open.
    """
    if set_mastered(db, level, set_number):
        return True
    sp = _set_prog(db, level, set_number, create=False)
    return bool(sp and sp.mastered_at)


def block_mastered(db: Session, level: str, block_letter: str) -> bool:
    block_letter = block_letter.upper()
    sets = [s for s in level_sets(level) if s.block_letter == block_letter]
    if not sets:
        return False
    return all(set_mastered(db, level, s.set_number) for s in sets)


def checkpoint_passed(db: Session, level: str, block_letter: str) -> bool:
    if dev_mode_enabled(db):
        return True
    cp = _checkpoint_prog(db, level, block_letter, create=False)
    return bool(cp and cp.passed)


def exam_passed(db: Session, level: str) -> bool:
    ep = _exam_prog(db, level, create=False)
    return bool(ep and ep.passed)


def _level_complete(db: Session, level: str) -> bool:
    if not all(set_unlocks_progress(db, level, s.set_number) for s in core_level_sets(level)):
        return False
    cps = level_checkpoints(level)
    if not all(checkpoint_passed(db, level, bl) for bl, ids in cps.items() if ids):
        return False
    if _has_exam(level) and not exam_passed(db, level):
        return False
    return True


def level_unlocked(db: Session, level: str) -> bool:
    if dev_mode_enabled(db):
        return True
    track = level_track(level)
    ordered = list_route_levels(track)
    rl = route_level(level)
    if rl not in ordered:
        return False
    idx = ordered.index(rl)
    if idx == 0:
        return True
    return _level_complete(db, ordered[idx - 1])


# ---------------------------------------------------------------------------
# progression pointer
# ---------------------------------------------------------------------------

def _has_exam(level: str) -> bool:
    cfg = level_exam(level)
    return bool(cfg.get("leetcode") or cfg.get("interview"))


def _exam_available(db: Session, level: str) -> bool:
    if dev_mode_enabled(db):
        return True
    if not all(set_mastered(db, level, s.set_number) for s in core_level_sets(level)):
        return False
    cps = level_checkpoints(level)
    return all(checkpoint_passed(db, level, bl) for bl, ids in cps.items() if ids)


def current_target(db: Session, level: str) -> dict:
    """What the learner should do next in this level (data-driven by blocks)."""
    if not level_unlocked(db, level):
        return {"type": "locked"}

    block_letters = _level_block_letters(level)
    first_block = block_letters[0] if block_letters else None
    checkpoints_cfg = level_checkpoints(level)
    sets = sorted(core_level_sets(level), key=lambda s: s.set_number)

    for s in sets:
        bl = s.block_letter
        if bl != first_block and _first_set_of_block(level, bl) == s.set_number:
            prev_idx = block_letters.index(bl) - 1
            prev_letter = block_letters[prev_idx]
            if checkpoints_cfg.get(prev_letter) and not checkpoint_passed(db, level, prev_letter):
                return {"type": "checkpoint", "block": prev_letter}
        if not set_mastered(db, level, s.set_number):
            sp = _set_prog(db, level, s.set_number, create=False)
            return {
                "type": "set",
                "set_number": s.set_number,
                "display_set_number": display_set_number(level, s.set_number),
                "repeating": bool(sp and sp.status == "repeating"),
            }

    # all sets mastered → remaining checkpoints then exam
    for bl in block_letters:
        if is_extra_block(level, bl):
            continue
        if checkpoints_cfg.get(bl) and not checkpoint_passed(db, level, bl):
            return {"type": "checkpoint", "block": bl}
    if _has_exam(level) and not exam_passed(db, level):
        return {"type": "exam"}
    return {"type": "complete"}


# ---------------------------------------------------------------------------
# roadmap (the "see all 200" view)
# ---------------------------------------------------------------------------

def _set_status(db: Session, level: str, set_number: int, target: dict) -> str:
    if is_extra_set(level, set_number):
        sp = _set_prog(db, level, set_number, create=False)
        if sp and sp.status == "mastered":
            return "mastered"
        return "extra"
    sp = _set_prog(db, level, set_number, create=False)
    today = date.today()
    if sp and sp.status == "mastered":
        return "mastered"
    if sp and sp.repeat_scheduled_for and sp.repeat_scheduled_for <= today:
        if not sp.repeat_completed_at or sp.repeat_completed_at < today:
            return "repeating"
    if target.get("type") == "set" and target.get("set_number") == set_number:
        return "repeating" if (sp and sp.status == "repeating") else "current"
    return "locked"


def level_roadmap(db: Session, level: str, locale: str = "en") -> dict:
    level = route_level(level)
    sets = level_sets(level)
    target = current_target(db, level)
    curriculum = load_curriculum()

    set_rows = []
    for s in sets:
        sp = _set_prog(db, level, s.set_number, create=False)
        total = len(get_set_pages(curriculum, level, s.set_number)) or 10
        set_rows.append({
            "set_number": s.set_number,
            "display_set_number": display_set_number(level, s.set_number),
            "block": s.block_letter,
            "title": set_title(level, s.set_number, locale),
            "page_start": s.page_start,
            "page_end": s.page_end,
            "standard_seconds": s.standard_seconds,
            "status": _set_status(db, level, s.set_number, target),
            "attempts": sp.attempts if sp else 0,
            "completed": len(sp.completed_pages or []) if sp else 0,
            "total": total,
            "best_time_ms": sp.best_time_ms if sp else None,
            "solid_mastery": bool(sp and sp.solid_mastery),
            "repeat_scheduled_for": str(sp.repeat_scheduled_for) if sp and sp.repeat_scheduled_for else None,
            "first_attempt_accuracy": sp.first_attempt_accuracy if sp else None,
        })

    blocks = []
    checkpoints = level_checkpoints(level)
    for letter in _level_block_letters(level):
        bid = f"{normalize_level(level)}.{letter}"
        bdef = get_block_def(bid)
        cp = _checkpoint_prog(db, level, letter, create=False)
        block_set_nums = [s.set_number for s in sets if s.block_letter == letter]
        block_set_count = len(block_set_nums)
        has_cp = bool(checkpoints.get(letter))
        blocks.append({
            "letter": letter,
            "title": block_title(bid, locale),
            "instruction": block_instruction(bid, locale),
            "set_start": 1 if block_set_count else 0,
            "set_end": block_set_count,
            "page_start": bdef.page_start if bdef else 0,
            "page_end": bdef.page_end if bdef else 0,
            "extra": is_extra_block(level, letter),
            "checkpoint": {
                "problems": checkpoints.get(letter, []),
                "passed": bool(cp and cp.passed) or not has_cp,
                "available": (block_mastered(db, level, letter) or dev_mode_enabled(db)),
                "exists": has_cp,
            },
        })

    exam_cfg = level_exam(level)
    ep = _exam_prog(db, level, create=False)
    exam_available = _exam_available(db, level)
    exam = {
        "leetcode": exam_cfg.get("leetcode", []),
        "interview": exam_cfg.get("interview", []),
        "passed": bool(ep and ep.passed),
        "available": exam_available,
        "exists": _has_exam(level),
    }

    mastered_count = sum(1 for r in set_rows if r["status"] == "mastered" and not is_extra_set(level, r["set_number"]))
    core_total = len(core_level_sets(level))
    return {
        "level": level,
        "unlocked": level_unlocked(db, level),
        "target": target,
        "sets": set_rows,
        "blocks": blocks,
        "exam": exam,
        "mastered_sets": mastered_count,
        "total_sets": core_total,
    }


# ---------------------------------------------------------------------------
# flexible study session
# ---------------------------------------------------------------------------

def _page_payload(p, locale: str = "en") -> dict:
    return page_payload(p, locale)


def build_review_session(db: Session, level: str, set_number: int, count: int = 10, *, locale: str = "en") -> dict:
    """Practice a mastered set — corrections use /api/run, not set submit."""
    level = route_level(level)
    sp = _set_prog(db, level, set_number, create=False)
    if not sp or sp.status != "mastered":
        if is_extra_set(level, set_number):
            pass  # extra sets are always open for practice
        elif not dev_mode_enabled(db):
            from fastapi import HTTPException
            raise HTTPException(400, "Solo puedes repasar sets dominados")

    curriculum = load_curriculum()
    pages = get_set_pages(curriculum, level, set_number)
    count = max(1, min(count, len(pages)))
    session_pages = pages if count >= len(pages) else pages[:count]

    s_def = next((s for s in level_sets(level) if s.set_number == set_number), None)
    block_letter = block_letter_for_set_num(level, set_number)
    bid = f"{normalize_level(level)}.{block_letter}"
    return {
        "type": "set",
        "mode": "review",
        "level": level,
        "set_number": set_number,
        "display_set_number": display_set_number(level, set_number),
        "set_title": set_title(level, set_number, locale),
        "block": block_letter,
        "block_title": block_title(bid, locale),
        "instruction": block_instruction(bid, locale),
        "standard_seconds": set_standard_seconds(level, set_number),
        "status": "mastered",
        "attempts": sp.attempts if sp else 0,
        "completed": len(pages),
        "total": len(pages),
        "accumulated_time_ms": sp.accumulated_time_ms if sp else 0,
        "page_range": f"{pages[0].page}-{pages[-1].page}" if pages else "",
        "drills": [_page_payload(p, locale) for p in session_pages],
    }


def build_session(db: Session, level: str, count: int = 10, *, locale: str = "en") -> dict:
    level = route_level(level)
    target = current_target(db, level)
    if target.get("type") != "set":
        return {"type": target.get("type"), "target": target, "level": level}

    set_number = target["set_number"]
    sp = _set_prog(db, level, set_number, create=True)
    curriculum = load_curriculum()
    pages = get_set_pages(curriculum, level, set_number)
    done = set(sp.completed_pages or [])
    remaining = [p for p in pages if p.id not in done]
    count = max(1, min(count, len(pages)))
    session_pages = remaining[:count] if remaining else pages[:count]

    s_def = next((s for s in level_sets(level) if s.set_number == set_number), None)
    block_letter = block_letter_for_set_num(level, set_number)
    bid = f"{normalize_level(level)}.{block_letter}"
    return {
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
        "drills": [_page_payload(p, locale) for p in session_pages],
    }


def _update_drill_mastery(db: Session, page_id: str, block_id: str, passed: bool) -> None:
    today = date.today()
    m = db.query(DrillMastery).filter_by(drill_id=page_id).first()
    if not m:
        m = DrillMastery(
            drill_id=page_id, block_id=block_id, pass_dates=[],
            times_passed=0, times_passed_no_hint=0, pass_streak=0, status="new",
        )
        db.add(m)
    if passed:
        m.times_passed = (m.times_passed or 0) + 1
        m.times_passed_no_hint = (m.times_passed_no_hint or 0) + 1
        m.pass_streak = (m.pass_streak or 0) + 1
        m.last_passed_date = today
        m.status = "solid"
    else:
        m.pass_streak = 0
        m.last_failed_date = today
        m.status = "shaky"


def submit_set(
    db: Session,
    level: str,
    set_number: int,
    answers: list,
    time_ms: int,
    *,
    is_repeat: bool = False,
) -> dict:
    """answers: list of objects with .exercise_id and .code."""
    level = route_level(level)
    curriculum = load_curriculum()
    sp = _set_prog(db, level, set_number, create=True)
    today = date.today()
    threshold = _first_attempt_threshold()
    repeat_days = _spaced_repeat_days()

    pages = get_set_pages(curriculum, level, set_number)
    total_pages = len(pages) or 10
    completed = set(sp.completed_pages or [])

    # Retry or stale partial state — do not carry over old time.
    if len(completed) >= total_pages and sp.status != "mastered":
        sp.accumulated_time_ms = 0
        sp.completed_pages = []
        completed = set()
    elif not completed and sp.accumulated_time_ms > 0:
        sp.accumulated_time_ms = 0

    results: dict[str, dict] = {}
    failed = 0
    per_time = time_ms // max(len(answers), 1)
    passed_count = 0
    answered_in_batch = 0

    for item in answers:
        d = curriculum.kumon.get(item.exercise_id)
        if not d or d.set != set_number or route_level(d.level) != level:
            continue
        answered_in_batch += 1
        res = run_kumon_code(item.code, d.validation, language=language_for_level(d.level))
        passed = res.get("passed", False)
        results[item.exercise_id] = {
            "passed": passed,
            "error": res.get("error"),
            "expected": res.get("expected"),
            "stdout": res.get("stdout"),
        }
        _update_drill_mastery(db, d.id, d.block_id, passed)
        db.add(Attempt(
            exercise_id=item.exercise_id, exercise_type="kumon", tier=0,
            hints_used=0, passed=passed, time_ms=per_time,
            code_snapshot=item.code, attempt_date=today,
        ))
        if passed:
            completed.add(item.exercise_id)
            passed_count += 1
        else:
            failed += 1

    sp.completed_pages = [p.id for p in pages if p.id in completed]
    sp.errors += failed
    if answered_in_batch >= total_pages:
        # Full set in one submit — time_ms is total session time (incl. rechecks).
        sp.accumulated_time_ms = time_ms
    else:
        sp.accumulated_time_ms += time_ms

    std_ms = int(set_standard_seconds(level, set_number) * 1000 * _time_tolerance())
    outcome = "in_progress"
    needs_repeat = False
    if len(completed) >= total_pages:
        is_first_complete = sp.attempts == 0
        if is_first_complete:
            if len(answers) >= total_pages:
                sp.first_attempt_accuracy = passed_count / total_pages
            else:
                sp.first_attempt_accuracy = max(0.0, 1.0 - sp.errors / total_pages)
            sp.first_attempt_at = datetime.utcnow()

        sp.attempts += 1
        sp.last_time_ms = sp.accumulated_time_ms
        within_time = sp.accumulated_time_ms <= std_ms
        low_accuracy = (
            sp.first_attempt_accuracy is not None
            and sp.first_attempt_accuracy < threshold
        )
        needs_repeat = not within_time or low_accuracy

        flags = list(sp.failure_flags or [])
        if needs_repeat:
            sp.repeat_scheduled_for = today + timedelta(days=repeat_days)
            sp.solid_mastery = False
            if not within_time and "too_slow" not in flags:
                flags.append("too_slow")
            if low_accuracy and "low_accuracy" not in flags:
                flags.append("low_accuracy")
            sp.failure_flags = flags
        else:
            sp.solid_mastery = True

        if within_time:
            sp.status = "mastered"
            sp.mastered_at = datetime.utcnow()
            if sp.best_time_ms is None or sp.accumulated_time_ms < sp.best_time_ms:
                sp.best_time_ms = sp.accumulated_time_ms
            outcome = "mastered"
            if is_repeat or (sp.repeat_scheduled_for and sp.repeat_scheduled_for <= today):
                sp.repeat_completed_at = today
                sp.repeat_scheduled_for = None
        else:
            sp.status = "current"
            outcome = "too_slow"
    elif sp.status != "repeating":
        sp.status = "current"

    db.commit()
    update_streak(db)
    db.commit()

    passed_total = sum(1 for r in results.values() if r["passed"])
    return {
        "results": results,
        "passed_count": passed_total,
        "total": len(answers),
        "outcome": outcome,
        "set_status": sp.status,
        "completed": len(sp.completed_pages or []),
        "set_total": total_pages,
        "accumulated_time_ms": sp.accumulated_time_ms,
        "standard_ms": std_ms,
        "mastered": outcome == "mastered",
        "needs_repeat": needs_repeat,
        "first_attempt_accuracy": sp.first_attempt_accuracy,
        "solid_mastery": sp.solid_mastery,
        "repeat_scheduled_for": str(sp.repeat_scheduled_for) if sp.repeat_scheduled_for else None,
    }


# ---------------------------------------------------------------------------
# checkpoints
# ---------------------------------------------------------------------------

def get_checkpoint(db: Session, level: str, block_letter: str, locale: str = "en") -> dict:
    level = route_level(level)
    block_letter = block_letter.upper()
    curriculum = load_curriculum()
    problem_ids = checkpoint_for_block(level, block_letter)
    problems = []
    for pid in problem_ids:
        p = curriculum.leetcode.get(pid)
        prog = db.query(LeetCodeProgress).filter_by(problem_id=pid).first()
        problems.append({
            "id": pid,
            "title": problem_title(p, locale, pid),
            "description": problem_description(p, locale) if p else "",
            "passed": bool(prog and prog.tier_passed >= 1),
        })
    cp = _checkpoint_prog(db, level, block_letter, create=False)
    bid = f"{normalize_level(level)}.{block_letter}"
    return {
        "level": level,
        "block": block_letter,
        "block_title": block_title(bid, locale),
        "available": block_mastered(db, level, block_letter) or dev_mode_enabled(db),
        "passed": bool(cp and cp.passed),
        "problems": problems,
    }


def _maybe_complete_checkpoint(db: Session, level: str, block_letter: str) -> bool:
    problem_ids = checkpoint_for_block(level, block_letter)
    if not problem_ids:
        return False
    for pid in problem_ids:
        prog = db.query(LeetCodeProgress).filter_by(problem_id=pid).first()
        if not prog or prog.tier_passed < 1:
            return False
    cp = _checkpoint_prog(db, level, block_letter, create=True)
    if not cp.passed:
        cp.passed = True
        cp.passed_at = datetime.utcnow()
        db.commit()
    return True


def block_for_checkpoint_problem(level: str, problem_id: str) -> str | None:
    for letter, ids in level_checkpoints(level).items():
        if problem_id in ids:
            return letter
    return None


def submit_checkpoint(db: Session, level: str, problem_id: str, code: str) -> dict:
    level = route_level(level)
    curriculum = load_curriculum()
    p = curriculum.leetcode.get(problem_id)
    if not p:
        return {"passed": False, "error": "Problema no encontrado"}
    res = run_leetcode_code(code, p.test_cases, p.fn_name, language=language_for_level(level))
    passed = res.get("passed", False)
    today = date.today()
    if passed:
        prog = db.query(LeetCodeProgress).filter_by(problem_id=problem_id).first()
        if not prog:
            prog = LeetCodeProgress(problem_id=problem_id, level=level, tier_passed=1)
            db.add(prog)
        else:
            prog.tier_passed = max(prog.tier_passed, 1)
        db.commit()
    db.add(Attempt(
        exercise_id=problem_id, exercise_type="leetcode", tier=1, hints_used=0,
        passed=passed, time_ms=0, code_snapshot=code, attempt_date=today,
    ))
    db.commit()

    checkpoint_done = False
    block_letter = block_for_checkpoint_problem(level, problem_id)
    if block_letter:
        checkpoint_done = _maybe_complete_checkpoint(db, level, block_letter)
    return {
        "passed": passed,
        "result": res,
        "checkpoint_passed": checkpoint_done,
        "block": block_letter,
    }


# ---------------------------------------------------------------------------
# level completion exam
# ---------------------------------------------------------------------------

def get_exam(db: Session, level: str, locale: str = "en") -> dict:
    level = route_level(level)
    curriculum = load_curriculum()
    cfg = level_exam(level)
    available = _exam_available(db, level)

    leetcode = []
    for pid in cfg.get("leetcode", []):
        p = curriculum.leetcode.get(pid)
        prog = db.query(LeetCodeProgress).filter_by(problem_id=pid).first()
        leetcode.append({
            "id": pid,
            "title": problem_title(p, locale, pid),
            "description": problem_description(p, locale) if p else "",
            "passed": bool(prog and prog.tier_passed >= 1),
        })
    interview = []
    for qid in cfg.get("interview", []):
        q = curriculum.interview.get(qid)
        prog = db.query(InterviewProgress).filter_by(question_id=qid).first()
        if q:
            payload = interview_payload(q, locale)
            interview.append({
                **payload,
                "completed": bool(prog and prog.completed),
            })
        else:
            interview.append({
                "id": qid,
                "question": qid,
                "completed": bool(prog and prog.completed),
            })
    ep = _exam_prog(db, level, create=False)
    return {
        "level": level,
        "available": available,
        "passed": bool(ep and ep.passed),
        "leetcode": leetcode,
        "interview": interview,
    }


def _maybe_complete_exam(db: Session, level: str) -> bool:
    cfg = level_exam(level)
    for pid in cfg.get("leetcode", []):
        prog = db.query(LeetCodeProgress).filter_by(problem_id=pid).first()
        if not prog or prog.tier_passed < 1:
            return False
    for qid in cfg.get("interview", []):
        prog = db.query(InterviewProgress).filter_by(question_id=qid).first()
        if not prog or not prog.completed:
            return False
    ep = _exam_prog(db, level, create=True)
    if not ep.passed:
        ep.passed = True
        ep.passed_at = datetime.utcnow()
        db.commit()
    return True


def submit_exam(db: Session, level: str, exercise_id: str, exercise_type: str,
                code: str = "", self_score: int | None = None, answer_text: str | None = None) -> dict:
    level = route_level(level)
    curriculum = load_curriculum()
    today = date.today()
    passed = False
    result: dict = {}

    if exercise_type == "leetcode":
        p = curriculum.leetcode.get(exercise_id)
        if not p:
            return {"passed": False, "error": "Problema no encontrado"}
        result = run_leetcode_code(code, p.test_cases, p.fn_name, language=language_for_level(level))
        passed = result.get("passed", False)
        if passed:
            prog = db.query(LeetCodeProgress).filter_by(problem_id=exercise_id).first()
            if not prog:
                prog = LeetCodeProgress(problem_id=exercise_id, level=level, tier_passed=1)
                db.add(prog)
            else:
                prog.tier_passed = max(prog.tier_passed, 1)
            db.commit()
    elif exercise_type == "interview":
        q = curriculum.interview.get(exercise_id)
        if not q:
            return {"passed": False, "error": "Pregunta no encontrada"}
        passed = True
        prog = db.query(InterviewProgress).filter_by(question_id=exercise_id).first()
        if not prog:
            prog = InterviewProgress(question_id=exercise_id, level=level, category=q.category)
            db.add(prog)
        prog.self_score = self_score or 0
        prog.completed = True
        db.commit()
        result = {"passed": True}

    db.add(Attempt(
        exercise_id=exercise_id, exercise_type=exercise_type, tier=1, hints_used=0,
        passed=passed, time_ms=0, code_snapshot=code, self_score=self_score, attempt_date=today,
    ))
    db.commit()

    exam_done = _maybe_complete_exam(db, level)
    return {"passed": passed, "result": result, "exam_passed": exam_done}


# ---------------------------------------------------------------------------
# nav unlock helpers (used by progress.get_unlock_status)
# ---------------------------------------------------------------------------

def leetcode_unlocked(db: Session, level: str) -> bool:
    if dev_mode_enabled(db):
        return True
    return block_mastered(db, level, "A")


def interview_unlocked(db: Session, level: str) -> bool:
    return _exam_available(db, level)


# ---------------------------------------------------------------------------
# streak (kept from old progress logic; imported lazily to avoid cycle)
# ---------------------------------------------------------------------------

def update_streak(db: Session):
    from .progress import update_streak as _update
    return _update(db)
