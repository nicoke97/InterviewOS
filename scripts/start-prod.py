#!/usr/bin/env python3
"""Build frontend (if needed), init DB, and run production server."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
DIST_INDEX = ROOT / "frontend" / "dist" / "index.html"

os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("SERVE_STATIC", "true")
os.environ.setdefault("HOST", "0.0.0.0")
os.environ.setdefault("PORT", "8001")


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd or ROOT, check=True)


def main() -> None:
    if not DIST_INDEX.is_file():
        print("Building frontend…", flush=True)
        run(["npm", "run", "build"])

    run([sys.executable, str(ROOT / "scripts" / "init-db.py")])

    host = os.environ["HOST"]
    port = os.environ["PORT"]
    print(f"Starting Codenda on http://{host}:{port}", flush=True)
    run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            host,
            "--port",
            port,
        ],
        cwd=BACKEND,
    )


if __name__ == "__main__":
    main()
