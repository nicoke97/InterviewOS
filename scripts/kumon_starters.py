"""Build Kumon starter templates with ___ slots for full scaffolding (order 1-3)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.slot_answers import extract_slot_answers  # noqa: E402


def _blank_assignment(line: str) -> str:
    m = re.match(r"^(\s*)(\w+)\s*=\s*.+", line)
    if m:
        return f"{m.group(1)}{m.group(2)} = ___"
    return line


def _blank_for_header(line: str) -> str:
    m = re.match(r"^(\s*for \w+ in )(.+?)(:?\s*)$", line)
    if m:
        colon = ":" if ":" in line else ""
        return f"{m.group(1)}___{colon}"
    m = re.match(r"^(\s*while )(.+?)(:?\s*)$", line)
    if m:
        colon = ":" if ":" in line else ""
        return f"{m.group(1)}___{colon}"
    return line


def _blank_print(line: str, *, blank_var: bool = False) -> str:
    m = re.match(r"^(\s*)print\((.+)\)\s*$", line)
    if not m:
        return line
    inner = m.group(2).strip()
    if not blank_var and re.match(r"^[a-zA-Z_]\w*$", inner):
        return f"{m.group(1)}print({inner})"
    if not blank_var and "," in inner:
        # Keep structured calls like print(i, end=' ')
        return line
    return f"{m.group(1)}print(___)"


def build_starter(code: str, order: int) -> str:
    """Return a starter template for full scaffolding (order 1..3)."""
    code = code.strip()
    if order > 3 or not code:
        return ""

    if order == 3:
        return "___" if "\n" not in code else "# Completa el codigo\n___"

    lines = code.split("\n")

    if order == 1:
        if len(lines) == 1:
            return "print(___)" if code.startswith("print(") else "___"
        out: list[str] = []
        for line in lines:
            stripped = line.strip()
            if re.match(r"\w+\s*=", stripped):
                out.append(_blank_assignment(line))
            elif stripped.startswith("print("):
                out.append(_blank_print(line, blank_var=False))
            elif stripped == "pass":
                out.append(line)
            elif stripped.startswith(("for ", "while ")):
                out.append(_blank_for_header(line))
            elif stripped.startswith(("class ", "def ")):
                out.append(line)
            elif stripped.startswith(("if ", "elif ")):
                out.append(re.sub(r"((?:if|elif) .+)", r"\1", line))  # keep condition for now
            else:
                out.append(_blank_print(line) if "print(" in line else line)
        return "\n".join(out)

    # order == 2 — more blanks, less fixed text
    if len(lines) == 1:
        return "# Escribe tu codigo\nprint(___)" if code.startswith("print(") else "___"
    out = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"\w+\s*=", stripped):
            out.append(_blank_assignment(line))
        elif stripped.startswith("print("):
            out.append(_blank_print(line, blank_var=True))
        elif stripped == "pass":
            indent = line[: len(line) - len(line.lstrip())]
            out.append(f"{indent}___")
        elif stripped.startswith(("for ", "while ")):
            out.append(_blank_for_header(line))
        elif stripped.startswith("class "):
            out.append(line)
        else:
            out.append(_blank_print(line, blank_var=True) if "print(" in line else line)
    return "\n".join(out)


def slot_answers_ok(starter: str, code: str) -> bool:
    answers = extract_slot_answers(starter, code)
    if not answers:
        return False
    assembled = starter
    for answer in answers:
        assembled = assembled.replace("___", answer, 1)
    return assembled.replace("\r\n", "\n").strip() == code.replace("\r\n", "\n").strip()


def safe_starter(code: str, order: int) -> str:
    """Build starter and fall back to a single slot if parsing fails."""
    starter = build_starter(code, order)
    if not starter or "___" not in starter:
        starter = "___"
    if slot_answers_ok(starter, code):
        return starter
    if order == 3:
        return "___"
    if code.strip().startswith("print(") and "\n" not in code.strip():
        return "print(___)"
    return "___" if "\n" in code.strip() else "print(___)"
