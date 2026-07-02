#!/usr/bin/env python3
"""Validate all curriculum YAML files."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.kumon_hierarchy import page_id as expected_page_id  # noqa: E402

CONTENT = ROOT / "content" / "levels"
SCHEDULE = ROOT / "content" / "schedule"
REQUIRED_BLOCKS = 12
REQUIRED_PAGES_PER_BLOCK = 20
REQUIRED_PAGES_PER_LEVEL = 80
REQUIRED_LEETCODE_PER_LEVEL = 4
REQUIRED_INTERVIEW_PER_LEVEL = 3


def page_to_set(page: int) -> int:
    return (page - 1) // 10 + 1


def main() -> int:
    errors: list[str] = []
    page_counts_by_block: dict[str, int] = {}
    page_counts_by_level: dict[str, int] = {}
    seen_ids: set[str] = set()
    leetcode_counts: dict[str, int] = {}
    interview_counts: dict[str, int] = {}
    odoo_counts: dict[str, int] = {}

    levels_yaml = yaml.safe_load((SCHEDULE / "kumon-levels.yaml").read_text(encoding="utf-8"))
    expected_blocks = {
        f"{lvl}.{blk}"
        for lvl, ldata in (levels_yaml.get("levels") or {}).items()
        for blk in (ldata.get("blocks") or {})
    }

    for level_dir in sorted(CONTENT.glob("level-*")):
        level = level_dir.name.replace("level-", "")
        kumon_dir = level_dir / "kumon"
        if kumon_dir.exists():
            for f in sorted(kumon_dir.glob("*.yaml")):
                data = yaml.safe_load(f.read_text(encoding="utf-8"))
                if not data:
                    errors.append(f"Empty file: {f}")
                    continue
                for field in ("id", "level", "page", "set", "block", "block_id", "order", "prompt", "validation"):
                    if field not in data:
                        errors.append(f"{f}: missing {field}")
                page_id = data.get("id", "")
                if page_id in seen_ids:
                    errors.append(f"Duplicate page id: {page_id}")
                seen_ids.add(page_id)

                level_letter = str(data.get("level", "")).upper()
                page_num = data.get("page", 0)
                expected_id = expected_page_id(level_letter, page_num)
                if page_id != expected_id:
                    errors.append(f"{f}: id {page_id} != expected {expected_id}")

                if data.get("set") != page_to_set(page_num):
                    errors.append(f"{f}: set {data.get('set')} != expected {page_to_set(page_num)}")

                block_id = data.get("block_id", "")
                if block_id not in expected_blocks:
                    errors.append(f"{f}: unknown block_id {block_id}")

                page_counts_by_block[block_id] = page_counts_by_block.get(block_id, 0) + 1
                page_counts_by_level[level_letter] = page_counts_by_level.get(level_letter, 0) + 1

                order = data.get("order", 0)
                if order <= 3 and data.get("scaffolding", "full") != "full":
                    errors.append(f"{f}: pages 1-3 in block should have scaffolding=full")
                if order > 3 and data.get("scaffolding") == "full":
                    errors.append(f"{f}: page order {order} should not have full scaffolding")

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

    for block_id, count in page_counts_by_block.items():
        if count != REQUIRED_PAGES_PER_BLOCK:
            errors.append(f"Block {block_id}: expected {REQUIRED_PAGES_PER_BLOCK} pages, got {count}")

    if len(page_counts_by_block) != REQUIRED_BLOCKS:
        errors.append(f"Expected {REQUIRED_BLOCKS} blocks, got {len(page_counts_by_block)}")

    for level_letter in ("A", "B", "C"):
        if page_counts_by_level.get(level_letter, 0) != REQUIRED_PAGES_PER_LEVEL:
            errors.append(
                f"Level {level_letter}: expected {REQUIRED_PAGES_PER_LEVEL} pages, "
                f"got {page_counts_by_level.get(level_letter, 0)}"
            )

    for level in ("a", "b", "c"):
        if leetcode_counts.get(level, 0) != REQUIRED_LEETCODE_PER_LEVEL:
            errors.append(f"Level {level}: expected {REQUIRED_LEETCODE_PER_LEVEL} leetcode, got {leetcode_counts.get(level, 0)}")
        if interview_counts.get(level, 0) != REQUIRED_INTERVIEW_PER_LEVEL:
            errors.append(f"Level {level}: expected {REQUIRED_INTERVIEW_PER_LEVEL} interview, got {interview_counts.get(level, 0)}")
        if odoo_counts.get(level, 0) != REQUIRED_INTERVIEW_PER_LEVEL:
            errors.append(f"Level {level}: expected {REQUIRED_INTERVIEW_PER_LEVEL} odoo, got {odoo_counts.get(level, 0)}")

    total_pages = sum(page_counts_by_level.values())
    print(f"Validated {total_pages} kumon pages, {sum(leetcode_counts.values())} leetcode, "
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
