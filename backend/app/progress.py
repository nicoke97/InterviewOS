from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from .content_loader import get_block_pages, get_set_pages, load_curriculum
from .kumon_hierarchy import all_block_order, block_title, level_sets, list_route_levels, route_level
from .models import Attempt, SetProgress, Streak
from .set_engine import (
    current_target,
    interview_unlocked,
    leetcode_unlocked,
)

# Re-exported for routes/back-compat.
__all__ = [
    "leetcode_unlocked", "interview_unlocked", "update_streak", "get_effective_streak",
    "get_activity_calendar", "get_month_calendar", "get_today_activity",
    "get_block_accuracy", "get_unlock_status",
]


# ---------------------------------------------------------------------------
# streak
# ---------------------------------------------------------------------------

def get_effective_streak(db: Session, streak: Streak | None) -> dict:
    if not streak or not streak.last_active_date:
        return {"current": 0, "best": streak.best_streak if streak else 0}
    today = date.today()
    gap = (today - streak.last_active_date).days
    if gap > 1 and streak.current_streak > 0:
        streak.current_streak = 0
        db.commit()
    return {"current": streak.current_streak, "best": streak.best_streak}


def update_streak(db: Session) -> Streak:
    streak = db.query(Streak).first()
    if not streak:
        streak = Streak()
        db.add(streak)
    today = date.today()
    if streak.last_active_date == today:
        db.commit()
        return streak
    if streak.last_active_date == today - timedelta(days=1):
        streak.current_streak += 1
    else:
        streak.current_streak = 1
    streak.best_streak = max(streak.best_streak, streak.current_streak)
    streak.last_active_date = today
    db.commit()
    return streak


# ---------------------------------------------------------------------------
# activity calendar (now derived from attempts, not sheets)
# ---------------------------------------------------------------------------

def _day_level(passed: int) -> str:
    if passed >= 10:
        return "complete"
    if passed >= 1:
        return "partial"
    return "none"


def get_activity_calendar(db: Session, days: int = 90) -> list[dict]:
    today = date.today()
    start = today - timedelta(days=days - 1)

    attempt_counts = dict(
        db.query(Attempt.attempt_date, func.count(Attempt.id))
        .filter(Attempt.attempt_date >= start)
        .group_by(Attempt.attempt_date)
        .all()
    )
    passed_counts = dict(
        db.query(Attempt.attempt_date, func.count(Attempt.id))
        .filter(Attempt.attempt_date >= start, Attempt.passed == True)  # noqa: E712
        .group_by(Attempt.attempt_date)
        .all()
    )

    calendar = []
    for offset in range(days):
        d = start + timedelta(days=offset)
        attempts = attempt_counts.get(d, 0)
        passed = passed_counts.get(d, 0)
        level = _day_level(passed)
        calendar.append({
            "date": str(d),
            "level": level,
            "attempts": attempts,
            "passed": passed,
            "morning_done": passed >= 5,
            "evening_done": level == "complete",
        })
    return calendar


def get_month_calendar(db: Session, year: int, month: int) -> dict:
    import calendar as cal

    first = date(year, month, 1)
    days_in_month = cal.monthrange(year, month)[1]
    last = date(year, month, days_in_month)

    first_weekday = (first.weekday() + 1) % 7
    grid_start = first - timedelta(days=first_weekday)
    last_weekday = (last.weekday() + 1) % 7
    grid_end = last + timedelta(days=(6 - last_weekday))

    passed_counts = dict(
        db.query(Attempt.attempt_date, func.count(Attempt.id))
        .filter(Attempt.attempt_date >= grid_start, Attempt.attempt_date <= grid_end,
                Attempt.passed == True)  # noqa: E712
        .group_by(Attempt.attempt_date)
        .all()
    )

    today = date.today()
    days = []
    d = grid_start
    while d <= grid_end:
        passed = passed_counts.get(d, 0)
        level = _day_level(passed)
        days.append({
            "date": str(d),
            "day": d.day,
            "in_month": d.month == month,
            "is_today": d == today,
            "level": level,
            "morning_done": passed >= 5,
            "evening_done": level == "complete",
        })
        d += timedelta(days=1)

    in_month = [day for day in days if day["in_month"]]
    return {
        "year": year,
        "month": month,
        "month_name": cal.month_name[month],
        "days": days,
        "stats": {
            "complete": sum(1 for day in in_month if day["level"] == "complete"),
            "partial": sum(1 for day in in_month if day["level"] == "partial"),
            "none": sum(1 for day in in_month if day["level"] == "none"),
        },
    }


