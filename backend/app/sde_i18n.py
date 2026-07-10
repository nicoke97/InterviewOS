"""Localize SDE content. Canonical fields are English; *_es is Spanish."""
from __future__ import annotations

from typing import Any

RUNG_PROMPT = {
    1: {
        "en": "Rung 1: set up the start (structures / first line). Different variable names.",
        "es": "Peldaño 1: arma el inicio (estructuras / primera línea). Otras variables.",
    },
    2: {
        "en": "Rung 2: the loop / the middle idea.",
        "es": "Peldaño 2: el recorrido / la idea del medio.",
    },
    3: {
        "en": "Rung 3: the returns and the close.",
        "es": "Peldaño 3: los return y el cierre.",
    },
    4: {
        "en": "Full algorithm, first try.",
        "es": "Algoritmo completo, a la primera.",
    },
}

RECALL_PROMPT = {
    "en": "Day 2 / pool: the whole thing, first try.",
    "es": "Día 2 / pool: el entero, a la primera.",
}

CODI = {
    "return": {
        "en": {"headline": "Days without evidence. Cards and one full problem; syllabus frozen.", "cta": "Start return"},
        "es": {"headline": "Llevas días sin evidencia. Cartas y un entero, temario congelado.", "cta": "Empezar retorno"},
    },
    "flojo": {
        "en": {"headline": "Yesterday's block did not close. Few cards and the last sheet.", "cta": "Warm-up"},
        "es": {"headline": "Ayer no cerraste el bloque. Pocas cartas y la última hoja.", "cta": "Warm-up"},
    },
    "pool": {
        "en": {"headline": "Pool: {title}, full problem.", "cta": "Open"},
        "es": {"headline": "Pool: {title} entero.", "cta": "Abrir"},
    },
    "sheet": {
        "en": {"headline": "{title} · {lang} · {prompt}", "cta": "Code"},
        "es": {"headline": "{title} · {lang} · {prompt}", "cta": "Codear"},
    },
    "ready": {
        "en": {"headline": "Today's plan is ready.", "cta": "Start"},
        "es": {"headline": "Plan de hoy listo.", "cta": "Empezar"},
    },
    "continue": {"en": "Continue", "es": "Continuar"},
}

ANALYSIS = {
    "card_fail": {
        "en": ("{n} card(s) wrong. Those come up more tomorrow.", "Deck"),
        "es": ("{n} carta(s) mal. Esas salen más mañana.", "Mazo"),
    },
    "pool_fail2": {
        "en": ("{title} goes to the failed pool. Day 1 again.", "Restart"),
        "es": ("{title} al pool de fallados. Día 1 de nuevo.", "Reiniciar"),
    },
    "pool_fail": {
        "en": ("{title} failed. Rungs 1–3 and the full problem.", "Rungs"),
        "es": ("{title} falló. Peldaños 1-2-3 y el entero.", "Peldaños"),
    },
    "warmup_fail": {
        "en": ("Warm-up missed: only this sheet today.", "Repeat sheet"),
        "es": ("Warm-up mal: solo esta hoja hoy.", "Repetir hoja"),
    },
    "sheet_fail": {
        "en": ("This sheet again. The rung does not advance.", "Repeat"),
        "es": ("Esta hoja otra vez. No avanzas el peldaño.", "Repetir"),
    },
    "voice_fail": {
        "en": ("The explanation did not land. Language stays locked.", "Speak again"),
        "es": ("No cerró la explicación. No hay cambio de idioma.", "Hablar otra vez"),
    },
    "theory_fail": {
        "en": ("Quiz missed. Same section tomorrow, not the next one.", "Reread"),
        "es": ("Quiz mal. Mañana la misma sección, no la siguiente.", "Releer"),
    },
    "sql_fail": {
        "en": ("SQL missed. Check the join/index and retry.", "SQL"),
        "es": ("SQL mal. Revisa el join/índice y reintenta.", "SQL"),
    },
}

PACK = {
    "title": {"en": "# Codi travel pack", "es": "# Paquete de viaje Codi"},
    "cards": {"en": "## Cards", "es": "## Cartas"},
}


def is_es(locale: str | None) -> bool:
    return (locale or "en").split("-")[0].lower() == "es"


def pick(obj: dict | None, key: str, locale: str, fallback: str = "") -> str:
    data = obj or {}
    if is_es(locale):
        return str(data.get(f"{key}_es") or data.get(key) or fallback)
    return str(data.get(f"{key}_en") or data.get(key) or fallback)


def sheet_prompt(sheet: dict | None, locale: str) -> str:
    sheet = sheet or {}
    if sheet.get("id") == "full-recall":
        stored = pick(sheet, "prompt", locale)
        if stored and not (not is_es(locale) and "Día" in stored):
            return stored
        return RECALL_PROMPT["es" if is_es(locale) else "en"]
    rung = int(sheet.get("rung") or 0)
    stored = pick(sheet, "prompt", locale)
    if not is_es(locale) and stored and ("Peldaño" in stored or stored.startswith("Día")):
        stored = ""
    if stored:
        return stored
    table = RUNG_PROMPT.get(rung) or RUNG_PROMPT[4]
    return table["es" if is_es(locale) else "en"]


def localize_card(card: dict, locale: str) -> dict:
    return {
        **card,
        "front": pick(card, "front", locale),
        "back": pick(card, "back", locale),
    }


def localize_question(q: dict, locale: str) -> dict:
    choices = q.get("choices_es" if is_es(locale) else "choices") or q.get("choices") or []
    return {
        **q,
        "q": pick(q, "q", locale),
        "choices": list(choices),
    }


def localize_section(sec: dict, locale: str) -> dict:
    out = dict(sec)
    out["title"] = pick(sec, "title", locale)
    out["reading"] = pick(sec, "reading", locale)
    out["week_title"] = pick(sec, "week_title", locale)
    out["anchor"] = pick(sec, "anchor", locale)
    out["questions"] = [localize_question(q, locale) for q in sec.get("questions") or []]
    out["cards"] = [localize_card(c, locale) for c in sec.get("cards") or []]
    return out


def localize_sql(drill: dict, locale: str) -> dict:
    return {**drill, "prompt": pick(drill, "prompt", locale)}


def analysis_view(cause: str, locale: str, *, title: str = "", n: int = 0, fallback_line: str = "", fallback_cta: str = "") -> dict:
    pair = ANALYSIS.get(cause, {}).get("es" if is_es(locale) else "en")
    if not pair:
        return {"cause": cause, "line": fallback_line, "cta": fallback_cta}
    line, cta = pair
    return {"cause": cause, "line": line.format(title=title, n=n), "cta": cta}


def codi_copy(kind: str, locale: str, **fmt: Any) -> dict:
    loc = "es" if is_es(locale) else "en"
    block = CODI.get(kind, CODI["ready"])[loc]
    return {"headline": block["headline"].format(**fmt), "cta": block["cta"]}
