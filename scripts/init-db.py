#!/usr/bin/env python3
"""Initialize the InterviewOS SQLite database."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.models import init_db

if __name__ == "__main__":
    init_db()
    print("Database initialized at data/progress.db")
