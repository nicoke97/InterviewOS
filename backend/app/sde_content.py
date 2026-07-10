"""Load SDE program content (theory, algorithms, SQL)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
SDE_DIR = ROOT / "content" / "sde"


def _load(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def load_sde() -> dict[str, Any]:
    program = _load(SDE_DIR / "program.yaml")
    sections = _load(SDE_DIR / "sections.yaml").get("sections") or []
    sql = _load(SDE_DIR / "sql.yaml").get("drills") or []
    algos: dict[str, dict] = {}
    for p in sorted((SDE_DIR / "algos").glob("*.yaml")):
        data = _load(p)
        algos[data["id"]] = data
    by_id = {s["id"]: s for s in sections}
    cards: list[dict] = []
    for s in sections:
        for c in s.get("cards") or []:
            cards.append({**c, "section_id": s["id"]})
    return {
        "program": program,
        "sections": sections,
        "section_by_id": by_id,
        "cards": cards,
        "sql": sql,
        "algos": algos,
        "algo_order": program.get("algos") or [],
        "first_lang": program.get("first_lang", "csharp"),
        "second_lang": program.get("second_lang", "python"),
        "card_cap": int(program.get("card_cap", 40)),
        "card_cap_light": int(program.get("card_cap_light", 12)),
        "inactivity_days": int(program.get("inactivity_days", 3)),
    }


def invalidate_sde_cache() -> None:
    load_sde.cache_clear()


def day1_sheet_ids(algo: dict, lang: str) -> list[str]:
    sheets = (algo.get("languages") or {}).get(lang, {}).get("sheets") or []
    rungs = {1: [], 2: [], 3: [], 4: []}
    for s in sheets:
        if s.get("kind") == "full" and s["id"] == "full-recall":
            continue
        rungs.setdefault(int(s.get("rung", 0)), []).append(s["id"])
    return rungs.get(1, []) + rungs.get(2, []) + rungs.get(3, []) + [i for i in rungs.get(4, []) if i.startswith("full-")]


def recovery_sheet_ids(algo: dict, lang: str) -> list[str]:
    sheets = (algo.get("languages") or {}).get(lang, {}).get("sheets") or []
    pick = {}
    for s in sheets:
        r = int(s.get("rung", 0))
        if r in (1, 2, 3) and r not in pick:
            pick[r] = s["id"]
    ids = [pick[r] for r in (1, 2, 3) if r in pick]
    if any(s["id"] == "full-recall" for s in sheets):
        ids.append("full-recall")
    return ids


def get_sheet(algo: dict, lang: str, sheet_id: str) -> dict | None:
    for s in (algo.get("languages") or {}).get(lang, {}).get("sheets") or []:
        if s["id"] == sheet_id:
            return s
    return None
