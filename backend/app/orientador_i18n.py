"""Orientador explain texts and priority rules (EN/ES)."""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from .kumon_hierarchy import display_set_number, route_level


def assignment_title(assignment: dict, locale: str = "en") -> str:
    atype = assignment.get("type", "")
    level = route_level(assignment.get("level", "a"))
    if atype == "set":
        sn = assignment.get("display_set_number") or assignment.get("set_number", 0)
        if locale == "es":
            return f"Set {sn} · Nivel {level.upper()}"
        return f"Set {sn} · Level {level.upper()}"
    if atype == "checkpoint":
        block = assignment.get("block", "")
        if locale == "es":
            return f"Checkpoint Bloque {block} · Nivel {level.upper()}"
        return f"Checkpoint Block {block} · Level {level.upper()}"
    if atype == "exam":
        if locale == "es":
            return f"Examen · Nivel {level.upper()}"
        return f"Exam · Level {level.upper()}"
    return "Activity" if locale == "en" else "Actividad"


def explain_set_summary(
    reason: str,
    detail: dict,
    threshold: float,
    lap: int = 1,
    locale: str = "en",
) -> str:
    flags = detail.get("failure_flags") or []
    acc = detail.get("first_attempt_accuracy")
    acc_pct = round(acc * 100) if acc is not None else None

    if reason == "repeat":
        if locale == "es":
            parts = [f"Repeticion programada para hoy ({detail.get('repeat_scheduled_for')})."]
            if "return_exam" in flags:
                parts.append(
                    "Fallaste un ejercicio de este set en el examen de retorno "
                    "tras varios días sin practicar. Debes repetir el set completo."
                )
            if "too_slow" in flags:
                parts.append("En el primer intento completo superaste el tiempo estandar del set.")
            if "low_accuracy" in flags:
                parts.append(
                    f"En el primer intento completo tu precision fue {acc_pct}% "
                    f"(umbral {round(threshold * 100)}%)."
                )
            if not flags:
                parts.append("Necesitas consolidar este set antes de seguir avanzando.")
            return " ".join(parts)
        parts = [f"Repeat scheduled for today ({detail.get('repeat_scheduled_for')})."]
        if "return_exam" in flags:
            parts.append(
                "You missed an exercise from this set on the return exam "
                "after several days away. You must repeat the full set."
            )
        if "too_slow" in flags:
            parts.append("On the first full attempt you exceeded the set's standard time.")
        if "low_accuracy" in flags:
            parts.append(
                f"On the first full attempt your accuracy was {acc_pct}% "
                f"(threshold {round(threshold * 100)}%)."
            )
        if not flags:
            parts.append("You need to consolidate this set before moving on.")
        return " ".join(parts)

    if reason == "pre_exam":
        if locale == "es":
            summary = (
                "Repaso obligatorio antes del examen de nivel: este set ya lo dominaste "
                "pero no alcanzo dominio solido"
            )
            return summary + (f" (primer intento {acc_pct}%)." if acc_pct is not None else ".")
        summary = (
            "Required pre-exam review: you mastered this set but not solid mastery yet"
        )
        return summary + (f" (first attempt {acc_pct}%)." if acc_pct is not None else ".")

    if reason == "repaso":
        if locale == "es":
            if detail.get("solid_mastery"):
                return (
                    "Set dominado con buen desempeno. Se incluye como repaso para mantener "
                    "velocidad y precision."
                )
            summary = (
                "Set dominado pero con historial de fallas o precision baja. "
                "Conviene repasarlo antes de avanzar."
            )
            return summary + (f" Primer intento: {acc_pct}%." if acc_pct is not None else "")
        if detail.get("solid_mastery"):
            return (
                "Set mastered with good performance. Included as review to maintain "
                "speed and accuracy."
            )
        summary = (
            "Set mastered but with a history of failures or low accuracy. "
            "Worth reviewing before advancing."
        )
        return summary + (f" First attempt: {acc_pct}%." if acc_pct is not None else "")

    if reason == "repaso_extra":
        if locale == "es":
            return (
                f"Repaso adicional (vuelta {lap}) para aprovechar el tiempo libre de tu sesión. "
                "Mismo contenido ya dominado — refuerza memoria y velocidad."
            )
        return (
            f"Extra review (lap {lap}) to use remaining session time. "
            "Same content already mastered — reinforces memory and speed."
        )

    if reason == "new":
        if locale == "es":
            return (
                "Es tu set actual en el nivel: el siguiente paso del camino que aun no has "
                "dominado por completo."
            )
        return (
            "Your current set in the level: the next step on the path you haven't "
            "fully mastered yet."
        )

    return "Set activity included in today's plan." if locale == "en" else "Actividad de set incluida en tu plan de hoy."


