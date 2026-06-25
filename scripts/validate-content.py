#!/usr/bin/env python3
"""Validate all curriculum YAML files."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "levels"
REQUIRED_BLOCKS = 12
REQUIRED_DRILLS_PER_BLOCK = 20
REQUIRED_LEETCODE_PER_LEVEL = 4
REQUIRED_INTERVIEW_PER_LEVEL = 3


def main() -> int:
    errors: list[str] = []
    drill_counts: dict[str, int] = {}
    leetcode_counts: dict[str, int] = {}
    interview_counts: dict[str, int] = {}
    odoo_counts: dict[str, int] = {}

    for level_dir in sorted(CONTENT.glob("level-*")):
        level = level_dir.name.replace("level-", "")
        kumon_dir = level_dir / "kumon"
        if kumon_dir.exists():
            for f in kumon_dir.glob("*.yaml"):
                data = yaml.safe_load(f.read_text(encoding="utf-8"))
                if not data:
                    errors.append(f"Empty file: {f}")
                    continue
                for field in ("id", "block", "order", "prompt", "validation"):
                    if field not in data:
                        errors.append(f"{f}: missing {field}")
                block = data.get("block", "")
                drill_counts[block] = drill_counts.get(block, 0) + 1
                order = data.get("order", 0)
                if order <= 3 and data.get("scaffolding", "full") != "full":
                    errors.append(f"{f}: drills 1-3 should have scaffolding=full")
                if order > 3 and data.get("scaffolding") == "full":
                    errors.append(f"{f}: drill {order} should not have full scaffolding")

        lc_dir = level_dir / "leetcode"
        if lc_dir.exists():
            for f in lc_dir.glob("*.yaml"):
                data = yaml.safe_load(f.read_text(encoding="utf-8"))
                if not data or "tiers" not in data:
                    errors.append(f"{f}: missing tiers")
                    continue
                if set(int(k) for k in data["tiers"]) != {1, 2, 3}:
                    errors.append(f"{f}: must have tiers 1, 2, 3")
                leetcode_counts[level] = leetcode_counts.get(level, 0) + 1

        for sub, counter in (("interview", interview_counts), ("odoo", odoo_counts)):
            sub_dir = level_dir / sub
            if sub_dir.exists():
                for f in sub_dir.glob("*.yaml"):
                    data = yaml.safe_load(f.read_text(encoding="utf-8"))
                    if not data or "question" not in data:
                        errors.append(f"{f}: missing question")
                    counter[level] = counter.get(level, 0) + 1

    for block, count in drill_counts.items():
        if count != REQUIRED_DRILLS_PER_BLOCK:
            errors.append(f"Block {block}: expected {REQUIRED_DRILLS_PER_BLOCK} drills, got {count}")

    if len(drill_counts) != REQUIRED_BLOCKS:
        errors.append(f"Expected {REQUIRED_BLOCKS} blocks, got {len(drill_counts)}")

    for level in ("a", "b", "c"):
        if leetcode_counts.get(level, 0) != REQUIRED_LEETCODE_PER_LEVEL:
            errors.append(f"Level {level}: expected {REQUIRED_LEETCODE_PER_LEVEL} leetcode, got {leetcode_counts.get(level, 0)}")
        if interview_counts.get(level, 0) != REQUIRED_INTERVIEW_PER_LEVEL:
            errors.append(f"Level {level}: expected {REQUIRED_INTERVIEW_PER_LEVEL} interview, got {interview_counts.get(level, 0)}")
        if odoo_counts.get(level, 0) != REQUIRED_INTERVIEW_PER_LEVEL:
            errors.append(f"Level {level}: expected {REQUIRED_INTERVIEW_PER_LEVEL} odoo, got {odoo_counts.get(level, 0)}")

    total_drills = sum(drill_counts.values())
    print(f"Validated {total_drills} kumon drills, {sum(leetcode_counts.values())} leetcode, "
          f"{sum(interview_counts.values())} interview, {sum(odoo_counts.values())} odoo")

    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("All content valid!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
