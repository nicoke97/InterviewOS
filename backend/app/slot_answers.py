from __future__ import annotations

import re


def extract_slot_answers(template: str, reference: str) -> list[str]:
    """Derive each ___ fill from a completed reference solution."""
    template = template.replace("\r\n", "\n")
    reference = reference.replace("\r\n", "\n")
    answers: list[str] = []
    t_pos = 0
    r_pos = 0

    while t_pos < len(template):
        blank_idx = template.find("___", t_pos)
        if blank_idx == -1:
            break

        prefix = template[t_pos:blank_idx]
        if prefix:
            if reference[r_pos:].startswith(prefix):
                r_pos += len(prefix)
            else:
                found = reference.find(prefix, r_pos)
                if found == -1:
                    return []
                r_pos = found + len(prefix)

        t_pos = blank_idx + 3
        next_blank = template.find("___", t_pos)
        suffix = template[t_pos:] if next_blank == -1 else template[t_pos:next_blank]

        if suffix:
            suffix_pos = reference.find(suffix, r_pos)
            if suffix_pos == -1:
                return []
            answers.append(reference[r_pos:suffix_pos])
            r_pos = suffix_pos
        else:
            answers.append(reference[r_pos:])
            r_pos = len(reference)

    return answers


def infer_a1_slot_answers(prompt: str) -> list[str] | None:
    name_match = re.search(r"name='([^']+)'", prompt)
    age_match = re.search(r"age=(\d+)", prompt)
    if not name_match or not age_match:
        return None
    name, age = name_match.group(1), age_match.group(1)
    return [f"'{name}'", age, f"f'{{name}} is {{age}} years old'"]


def infer_full_code_slot(starter_code: str, reference_code: str) -> list[str] | None:
    if not reference_code:
        return None
    normalized = starter_code.strip()
    if normalized == "___":
        return [reference_code.strip()]
    if re.match(r"^#\s*.+\n\s*___\s*$", normalized, re.DOTALL):
        return [reference_code.strip()]
    return None


def infer_print_slot_answer(starter_code: str, validation: dict) -> list[str] | None:
    if starter_code.count("___") != 1:
        return None
    if "print(___)" not in starter_code:
        return None
    expected = validation.get("expected")
    if expected is None:
        return None
    if isinstance(expected, str) and expected.isdigit():
        return [expected]
    return [f"'{expected}'"]


def resolve_slot_answers(
    starter_code: str,
    validation: dict,
    reference_code: str = "",
    explicit: list[str] | None = None,
    prompt: str = "",
) -> list[str]:
    if explicit:
        return explicit
    if reference_code:
        answers = extract_slot_answers(starter_code, reference_code)
        if answers:
            return answers
        full = infer_full_code_slot(starter_code, reference_code)
        if full:
            return full
    if "name = ___" in starter_code and "age = ___" in starter_code:
        inferred = infer_a1_slot_answers(prompt)
        if inferred:
            return inferred
    inferred = infer_print_slot_answer(starter_code, validation)
    if inferred:
        return inferred
    return []
