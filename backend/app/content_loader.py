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
from .content_i18n import translate_hints, translate_prompt
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
    prompt_en: str = ""
    hints_en: list[str] = field(default_factory=list)
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
    topic: str = ""
    difficulty: str = ""
    global_order: int = 0
    leetcode_ref: int = 0
    track: str = "kumon"
    hints: list[str] = field(default_factory=list)
    approach: str = ""
    learning: list[str] = field(default_factory=list)
    interview_questions: list[str] = field(default_factory=list)
    solution_code: str = ""


@dataclass
class LeetcodesSchedule:
    track: str = "leetcodes"
    topics: list[dict[str, Any]] = field(default_factory=list)
    orientador: dict[str, Any] = field(default_factory=dict)


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
    leetcodes: dict[str, LeetCodeProblem] = field(default_factory=dict)
    leetcodes_schedule: LeetcodesSchedule = field(default_factory=LeetcodesSchedule)
    interview: dict[str, InterviewQuestion] = field(default_factory=dict)
    blocks: dict[str, dict] = field(default_factory=dict)
    progression: dict = field(default_factory=dict)


def _parse_leetcode_problem(data: dict, *, level: str = "lc", track: str = "kumon") -> LeetCodeProblem:
    tiers_raw = data.get("tiers", {})
    tiers = {int(k): v for k, v in tiers_raw.items()}
    return LeetCodeProblem(
        id=data["id"],
        level=level,
        title=data.get("title", data["id"]),
        description=data.get("description", ""),
        fn_name=data.get("fn_name", "solution"),
        tiers=tiers,
        test_cases=data.get("test_cases", []),
        topic=data.get("topic", ""),
        difficulty=data.get("difficulty", ""),
        global_order=int(data.get("global_order", 0)),
        leetcode_ref=int(data.get("leetcode_ref", 0)),
        track=track,
        hints=data.get("hints", []),
        approach=data.get("approach", ""),
        learning=data.get("learning", []),
        interview_questions=data.get("interview_questions", []),
        solution_code=data.get("solution_code", ""),
    )

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
    level_dirs += sorted((CONTENT_DIR / "csharp").glob("level-*"))
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
                    prompt_en=data.get("prompt_en") or translate_prompt(data["prompt"]),
                    hints_en=data.get("hints_en") or translate_hints(data.get("hints", [])),
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
                curriculum.leetcode[data["id"]] = _parse_leetcode_problem(data, level=folder_level, track="kumon")

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

    lc_schedule_path = CONTENT_DIR / "schedule" / "leetcode-interview.yaml"
    if lc_schedule_path.exists():
        sched = load_yaml(lc_schedule_path)
        curriculum.leetcodes_schedule = LeetcodesSchedule(
            track=sched.get("track", "leetcodes"),
            topics=sched.get("topics", []),
            orientador=sched.get("orientador", {}),
        )

    lc_catalog = CONTENT_DIR / "leetcodes"
    if lc_catalog.exists():
        for f in sorted(lc_catalog.glob("*.yaml")):
            data = load_yaml(f)
            if not data or "id" not in data:
                continue
            curriculum.leetcodes[data["id"]] = _parse_leetcode_problem(
                data, level="lc", track="leetcodes",
            )

    return curriculum


def _content_revision() -> tuple[int, float]:
    """Fingerprint YAML on disk so dev picks up generate-content without restart."""
    count = 0
    latest = 0.0
    for root in (CONTENT_DIR / "levels", CONTENT_DIR / "odoo", CONTENT_DIR / "csharp", CONTENT_DIR / "leetcodes"):
        if not root.exists():
            continue
        for path in root.rglob("*.yaml"):
            count += 1
            latest = max(latest, path.stat().st_mtime)
    for prog_name in ("kumon-progression.yaml", "leetcode-interview.yaml"):
        prog = CONTENT_DIR / "schedule" / prog_name
        if prog.exists():
            count += 1
            latest = max(latest, prog.stat().st_mtime)
    return count, latest


@lru_cache(maxsize=1)
def _cached_curriculum(_revision: tuple[int, float]) -> Curriculum:
    return _build_curriculum()


def load_curriculum() -> Curriculum:
    return _cached_curriculum(_content_revision())


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


def get_leetcode_problem(curriculum: Curriculum, problem_id: str) -> LeetCodeProblem | None:
    return curriculum.leetcodes.get(problem_id) or curriculum.leetcode.get(problem_id)


