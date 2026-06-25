from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path

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
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "progress.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


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
    drill_ids: Mapped[list] = mapped_column(JSON)
    completed_ids: Mapped[list] = mapped_column(JSON, default=list)
    generated_by_rule: Mapped[str] = mapped_column(String(32))
    current_index: Mapped[int] = mapped_column(Integer, default=0)


class LeetCodeProgress(Base):
    __tablename__ = "leetcode_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[str] = mapped_column(String(64), index=True)
    level: Mapped[str] = mapped_column(String(8))
    tier_passed: Mapped[int] = mapped_column(Integer, default=0)  # highest tier passed (1-3)


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
    active_block: Mapped[str] = mapped_column(String(32), default="a1-variables")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(Streak).first():
            db.add(Streak())
        if not db.query(AppSettings).filter_by(key="focus_mode").first():
            db.add(AppSettings(key="focus_mode", value="false"))
        if not db.query(StudyDay).first():
            db.add(StudyDay(date=date.today(), day_number=1, active_block="a1-variables"))
        db.commit()
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
