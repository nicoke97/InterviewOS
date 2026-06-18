from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

FORBIDDEN_IMPORTS = {"os", "subprocess", "socket", "shutil", "sys", "ctypes", "signal"}


def _compare_values(actual, expected) -> bool:
    if actual == expected:
        return True
    if isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            return False
        if actual and isinstance(actual[0], list):
            norm = lambda lst: sorted([sorted(x) if isinstance(x, list) else x for x in lst])
            return norm(actual) == norm(expected)
        if actual and isinstance(actual[0], dict):
            return sorted(actual, key=str) == sorted(expected, key=str)
        try:
            return sorted(actual) == sorted(expected)
        except TypeError:
            return False
    if isinstance(actual, dict) and isinstance(expected, dict):
        return actual == expected
    return False


def _check_ast(code: str) -> str | None:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Syntax error: {e}"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in FORBIDDEN_IMPORTS:
                    return f"Import of '{alias.name}' is not allowed"
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in FORBIDDEN_IMPORTS:
                return f"Import from '{node.module}' is not allowed"
    return None


def run_kumon_code(code: str, validation: dict[str, Any], timeout: int = 5, language: str = "python") -> dict[str, Any]:
    if language == "csharp":
        from .csharp_executor import run_csharp_kumon
        return run_csharp_kumon(code, validation, timeout)

    err = _check_ast(code)
    if err:
        return {"passed": False, "error": err, "stdout": "", "expected": validation.get("expected", "")}

    vtype = validation.get("type", "run_and_match_stdout")
    full_code = code
    if validation.get("setup"):
        full_code = validation["setup"] + "\n" + code

    if vtype == "run_and_match_stdout":
        result = _run_subprocess(full_code, timeout)
        if result.get("error"):
            return {**result, "passed": False, "expected": validation.get("expected", "")}
        actual = result["stdout"].strip()
        expected = str(validation.get("expected", "")).strip()
        passed = actual == expected
        return {
            "passed": passed,
            "stdout": actual,
            "expected": expected,
            "error": None if passed else f"Expected: {expected!r}, Got: {actual!r}",
        }

    if vtype == "run_and_match_value":
        wrapped = full_code + "\nimport json\nprint(json.dumps(result))"
        result = _run_subprocess(wrapped, timeout)
        if result.get("error"):
            return {**result, "passed": False}
        try:
            actual = json.loads(result["stdout"].strip())
        except json.JSONDecodeError:
            return {"passed": False, "error": "Could not parse output", "stdout": result["stdout"]}
        expected = validation.get("expected")
        passed = actual == expected
        return {"passed": passed, "stdout": str(actual), "expected": str(expected), "error": None if passed else "Value mismatch"}

    if vtype == "exact_match":
        passed = code.strip() == validation.get("expected", "").strip()
        return {"passed": passed, "stdout": code.strip(), "expected": validation.get("expected", ""), "error": None if passed else "Code does not match expected"}

    return {"passed": False, "error": f"Unknown validation type: {vtype}"}


def run_leetcode_code(code: str, test_cases: list[dict], fn_name: str = "solution", timeout: int = 5, language: str = "python") -> dict[str, Any]:
    if language == "csharp":
        from .csharp_executor import run_csharp_leetcode
        return run_csharp_leetcode(code, test_cases, fn_name, timeout)

    err = _check_ast(code)
    if err:
        return {"passed": False, "error": err, "results": []}

    results = []
    all_passed = True
    for i, tc in enumerate(test_cases):
        args = tc.get("args", [])
        expected = tc.get("expected")
        harness = f"""
{code}

import json
_args = {repr(args)}
_result = {fn_name}(*_args) if len(_args) > 1 else ({fn_name}(_args[0]) if len(_args) == 1 else {fn_name}())
print(json.dumps(_result))
"""
        result = _run_subprocess(harness, timeout)
        if result.get("error"):
            results.append({"case": i + 1, "passed": False, "error": result["error"]})
            all_passed = False
            continue
        try:
            actual = json.loads(result["stdout"].strip())
        except json.JSONDecodeError:
            results.append({"case": i + 1, "passed": False, "error": "Invalid output", "stdout": result["stdout"]})
            all_passed = False
            continue
        passed = _compare_values(actual, expected)
        if not passed:
            all_passed = False
        results.append({"case": i + 1, "passed": passed, "expected": expected, "actual": actual})

    return {"passed": all_passed, "results": results, "error": None if all_passed else "Some test cases failed"}


def _run_subprocess(code: str, timeout: int) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        path = f.name
    try:
        proc = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode != 0:
            return {"error": proc.stderr.strip() or "Runtime error", "stdout": proc.stdout}
        return {"stdout": proc.stdout, "error": None}
    except subprocess.TimeoutExpired:
        return {"error": f"Timeout ({timeout}s exceeded)", "stdout": ""}
    finally:
        Path(path).unlink(missing_ok=True)