def guide_fields(problem: LeetCodeProblem, tier_data: dict, tier: int, locale: str = "en") -> dict:
    from .leetcodes_i18n import localized_tier_lists, pick
    from .kumon_leetcode_i18n import localize_field as kumon_lc_field

    hints_allowed = tier_data.get("hints_allowed", tier < 3)
    hints = list(problem.hints) if hints_allowed else []
    if hints_allowed and tier == 2:
        hints = hints[:1]

    if locale != "es":
        if problem.track == "kumon":
            if hints_allowed:
                full = kumon_lc_field(problem.id, "hints", problem.hints, locale)
                hints = full[:1] if tier == 2 else full
            approach = kumon_lc_field(problem.id, "approach", problem.approach, locale) if hints_allowed else ""
            learning = kumon_lc_field(problem.id, "learning", problem.learning, locale) if hints_allowed else []
            interview_questions = kumon_lc_field(
                problem.id, "interview_questions", problem.interview_questions, locale,
            ) if hints_allowed else []
        else:
            if hints_allowed:
                full = pick(problem.id, problem.topic, "hints", problem.hints, locale)
                hints = full[:1] if tier == 2 else full
            approach = pick(problem.id, problem.topic, "approach", problem.approach, locale) if hints_allowed else ""
            learning = pick(problem.id, problem.topic, "learning", problem.learning, locale) if hints_allowed else []
            interview_questions = pick(
                problem.id, problem.topic, "interview_questions", problem.interview_questions, locale,
            ) if hints_allowed else []
    else:
        approach = problem.approach if hints_allowed else ""
        learning = problem.learning if hints_allowed else []
        interview_questions = problem.interview_questions if hints_allowed else []

    explain_checklist, narration_prompts = localized_tier_lists(tier_data, locale)
    return {
        "hints_allowed": hints_allowed,
        "hints": hints,
        "approach": approach,
        "learning": learning,
        "interview_questions": interview_questions,
        "solution_code": problem.solution_code if hints_allowed and tier == 1 else "",
        "explain_checklist": explain_checklist,
        "narration_prompts": narration_prompts,
    }


def problem_description(problem: LeetCodeProblem, locale: str = "en") -> str:
    if locale == "es":
        return problem.description
    if problem.track == "kumon":
        from .kumon_leetcode_i18n import localize_field
        return localize_field(problem.id, "description", problem.description, locale)
    from .leetcodes_i18n import pick
    return pick(problem.id, problem.topic, "description", problem.description, locale)


def problem_title(problem: LeetCodeProblem | None, locale: str = "en", fallback: str = "") -> str:
    if not problem:
        return fallback
    if locale == "es":
        return problem.title
    if problem.track == "kumon":
        from .kumon_leetcode_i18n import localize_field
        return localize_field(problem.id, "title", problem.title, locale)
    return problem.title


def interview_payload(question, locale: str = "en") -> dict:
    from .interview_i18n import localize_interview
    return {
        "id": question.id,
        "category": question.category,
        "question": localize_interview(question.id, "question", question.question, locale),
        "type": question.question_type,
        "rubric": localize_interview(question.id, "rubric", question.rubric, locale),
        "sample_answer": localize_interview(question.id, "sample_answer", question.sample_answer, locale),
    }


def get_level_blocks(curriculum: Curriculum, level: str) -> list[str]:
    rl = route_level(level)
    return [bid for bid, info in curriculum.blocks.items() if info.get("level") == rl]


def page_payload(page: KumonPage, locale: str = "en") -> dict:
    from .content_i18n import localize_starter_code

    use_en = locale != "es"
    prompt = page.prompt_en if use_en and page.prompt_en else page.prompt
    hints = page.hints_en if use_en and page.hints_en else page.hints
    return {
        "id": page.id,
        "level": page.level,
        "page": page.page,
        "set": page.set,
        "block": page.block,
        "block_id": page.block_id,
        "order": page.order,
        "scaffolding": page.scaffolding,
        "prompt": prompt,
        "starter_code": localize_starter_code(page.starter_code, locale),
        "slot_answers": page.slot_answers,
        "reference_code": page.reference_code,
        "hints": hints,
        "time_estimate_seconds": page.time_estimate_seconds,
    }
