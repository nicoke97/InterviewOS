from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from .content_loader import Curriculum, get_block_drills, load_curriculum
from .models import Attempt, BlockProgress, DailySheet, DrillMastery, StudyDay


BLOCK_ORDER = [
    "a1-variables", "a2-conditionals", "a3-loops", "a4-functions",
    "b1-lists", "b2-dicts", "b3-strings", "b4-errors",
    "c1-classes", "c2-inheritance", "c3-nested", "c4-git",
]

LEVEL_BLOCKS = {
    "a": ["a1-variables", "a2-conditionals", "a3-loops", "a4-functions"],
    "b": ["b1-lists", "b2-dicts", "b3-strings", "b4-errors"],
    "c": ["c1-classes", "c2-inheritance", "c3-nested", "c4-git"],
}


def _drill_slice(drills: list, start: int, end: int) -> list[str]:
    subset = drills[start - 1 : end]
    return [d.id for d in subset]


def _get_or_create_block_progress(db: Session, block_id: str) -> BlockProgress:
    bp = db.query(BlockProgress).filter_by(block_id=block_id).first()
    if not bp:
        level = block_id[0]
        bp = BlockProgress(block_id=block_id, level=level, phase="intro", days_on_block=0)
        db.add(bp)
        db.commit()
        db.refresh(bp)
    return bp


def _get_study_day(db: Session) -> StudyDay:
    today = date.today()
    sd = db.query(StudyDay).filter_by(date=today).first()
    if not sd:
        last = db.query(StudyDay).order_by(StudyDay.day_number.desc()).first()
        day_num = (last.day_number + 1) if last else 1
        active = last.active_block if last else "a1-variables"
        sd = StudyDay(date=today, day_number=day_num, active_block=active)
        db.add(sd)
        db.commit()
        db.refresh(sd)
    return sd


def _failed_yesterday(db: Session) -> list[str]:
    yesterday = date.today() - timedelta(days=1)
    failed = (
        db.query(Attempt)
        .filter(Attempt.attempt_date == yesterday, Attempt.passed == False, Attempt.exercise_type == "kumon")
        .all()
    )
    ids = []
    for a in failed:
        m = db.query(DrillMastery).filter_by(drill_id=a.exercise_id).first()
        if not m or m.pass_streak < 2:
            ids.append(a.exercise_id)
    return list(dict.fromkeys(ids))


def _determine_phase(day_number: int, block_index: int) -> str:
    """Map day number within block progression to sheet phase."""
    cycle = (day_number - 1) % 7
    phases = ["intro", "repeat", "bridge", "advance", "maintenance", "repeat", "bridge"]
    return phases[cycle]


def _compose_drills_for_phase(
    curriculum: Curriculum,
    phase: str,
    active_block: str,
    slot: str,
    day_number: int,
) -> tuple[list[str], str]:
    idx = BLOCK_ORDER.index(active_block) if active_block in BLOCK_ORDER else 0
    prev_block = BLOCK_ORDER[idx - 1] if idx > 0 else None
    next_block = BLOCK_ORDER[idx + 1] if idx < len(BLOCK_ORDER) - 1 else None

    active_drills = get_block_drills(curriculum, active_block)

    if phase == "intro":
        if day_number == 1:
            if slot == "morning":
                return _drill_slice(active_drills, 1, 10), "intro"
            return _drill_slice(active_drills, 11, 20), "intro"
        return [d.id for d in active_drills], "intro"

    if phase == "repeat":
        return [d.id for d in active_drills], "repeat"

    if phase == "bridge" and prev_block:
        prev_drills = get_block_drills(curriculum, prev_block)
        if slot == "morning":
            ids = _drill_slice(prev_drills, 11, 20)
            return ids[:12], "bridge"
        if next_block:
            next_drills = get_block_drills(curriculum, next_block)
            return _drill_slice(next_drills, 1, 10), "bridge"
        return _drill_slice(prev_drills, 11, 20), "bridge"

    if phase == "advance":
        return [d.id for d in active_drills], "advance"

    if phase == "maintenance":
        ids = []
        if prev_block:
            prev_drills = get_block_drills(curriculum, prev_block)
            ids.extend(_drill_slice(prev_drills, 11, 20))
        if slot == "evening":
            ids = _drill_slice(active_drills, 1, 5)
        else:
            ids.extend(_drill_slice(active_drills, 1, 5))
        return ids[:12], "maintenance"

    return [d.id for d in active_drills[:12]], "intro"


