#!/usr/bin/env python3
"""Validate that Kumon EN translations keep required literals and drop Spanish."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.content_i18n import translate_hints, translate_prompt  # noqa: E402
from app.kumon_leetcode_i18n import TITLES_EN  # noqa: E402
from app.schedule_i18n import TITLE_EN  # noqa: E402

SPANISH = re.compile(
    r"\b(?:imprime|imprimir|crea|calcula|dado|dada|dados|dadas|declara|asigna|"
    r"convierte|recorre|cuenta|ordena|invierte|separa|quita|"
    r"elimina|agrega|concatena|verifica|captura|maneja|intenta|"
    r"accede|lanza|valida|reemplaza|encuentra|desempaqueta|repite|"
    r"usando|llamala|llámala|numeros|números|caracter|carácter|"
    r"mayuscula|mayúscula|minuscula|minúscula|anidado|multiplo|"
    r"múltiplo|cuantas|cuántas|cuantos|cuántos|segun|según|tambien|"
    r"también|despues|después|vacio|vacío|conviertela|imprimelo|"
    r"luego|mientras|hasta|donde|cuando|porque|diccionario|clave|"
    r"indice|índice|guarda|entonces|copia|espacios|pares|letra|"
    r"metodos|métodos|expresion|expresión|resultado|dentro|devuelve|"
    r"busca|llave|rapido|rápido|entero|comas|guiones|"
    r"la|el|con|para|si|de|en|al)\b",
    re.I,
)


def strip_literals(text: str) -> str:
    text = re.sub(r"\(exact format: [^)]*\)", " ", text)
    text = re.sub(r"\(formato:\s*[^)]*\)", " ", text)
    text = re.sub(r"'(?:\\.|[^'\\])*'", " ", text)
    text = re.sub(r'"(?:\\.|[^"\\])*"', " ", text)
    text = re.sub(r"\b[A-Za-z_]\w*\s*=", " ", text)
    text = re.sub(r"\b[A-Za-z_]\w*\(", " ", text)
    text = re.sub(r"\bdel\b", " ", text)
    # Class names (Cuenta, Perro) are identifiers, not leftover Spanish
    text = re.sub(r"\b[A-Z][A-Za-z]+\b", " ", text)
    return text


def leftover(text: str) -> bool:
    return bool(SPANISH.search(strip_literals(text)))


def regression_errors() -> list[str]:
    cases = [
        (
            "Asigna name='Ana' y age=22. Usa f-string para presentarla (formato: nombre tiene edad años).",
            lambda en: "años" in en and "years old" not in en,
            "must keep años in the required format",
        ),
        (
            "Declara producto='Libro' y precio=25, imprime: 'Libro cuesta 25'",
            lambda en: "'Libro cuesta 25'" in en,
            "must keep required print literal",
        ),
        (
            "Define Cuenta con saldo=0; metodo depositar(self, n) suma al saldo; metodo saldo_actual(self) lo retorna. Deposita [100, 50] e imprime el saldo final.",
            lambda en: "Define Cuenta" in en and "Define Count" not in en,
            "must keep class name Cuenta",
        ),
        (
            "Dado n=4, imprime 'par' si es par o 'impar' si es impar.",
            lambda en: "'par'" in en and "'impar'" in en,
            "must keep par/impar literals",
        ),
    ]
    errors = []
    for src, ok, reason in cases:
        en = translate_prompt(src)
        if not ok(en):
            errors.append(f"regression: {reason}\n  EN: {en}")
    return errors


def main() -> int:
    leftover_n = broken = total = hint_n = 0
    samples: list[str] = []
    regressions = regression_errors()
    samples.extend(regressions)
    for f in sorted((ROOT / "content" / "levels").glob("*/kumon/*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        if not data or "prompt" not in data:
            continue
        prompt = data["prompt"]
        total += 1
        en = translate_prompt(prompt)
        if leftover(en):
            leftover_n += 1
            samples.append(f"[{f.stem}] leftover prompt\n  ES: {prompt}\n  EN: {en}")
        quoted_es = re.findall(r"'([^']*)'", prompt)
        quoted_en = re.findall(r"'([^']*)'", en)
        if quoted_es != quoted_en:
            broken += 1
            samples.append(f"[{f.stem}] broken quotes\n  ES: {quoted_es}\n  EN: {quoted_en}")
        if "years old" in en and "años" in prompt:
            broken += 1
            samples.append(f"[{f.stem}] translated required años\n  EN: {en}")
        for h in translate_hints(data.get("hints") or []):
            if leftover(h):
                hint_n += 1
                samples.append(f"[{f.stem}] leftover hint\n  EN: {h}")
                break

    missing_titles: list[str] = []
    for yaml_path in (
        ROOT / "content" / "schedule" / "kumon-levels.yaml",
        ROOT / "content" / "schedule" / "csharp-levels.yaml",
        ROOT / "content" / "schedule" / "odoo-levels.yaml",
    ):
        schedule = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        for ld in (schedule.get("levels") or {}).values():
            if ld.get("title") and ld["title"] not in TITLE_EN:
                missing_titles.append(ld["title"])
            for bd in (ld.get("blocks") or {}).values():
                for title in [bd.get("title"), *(s.get("title") for s in bd.get("sets") or [])]:
                    if title and title not in TITLE_EN:
                        missing_titles.append(title)
    lc_ids = {p.stem for p in (ROOT / "content" / "levels").glob("*/leetcode/*.yaml")}
    missing_lc = sorted(lc_ids - set(TITLES_EN))

    print(
        f"total={total} leftover_prompts={leftover_n} leftover_hint_pages={hint_n} "
        f"broken={broken} regressions={len(regressions)} "
        f"missing_schedule_titles={len(missing_titles)} "
        f"missing_lc_titles={len(missing_lc)}"
    )
    for line in samples[:40]:
        print(line)
    if missing_titles:
        print("missing schedule titles:", missing_titles)
    if missing_lc:
        print("missing kumon LC titles:", missing_lc)
    failed = leftover_n or broken or hint_n or regressions or missing_titles or missing_lc
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