# ---------------------------------------------------------------------------
# today's activity (set-based)
# ---------------------------------------------------------------------------

def get_today_activity(db: Session, level: str | None = None) -> dict:
    level = route_level(level or get_active_level(db))
    target = current_target(db, level)
    today = date.today()
    pages_today = (
        db.query(func.count(Attempt.id))
        .filter(Attempt.attempt_date == today, Attempt.exercise_type == "kumon",
                Attempt.passed == True)  # noqa: E712
        .scalar()
    ) or 0
    return {
        "level": level,
        "target": target,
        "pages_passed_today": pages_today,
    }


# ---------------------------------------------------------------------------
# block accuracy (SetProgress + curriculum)
# ---------------------------------------------------------------------------

def load_set_progress_map(db: Session) -> dict[tuple[str, int], SetProgress]:
    return {
        (route_level(sp.level), sp.set_number): sp
        for sp in db.query(SetProgress).all()
    }


def _page_completed_from_map(progress: dict[tuple[str, int], SetProgress], page) -> bool:
    level = route_level(page.level)
    sp = progress.get((level, page.set))
    if sp and sp.status == "mastered":
        return True
    if sp and page.id in (sp.completed_pages or []):
        return True
    return False


def _level_page_progress_from_map(
    progress: dict[tuple[str, int], SetProgress],
    level: str,
    curriculum=None,
) -> dict:
    level = route_level(level)
    curriculum = curriculum or load_curriculum()
    sets = level_sets(level)
    total_pages = 0
    completed_pages = 0
    mastered_sets = 0
    for s in sets:
        pages = get_set_pages(curriculum, level, s.set_number)
        n = len(pages) or 10
        total_pages += n
        sp = progress.get((level, s.set_number))
        if sp and sp.status == "mastered":
            mastered_sets += 1
            completed_pages += n
        elif sp:
            completed_pages += len(sp.completed_pages or [])
    return {
        "sets_mastered": mastered_sets,
        "total_sets": len(sets),
        "pages_completed": completed_pages,
        "total_pages": total_pages,
        "progress_pct": round(completed_pages / total_pages * 100) if total_pages else 0,
    }


def get_block_accuracy(db: Session, progress: dict[tuple[str, int], SetProgress] | None = None) -> list[dict]:
    progress = progress if progress is not None else load_set_progress_map(db)
    curriculum = load_curriculum()
    accuracy = []
    for block_id in all_block_order():
        pages = get_block_pages(curriculum, block_id)
        if not pages:
            continue
        mastered = sum(1 for p in pages if _page_completed_from_map(progress, p))
        accuracy.append({
            "block": block_id,
            "block_title": block_title(block_id),
            "accuracy": round(mastered / len(pages) * 100),
            "mastered": mastered,
            "total": len(pages),
        })
    return accuracy


# ---------------------------------------------------------------------------
# unlock status (per level, for nav + dashboard)
# ---------------------------------------------------------------------------

def get_active_level(db: Session, track: str = "python") -> str:
    from .set_engine import _level_complete

    levels = list_route_levels(track)
    for level in levels:
        if level_unlocked(db, level) and not _level_complete(db, level):
            return level
    return levels[0] if levels else "a"


def level_unlocked(db: Session, level: str) -> bool:
    from .set_engine import level_unlocked as _level_unlocked

    return _level_unlocked(db, level)


def get_unlock_status(db: Session, progress: dict[tuple[str, int], SetProgress] | None = None) -> dict:
    progress = progress if progress is not None else load_set_progress_map(db)
    curriculum = load_curriculum()
    status: dict[str, dict] = {}
    for level in list_route_levels("python"):
        status[level] = {
            "leetcode_unlocked": leetcode_unlocked(db, level),
            "interview_unlocked": interview_unlocked(db, level),
            **_level_page_progress_from_map(progress, level, curriculum),
        }
    return status
