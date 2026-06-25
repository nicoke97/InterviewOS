from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTENT_DIR = ROOT / "content"


@dataclass
class KumonDrill:
    id: str
    block: str
    level: str
    order: int
    scaffolding: str
    prompt: str
    starter_code: str
    hints: list[str]
    validation: dict[str, Any]
    csharp_note: str = ""


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
    kumon: dict[str, KumonDrill] = field(default_factory=dict)
    leetcode: dict[str, LeetCodeProblem] = field(default_factory=dict)
    interview: dict[str, InterviewQuestion] = field(default_factory=dict)
    blocks: dict[str, dict] = field(default_factory=dict)
    progression: dict = field(default_factory=dict)


def _scaffolding_for_order(order: int) -> str:
    if order <= 3:
        return "full"
    if order <= 10:
        return "minimal"
    return "none"


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_curriculum() -> Curriculum:
    curriculum = Curriculum()

    prog_path = CONTENT_DIR / "schedule" / "kumon-progression.yaml"
    if prog_path.exists():
        curriculum.progression = load_yaml(prog_path)

    blocks_path = CONTENT_DIR / "schedule" / "blocks.yaml"
    if blocks_path.exists():
        data = load_yaml(blocks_path)
        curriculum.blocks = data.get("blocks", {})

    for level_dir in sorted((CONTENT_DIR / "levels").glob("level-*")):
        level = level_dir.name.replace("level-", "")

        kumon_dir = level_dir / "kumon"
        if kumon_dir.exists():
            for f in sorted(kumon_dir.glob("*.yaml")):
                data = load_yaml(f)
                if not data or "id" not in data:
                    continue
                order = data.get("order", 1)
                curriculum.kumon[data["id"]] = KumonDrill(
                    id=data["id"],
                    block=data["block"],
                    level=level,
                    order=order,
                    scaffolding=data.get("scaffolding", _scaffolding_for_order(order)),
                    prompt=data["prompt"],
                    starter_code=data.get("starter_code", ""),
                    hints=data.get("hints", []),
                    validation=data.get("validation", {}),
                    csharp_note=data.get("csharp_note", ""),
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
                    level=level,
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
                    level=level,
                    category=data.get("category", cat),
                    question=data["question"],
                    rubric=data.get("rubric", []),
                    sample_answer=data.get("sample_answer", ""),
                    question_type=data.get("type", "open_text"),
                )

    return curriculum


def get_block_drills(curriculum: Curriculum, block_id: str) -> list[KumonDrill]:
    drills = [d for d in curriculum.kumon.values() if d.block == block_id]
    return sorted(drills, key=lambda d: d.order)


def get_level_blocks(curriculum: Curriculum, level: str) -> list[str]:
    prefix = level[0] if level else "a"
    return [bid for bid, info in curriculum.blocks.items() if info.get("level") == level or bid.startswith(prefix)]
