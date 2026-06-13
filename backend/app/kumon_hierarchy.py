from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCHEDULE_DIR = ROOT / "content" / "schedule"
LEVELS_PATH = SCHEDULE_DIR / "kumon-levels.yaml"
ODOO_LEVELS_PATH = SCHEDULE_DIR / "odoo-levels.yaml"
CSHARP_LEVELS_PATH = SCHEDULE_DIR / "csharp-levels.yaml"

# All curriculum files, in order. Each may define its own `track`.
LEVEL_FILES = [LEVELS_PATH, ODOO_LEVELS_PATH, CSHARP_LEVELS_PATH]


@dataclass(frozen=True)
class SetDef:
    level: str          # e.g. "A"
    set_number: int     # 1..20 within the level
    block_letter: str   # "A".."D"
    title: str
    standard_seconds: int
    page_start: int
    page_end: int


@dataclass(frozen=True)
class BlockDef:
    letter: str
    title: str
    page_start: int
    page_end: int
    block_id: str
    level: str
    extra: bool = False


@dataclass(frozen=True)
class LevelDef:
    letter: str
    title: str
    track: str
    pages_per_level: int
    pages_per_set: int
    pages_per_block: int
    blocks: dict[str, BlockDef]
    sets: tuple[SetDef, ...] = field(default_factory=tuple)
    checkpoints: dict[str, list[str]] = field(default_factory=dict)
    exam: dict[str, list[str]] = field(default_factory=dict)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _mtimes() -> tuple[float, ...]:
    return tuple(p.stat().st_mtime if p.exists() else 0.0 for p in LEVEL_FILES)


def load_kumon_levels() -> dict[str, LevelDef]:
    return _parse_all_levels(_mtimes())


@lru_cache
def _parse_all_levels(_mtimes: tuple[float, ...]) -> dict[str, LevelDef]:
    levels: dict[str, LevelDef] = {}
    for path in LEVEL_FILES:
        data = _load_yaml(path)
        track = data.get("track", "python")
        checkpoints_all = data.get("checkpoints") or {}
        exam_all = data.get("completion_exam") or {}
        for level_letter, level_data in (data.get("levels") or {}).items():
            level_letter = level_letter.upper()
            pages_per_set = level_data.get("pages_per_set", 10)
            pages_per_block = level_data.get("pages_per_block", 50)
            blocks: dict[str, BlockDef] = {}
            sets: list[SetDef] = []
            for block_letter, block_data in (level_data.get("blocks") or {}).items():
                block_letter = block_letter.upper()
                bid = block_id(level_letter, block_letter)
                blocks[block_letter] = BlockDef(
                    letter=block_letter,
                    title=block_data["title"],
                    page_start=block_data["page_start"],
                    page_end=block_data["page_end"],
                    block_id=bid,
                    level=level_letter,
                    extra=bool(block_data.get("extra")),
                )
                block_start = block_data["page_start"]
                for i, set_data in enumerate(block_data.get("sets") or []):
                    page_start = block_start + i * pages_per_set
                    page_end = page_start + pages_per_set - 1
                    set_number = (page_start - 1) // pages_per_set + 1
                    sets.append(
                        SetDef(
                            level=level_letter,
                            set_number=set_number,
                            block_letter=block_letter,
                            title=set_data.get("title", f"Set {set_number}"),
                            standard_seconds=set_data.get("standard_seconds", 600),
                            page_start=page_start,
                            page_end=page_end,
                        )
                    )
            sets.sort(key=lambda s: s.set_number)
            route = route_level(level_letter)
            levels[level_letter] = LevelDef(
                letter=level_letter,
                title=level_data.get("title", f"Level {level_letter}"),
                track=track,
                pages_per_level=level_data.get("pages_per_level", 200),
                pages_per_set=pages_per_set,
                pages_per_block=pages_per_block,
                blocks=blocks,
                sets=tuple(sets),
                checkpoints=checkpoints_all.get(route, {}),
                exam=exam_all.get(route, {}),
            )
    return levels


