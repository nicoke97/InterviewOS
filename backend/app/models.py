from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import DATA_DIR, DATABASE_URL, engine_connect_args

engine = create_engine(DATABASE_URL, connect_args=engine_connect_args())
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@event.listens_for(engine, "connect")
def _sqlite_pragmas(dbapi_conn, _connection_record):
    if not DATABASE_URL.startswith("sqlite"):
        return
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


class Base(DeclarativeBase):
    pass


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    slot: Mapped[str] = mapped_column(String(16))  # morning | evening
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exercise_id: Mapped[str] = mapped_column(String(64), index=True)
    exercise_type: Mapped[str] = mapped_column(String(16))  # kumon | leetcode | interview
    tier: Mapped[int] = mapped_column(Integer, default=0)
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    time_ms: Mapped[int] = mapped_column(Integer, default=0)
    code_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    self_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    attempt_date: Mapped[date] = mapped_column(Date, index=True)


class BlockProgress(Base):
    __tablename__ = "block_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    block_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    level: Mapped[str] = mapped_column(String(8))
    phase: Mapped[str] = mapped_column(String(16), default="intro")
    days_on_block: Mapped[int] = mapped_column(Integer, default=0)
    is_stable: Mapped[bool] = mapped_column(Boolean, default=False)
    repeat_pass_rate: Mapped[float] = mapped_column(Float, default=0.0)
    maintenance_sheets: Mapped[int] = mapped_column(Integer, default=0)
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Streak(Base):
    __tablename__ = "streaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_active_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class DrillMastery(Base):
    __tablename__ = "drill_mastery"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    drill_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    block_id: Mapped[str] = mapped_column(String(32), index=True)
    times_passed: Mapped[int] = mapped_column(Integer, default=0)
    times_passed_no_hint: Mapped[int] = mapped_column(Integer, default=0)
    pass_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_passed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_failed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    pass_dates: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(16), default="new")  # new | shaky | solid


class DailySheet(Base):
    __tablename__ = "daily_sheets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    slot: Mapped[str] = mapped_column(String(16))
    level: Mapped[str] = mapped_column(String(8), default="a", index=True)
    drill_ids: Mapped[list] = mapped_column(JSON)
    completed_ids: Mapped[list] = mapped_column(JSON, default=list)
    generated_by_rule: Mapped[str] = mapped_column(String(32))
    current_index: Mapped[int] = mapped_column(Integer, default=0)


class LeetCodeProgress(Base):
    __tablename__ = "leetcode_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[str] = mapped_column(String(64), index=True)
    level: Mapped[str] = mapped_column(String(8))
    track: Mapped[str] = mapped_column(String(16), default="kumon", index=True)
    tier_passed: Mapped[int] = mapped_column(Integer, default=0)  # highest tier passed (1-3)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    solid_mastery: Mapped[bool] = mapped_column(Boolean, default=False)
    topic: Mapped[str] = mapped_column(String(32), default="")
    global_order: Mapped[int] = mapped_column(Integer, default=0)
    last_practiced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class InterviewProgress(Base):
    __tablename__ = "interview_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[str] = mapped_column(String(64), unique=True)
    level: Mapped[str] = mapped_column(String(8))
    category: Mapped[str] = mapped_column(String(16))  # python | odoo
    self_score: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)


class AppSettings(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True)
    value: Mapped[str] = mapped_column(Text)


class StudyDay(Base):
    __tablename__ = "study_days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    day_number: Mapped[int] = mapped_column(Integer, default=1)
    active_block: Mapped[str] = mapped_column(String(32), default="A.A")
    curriculum_advanced: Mapped[bool] = mapped_column(Boolean, default=False)


# ---------------------------------------------------------------------------
# New Kumon mastery model (set-based, domain progression)
# ---------------------------------------------------------------------------

class SetProgress(Base):
    """Progress for a single set of 10 pages within a level.

    A set is "mastered" only when all 10 pages have been answered correctly
    (self-correction allowed) AND the accumulated time is within the set's
    standard time. Otherwise it goes into "repeating" and the page progress
    resets so it must be solved again — the Kumon repetition loop.
    """

    __tablename__ = "set_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    track: Mapped[str] = mapped_column(String(16), default="python", index=True)
    level: Mapped[str] = mapped_column(String(8), index=True)        # route level: a..e, oa..
    set_number: Mapped[int] = mapped_column(Integer, index=True)     # 1..20
    status: Mapped[str] = mapped_column(String(16), default="current")  # current|mastered|repeating
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    completed_pages: Mapped[list] = mapped_column(JSON, default=list)   # page ids passed this attempt
    errors: Mapped[int] = mapped_column(Integer, default=0)             # failed checks this attempt
    accumulated_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    best_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mastered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    first_attempt_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    first_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    solid_mastery: Mapped[bool] = mapped_column(Boolean, default=False)
    repeat_scheduled_for: Mapped[date | None] = mapped_column(Date, nullable=True)
    repeat_completed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    failure_flags: Mapped[list] = mapped_column(JSON, default=list)


class DailyPlan(Base):
    """Orientador session plan for a calendar day (one or more per day)."""

    __tablename__ = "daily_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    track: Mapped[str] = mapped_column(String(16), default="python", index=True)
    session_number: Mapped[int] = mapped_column(Integer, default=1)
    minutes_budget: Mapped[int] = mapped_column(Integer, default=20)
    assignments: Mapped[list] = mapped_column(JSON, default=list)
    completed_indices: Mapped[list] = mapped_column(JSON, default=list)
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(16), default="active")  # active | completed


