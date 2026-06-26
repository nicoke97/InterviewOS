from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .kumon_hierarchy import (
    block_for_page,
    blocks_metadata,
    normalize_level,
    page_id as make_page_id,
    page_to_set,
    route_level,
)
from .slot_answers import resolve_slot_answers

ROOT = Path(__file__).resolve().parents[2]
CONTENT_DIR = ROOT / "content"


@dataclass
class KumonPage:
    id: str
    level: str
    page: int
    set: int
    block: str
    block_id: str
    order: int
    scaffolding: str
    prompt: str
    starter_code: str
    hints: list[str]
    validation: dict[str, Any]
    csharp_note: str = ""
    reference_code: str = ""
    slot_answers: list[str] = field(default_factory=list)
    time_estimate_seconds: int = 60


# Backward-compatible alias
KumonDrill = KumonPage


@dataclass
class LeetCodeProblem:
    id: str
    level: str
    title: str
    description: str
    fn_name: str
    tiers: dict[int, dict[str, Any]]
    test_cases: list[dict[str, Any]]


@dataclass
class InterviewQuestion:
    id: str
    level: str
    category: str  # python | odoo | git
    question: str
    rubric: list[str]
    sample_answer: str
    question_type: str = "open_text"


@dataclass
class Curriculum:
    kumon: dict[str, KumonPage] = field(default_factory=dict)
    leetcode: dict[str, LeetCodeProblem] = field(default_factory=dict)
    interview: dict[str, InterviewQuestion] = field(default_factory=dict)
    blocks: dict[str, dict] = field(default_factory=dict)
    progression: dict = field(default_factory=dict)


def _scaffolding_for_order(order: int) -> str:
    """Order is the 1..10 position within a set; scaffolding ramps down."""
    if order <= 3:
        return "full"
    if order <= 7:
        return "minimal"
    return "none"


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}



def _build_curriculum() -> Curriculum:
    curriculum = Curriculum()
    curriculum.blocks = blocks_metadata()

    prog_path = CONTENT_DIR / "schedule" / "kumon-progression.yaml"
    if prog_path.exists():
        curriculum.progression = load_yaml(prog_path)

    level_dirs = sorted((CONTENT_DIR / "levels").glob("level-*"))
    level_dirs += sorted((CONTENT_DIR / "odoo").glob("level-*"))
    for level_dir in level_dirs:
        folder_level = level_dir.name.replace("level-", "")

        kumon_dir = level_dir / "kumon"
        if kumon_dir.exists():
            for f in sorted(kumon_dir.glob("*.yaml")):
                data = load_yaml(f)
                if not data or "id" not in data:
                    continue
                order = data.get("order", 1)
                level = normalize_level(data.get("level", folder_level))
                page_num = data.get("page", order)
                set_num = data.get("set", page_to_set(page_num))
                block_letter = data.get("block", "A")
                bid = data.get("block_id") or block_for_page(level, page_num) or f"{level}.{block_letter}"
                page_key = data["id"]
                reference = data.get("reference_code") or data.get("_reference_code", "")
                starter = data.get("starter_code", "")
                validation = data.get("validation", {})
                explicit_slots = data.get("slot_answers")
                slot_answers = resolve_slot_answers(
                    starter,
                    validation,
                    reference_code=reference,
                    explicit=explicit_slots,
                    prompt=data.get("prompt", ""),
                )
                curriculum.kumon[page_key] = KumonPage(
                    id=page_key,
                    level=level,
                    page=page_num,
                    set=set_num,
                    block=block_letter,
                    block_id=bid,
                    order=order,
                    scaffolding=data.get("scaffolding", _scaffolding_for_order(order)),
                    prompt=data["prompt"],
                    starter_code=starter,
                    hints=data.get("hints", []),
                    validation=validation,
                    csharp_note=data.get("csharp_note", ""),
                    reference_code=reference,
                    slot_answers=slot_answers,
                    time_estimate_seconds=data.get("time_estimate_seconds", 60),
                )

        lc_dir = level_dir / "leetcode"
        if lc_dir.exists():
            for f in sorted(lc_dir.glob("*.yaml")):
                data = load_yaml(f)
                if not data or "id" not in data:
                    continue
                tiers_raw = data.get("tiers", {})
                tiers = {int(k): v for k, v in tiers_raw.items()}
                curriculum.leetcode[data["id"]] = LeetCodeProblem(
                    id=data["id"],
                    level=folder_level,
                    title=data.get("title", data["id"]),
                    description=data.get("description", ""),
                    fn_name=data.get("fn_name", "solution"),
                    tiers=tiers,
                    test_cases=data.get("test_cases", []),
                )

        for sub in ("interview", "odoo"):
            sub_dir = level_dir / sub
            if not sub_dir.exists():
                continue
            cat = "odoo" if sub == "odoo" else "python"
            for f in sorted(sub_dir.glob("*.yaml")):
                data = load_yaml(f)
                if not data or "id" not in data:
                    continue
                curriculum.interview[data["id"]] = InterviewQuestion(
                    id=data["id"],
                    level=folder_level,
                    category=data.get("category", cat),
                    question=data["question"],
                    rubric=data.get("rubric", []),
                    sample_answer=data.get("sample_answer", ""),
                    question_type=data.get("type", "open_text"),
                )

    return curriculum


@lru_cache(maxsize=1)
def _cached_curriculum() -> Curriculum:
    return _build_curriculum()


def load_curriculum() -> Curriculum:
    return _cached_curriculum()


def invalidate_curriculum_cache() -> None:
    _cached_curriculum.cache_clear()


def get_block_pages(curriculum: Curriculum, block_id: str) -> list[KumonPage]:
    pages = [p for p in curriculum.kumon.values() if p.block_id == block_id]
    return sorted(pages, key=lambda p: p.page)


def get_level_pages(curriculum: Curriculum, level: str) -> list[KumonPage]:
    lvl = level.upper()
    pages = [p for p in curriculum.kumon.values() if p.level.upper() == lvl]
    return sorted(pages, key=lambda p: p.page)


def get_set_pages(curriculum: Curriculum, level: str, set_number: int) -> list[KumonPage]:
    lvl = level.upper()
    pages = [
        p for p in curriculum.kumon.values()
        if p.level.upper() == lvl and p.set == set_number
    ]
    return sorted(pages, key=lambda p: p.page)


def get_block_drills(curriculum: Curriculum, block_id: str) -> list[KumonPage]:
    return get_block_pages(curriculum, block_id)


def get_level_blocks(curriculum: Curriculum, level: str) -> list[str]:
    rl = route_level(level)
    return [bid for bid, info in curriculum.blocks.items() if info.get("level") == rl]