def load_block_instructions() -> dict[str, str]:
    return _parse_block_instructions(_mtimes())


@lru_cache
def _parse_block_instructions(_mtimes: tuple[float, ...]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for path in LEVEL_FILES:
        data = _load_yaml(path)
        merged.update(data.get("instructions") or {})
    return merged


def normalize_level(level: str) -> str:
    return level.upper() if level else "A"


def route_level(level: str) -> str:
    return normalize_level(level).lower()


def page_id(level: str, page_num: int) -> str:
    return f"{normalize_level(level)}{page_num}"


def page_belongs_to_level(page_id: str, level: str) -> bool:
    lvl = normalize_level(level)
    pid = page_id.upper()
    if not pid.startswith(lvl):
        return False
    rest = pid[len(lvl):]
    return rest.isdigit() and int(rest) > 0


def page_to_set(page_num: int, pages_per_set: int = 10) -> int:
    return (page_num - 1) // pages_per_set + 1


def block_id(level: str, block_letter: str) -> str:
    return f"{normalize_level(level)}.{block_letter.upper()}"


def level_from_block_id(bid: str) -> str:
    if not bid:
        return "a"
    return bid.split(".")[0].lower()


def block_order(level: str) -> list[str]:
    level_def = load_kumon_levels().get(normalize_level(level))
    if not level_def:
        return []
    return [b.block_id for b in _sorted_blocks(level_def)]


def level_blocks(level: str) -> list[str]:
    return block_order(level)


def all_block_order() -> list[str]:
    order: list[str] = []
    for level_letter in sorted(load_kumon_levels()):
        order.extend(block_order(level_letter))
    return order


def _sorted_blocks(level_def: LevelDef) -> list[BlockDef]:
    return sorted(level_def.blocks.values(), key=lambda b: b.page_start)


def get_block_def(bid: str) -> BlockDef | None:
    if not bid or "." not in bid:
        return None
    level_letter, block_letter = bid.split(".", 1)
    level_def = load_kumon_levels().get(level_letter.upper())
    if not level_def:
        return None
    return level_def.blocks.get(block_letter.upper())


def block_title(bid: str, locale: str = "en") -> str:
    from .schedule_i18n import localize_title

    block = get_block_def(bid)
    title = block.title if block else bid
    return localize_title(title, locale)


def block_instruction(bid: str, locale: str = "en") -> str:
    from .schedule_i18n import localize_instruction

    default = "Resuelve cada problema. Revisa todas tus respuestas al terminar."
    instruction = load_block_instructions().get(bid, default)
    return localize_instruction(bid, instruction, locale)


def block_for_page(level: str, page_num: int) -> str | None:
    level_def = load_kumon_levels().get(normalize_level(level))
    if not level_def:
        return None
    for block in _sorted_blocks(level_def):
        if block.page_start <= page_num <= block.page_end:
            return block.block_id
    return None


def first_block_id(level: str) -> str:
    blocks = block_order(level)
    return blocks[0] if blocks else "A.A"


# ---------------------------------------------------------------------------
# Set-level helpers (new Kumon mastery model)
# ---------------------------------------------------------------------------

def level_sets(level: str) -> list[SetDef]:
    level_def = load_kumon_levels().get(normalize_level(level))
    return list(level_def.sets) if level_def else []


def get_set_def(level: str, set_number: int) -> SetDef | None:
    for s in level_sets(level):
        if s.set_number == set_number:
            return s
    return None


def set_count(level: str) -> int:
    return len(level_sets(level))


def set_title(level: str, set_number: int, locale: str = "en") -> str:
    from .schedule_i18n import localize_title

    s = get_set_def(level, set_number)
    title = s.title if s else f"Set {set_number}"
    return localize_title(title, locale)


def set_standard_seconds(level: str, set_number: int) -> int:
    s = get_set_def(level, set_number)
    return s.standard_seconds if s else 600


def set_for_page(level: str, page_num: int) -> int:
    return page_to_set(page_num)


def block_letter_for_set(level: str, set_number: int) -> str:
    s = get_set_def(level, set_number)
    return s.block_letter if s else "A"


def sets_in_block(level: str, block_letter: str) -> list[SetDef]:
    return [s for s in level_sets(level) if s.block_letter == block_letter.upper()]


def is_extra_block(level: str, block_letter: str) -> bool:
    level_def = load_kumon_levels().get(normalize_level(level))
    if not level_def:
        return False
    block = level_def.blocks.get(block_letter.upper())
    return bool(block and block.extra)


def is_extra_set(level: str, set_number: int) -> bool:
    return is_extra_block(level, block_letter_for_set(level, set_number))


def core_level_sets(level: str) -> list[SetDef]:
    """Sets that count toward level mastery (excludes optional extra blocks)."""
    return [s for s in level_sets(level) if not is_extra_block(level, s.block_letter)]


def display_set_number(level: str, set_number: int) -> int:
    """Student-facing set index within the block (1..N), not the global 1..20 index."""
    block = block_letter_for_set(level, set_number)
    block_sets = sorted(sets_in_block(level, block), key=lambda s: s.set_number)
    for i, s in enumerate(block_sets, start=1):
        if s.set_number == set_number:
            return i
    level_def = load_kumon_levels().get(normalize_level(level))
    per_block = 5
    if level_def and level_def.pages_per_set:
        per_block = max(1, level_def.pages_per_block // level_def.pages_per_set)
    return ((set_number - 1) % per_block) + 1


def level_checkpoints(level: str) -> dict[str, list[str]]:
    level_def = load_kumon_levels().get(normalize_level(level))
    return dict(level_def.checkpoints) if level_def else {}


def level_exam(level: str) -> dict[str, list[str]]:
    level_def = load_kumon_levels().get(normalize_level(level))
    return dict(level_def.exam) if level_def else {}


def checkpoint_for_block(level: str, block_letter: str) -> list[str]:
    return level_checkpoints(level).get(block_letter.upper(), [])


# ---------------------------------------------------------------------------
# Track / level listing
# ---------------------------------------------------------------------------

def list_route_levels(track: str | None = None) -> list[str]:
    out = []
    for letter in sorted(load_kumon_levels()):
        defn = load_kumon_levels()[letter]
        if track is None or defn.track == track:
            out.append(route_level(letter))
    return out


def level_track(level: str) -> str:
    defn = load_kumon_levels().get(normalize_level(level))
    return defn.track if defn else "python"


def language_for_level(level: str) -> str:
    """Execution language for a level. Only the csharp track runs C#; the
    python and odoo tracks both execute Python."""
    return "csharp" if level_track(level) == "csharp" else "python"


def is_valid_route_level(level: str) -> bool:
    return normalize_level(level) in load_kumon_levels()


def coerce_route_level(level: str) -> str:
    if is_valid_route_level(level):
        return route_level(level)
    levels = list_route_levels("python")
    return levels[0] if levels else "a"


def levels_for_api(track: str = "python", locale: str = "en") -> list[dict]:
    from .schedule_i18n import localize_title

    return [
        {
            "id": route_level(defn.letter),
            "letter": defn.letter,
            "title": localize_title(defn.title, locale),
            "track": defn.track,
        }
        for defn in sorted(load_kumon_levels().values(), key=lambda d: d.letter)
        if defn.track == track
    ]


def blocks_metadata() -> dict[str, dict]:
    """Flat block metadata for API responses."""
    meta: dict[str, dict] = {}
    for level_def in load_kumon_levels().values():
        for block in _sorted_blocks(level_def):
            meta[block.block_id] = {
                "level": route_level(level_def.letter),
                "block": block.letter,
                "title": block.title,
                "page_start": block.page_start,
                "page_end": block.page_end,
                "order": (block.page_start - 1) // level_def.pages_per_block + 1,
                "extra": block.extra,
            }
    return meta