class CheckpointProgress(Base):
    """LeetCode checkpoint at the end of each 50-page block."""

    __tablename__ = "checkpoint_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level: Mapped[str] = mapped_column(String(8), index=True)
    block_letter: Mapped[str] = mapped_column(String(4))
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    passed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class LevelExamProgress(Base):
    """Level completion exam (LeetCode + interview) at page 200."""

    __tablename__ = "level_exam_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    passed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class SdeCursor(Base):
    __tablename__ = "sde_cursors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    next_section_index: Mapped[int] = mapped_column(Integer, default=0)
    active_algo_id: Mapped[str] = mapped_column(String(64), default="two-sum")
    active_lang: Mapped[str] = mapped_column(String(16), default="csharp")
    algo_phase: Mapped[str] = mapped_column(String(16), default="day1")  # day1|day2|voice
    day1_index: Mapped[int] = mapped_column(Integer, default=0)
    last_sheet_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_evidence_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    session_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    session_kind: Mapped[str] = mapped_column(String(16), default="advance")  # advance|flojo|return
    session_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    today_assignments: Mapped[list] = mapped_column(JSON, default=list)
    pending_voice_algo: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pending_voice_lang: Mapped[str | None] = mapped_column(String(16), nullable=True)
    next_debug_index: Mapped[int] = mapped_column(Integer, default=0)


class SdeAlgoProgress(Base):
    __tablename__ = "sde_algo_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    algo_id: Mapped[str] = mapped_column(String(64), index=True)
    lang: Mapped[str] = mapped_column(String(16), index=True)
    status: Mapped[str] = mapped_column(String(16), default="active")  # active|completed|failed
    pool_fails: Mapped[int] = mapped_column(Integer, default=0)
    voice_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class SdeSectionProgress(Base):
    __tablename__ = "sde_section_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    section_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(16), default="unseen")  # unseen|current|dirty|mastered
    dirty_fails: Mapped[int] = mapped_column(Integer, default=0)
    last_score: Mapped[float | None] = mapped_column(Float, nullable=True)


class SdeCardProgress(Base):
    __tablename__ = "sde_card_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    section_id: Mapped[str] = mapped_column(String(64), index=True)
    fails: Mapped[int] = mapped_column(Integer, default=0)
    seen: Mapped[int] = mapped_column(Integer, default=0)
    last_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)


class SdeDebugProgress(Base):
    __tablename__ = "sde_debug_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bug_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(16), default="unseen")  # unseen|failed|completed
    fails: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class SdeOfflineLog(Base):
    __tablename__ = "sde_offline_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    kinds: Mapped[list] = mapped_column(JSON, default=list)
    section_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SdeAnalysis(Base):
    __tablename__ = "sde_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    cause: Mapped[str] = mapped_column(String(64), default="")
    line: Mapped[str] = mapped_column(Text, default="")
    cta: Mapped[str] = mapped_column(String(128), default="")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)


class ReturnExam(Base):
    """Retention quiz after several days away. Failed items force a full set repeat."""

    __tablename__ = "return_exams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    inactivity_days: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending | completed
    items: Mapped[list] = mapped_column(JSON, default=list)
    results: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    failed_sets: Mapped[list] = mapped_column(JSON, default=list)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


def _migrate_schema() -> None:
    """Lightweight SQLite migrations for columns added after first deploy."""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if "study_days" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("study_days")}
        if "curriculum_advanced" not in cols:
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE study_days ADD COLUMN curriculum_advanced BOOLEAN DEFAULT 0")
                )
    if "daily_sheets" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("daily_sheets")}
        if "level" not in cols:
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE daily_sheets ADD COLUMN level VARCHAR(8) DEFAULT 'a'")
                )
    if "set_progress" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("set_progress")}
        migrations = [
            ("first_attempt_accuracy", "FLOAT"),
            ("first_attempt_at", "DATETIME"),
            ("solid_mastery", "BOOLEAN DEFAULT 0"),
            ("repeat_scheduled_for", "DATE"),
            ("repeat_completed_at", "DATE"),
            ("failure_flags", "TEXT DEFAULT '[]'"),
        ]
        for col, typ in migrations:
            if col not in cols:
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE set_progress ADD COLUMN {col} {typ}"))
    if "daily_plans" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("daily_plans")}
        if "session_number" not in cols:
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE daily_plans ADD COLUMN session_number INTEGER DEFAULT 1")
                )
    if "sde_cursors" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("sde_cursors")}
        if "next_debug_index" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE sde_cursors ADD COLUMN next_debug_index INTEGER DEFAULT 0"))
    if "leetcode_progress" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("leetcode_progress")}
        lc_migrations = [
            ("track", "VARCHAR(16) DEFAULT 'kumon'"),
            ("attempts", "INTEGER DEFAULT 0"),
            ("solid_mastery", "BOOLEAN DEFAULT 0"),
            ("topic", "VARCHAR(32) DEFAULT ''"),
            ("global_order", "INTEGER DEFAULT 0"),
            ("last_practiced_at", "DATETIME"),
        ]
        for col, typ in lc_migrations:
            if col not in cols:
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE leetcode_progress ADD COLUMN {col} {typ}"))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate_schema()
    db = SessionLocal()
    try:
        if not db.query(Streak).first():
            db.add(Streak())
        if not db.query(AppSettings).filter_by(key="focus_mode").first():
            db.add(AppSettings(key="focus_mode", value="false"))
        if not db.query(AppSettings).filter_by(key="dev_mode").first():
            db.add(AppSettings(key="dev_mode", value="false"))
        if not db.query(AppSettings).filter_by(key="locale").first():
            db.add(AppSettings(key="locale", value="en"))
        if not db.query(StudyDay).first():
            db.add(StudyDay(date=date.today(), day_number=1, active_block="A.A"))
        db.commit()
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
