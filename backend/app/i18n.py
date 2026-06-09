"""Backend internationalization helpers."""
from __future__ import annotations

from fastapi import Request

SUPPORTED = frozenset({"en", "es"})
DEFAULT = "en"

TIER_LABELS = {
    "en": {1: "With hints", 2: "Minimal help", 3: "From memory"},
    "es": {1: "Con hints", 2: "Ayuda mínima", 3: "De memoria"},
}

MESSAGES: dict[str, dict[str, str]] = {
    "unknown_level": {
        "en": "Unknown level: {level}",
        "es": "Nivel desconocido: {level}",
    },
    "problem_not_found": {
        "en": "Problem not found",
        "es": "Problema no encontrado",
    },
    "question_not_found": {
        "en": "Question not found",
        "es": "Pregunta no encontrada",
    },
    "unknown_exercise_type": {
        "en": "Unknown exercise type",
        "es": "Tipo de ejercicio desconocido",
    },
    "invalid_month": {
        "en": "month must be 1-12",
        "es": "month debe ser 1-12",
    },
    "session_not_found_today": {
        "en": "Session not found for today",
        "es": "Sesion no encontrada para hoy",
    },
    "finish_active_session": {
        "en": "Finish the active session before adding another",
        "es": "Termina la sesión activa antes de añadir otra",
    },
    "session_completed": {
        "en": "The session is already completed",
        "es": "La sesión ya está completada",
    },
    "no_active_plan": {
        "en": "No active plan for today",
        "es": "No hay plan activo para hoy",
    },
    "assignment_not_found": {
        "en": "Assignment not found in the plan",
        "es": "Asignacion no encontrada en el plan",
    },
    "assignment_type_mismatch": {
        "en": "Assignment type does not match the plan",
        "es": "Tipo de asignación no coincide con el plan",
    },
    "level_mismatch": {
        "en": "Level does not match the plan",
        "es": "Nivel no coincide con el plan",
    },
    "set_mismatch": {
        "en": "Set does not match the plan",
        "es": "Set no coincide con el plan",
    },
    "checkpoint_mismatch": {
        "en": "Checkpoint does not match the plan",
        "es": "Checkpoint no coincide con el plan",
    },
    "plan_not_found": {
        "en": "Plan not found",
        "es": "Plan no encontrado",
    },
    "unknown_assignment_type": {
        "en": "Unknown assignment type",
        "es": "Tipo de asignación desconocido",
    },
    "review_mastered_only": {
        "en": "You can only review mastered sets",
        "es": "Solo puedes repasar sets dominados",
    },
    "leetcodes_session_active": {
        "en": "A LeetCodes session is already active today",
        "es": "Ya hay una sesion LeetCodes activa hoy",
    },
    "leetcodes_plan_not_found": {
        "en": "LeetCodes plan not found",
        "es": "Plan LeetCodes no encontrado",
    },
    "assignment_already_completed": {
        "en": "Assignment already completed",
        "es": "Asignacion ya completada",
    },
    "return_exam_not_pending": {
        "en": "No return exam is pending",
        "es": "No hay examen de retorno pendiente",
    },
    "return_exam_incomplete": {
        "en": "Complete every exercise in the exam",
        "es": "Completa todos los ejercicios del examen",
    },
    "return_exam_required": {
        "en": "Take the return exam before starting a new session",
        "es": "Haz el examen de retorno antes de empezar una sesión nueva",
    },
}

PRIORITY_RULES = {
    "en": [
        {"id": "repeat", "label": "Repeat", "description": "Sets that failed on time or accuracy need another pass."},
        {"id": "pre_exam", "label": "Pre-exam review", "description": "Mastered sets without solid mastery before the level exam."},
        {"id": "repaso", "label": "Review", "description": "Maintain speed on sets you already mastered."},
        {"id": "new", "label": "New set", "description": "Advance to the next set in the level sequence."},
        {"id": "checkpoint", "label": "Checkpoint", "description": "LeetCode checkpoint at the end of a block."},
        {"id": "exam", "label": "Exam", "description": "Level completion exam."},
    ],
    "es": [
        {"id": "repeat", "label": "Repetición", "description": "Sets que fallaron en tiempo o precisión necesitan otra vuelta."},
        {"id": "pre_exam", "label": "Repaso pre-examen", "description": "Sets dominados sin dominio sólido antes del examen de nivel."},
        {"id": "repaso", "label": "Repaso", "description": "Mantener velocidad en sets que ya dominaste."},
        {"id": "new", "label": "Nuevo set", "description": "Avanzar al siguiente set en la secuencia del nivel."},
        {"id": "checkpoint", "label": "Checkpoint", "description": "Checkpoint LeetCode al final de un bloque."},
        {"id": "exam", "label": "Examen", "description": "Examen de conclusión del nivel."},
    ],
}

LEETCODES_PRIORITY_RULES = {
    "en": [
        {"id": "repeat", "label": "Repeat", "description": "Problems that need another tier attempt."},
        {"id": "new", "label": "New problem", "description": "Next problem in the interview catalog."},
    ],
    "es": [
        {"id": "repeat", "label": "Repetición", "description": "Problemas que necesitan otro intento de tier."},
        {"id": "new", "label": "Nuevo problema", "description": "Siguiente problema en el catálogo de entrevista."},
    ],
}


def normalize_locale(raw: str | None) -> str:
    if not raw:
        return DEFAULT
    code = raw.split(",")[0].split("-")[0].strip().lower()
    return code if code in SUPPORTED else DEFAULT


def locale_from_request(request: Request | None) -> str:
    if request is None:
        return DEFAULT
    return normalize_locale(request.headers.get("Accept-Language"))


def t(key: str, locale: str = DEFAULT, **kwargs: str) -> str:
    loc = locale if locale in SUPPORTED else DEFAULT
    template = MESSAGES.get(key, {}).get(loc) or MESSAGES.get(key, {}).get(DEFAULT) or key
    return template.format(**kwargs) if kwargs else template


def tier_label(tier: int, locale: str = DEFAULT) -> str:
    loc = locale if locale in SUPPORTED else DEFAULT
    return TIER_LABELS.get(loc, TIER_LABELS[DEFAULT]).get(tier, f"Tier {tier}")


def priority_rules(locale: str = DEFAULT, *, track: str = "python") -> list[dict]:
    loc = locale if locale in SUPPORTED else DEFAULT
    if track == "leetcodes":
        return list(LEETCODES_PRIORITY_RULES.get(loc, LEETCODES_PRIORITY_RULES[DEFAULT]))
    return list(PRIORITY_RULES.get(loc, PRIORITY_RULES[DEFAULT]))


def localize_text(data: dict, field: str, locale: str = DEFAULT) -> str:
    """Return localized field value from YAML dict (field_en fallback to field)."""
    if locale == "es":
        return str(data.get(field, "") or "")
    en_field = f"{field}_en"
    if en_field in data and data[en_field]:
        return str(data[en_field])
    return str(data.get(field, "") or "")


def localize_list(data: dict, field: str, locale: str = DEFAULT) -> list[str]:
    if locale == "es":
        return list(data.get(field, []) or [])
    en_field = f"{field}_en"
    if en_field in data and data[en_field]:
        return list(data[en_field])
    return list(data.get(field, []) or [])
