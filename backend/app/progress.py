from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from .content_loader import Curriculum, get_block_drills, load_curriculum
from .models import BlockProgress, LeetCodeProgress, Streak
from .sheet_composer import LEVEL_BLOCKS, check_block_stable


def all_kumon_blocks_stable(db: Session, level: str, curriculum: Curriculum) -> bool:
    blocks = LEVEL_BLOCKS.get(level, [])
    if not blocks:
        return False

    for block_id in blocks:
        if not check_block_stable(db, block_id, curriculum):
            return False
        bp = db.query(BlockProgress).filter_by(block_id=block_id).first()
        if not bp or bp.maintenance_sheets < 5:
            return False
    return True


def leetcode_unlocked(db: Session, level: str) -> bool:
    curriculum = load_curriculum()
    return all_kumon_blocks_stable(db, level, curriculum)


def interview_unlocked(db: Session, level: str) -> bool:
    problems = [p for p in load_curriculum().leetcode.values() if p.level == level]
    if not problems:
        return False
    for p in problems:
        prog = db.query(LeetCodeProgress).filter_by(problem_id=p.id).first()
        if not prog or prog.tier_passed < 3:
            return False
    return True


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
    elif streak.last_active_date != today:
        streak.current_streak = 1

    streak.best_streak = max(streak.best_streak, streak.current_streak)
    streak.last_active_date = today
    db.commit()
    return streak


def get_unlock_status(db: Session) -> dict:
    curriculum = load_curriculum()
    status = {}
    for level in ("a", "b", "c"):
        status[level] = {
            "leetcode_unlocked": leetcode_unlocked(db, level),
            "interview_unlocked": interview_unlocked(db, level),
            "blocks": {},
        }
        for block_id in LEVEL_BLOCKS.get(level, []):
            bp = db.query(BlockProgress).filter_by(block_id=block_id).first()
            drills = get_block_drills(curriculum, block_id)
            passed = 0
            for d in drills:
                from .models import DrillMastery
                m = db.query(DrillMastery).filter_by(drill_id=d.id).first()
                if m and m.times_passed > 0:
                    passed += 1
            status[level]["blocks"][block_id] = {
                "stable": bp.is_stable if bp else False,
                "phase": bp.phase if bp else "intro",
                "drills_passed": passed,
                "total": len(drills),
            }
    return status
