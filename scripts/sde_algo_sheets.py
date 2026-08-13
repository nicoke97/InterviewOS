"""Build 5+5+5+2 Kumon sheets for every interview LeetCode."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.leetcodes_csharp import csharp_spec  # noqa: E402

CONTENT = ROOT / "content" / "leetcodes"
SCHEDULE = ROOT / "content" / "schedule" / "leetcode-interview.yaml"
OUT = ROOT / "content" / "sde" / "algos"

PROMPTS = {
    1: "Rung 1: set up the start (structures / first line). Different variable names.",
    2: "Rung 2: the loop / the middle idea.",
    3: "Rung 3: the returns and the close.",
    4: "Full algorithm, first try.",
}
PROMPTS_ES = {
    1: "Peldaño 1: arma el inicio (estructuras / primera línea). Otras variables.",
    2: "Peldaño 2: el recorrido / la idea del medio.",
    3: "Peldaño 3: los return y el cierre.",
    4: "Algoritmo completo, a la primera.",
}

ARRAY_POOL = ["nums", "arr", "xs", "values", "items", "data", "seq", "vals"]
SCALAR_POOL = ["target", "goal", "want", "cap", "limit", "other", "needle", "bound"]
COUNT_POOL = ["n", "m", "k", "steps", "cap", "limit", "bound", "x"]
STR_POOL = ["s", "text", "src", "word", "raw", "chunk", "leftS", "probe"]
COUNTISH = {"n", "k", "m", "amount", "pos", "numcourses"}
STRISH = {"s", "t", "str", "text", "word"}

VOICE_BY_ID = {
    "two-sum": {
        "prompt": "¿Qué guarda el diccionario y por qué Two Sum es O(n)?",
        "prompt_en": "What does the dictionary store and why is Two Sum O(n)?",
        "keywords": ["diccionario", "dictionary", "mapa", "complemento", "índice", "index", "o(n)", "hash"],
    },
    "contains-duplicate": {
        "prompt": "¿Por qué un set y no un loop O(n²)?",
        "prompt_en": "Why a set instead of an O(n²) loop?",
        "keywords": ["set", "hash", "o(n)", "visto", "duplicado"],
    },
    "valid-anagram": {
        "prompt": "¿Qué comparas para saber si es anagrama?",
        "prompt_en": "What do you compare to know it is an anagram?",
        "keywords": ["frecuencia", "count", "longitud", "letra", "o(n)"],
    },
    "two-sum-ii": {
        "prompt": "¿Por qué dos punteros y no un diccionario aquí?",
        "prompt_en": "Why two pointers and not a dictionary here?",
        "keywords": ["ordenado", "puntero", "left", "right", "o(1)", "espacio"],
    },
}

CS_KEYWORDS = {
    "int", "string", "bool", "object", "var", "new", "return", "if", "else", "for",
    "foreach", "while", "class", "void", "null", "true", "false", "public", "static",
}


def _load(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def catalog_ids() -> list[str]:
    data = _load(SCHEDULE)
    ids: list[str] = []
    for topic in data.get("topics") or []:
        ids.extend(topic.get("problems") or [])
    return ids


def sde_id(lc_id: str) -> str:
    return lc_id.removeprefix("lc-")


def sde_algo_ids() -> list[str]:
    return [sde_id(x) for x in catalog_ids()]


def _idents(code: str) -> set[str]:
    return set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", code))


def _py_params(code: str, fn_name: str) -> list[str]:
    m = re.search(rf"def\s+{re.escape(fn_name)}\((.*?)\)\s*:", code)
    if not m:
        return []
    parts = []
    for raw in m.group(1).split(","):
        raw = raw.strip()
        if not raw or raw.startswith("*"):
            continue
        name = raw.split(":")[0].split("=")[0].strip()
        if name:
            parts.append(name)
    return parts


def _split_cs_params(inner: str) -> list[tuple[str, str]]:
    parts: list[str] = []
    depth = 0
    buf = []
    for ch in inner:
        if ch in "<[":
            depth += 1
            buf.append(ch)
        elif ch in ">]":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    out: list[tuple[str, str]] = []
    for raw in parts:
        toks = raw.split()
        if not toks:
            continue
        name = toks[-1].strip("[]")
        typ = " ".join(toks[:-1]) if len(toks) > 1 else ""
        if name and name not in CS_KEYWORDS:
            out.append((typ, name))
    return out


def _cs_params_typed(code: str, fn_name: str) -> list[tuple[str, str]]:
    m = re.search(rf"\b{re.escape(fn_name)}\s*\((.*?)\)", code, re.S)
    if not m:
        return []
    return _split_cs_params(m.group(1).replace("\n", " "))


def _pool_for(name: str, typ: str = "") -> list[str]:
    t = (typ or "").replace(" ", "").lower()
    key = name.lower()
    if "[]" in t or key in {"nums", "arr", "prices", "height", "intervals", "grid", "ops", "nodes", "strs", "coins", "values"}:
        return ARRAY_POOL
    if "string" in t or key in STRISH:
        return STR_POOL
    if key in {"target", "goal", "want"}:
        return SCALAR_POOL
    if key in COUNTISH or (t in {"int", "long"} and "[]" not in t):
        return COUNT_POOL
    if t in {"int", "long", "bool", "object"} or key in {"target", "goal", "want", "amount"}:
        return SCALAR_POOL
    return ARRAY_POOL if not t else SCALAR_POOL


def _rename(code: str, old: list[str], new: list[str], fn_name: str) -> str:
    mapping = []
    for i, o in enumerate(old):
        if i < len(new) and o != new[i] and o != fn_name:
            mapping.append((o, new[i]))
    mapping.sort(key=lambda x: len(x[0]), reverse=True)
    out = code
    for o, n in mapping:
        out = re.sub(rf"\b{re.escape(o)}\b", n, out)
    return out


def variant_names(code: str, params: list[str], variant: int, types: list[str] | None = None) -> list[str]:
    if not params:
        return []
    types = types or [""] * len(params)
    used = (_idents(code) - set(params)) | CS_KEYWORDS
    out: list[str] = []
    for i, original in enumerate(params):
        pool = _pool_for(original, types[i] if i < len(types) else "")
        start = variant % len(pool)
        ordered = pool[start:] + pool[:start]
        chosen = next((n for n in ordered if n not in used), f"{original}{variant + 1}")
        out.append(chosen)
        used.add(chosen)
    return out


def _lines(code: str) -> list[str]:
    return code.splitlines(True)


def _join(lines: list[str]) -> str:
    text = "".join(lines)
    if text and not text.endswith("\n"):
        text += "\n"
    return text


def _py_span(lines: list[str], fn_name: str) -> tuple[int, int] | None:
    start = None
    for i, line in enumerate(lines):
        if re.match(rf"def\s+{re.escape(fn_name)}\s*\(", line):
            start = i
            break
    if start is None:
        return None
    end = len(lines) - 1
    for i in range(start + 1, len(lines)):
        raw = lines[i]
        if raw.strip() and not raw[0].isspace() and not raw.lstrip().startswith("#"):
            end = i - 1
            break
    while end > start and not lines[end].strip():
        end -= 1
    return start, end


def _cs_span(lines: list[str], fn_name: str) -> tuple[int, int] | None:
    text = "".join(lines)
    m = re.search(rf"\b{re.escape(fn_name)}\s*\(", text)
    if not m:
        return None
    # Walk from the match to the signature's closing paren, then the opening brace.
    i = m.end() - 1  # at '('
    depth = 0
    while i < len(text):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                i += 1
                break
        i += 1
    while i < len(text) and text[i] in " \t\r\n":
        i += 1
    if i >= len(text) or text[i] != "{":
        return None
    brace_start = i
    depth = 0
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    start_line = text[: m.start()].count("\n")
    end_line = text[: i].count("\n")
    _ = brace_start
    return start_line, end_line


def _method_span(lines: list[str], fn_name: str, csharp: bool) -> tuple[int, int] | None:
    return _cs_span(lines, fn_name) if csharp else _py_span(lines, fn_name)


def _open_brace_line(lines: list[str], start: int, end: int) -> int:
    for i in range(start, end + 1):
        if "{" in lines[i]:
            return i
    return start


def _stmt_lines(lines: list[str], lo: int, hi: int) -> list[int]:
    out = []
    for i in range(lo, hi + 1):
        s = lines[i].strip()
        if not s or s in {"{", "}"} or s.startswith("//") or s.startswith("#"):
            continue
        if s.startswith("class ") or s.startswith("def "):
            continue
        out.append(i)
    return out


def _indent_of(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def punch(code: str, fn_name: str, rung: int, csharp: bool) -> str:
    lines = _lines(code)
    span = _method_span(lines, fn_name, csharp)
    if not span:
        return code
    start, end = span
    if csharp:
        body_lo = _open_brace_line(lines, start, end) + 1
        body_hi = end - 1
    else:
        body_lo = start + 1
        body_hi = end
    stmts = _stmt_lines(lines, body_lo, max(body_lo, body_hi))
    if not stmts:
        return code
    hole = f"{_indent_of(lines[stmts[0]])}___\n"

    if rung == 1:
        lines[stmts[0]] = hole
        return _join(lines)

    if rung == 2:
        loop = next(
            (i for i in stmts if re.search(r"\b(for|while|foreach)\b", lines[i])),
            None,
        )
        if loop is not None:
            last = stmts[-1]
            if re.search(r"\breturn\b", lines[last]) and last > loop:
                cut_end = stmts[-2] if len(stmts) > 1 else last
            else:
                cut_end = last
            if cut_end < loop:
                cut_end = loop
            lines[loop : cut_end + 1] = [f"{_indent_of(lines[loop])}___\n"]
            return _join(lines)
        if len(stmts) == 1:
            lines[stmts[0]] = hole
            return _join(lines)
        mid = stmts[len(stmts) // 3 : max(len(stmts) // 3 + 1, (2 * len(stmts)) // 3)]
        if not mid:
            mid = stmts[1:2] or stmts
        first, last = mid[0], mid[-1]
        lines[first : last + 1] = [f"{_indent_of(lines[first])}___\n"]
        return _join(lines)

    if rung == 3:
        returns = [i for i in stmts if re.search(r"\breturn\b", lines[i])]
        if not returns:
            lines[stmts[-1]] = f"{_indent_of(lines[stmts[-1]])}___\n"
            return _join(lines)
        for i in returns:
            lines[i] = f"{_indent_of(lines[i])}___\n"
        return _join(lines)
    return code


def _py_stub(code: str, fn_name: str, starter: str | None) -> str:
    if starter and starter.strip():
        return starter if starter.endswith("\n") else starter + "\n"
    m = re.search(rf"def\s+{re.escape(fn_name)}\([^)]*\)\s*:", code)
    sig = m.group(0) if m else f"def {fn_name}(*args):"
    last = "None"
    for line in code.splitlines():
        stripped = line.strip()
        if stripped.startswith("return ") and "___" not in stripped:
            last = stripped[7:]
    return f"{sig}\n    # write the full algorithm\n    return {last}\n"


def _cs_stub(code: str, fn_name: str, starter: str | None) -> str:
    lines = _lines(code)
    span = _cs_span(lines, fn_name)
    prefix = _join(lines[: span[0]]) if span else ""
    if starter and starter.strip():
        body = starter if starter.endswith("\n") else starter + "\n"
        return prefix + body
    if not span:
        return code
    sig = "".join(lines[span[0] : _open_brace_line(lines, span[0], span[1]) + 1])
    last = "default"
    for line in lines[span[0] : span[1] + 1]:
        if "return" in line and "___" not in line:
            last = line.strip().rstrip(";").replace("return ", "", 1)
            break
    if not sig.strip().endswith("{"):
        sig = sig.rstrip() + "\n{\n"
    return f"{prefix}{sig}    // write the full algorithm\n    return {last};\n}}\n"


def sheets_for(
    full: str,
    fn_name: str,
    csharp: bool,
    stub_src: str | None,
) -> list[dict]:
    typed = _cs_params_typed(full, fn_name) if csharp else [("", p) for p in _py_params(full, fn_name)]
    old = [name for _, name in typed]
    types = [typ for typ, _ in typed]
    out: list[dict] = []
    for rung in (1, 2, 3):
        for i in range(5):
            names = variant_names(full, old, i, types)
            renamed = _rename(full, old, names, fn_name)
            out.append({
                "id": f"r{rung}-{i + 1:02d}",
                "rung": rung,
                "kind": "rung",
                "fn_name": fn_name,
                "prompt": PROMPTS[rung],
                "prompt_es": PROMPTS_ES[rung],
                "starter_code": punch(renamed, fn_name, rung, csharp),
            })
    for i in range(2):
        names = variant_names(full, old, i, types)
        renamed = _rename(full, old, names, fn_name)
        stub = _cs_stub(renamed, fn_name, _rename(stub_src or "", old, names, fn_name) if stub_src else None) if csharp else _py_stub(
            renamed, fn_name, _rename(stub_src or "", old, names, fn_name) if stub_src else None
        )
        out.append({
            "id": f"full-{i + 1:02d}",
            "rung": 4,
            "kind": "full",
            "fn_name": fn_name,
            "prompt": PROMPTS[4],
            "prompt_es": PROMPTS_ES[4],
            "starter_code": stub,
        })
    names = variant_names(full, old, 2, types)
    renamed = _rename(full, old, names, fn_name)
    stub = _cs_stub(renamed, fn_name, _rename(stub_src or "", old, names, fn_name) if stub_src else None) if csharp else _py_stub(
        renamed, fn_name, _rename(stub_src or "", old, names, fn_name) if stub_src else None
    )
    out.append({
        "id": "full-recall",
        "rung": 4,
        "kind": "full",
        "fn_name": fn_name,
        "prompt": "Day 2 / pool: the whole thing, first try.",
        "prompt_es": "Día 2 / pool: el entero, a la primera.",
        "starter_code": stub,
    })
    return out


def voice_for(aid: str, prob: dict) -> dict:
    if aid in VOICE_BY_ID:
        return VOICE_BY_ID[aid]
    qs = [str(q) for q in (prob.get("interview_questions") or []) if q]
    prompt = qs[0] if qs else "¿Cuál es el enfoque y la complejidad?"
    if "¿" not in prompt and not prompt.endswith("?"):
        prompt = f"¿{prompt}?"
    elif "¿" not in prompt:
        prompt = f"¿{prompt.rstrip('?')}?"
    text = " ".join(str(x) for x in (prob.get("learning") or []) + qs)
    stop = {
        "entre", "cuando", "cual", "cuál", "como", "cómo", "para", "este", "esta",
        "estos", "where", "which", "would", "could", "about", "their", "there",
    }
    keys = ["o(n)", "o(1)", "complejidad", "enfoque"]
    for word in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúñÑ]{5,}", text.lower()):
        if word in keys or word in stop:
            continue
        keys.append(word)
        if len(keys) >= 10:
            break
    return {
        "prompt": prompt,
        "prompt_en": "Explain the approach and the complexity out loud.",
        "keywords": keys,
    }


def py_starter(prob: dict) -> str:
    tiers = prob.get("tiers") or {}
    t1 = tiers.get(1) or tiers.get("1") or {}
    return (t1.get("starter_code") or "").rstrip() + "\n"


def build_all_algos() -> list[str]:
    written: list[str] = []
    OUT.mkdir(parents=True, exist_ok=True)
    for lc_id in catalog_ids():
        path = CONTENT / f"{lc_id}.yaml"
        if not path.exists():
            continue
        prob = _load(path)
        py_fn = prob.get("fn_name", "solution")
        py_full = (prob.get("solution_code") or "").rstrip() + "\n"
        cs = csharp_spec(lc_id, 1) or {}
        cs_fn = cs.get("fn_name") or py_fn
        cs_full = (cs.get("solution_code") or "").rstrip() + "\n"
        if not py_full.strip() or not cs_full.strip():
            continue
        aid = sde_id(lc_id)
        payload = {
            "id": aid,
            "title": prob.get("title", aid),
            "leetcode_id": lc_id,
            "test_cases": prob.get("test_cases") or [],
            "voice": voice_for(aid, prob),
            "languages": {
                "csharp": {
                    "fn_name": cs_fn,
                    "sheets": sheets_for(cs_full, cs_fn, True, cs.get("starter_code")),
                },
                "python": {
                    "fn_name": py_fn,
                    "sheets": sheets_for(py_full, py_fn, False, py_starter(prob)),
                },
            },
        }
        (OUT / f"{aid}.yaml").write_text(
            yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=100),
            encoding="utf-8",
        )
        written.append(aid)
    return written
