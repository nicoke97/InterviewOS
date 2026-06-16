"""Client for the persistent C# execution runner (backend/csharp-runner).

The runner is a long-lived `dotnet` process that compiles and runs C# snippets
in-process via Roslyn scripting. Keeping it alive avoids paying the compiler
warm-up cost on every drill. We talk to it with newline-delimited JSON over
stdin/stdout, guarded by a lock so concurrent requests don't interleave.

Public API mirrors `executor.py` so the dispatcher can treat both languages the
same way.
"""
from __future__ import annotations

import atexit
import json
import subprocess
import threading
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RUNNER_DIR = ROOT / "backend" / "csharp-runner"
RUNNER_DLL = RUNNER_DIR / "bin" / "Release" / "net10.0" / "csharp-runner.dll"

_proc: subprocess.Popen | None = None
_lock = threading.Lock()


def _ensure_built() -> None:
    if RUNNER_DLL.exists():
        return
    subprocess.run(
        ["dotnet", "build", "-c", "Release"],
        cwd=str(RUNNER_DIR),
        check=True,
        capture_output=True,
        text=True,
    )


def _start() -> subprocess.Popen:
    global _proc
    _ensure_built()
    _proc = subprocess.Popen(
        ["dotnet", str(RUNNER_DLL)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    # Consume the initial {"type":"ready"} handshake line.
    ready = _proc.stdout.readline()
    if not ready:
        raise RuntimeError("C# runner failed to start")
    return _proc


def _get_proc() -> subprocess.Popen:
    global _proc
    if _proc is None or _proc.poll() is not None:
        _start()
    return _proc


def _request(payload: dict[str, Any]) -> dict[str, Any]:
    line = json.dumps(payload, ensure_ascii=True)
    with _lock:
        for attempt in (1, 2):
            proc = _get_proc()
            try:
                proc.stdin.write(line + "\n")
                proc.stdin.flush()
                out = proc.stdout.readline()
                if not out:
                    raise BrokenPipeError("empty response")
                return json.loads(out)
            except (BrokenPipeError, OSError, ValueError):
                # Runner died or produced garbage; restart once and retry.
                global _proc
                _proc = None
                if attempt == 2:
                    return {"error": "El motor de C# no respondió"}
    return {"error": "El motor de C# no respondió"}


@atexit.register
def _shutdown() -> None:
    global _proc
    if _proc and _proc.poll() is None:
        try:
            _proc.stdin.close()
        except Exception:
            pass
        try:
            _proc.terminate()
        except Exception:
            pass
    _proc = None


def run_csharp_kumon(code: str, validation: dict[str, Any], timeout: int = 5) -> dict[str, Any]:
    vtype = validation.get("type", "run_and_match_stdout")
    full_code = code
    if validation.get("setup"):
        full_code = validation["setup"] + "\n" + code

    if vtype in ("run_and_match_stdout", "run_and_match_value", "exact_match"):
        # C# content is stdout-based; other validation types fall back to stdout.
        resp = _request({
            "type": "run",
            "code": full_code,
            "expected": str(validation.get("expected", "")),
            "timeoutMs": timeout * 1000,
        })
        if "error" in resp and "passed" not in resp:
            return {"passed": False, "stdout": "", "expected": str(validation.get("expected", "")), "error": resp["error"]}
        return {
            "passed": resp.get("passed", False),
            "stdout": resp.get("stdout", ""),
            "expected": resp.get("expected", ""),
            "error": resp.get("error"),
        }

    return {"passed": False, "error": f"Tipo de validación desconocido: {vtype}"}


def run_csharp_leetcode(code: str, test_cases: list[dict], fn_name: str = "Solution", timeout: int = 5) -> dict[str, Any]:
    resp = _request({
        "type": "leetcode",
        "code": code,
        "fnName": fn_name,
        "testCases": [
            {"args": tc.get("args", []), "expected": tc.get("expected")}
            for tc in test_cases
        ],
        "timeoutMs": timeout * 1000,
    })
    if "error" in resp and "results" not in resp:
        return {"passed": False, "results": [], "error": resp["error"]}
    return {
        "passed": resp.get("passed", False),
        "results": resp.get("results", []),
        "error": resp.get("error"),
    }