def build_sheet(db: Session, slot: str) -> DailySheet:
    today = date.today()
    existing = db.query(DailySheet).filter_by(date=today, slot=slot).first()
    if existing:
        return existing

    curriculum = load_curriculum()
    study_day = _get_study_day(db)
    active_block = study_day.active_block
    day_number = study_day.day_number

    if day_number <= 2:
        active_block = "a1-variables"

    block_idx = BLOCK_ORDER.index(active_block) if active_block in BLOCK_ORDER else 0
    phase = _determine_phase(day_number, block_idx)

    drill_ids, rule = _compose_drills_for_phase(curriculum, phase, active_block, slot, day_number)

    failed = _failed_yesterday(db)
    for fid in reversed(failed):
        if fid not in drill_ids:
            drill_ids.insert(0, fid)
    drill_ids = drill_ids[:12]

    sheet = DailySheet(
        date=today,
        slot=slot,
        drill_ids=drill_ids,
        completed_ids=[],
        generated_by_rule=rule,
        current_index=0,
    )
    db.add(sheet)
    if rule == "maintenance" and active_block:
        bp = _get_or_create_block_progress(db, active_block)
        bp.maintenance_sheets += 1
    db.commit()
    db.refresh(sheet)
    return sheet


def advance_study_day(db: Session) -> None:
    """Call when user completes both slots or end of day."""
    sd = _get_study_day(db)
    sd.day_number += 1
    cycle = (sd.day_number - 1) % 7
    if cycle == 2 and sd.active_block in BLOCK_ORDER:
        idx = BLOCK_ORDER.index(sd.active_block)
        if idx < len(BLOCK_ORDER) - 1:
            sd.active_block = BLOCK_ORDER[idx + 1]
    db.commit()


def update_drill_mastery(db: Session, drill_id: str, block_id: str, passed: bool, hints_used: int) -> None:
    today = date.today()
    m = db.query(DrillMastery).filter_by(drill_id=drill_id).first()
    if not m:
        m = DrillMastery(drill_id=drill_id, block_id=block_id, pass_dates=[])
        db.add(m)

    if passed:
        m.times_passed += 1
        if hints_used == 0:
            m.times_passed_no_hint += 1
        m.pass_streak += 1
        m.last_passed_date = today
        dates = list(m.pass_dates or [])
        if str(today) not in dates:
            dates.append(str(today))
        m.pass_dates = dates
        if m.times_passed >= 2 and m.times_passed_no_hint >= 1:
            m.status = "solid"
        elif m.times_passed >= 1:
            m.status = "shaky"
    else:
        m.pass_streak = 0
        m.last_failed_date = today
        m.status = "shaky"
    db.commit()


def check_block_stable(db: Session, block_id: str, curriculum: Curriculum) -> bool:
    drills = get_block_drills(curriculum, block_id)
    if len(drills) < 20:
        return False

    all_twice = True
    no_hint_ok = True
    for d in drills:
        m = db.query(DrillMastery).filter_by(drill_id=d.id).first()
        if not m or m.times_passed < 2:
            all_twice = False
        if d.order >= 4 and (not m or m.times_passed_no_hint < 1):
            no_hint_ok = False

    bp = _get_or_create_block_progress(db, block_id)
    stable = all_twice and no_hint_ok
    if stable and not bp.is_stable:
        bp.is_stable = True
        from datetime import datetime
        bp.unlocked_at = datetime.utcnow()
    db.commit()
    return stable