def explain_checkpoint_summary(locale: str = "en") -> str:
    if locale == "es":
        return (
            "Completaste las paginas del bloque pero falta el checkpoint de LeetCode "
            "para desbloquear el siguiente bloque."
        )
    return (
        "You finished the block pages but the LeetCode checkpoint is still needed "
        "to unlock the next block."
    )


def explain_exam_summary(locale: str = "en") -> str:
    if locale == "es":
        return "Dominaste los 20 sets del nivel. Falta el examen de conclusion para pasar al siguiente nivel."
    return "You mastered all 20 sets in the level. The final exam is still needed to unlock the next level."


def python_priority_rules(threshold_pct: int, locale: str = "en") -> list[dict]:
    if locale == "es":
        return [
            {
                "order": 0,
                "id": "return_exam",
                "label": "Examen de retorno",
                "description": (
                    "Si pasaron 3 o más días sin practicar, primero un quiz de 2–3 ejercicios "
                    "de los niveles que ya hiciste. Cada ejercicio fallado obliga a repetir ese set completo."
                ),
            },
            {
                "order": 1,
                "id": "repeat",
                "label": "Repeticiones vencidas",
                "description": (
                    f"Sets con repeticion programada para hoy (fallaste tiempo o precision "
                    f"< {threshold_pct}% en el primer intento)."
                ),
            },
            {
                "order": 2,
                "id": "pre_exam",
                "label": "Repaso pre-examen",
                "description": "Sets dominados pero no solidos, cuando el examen de nivel esta disponible.",
            },
            {
                "order": 3,
                "id": "new",
                "label": "Set nuevo",
                "description": "El siguiente set que aun no dominas en tu nivel activo.",
            },
            {
                "order": 4,
                "id": "repaso",
                "label": "Repaso de sets dominados",
                "description": "Sets ya aprobados que conviene mantener frescos.",
            },
            {
                "order": 5,
                "id": "repaso_extra",
                "label": "Repaso adicional",
                "description": "Si sobra tiempo en tu presupuesto, se repiten sets de repaso para llenar la sesión.",
            },
        ]
    return [
        {
            "order": 0,
            "id": "return_exam",
            "label": "Return exam",
            "description": (
                "After 3 or more days away, take a 2–3 exercise quiz from levels you already finished. "
                "Each missed exercise requires repeating that full set."
            ),
        },
        {
            "order": 1,
            "id": "repeat",
            "label": "Due repeats",
            "description": (
                f"Sets with a repeat scheduled for today (failed on time or accuracy "
                f"< {threshold_pct}% on first attempt)."
            ),
        },
        {
            "order": 2,
            "id": "pre_exam",
            "label": "Pre-exam review",
            "description": "Mastered sets without solid mastery when the level exam is available.",
        },
        {
            "order": 3,
            "id": "new",
            "label": "New set",
            "description": "The next set you haven't mastered yet in your active level.",
        },
        {
            "order": 4,
            "id": "repaso",
            "label": "Mastered set review",
            "description": "Sets already passed that are worth keeping fresh.",
        },
        {
            "order": 5,
            "id": "repaso_extra",
            "label": "Extra review",
            "description": "If time remains in your budget, extra mastered sets fill the session.",
        },
    ]


def leetcodes_priority_rules(locale: str = "en") -> list[dict]:
    if locale == "es":
        return [
            {"order": 1, "id": "repeat", "label": "Repeticiones", "description": "Problemas con tier incompleto o fallos recientes."},
            {"order": 2, "id": "new", "label": "Nuevo problema", "description": "Siguiente en arrays/hashes y two pointers (medium). Hard y otros temas esperan a que ese bloque esté dominado."},
            {"order": 3, "id": "repaso", "label": "Repaso de memoria", "description": "Problemas dominados (tier 3) sin practicar recientemente."},
            {"order": 4, "id": "repaso_extra", "label": "Repaso adicional", "description": "Relleno de tiempo con tier 3."},
        ]
    return [
        {"order": 1, "id": "repeat", "label": "Repeats", "description": "Problems with incomplete tier or recent failures."},
        {"order": 2, "id": "new", "label": "New problem", "description": "Next in arrays/hashes and two pointers (medium). Hard and other topics wait until that block is mastered."},
        {"order": 3, "id": "repaso", "label": "Memory review", "description": "Mastered problems (tier 3) not practiced recently."},
        {"order": 4, "id": "repaso_extra", "label": "Extra review", "description": "Fill remaining time with tier 3 practice."},
    ]
