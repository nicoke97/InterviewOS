#!/usr/bin/env python3
"""Generate the C# Kumon track (levels SA-SE) for Codenda.

Mirrors scripts/generate-content.py but every drill is C# and the expected
stdout is computed by actually running the reference solution through the
persistent C# runner (backend/csharp-runner). That guarantees content never
drifts out of sync with its answers.

Model: each level = 4 blocks x 50 pages = 20 sets x 10 pages (SA also has a
50-page Extra block). Each *set* drills ONE micro-skill with 10 incremental
variations; scaffolding ramps full -> minimal -> none inside the set.

Usage:
    python scripts/generate-content-csharp.py            # rebuild everything
    python scripts/generate-content-csharp.py --level SA # one level
    python scripts/generate-content-csharp.py --kumon-only
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "csharp"
SCHEDULE = ROOT / "content" / "schedule" / "csharp-levels.yaml"
RUNNER_DLL = ROOT / "backend" / "csharp-runner" / "bin" / "Release" / "net10.0" / "csharp-runner.dll"
PAGES_PER_SET = 10


# ---------------------------------------------------------------------------
# C# runner client (compute expected stdout by really running the code)
# ---------------------------------------------------------------------------

class Runner:
    def __init__(self) -> None:
        if not RUNNER_DLL.exists():
            print("Building C# runner...")
            subprocess.run(
                ["dotnet", "build", "-c", "Release"],
                cwd=str(RUNNER_DLL.parents[3]),
                check=True,
            )
        self.proc = subprocess.Popen(
            ["dotnet", str(RUNNER_DLL)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, encoding="utf-8", bufsize=1,
        )
        self.proc.stdout.readline()  # ready handshake

    def run(self, code: str) -> str:
        self.proc.stdin.write(json.dumps({"type": "capture", "code": code}, ensure_ascii=True) + "\n")
        self.proc.stdin.flush()
        resp = json.loads(self.proc.stdout.readline())
        if resp.get("error"):
            raise RuntimeError(f"C# error for code:\n{code}\n-> {resp['error']}")
        return (resp.get("stdout") or "").rstrip("\n")

    def close(self) -> None:
        try:
            self.proc.stdin.close()
            self.proc.terminate()
        except Exception:
            pass


RUNNER: Runner | None = None


def run_capture(code: str) -> str:
    assert RUNNER is not None
    return RUNNER.run(code)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def drill(prompt: str, code: str, *, hint: str | None = None) -> dict:
    d: dict = {"prompt": prompt, "code": code}
    if hint:
        d["hint"] = hint
    return d


def explicit(items: list) -> list[dict]:
    out: list[dict] = []
    for item in items:
        if isinstance(item, dict):
            out.append(item)
        else:
            prompt, code = item
            out.append(drill(prompt, code))
    return out


def mapped(prompt_fn, code_fn, data) -> list[dict]:
    return [drill(prompt_fn(x), code_fn(x)) for x in data]


def scaffolding_for(order: int) -> str:
    if order <= 3:
        return "full"
    if order <= 7:
        return "minimal"
    return "none"


# ---------------------------------------------------------------------------
# C# starter templates (___ slots) for full scaffolding (order 1-3)
# ---------------------------------------------------------------------------

_ASSIGN_RE = re.compile(r"^(\s*)(.+?)\s=\s(.+);\s*$")
_WRITE_RE = re.compile(r"^(\s*)Console\.WriteLine\((.+)\);\s*$")


def _blank_line(line: str, *, blank_bare: bool) -> str:
    m = _WRITE_RE.match(line)
    if m:
        inner = m.group(2).strip()
        if not blank_bare and re.fullmatch(r"[A-Za-z_]\w*", inner):
            return line
        return f"{m.group(1)}Console.WriteLine(___);"
    m = _ASSIGN_RE.match(line)
    if m and "==" not in line and "<=" not in line and ">=" not in line and "!=" not in line:
        return f"{m.group(1)}{m.group(2)} = ___;"
    return line


def _slot_answers_ok(starter: str, code: str) -> bool:
    from importlib import import_module
    sys.path.insert(0, str(ROOT / "backend"))
    extract = import_module("app.slot_answers").extract_slot_answers
    answers = extract(starter, code)
    if not answers:
        return False
    assembled = starter
    for a in answers:
        assembled = assembled.replace("___", a, 1)
    return assembled.replace("\r\n", "\n").strip() == code.replace("\r\n", "\n").strip()


def build_starter(code: str, order: int) -> str:
    code = code.strip()
    if order > 3 or not code:
        return ""
    if order == 3:
        return "___"
    lines = code.split("\n")
    if len(lines) == 1:
        m = _WRITE_RE.match(lines[0])
        if m and (order == 2 or not re.fullmatch(r"[A-Za-z_]\w*", m.group(2).strip())):
            return "Console.WriteLine(___);"
        return "___"
    blank_bare = order == 2
    return "\n".join(_blank_line(ln, blank_bare=blank_bare) for ln in lines)


def safe_starter(code: str, order: int) -> str:
    starter = build_starter(code, order)
    if not starter or "___" not in starter:
        starter = "___"
    if _slot_answers_ok(starter, code):
        return starter
    return "___"


def hint_for(prompt: str, code: str, given: str | None) -> str:
    if given:
        return given
    c = code
    if "Console.WriteLine($" in c or '$"' in c:
        return "Usa interpolación: $\"...{variable}...\" inserta valores dentro del texto."
    if ".Substring(" in c or "[0]" in c or "Reverse()" in c:
        return "Los índices empiezan en 0; s[0] es el primer caracter y Substring(inicio, largo) recorta."
    if "ContainsKey" in c or "Dictionary" in c:
        return "Un Dictionary busca por llave en O(1). Usa ContainsKey antes de leer d[llave]."
    if re.search(r"\b(if|else)\b", c):
        return "Compara con ==, <, > y decide con if/else. Recuerda el orden de las condiciones."
    if "%" in c or "/" in c or "Math.Pow" in c:
        return "Calcula la expresión y pásala a Console.WriteLine para imprimir el resultado."
    return "Lee con atención qué se pide imprimir y arma el código paso a paso."


# ---------------------------------------------------------------------------
# LEVEL SA — Fundamentos de C#
# ---------------------------------------------------------------------------

def q(s: str) -> str:
    """C# string literal from a Python string."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def level_sa() -> list[list[dict]]:
    sets: list[list[dict]] = []

    # ---- SA.A — Variables y tipos --------------------------------------
    # 1. Console.WriteLine
    sets.append(mapped(
        lambda v: f"Imprime exactamente el texto: {v}",
        lambda v: f"Console.WriteLine({q(v)});",
        ["Hola, mundo", "C#", "Codenda", "Bienvenido", "Aprendiendo",
         "Listo", "Codigo", "Practica", "Avanzando", "Dotnet"],
    ))
    # 2. Variables y asignación
    sets.append(mapped(
        lambda t: f"Crea la variable {t[0]} de tipo string con el valor '{t[1]}' e imprímela.",
        lambda t: f"string {t[0]} = {q(t[1])};\nConsole.WriteLine({t[0]});",
        [("ciudad", "Lima"), ("pais", "Peru"), ("color", "azul"), ("animal", "gato"),
         ("fruta", "mango"), ("lenguaje", "CSharp"), ("equipo", "Odoo"), ("mes", "enero"),
         ("dia", "lunes"), ("plato", "ceviche")],
    ))
    # 3. Aritmética con enteros
    _notes = {"20 / 3": " (división entera, sin decimales)", "20 % 3": " (resto de la división)",
              "(int)Math.Pow(2, 5)": " (potencia 2^5)"}
    sets.append(mapped(
        lambda e: f"Calcula e imprime el resultado de {e}{_notes.get(e, '')}",
        lambda e: f"Console.WriteLine({e});",
        ["7 + 5", "20 / 3", "20 % 3", "10 - 3", "4 * 6", "(int)Math.Pow(2, 5)",
         "8 + 9", "15 - 7", "3 * 9", "100 / 7"],
    ))
    # 4. Interpolación $""
    sets.append(explicit([
        ("Asigna name=\"Ana\" y age=22. Usa interpolación para presentarla (formato: nombre tiene edad anios).",
         'string name = "Ana";\nint age = 22;\nConsole.WriteLine($"{name} tiene {age} anios");'),
        ("Asigna city=\"Lima\" y country=\"Peru\". Imprime la ubicación con interpolación (formato: ciudad, pais).",
         'string city = "Lima";\nstring country = "Peru";\nConsole.WriteLine($"{city}, {country}");'),
        ("Asigna producto=\"Libro\" y precio=25. Muestra qué producto es y cuánto cuesta (formato: producto cuesta precio).",
         'string producto = "Libro";\nint precio = 25;\nConsole.WriteLine($"{producto} cuesta {precio}");'),
        ("Asigna lenguaje=\"CSharp\" y anio=2000. Imprime en qué año apareció (formato: lenguaje nacio en anio).",
         'string lenguaje = "CSharp";\nint anio = 2000;\nConsole.WriteLine($"{lenguaje} nacio en {anio}");'),
        ("Asigna animal=\"gato\" y sonido=\"miau\". Describe el animal (formato: El animal dice sonido).",
         'string animal = "gato";\nstring sonido = "miau";\nConsole.WriteLine($"El {animal} dice {sonido}");'),
        ("Asigna equipo=\"Odoo\" e integrantes=5. Imprime cuántas personas hay (formato: equipo tiene N integrantes).",
         'string equipo = "Odoo";\nint integrantes = 5;\nConsole.WriteLine($"{equipo} tiene {integrantes} integrantes");'),
        ("Con a=4 y b=6, calcula la suma en una variable e imprímela (formato: Suma: resultado).",
         'int a = 4;\nint b = 6;\nint total = a + b;\nConsole.WriteLine($"Suma: {total}");'),
        ("Con nombre=\"Mia\", saluda (formato: Hola, nombre).",
         'string nombre = "Mia";\nConsole.WriteLine($"Hola, {nombre}");'),
        ("Asigna color=\"azul\" y objeto=\"cielo\". Describe (formato: El objeto es color).",
         'string color = "azul";\nstring objeto = "cielo";\nConsole.WriteLine($"El {objeto} es {color}");'),
        ("Presenta a Pablo, 29 años (formato: nombre tiene edad anios). Crea las variables que necesites.",
         'string name = "Pablo";\nint age = 29;\nConsole.WriteLine($"{name} tiene {age} anios");'),
    ]))
    # 5. Tipos y conversión
    sets.append(explicit([
        drill("Convierte \"5\" a entero con int.Parse y súmale 3.", 'Console.WriteLine(int.Parse("5") + 3);',
              hint="int.Parse(texto) convierte texto a entero."),
        drill("Imprime el booleano de (1 == 1).", "Console.WriteLine(1 == 1);",
              hint="Una comparación devuelve true o false."),
        drill("Convierte el número 42 a texto y agrégale \"!\".", 'Console.WriteLine(42.ToString() + "!");',
              hint="numero.ToString() convierte un número a texto."),
        drill("Convierte \"2.5\" a double con double.Parse y súmale 0.5.", 'Console.WriteLine(double.Parse("2.5") + 0.5);',
              hint="double.Parse(texto) convierte texto a decimal."),
        ("Convierte 3.9 a entero (trunca los decimales) con (int).", "Console.WriteLine((int)3.9);"),
        ("Imprime el booleano de (0 > 1).", "Console.WriteLine(0 > 1);"),
        drill("Redondea 3.14159 a 2 decimales con Math.Round.", "Console.WriteLine(Math.Round(3.14159, 2));",
              hint="Math.Round(numero, decimales) redondea."),
        ('Suma int.Parse("12") + int.Parse("8").', 'Console.WriteLine(int.Parse("12") + int.Parse("8"));'),
        ('Convierte "100" a entero y divídelo entre 4 (división entera).', 'Console.WriteLine(int.Parse("100") / 4);'),
        ("Imprime la longitud del texto \"dotnet\".", 'Console.WriteLine("dotnet".Length);'),
    ]))

    # ---- SA.B — Strings ------------------------------------------------
    # 6. Concatenación y Length
    sets.append(explicit([
        ('Une "Hola" y "mundo" con un espacio e imprime el resultado.',
         'string a = "Hola";\nstring b = "mundo";\nConsole.WriteLine(a + " " + b);'),
        ('Une "buen" y "dia" con un espacio e imprime el resultado.',
         'string a = "buen";\nstring b = "dia";\nConsole.WriteLine(a + " " + b);'),
        ('Une "Odoo" y "ERP" con un espacio e imprime el resultado.',
         'string a = "Odoo";\nstring b = "ERP";\nConsole.WriteLine(a + " " + b);'),
        ('Une "CSharp" y "rocks" con un espacio e imprime el resultado.',
         'string a = "CSharp";\nstring b = "rocks";\nConsole.WriteLine(a + " " + b);'),
        ('Une "hasta" y "luego" con un espacio e imprime el resultado.',
         'string a = "hasta";\nstring b = "luego";\nConsole.WriteLine(a + " " + b);'),
        drill('Dada s="interview", imprime cuántos caracteres tiene con .Length.',
              'string s = "interview";\nConsole.WriteLine(s.Length);',
              hint="s.Length devuelve cuántos caracteres tiene la cadena."),
        ('Dada s="odoo", imprime la longitud de s.', 'string s = "odoo";\nConsole.WriteLine(s.Length);'),
        ('Une "muy" y "bien" con espacio e imprime la longitud del resultado.',
         'string a = "muy";\nstring b = "bien";\nConsole.WriteLine((a + " " + b).Length);'),
        ('Dada palabra="csharp", imprime palabra.Length.', 'string palabra = "csharp";\nConsole.WriteLine(palabra.Length);'),
        ('Dada frase="buen dia", imprime cuántos caracteres tiene (incluye el espacio).',
         'string frase = "buen dia";\nConsole.WriteLine(frase.Length);'),
    ]))
    # 7. Índices y Substring
    sets.append(explicit([
        drill('Dada s="csharp", imprime el primer caracter con s[0].',
              'string s = "csharp";\nConsole.WriteLine(s[0]);',
              hint="s[0] es el primer caracter; s[s.Length - 1] es el último."),
        drill('Dada s="odoo", imprime el último caracter con s[s.Length - 1].',
              'string s = "odoo";\nConsole.WriteLine(s[s.Length - 1]);',
              hint="El último índice es s.Length - 1."),
        ('Dada s="kumon", imprime el primer y último caracter separados por un guion.',
         'string s = "kumon";\nConsole.WriteLine(s[0] + "-" + s[s.Length - 1]);'),
        drill('Dada s="csharp", imprime los primeros 3 caracteres con Substring(0, 3).',
              'string s = "csharp";\nConsole.WriteLine(s.Substring(0, 3));',
              hint="Substring(inicio, largo) extrae una parte del texto."),
        drill('Dada s="abc", invierte el texto usando Reverse().',
              'string s = "abc";\nConsole.WriteLine(new string(s.Reverse().ToArray()));',
              hint="s.Reverse() invierte los caracteres; new string(...) los une."),
    ] + [
        drill(f'Dada s="{w}", imprime el primer y último caracter separados por un guion.',
              f'string s = "{w}";\nConsole.WriteLine(s[0] + "-" + s[s.Length - 1]);')
        for w in ["variable", "metodo", "objeto", "cadena", "entero"]
    ]))
    # 8. Métodos de string
    sets.append(explicit([
        drill('Dada s="hola", imprímela en MAYÚSCULAS con ToUpper().',
              'string s = "hola";\nConsole.WriteLine(s.ToUpper());',
              hint="s.ToUpper() pasa todo a mayúsculas."),
        ('Dada s="ODOO", imprímela en minúsculas con ToLower().', 'string s = "ODOO";\nConsole.WriteLine(s.ToLower());'),
        drill('Dada s="  hola  ", quita los espacios de los extremos con Trim().',
              'string s = "  hola  ";\nConsole.WriteLine(s.Trim());',
              hint="Trim() elimina espacios al inicio y al final."),
        ('Dada s="csharp", reemplaza "s" por "C" con Replace.', 'string s = "csharp";\nConsole.WriteLine(s.Replace("s", "C"));'),
        ('Dada s="hola mundo", ponla en formato título con manual: primera de cada palabra en mayúscula. Usa "Hola Mundo".',
         'Console.WriteLine("Hola Mundo");'),
        ('Dada s="csharp", indica si contiene "har" (true/false) con Contains.',
         'string s = "csharp";\nConsole.WriteLine(s.Contains("har"));'),
        ('Dada s="banana", cuenta cuántas veces aparece "a" con Count(c => c == \'a\').',
         'string s = "banana";\nConsole.WriteLine(s.Count(c => c == \'a\'));'),
        ('Dada s="hola", imprime si empieza con "ho" usando StartsWith.',
         'string s = "hola";\nConsole.WriteLine(s.StartsWith("ho"));'),
        ('Dada s="reporte.pdf", imprime si termina en ".pdf" con EndsWith.',
         'string s = "reporte.pdf";\nConsole.WriteLine(s.EndsWith(".pdf"));'),
        ('Dada s="Odoo", imprime la posición de "o" (minúscula) con IndexOf.',
         'string s = "Odoo";\nConsole.WriteLine(s.IndexOf("o"));'),
    ]))
    # 9. Interpolación con cálculo
    sets.append(explicit([
        ('Con a=8 y b=3, imprime "8 + 3 = 11" usando interpolación y el cálculo dentro.',
         'int a = 8;\nint b = 3;\nConsole.WriteLine($"{a} + {b} = {a + b}");'),
        ('Con a=9 y b=4, imprime "9 - 4 = 5" con interpolación.',
         'int a = 9;\nint b = 4;\nConsole.WriteLine($"{a} - {b} = {a - b}");'),
        ('Con a=6 y b=7, imprime "6 * 7 = 42" con interpolación.',
         'int a = 6;\nint b = 7;\nConsole.WriteLine($"{a} * {b} = {a * b}");'),
        ('Con base_=5 y altura=4, imprime "Area: 20" (base*altura para un rectángulo... aquí base*altura).',
         'int base_ = 5;\nint altura = 4;\nConsole.WriteLine($"Area: {base_ * altura}");'),
        ('Con precio=100 y cantidad=3, imprime "Total: 300".',
         'int precio = 100;\nint cantidad = 3;\nConsole.WriteLine($"Total: {precio * cantidad}");'),
        ('Con n=7, imprime "El doble de 7 es 14".',
         'int n = 7;\nConsole.WriteLine($"El doble de {n} es {n * 2}");'),
        ('Con nota1=80 y nota2=90, imprime "Promedio: 85".',
         'int nota1 = 80;\nint nota2 = 90;\nConsole.WriteLine($"Promedio: {(nota1 + nota2) / 2}");'),
        ('Con km=10, imprime "10 km = 10000 m".',
         'int km = 10;\nConsole.WriteLine($"{km} km = {km * 1000} m");'),
        ('Con horas=3, imprime "3 horas = 180 minutos".',
         'int horas = 3;\nConsole.WriteLine($"{horas} horas = {horas * 60} minutos");'),
        ('Con a=20 y b=6, imprime "20 / 6 = 3 (resto 2)" usando / y %.',
         'int a = 20;\nint b = 6;\nConsole.WriteLine($"{a} / {b} = {a / b} (resto {a % b})");'),
    ]))
    # 10. Repetición y formato
    sets.append(explicit([
        drill('Imprime "=" repetido 5 veces (=====) con new string(\'=\', 5).',
              "Console.WriteLine(new string('=', 5));",
              hint="new string(caracter, n) repite un caracter n veces."),
        ("Imprime \"-\" repetido 10 veces.", "Console.WriteLine(new string('-', 10));"),
        ('Imprime "ab" repetido 3 veces (ababab) con string.Concat(Enumerable.Repeat("ab", 3)).',
         'Console.WriteLine(string.Concat(Enumerable.Repeat("ab", 3)));'),
        ('Imprime "ho" repetido 2 veces (hoho).',
         'Console.WriteLine(string.Concat(Enumerable.Repeat("ho", 2)));'),
        ("Imprime \"*\" repetido 7 veces.", "Console.WriteLine(new string('*', 7));"),
        ('Une la lista {"a", "b", "c"} con "," usando string.Join (a,b,c).',
         'Console.WriteLine(string.Join(",", new[] { "a", "b", "c" }));'),
        ('Une {"Lima", "Peru"} con " - " usando string.Join.',
         'Console.WriteLine(string.Join(" - ", new[] { "Lima", "Peru" }));'),
        ('Imprime el número 7 con 3 dígitos (007) usando ToString("D3").',
         'Console.WriteLine(7.ToString("D3"));'),
        ('Imprime 3.5 con 2 decimales (3.50) usando ToString("F2").',
         'Console.WriteLine((3.5).ToString("F2"));'),
        ('Une {"1", "2", "3"} con "+" (1+2+3).',
         'Console.WriteLine(string.Join("+", new[] { "1", "2", "3" }));'),
    ]))

    # ---- SA.C — Operadores y condicionales -----------------------------
    # 11. Comparaciones
    sets.append(mapped(
        lambda e: f"Imprime el resultado (true/false) de: {e}",
        lambda e: f"Console.WriteLine({e});",
        ["5 > 3", "10 == 10", "7 != 4", "2 <= 2", "9 < 1",
         "100 >= 99", "3 * 3 == 9", "5 % 2 == 0", "8 / 2 == 4", "1 > 0"],
    ))
    # 12. if / else
    sets.append(explicit([
        drill('Dada x=7, imprime "positivo" si x > 0, si no "no positivo".',
              'int x = 7;\nif (x > 0)\n    Console.WriteLine("positivo");\nelse\n    Console.WriteLine("no positivo");',
              hint="Usa if (condicion) { ... } else { ... }."),
        ('Dada n=4, imprime "par" si es par, si no "impar".',
         'int n = 4;\nif (n % 2 == 0)\n    Console.WriteLine("par");\nelse\n    Console.WriteLine("impar");'),
        ('Dada edad=20, imprime "mayor" si edad >= 18, si no "menor".',
         'int edad = 20;\nif (edad >= 18)\n    Console.WriteLine("mayor");\nelse\n    Console.WriteLine("menor");'),
        ('Dada nota=55, imprime "aprobado" si nota >= 60, si no "reprobado".',
         'int nota = 55;\nif (nota >= 60)\n    Console.WriteLine("aprobado");\nelse\n    Console.WriteLine("reprobado");'),
        ('Dada temp=30, imprime "calor" si temp > 25, si no "templado".',
         'int temp = 30;\nif (temp > 25)\n    Console.WriteLine("calor");\nelse\n    Console.WriteLine("templado");'),
        ('Dada saldo=0, imprime "sin fondos" si saldo == 0, si no "ok".',
         'int saldo = 0;\nif (saldo == 0)\n    Console.WriteLine("sin fondos");\nelse\n    Console.WriteLine("ok");'),
        ('Dada n=9, imprime "grande" si n > 5, si no "chico".',
         'int n = 9;\nif (n > 5)\n    Console.WriteLine("grande");\nelse\n    Console.WriteLine("chico");'),
        ('Dada letra count len de "hola"=4, imprime "largo" si Length > 3, si no "corto".',
         'string s = "hola";\nif (s.Length > 3)\n    Console.WriteLine("largo");\nelse\n    Console.WriteLine("corto");'),
        ('Dada x=-2, imprime "negativo" si x < 0, si no "no negativo".',
         'int x = -2;\nif (x < 0)\n    Console.WriteLine("negativo");\nelse\n    Console.WriteLine("no negativo");'),
        ('Dada stock=3, imprime "hay" si stock > 0, si no "agotado".',
         'int stock = 3;\nif (stock > 0)\n    Console.WriteLine("hay");\nelse\n    Console.WriteLine("agotado");'),
    ]))
    # 13. if / else if / else
    sets.append(explicit([
        drill('Dada nota=82, imprime "A" si >=90, "B" si >=80, "C" si >=70, si no "F".',
              'int nota = 82;\nif (nota >= 90)\n    Console.WriteLine("A");\nelse if (nota >= 80)\n    Console.WriteLine("B");\nelse if (nota >= 70)\n    Console.WriteLine("C");\nelse\n    Console.WriteLine("F");',
              hint="Compara de mayor a menor con else if."),
        ('Dada x=0, imprime "positivo" si >0, "cero" si ==0, si no "negativo".',
         'int x = 0;\nif (x > 0)\n    Console.WriteLine("positivo");\nelse if (x == 0)\n    Console.WriteLine("cero");\nelse\n    Console.WriteLine("negativo");'),
        ('Dada h=14, imprime "manana" si <12, "tarde" si <18, si no "noche".',
         'int h = 14;\nif (h < 12)\n    Console.WriteLine("manana");\nelse if (h < 18)\n    Console.WriteLine("tarde");\nelse\n    Console.WriteLine("noche");'),
        ('Dada n=3, imprime "uno" si ==1, "dos" si ==2, si no "otro".',
         'int n = 3;\nif (n == 1)\n    Console.WriteLine("uno");\nelse if (n == 2)\n    Console.WriteLine("dos");\nelse\n    Console.WriteLine("otro");'),
        ('Dada t=5, imprime "frio" si <10, "templado" si <25, si no "calor".',
         'int t = 5;\nif (t < 10)\n    Console.WriteLine("frio");\nelse if (t < 25)\n    Console.WriteLine("templado");\nelse\n    Console.WriteLine("calor");'),
        ('Dada v=75, imprime "alto" si >=80, "medio" si >=50, si no "bajo".',
         'int v = 75;\nif (v >= 80)\n    Console.WriteLine("alto");\nelse if (v >= 50)\n    Console.WriteLine("medio");\nelse\n    Console.WriteLine("bajo");'),
        ('Dada n=15, imprime "FizzBuzz" si divisible por 15, "Fizz" si por 3, "Buzz" si por 5, si no el numero.',
         'int n = 15;\nif (n % 15 == 0)\n    Console.WriteLine("FizzBuzz");\nelse if (n % 3 == 0)\n    Console.WriteLine("Fizz");\nelse if (n % 5 == 0)\n    Console.WriteLine("Buzz");\nelse\n    Console.WriteLine(n);'),
        ('Dada edad=65, imprime "nino" si <13, "adulto" si <65, si no "adulto mayor".',
         'int edad = 65;\nif (edad < 13)\n    Console.WriteLine("nino");\nelse if (edad < 65)\n    Console.WriteLine("adulto");\nelse\n    Console.WriteLine("adulto mayor");'),
        ('Dada s="B", imprime "primero" si =="A", "segundo" si =="B", si no "otro".',
         'string s = "B";\nif (s == "A")\n    Console.WriteLine("primero");\nelse if (s == "B")\n    Console.WriteLine("segundo");\nelse\n    Console.WriteLine("otro");'),
        ('Dada n=-4, imprime "cero" si ==0, "par" si par, si no "impar".',
         'int n = -4;\nif (n == 0)\n    Console.WriteLine("cero");\nelse if (n % 2 == 0)\n    Console.WriteLine("par");\nelse\n    Console.WriteLine("impar");'),
    ]))
    # 14. Operadores lógicos
    sets.append(mapped(
        lambda e: f"Imprime el resultado (true/false) de: {e}",
        lambda e: f"Console.WriteLine({e});",
        ["true && false", "true || false", "!false", "5 > 3 && 2 < 4", "1 > 2 || 3 > 2",
         "!(5 == 5)", "10 > 0 && 10 < 100", "false || (2 == 2)", "3 > 1 && 1 > 3", "!(1 > 2)"],
    ))
    # 15. Condicionales anidados
    sets.append(explicit([
        drill('Dada edad=20 y licencia=true, imprime "puede conducir" solo si edad>=18 Y licencia; si no "no puede".',
              'int edad = 20;\nbool licencia = true;\nif (edad >= 18 && licencia)\n    Console.WriteLine("puede conducir");\nelse\n    Console.WriteLine("no puede");',
              hint="Combina condiciones con &&."),
        ('Dada n=12, imprime "divisible por 6" si es divisible por 2 y por 3, si no "no".',
         'int n = 12;\nif (n % 2 == 0 && n % 3 == 0)\n    Console.WriteLine("divisible por 6");\nelse\n    Console.WriteLine("no");'),
        ('Dada x=5, imprime "en rango" si 1<=x<=10 (usa &&), si no "fuera".',
         'int x = 5;\nif (x >= 1 && x <= 10)\n    Console.WriteLine("en rango");\nelse\n    Console.WriteLine("fuera");'),
        ('Dada user="admin" y activo=true, imprime "acceso" si user=="admin" y activo, si no "denegado".',
         'string user = "admin";\nbool activo = true;\nif (user == "admin" && activo)\n    Console.WriteLine("acceso");\nelse\n    Console.WriteLine("denegado");'),
        ('Dada a=3 y b=0, imprime "ok" si b!=0, si no "no dividir por cero".',
         'int a = 3;\nint b = 0;\nif (b != 0)\n    Console.WriteLine("ok");\nelse\n    Console.WriteLine("no dividir por cero");'),
        ('Dada n=7, imprime "impar y positivo" si n>0 y n impar, si no "otro".',
         'int n = 7;\nif (n > 0 && n % 2 != 0)\n    Console.WriteLine("impar y positivo");\nelse\n    Console.WriteLine("otro");'),
        ('Dada temp=20 y llueve=false, imprime "salir" si temp>15 y no llueve, si no "quedarse".',
         'int temp = 20;\nbool llueve = false;\nif (temp > 15 && !llueve)\n    Console.WriteLine("salir");\nelse\n    Console.WriteLine("quedarse");'),
        ('Dada nota=95, imprime "excelente" si >=90, con else if "bien" si >=70, si no "mejorar".',
         'int nota = 95;\nif (nota >= 90)\n    Console.WriteLine("excelente");\nelse if (nota >= 70)\n    Console.WriteLine("bien");\nelse\n    Console.WriteLine("mejorar");'),
        ('Dada year=2000, imprime "bisiesto" si divisible por 400 o (por 4 y no por 100), si no "comun".',
         'int year = 2000;\nif (year % 400 == 0 || (year % 4 == 0 && year % 100 != 0))\n    Console.WriteLine("bisiesto");\nelse\n    Console.WriteLine("comun");'),
        ('Dada saldo=50 y monto=30, imprime "aprobado" si saldo>=monto, si no "rechazado".',
         'int saldo = 50;\nint monto = 30;\nif (saldo >= monto)\n    Console.WriteLine("aprobado");\nelse\n    Console.WriteLine("rechazado");'),
    ]))

    # ---- SA.D — Repaso -------------------------------------------------
    # 16. Variables e interpolación (repaso)
    sets.append(mapped(
        lambda t: f"Crea nombre=\"{t[0]}\" y edad={t[1]}, imprime \"{t[0]} tiene {t[1]} anios\".",
        lambda t: f'string nombre = {q(t[0])};\nint edad = {t[1]};\nConsole.WriteLine($"{{nombre}} tiene {{edad}} anios");',
        [("Ana", 22), ("Luis", 30), ("Mia", 8), ("Pablo", 45), ("Sofia", 19),
         ("Juan", 60), ("Rosa", 27), ("Diego", 33), ("Lucia", 15), ("Marco", 51)],
    ))
    # 17. Aritmética aplicada
    sets.append(explicit([
        ('Un producto cuesta 250 y hay 4 unidades. Imprime el total (1000).', 'Console.WriteLine(250 * 4);'),
        ('Divide 1000 entre 8 personas (división entera) e imprime.', 'Console.WriteLine(1000 / 8);'),
        ('Calcula el 10% de 350 (usa 350 * 10 / 100) e imprime.', 'Console.WriteLine(350 * 10 / 100);'),
        ('Suma 15 + 27 + 33 e imprime.', 'Console.WriteLine(15 + 27 + 33);'),
        ('Un rectángulo mide 6x9. Imprime su área.', 'Console.WriteLine(6 * 9);'),
        ('Convierte 3 horas a segundos (3*3600) e imprime.', 'Console.WriteLine(3 * 3600);'),
        ('Calcula el resto de 47 entre 5 e imprime.', 'Console.WriteLine(47 % 5);'),
        ('Promedio entero de 70, 80 y 90 ((70+80+90)/3) e imprime.', 'Console.WriteLine((70 + 80 + 90) / 3);'),
        ('Eleva 3 al cubo con (int)Math.Pow(3, 3) e imprime.', 'Console.WriteLine((int)Math.Pow(3, 3));'),
        ('Cuántas docenas hay en 50 (50/12) e imprime.', 'Console.WriteLine(50 / 12);'),
    ]))
    # 18. Strings y condicionales
    sets.append(explicit([
        ('Dada s="password", imprime "valida" si Length >= 8, si no "corta".',
         'string s = "password";\nif (s.Length >= 8)\n    Console.WriteLine("valida");\nelse\n    Console.WriteLine("corta");'),
        ('Dada email="a@b.com", imprime "ok" si contiene "@", si no "invalido".',
         'string email = "a@b.com";\nif (email.Contains("@"))\n    Console.WriteLine("ok");\nelse\n    Console.WriteLine("invalido");'),
        ('Dada s="Hola", imprime la primera letra en mayúscula (ya lo está): imprime s[0].',
         'string s = "Hola";\nConsole.WriteLine(s[0]);'),
        ('Dada archivo="foto.png", imprime "imagen" si termina en ".png", si no "otro".',
         'string archivo = "foto.png";\nif (archivo.EndsWith(".png"))\n    Console.WriteLine("imagen");\nelse\n    Console.WriteLine("otro");'),
        ('Dada s="", imprime "vacio" si Length == 0, si no "tiene texto".',
         'string s = "";\nif (s.Length == 0)\n    Console.WriteLine("vacio");\nelse\n    Console.WriteLine("tiene texto");'),
        ('Dada s="racecar", imprime "palindromo" si s es igual a su reverso, si no "no".',
         'string s = "racecar";\nstring r = new string(s.Reverse().ToArray());\nif (s == r)\n    Console.WriteLine("palindromo");\nelse\n    Console.WriteLine("no");'),
        ('Dada s="HOLA", imprime "grita" si es igual a su ToUpper(), si no "normal".',
         'string s = "HOLA";\nif (s == s.ToUpper())\n    Console.WriteLine("grita");\nelse\n    Console.WriteLine("normal");'),
        ('Dada s="abc", imprime la cantidad de caracteres y luego "corto" si <5.',
         'string s = "abc";\nif (s.Length < 5)\n    Console.WriteLine("corto");\nelse\n    Console.WriteLine("largo");'),
        ('Dada user="", imprime "anonimo" si está vacío, si no el user.',
         'string user = "";\nif (user.Length == 0)\n    Console.WriteLine("anonimo");\nelse\n    Console.WriteLine(user);'),
        ('Dada s="dotnet", imprime "contiene net" si Contains("net"), si no "no".',
         'string s = "dotnet";\nif (s.Contains("net"))\n    Console.WriteLine("contiene net");\nelse\n    Console.WriteLine("no");'),
    ]))
    # 19. Condicionales combinados
    sets.append(explicit([
        ('Dada n=18, imprime "FizzBuzz/Fizz/Buzz/numero" según divisibilidad por 3 y 5.',
         'int n = 18;\nif (n % 15 == 0)\n    Console.WriteLine("FizzBuzz");\nelse if (n % 3 == 0)\n    Console.WriteLine("Fizz");\nelse if (n % 5 == 0)\n    Console.WriteLine("Buzz");\nelse\n    Console.WriteLine(n);'),
        ('Dada x=5 y y=10, imprime el mayor de los dos.',
         'int x = 5;\nint y = 10;\nif (x > y)\n    Console.WriteLine(x);\nelse\n    Console.WriteLine(y);'),
        ('Dada a=3, b=7, c=5, imprime el mayor de los tres.',
         'int a = 3;\nint b = 7;\nint c = 5;\nint max = a;\nif (b > max) max = b;\nif (c > max) max = c;\nConsole.WriteLine(max);'),
        ('Dada nota=60, imprime "aprobado" si >=60 && <=100, si no "revisar".',
         'int nota = 60;\nif (nota >= 60 && nota <= 100)\n    Console.WriteLine("aprobado");\nelse\n    Console.WriteLine("revisar");'),
        ('Dada n=0, imprime "cero" / "positivo" / "negativo".',
         'int n = 0;\nif (n == 0)\n    Console.WriteLine("cero");\nelse if (n > 0)\n    Console.WriteLine("positivo");\nelse\n    Console.WriteLine("negativo");'),
        ('Dada mes=2, imprime cuántos días base tiene (28 si feb, 30 si abr/jun/sep/nov, si no 31). Prueba mes=2.',
         'int mes = 2;\nif (mes == 2)\n    Console.WriteLine(28);\nelse if (mes == 4 || mes == 6 || mes == 9 || mes == 11)\n    Console.WriteLine(30);\nelse\n    Console.WriteLine(31);'),
        ('Dada punt=85, imprime "medalla" si >=80, con "oro" si >=90 dentro. Prueba 85 -> "medalla plata".',
         'int punt = 85;\nif (punt >= 90)\n    Console.WriteLine("medalla oro");\nelse if (punt >= 80)\n    Console.WriteLine("medalla plata");\nelse\n    Console.WriteLine("sin medalla");'),
        ('Dada edad=70 y jubilado=true, imprime "descuento" si edad>=65 o jubilado.',
         'int edad = 70;\nbool jubilado = true;\nif (edad >= 65 || jubilado)\n    Console.WriteLine("descuento");\nelse\n    Console.WriteLine("precio normal");'),
        ('Dada n=100, imprime "grande" si >50, "mediano" si >10, si no "chico".',
         'int n = 100;\nif (n > 50)\n    Console.WriteLine("grande");\nelse if (n > 10)\n    Console.WriteLine("mediano");\nelse\n    Console.WriteLine("chico");'),
        ('Dada temp=-5, imprime "congelado" si <=0, "frio" si <15, si no "ok".',
         'int temp = -5;\nif (temp <= 0)\n    Console.WriteLine("congelado");\nelse if (temp < 15)\n    Console.WriteLine("frio");\nelse\n    Console.WriteLine("ok");'),
    ]))
    # 20. Mini-retos integrados
    sets.append(explicit([
        ('Dada s="hola mundo", imprime cuántos caracteres tiene sin contar espacios (usa Replace).',
         'string s = "hola mundo";\nConsole.WriteLine(s.Replace(" ", "").Length);'),
        ('Dada n=1234, imprime la suma de sus dígitos (1+2+3+4=10). Usa % y /.',
         'int n = 1234;\nint suma = 0;\nwhile (n > 0) { suma += n % 10; n /= 10; }\nConsole.WriteLine(suma);'),
        ('Dada s="Codenda", imprime "C-a" (primer y último caracter unidos por guion).',
         'string s = "Codenda";\nConsole.WriteLine(s[0] + "-" + s[s.Length - 1]);'),
        ('Dada base=5 y exp=3, imprime base^exp usando Math.Pow y (int).',
         'int base_ = 5;\nint exp = 3;\nConsole.WriteLine((int)Math.Pow(base_, exp));'),
        ('Dada frase="uno dos tres", imprime cuántas palabras tiene (Split por espacio).',
         'string frase = "uno dos tres";\nConsole.WriteLine(frase.Split(" ").Length);'),
        ('Dada n=7, imprime "primo" si es primo (para 7 verifica 2..6), si no "no".',
         'int n = 7;\nbool primo = n > 1;\nfor (int i = 2; i < n; i++) if (n % i == 0) primo = false;\nConsole.WriteLine(primo ? "primo" : "no");'),
        ('Dada s="Nivel", imprime en mayúsculas y su longitud, formato "NIVEL 5".',
         'string s = "Nivel";\nConsole.WriteLine($"{s.ToUpper()} {s.Length}");'),
        ('Dada temp_c=25, conviértela a Fahrenheit (c*9/5+32) e imprime.',
         'int temp_c = 25;\nConsole.WriteLine(temp_c * 9 / 5 + 32);'),
        ('Dada nums {4, 8, 15, 16}, imprime su suma con Sum().',
         'Console.WriteLine(new[] { 4, 8, 15, 16 }.Sum());'),
        ('Dada s="madam", imprime "si" si es palíndromo, si no "no".',
         'string s = "madam";\nConsole.WriteLine(s == new string(s.Reverse().ToArray()) ? "si" : "no");'),
    ]))

    # ---- SA.Extra — Dictionaries O(1) ----------------------------------
    # 21. Par llave -> valor
    sets.append(explicit([
        drill('Crea un Dictionary<string,int> con {"a": 1} e imprime d["a"].',
              'var d = new Dictionary<string, int> { ["a"] = 1 };\nConsole.WriteLine(d["a"]);',
              hint="Un Dictionary guarda pares llave -> valor y se lee con d[llave]."),
        ('Crea d con {"edad": 30} e imprime d["edad"].',
         'var d = new Dictionary<string, int> { ["edad"] = 30 };\nConsole.WriteLine(d["edad"]);'),
        ('Crea d con {"x": 5, "y": 9} e imprime d["y"].',
         'var d = new Dictionary<string, int> { ["x"] = 5, ["y"] = 9 };\nConsole.WriteLine(d["y"]);'),
        ('Crea un Dictionary<string,string> con {"pais": "Peru"} e imprime d["pais"].',
         'var d = new Dictionary<string, string> { ["pais"] = "Peru" };\nConsole.WriteLine(d["pais"]);'),
        ('Crea d vacío, asigna d["n"]=7 e imprime d["n"].',
         'var d = new Dictionary<string, int>();\nd["n"] = 7;\nConsole.WriteLine(d["n"]);'),
        ('Crea d con {"a":1,"b":2}, imprime la suma d["a"]+d["b"].',
         'var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };\nConsole.WriteLine(d["a"] + d["b"]);'),
        ('Crea d con {"nombre":"Ana"}, imprime la longitud de d["nombre"].',
         'var d = new Dictionary<string, string> { ["nombre"] = "Ana" };\nConsole.WriteLine(d["nombre"].Length);'),
        ('Crea d con {"uno":1}, cambia d["uno"]=100 e imprímelo.',
         'var d = new Dictionary<string, int> { ["uno"] = 1 };\nd["uno"] = 100;\nConsole.WriteLine(d["uno"]);'),
        ('Crea d con {"a":10,"b":20}, imprime cuántas llaves tiene con d.Count.',
         'var d = new Dictionary<string, int> { ["a"] = 10, ["b"] = 20 };\nConsole.WriteLine(d.Count);'),
        ('Crea d con {"gato":"miau"}, imprime d["gato"].',
         'var d = new Dictionary<string, string> { ["gato"] = "miau" };\nConsole.WriteLine(d["gato"]);'),
    ]))
    # 22. Buscar por llave (ContainsKey)
    sets.append(explicit([
        drill('Con d={"a":1}, imprime true/false de d.ContainsKey("a").',
              'var d = new Dictionary<string, int> { ["a"] = 1 };\nConsole.WriteLine(d.ContainsKey("a"));',
              hint="ContainsKey(llave) devuelve true si la llave existe, en O(1)."),
        ('Con d={"a":1}, imprime d.ContainsKey("z").',
         'var d = new Dictionary<string, int> { ["a"] = 1 };\nConsole.WriteLine(d.ContainsKey("z"));'),
        ('Con d={"x":5}, imprime "existe" si ContainsKey("x"), si no "no".',
         'var d = new Dictionary<string, int> { ["x"] = 5 };\nif (d.ContainsKey("x"))\n    Console.WriteLine("existe");\nelse\n    Console.WriteLine("no");'),
        ('Con d={"a":1,"b":2}, imprime d["b"] solo si existe la llave "b".',
         'var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };\nif (d.ContainsKey("b"))\n    Console.WriteLine(d["b"]);'),
        ('Con d vacío, usa GetValueOrDefault("a") e imprime (0).',
         'var d = new Dictionary<string, int>();\nConsole.WriteLine(d.GetValueOrDefault("a"));'),
        ('Con d={"a":9}, usa GetValueOrDefault("a", -1) e imprime (9).',
         'var d = new Dictionary<string, int> { ["a"] = 9 };\nConsole.WriteLine(d.GetValueOrDefault("a", -1));'),
        ('Con d={"a":9}, usa GetValueOrDefault("z", -1) e imprime (-1).',
         'var d = new Dictionary<string, int> { ["a"] = 9 };\nConsole.WriteLine(d.GetValueOrDefault("z", -1));'),
        ('Con d={"perro":4}, imprime "si" si ContainsKey("perro").',
         'var d = new Dictionary<string, int> { ["perro"] = 4 };\nConsole.WriteLine(d.ContainsKey("perro") ? "si" : "no");'),
        ('Con d={"a":1,"b":2}, imprime cuántas de "a","z" existen (0,1,o2).',
         'var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };\nint c = 0;\nif (d.ContainsKey("a")) c++;\nif (d.ContainsKey("z")) c++;\nConsole.WriteLine(c);'),
        ('Con d={"k":7}, usa TryGetValue para imprimir el valor si existe.',
         'var d = new Dictionary<string, int> { ["k"] = 7 };\nif (d.TryGetValue("k", out int v))\n    Console.WriteLine(v);'),
    ]))
    # 23. Que va como llave
    sets.append(explicit([
        ('Cuenta letras: con d vacío, para "aab" incrementa d[c]. Imprime d["a"] (2).',
         'var d = new Dictionary<char, int>();\nforeach (char c in "aab") d[c] = d.GetValueOrDefault(c) + 1;\nConsole.WriteLine(d[\'a\']);'),
        ('Usa un int como llave: d[1]="uno". Imprime d[1].',
         'var d = new Dictionary<int, string> { [1] = "uno" };\nConsole.WriteLine(d[1]);'),
        ('Mapea nota->letra: d[90]="A". Imprime d[90].',
         'var d = new Dictionary<int, string> { [90] = "A" };\nConsole.WriteLine(d[90]);'),
        ('Con "banana", cuenta las "a" con un Dictionary e imprime.',
         'var d = new Dictionary<char, int>();\nforeach (char c in "banana") d[c] = d.GetValueOrDefault(c) + 1;\nConsole.WriteLine(d[\'a\']);'),
        ('Guarda precios: d["pan"]=3. Imprime d["pan"].',
         'var d = new Dictionary<string, int> { ["pan"] = 3 };\nConsole.WriteLine(d["pan"]);'),
        ('Con lista {1,1,2}, cuenta apariciones de 1 en un Dictionary e imprime.',
         'var d = new Dictionary<int, int>();\nforeach (int n in new[] { 1, 1, 2 }) d[n] = d.GetValueOrDefault(n) + 1;\nConsole.WriteLine(d[1]);'),
        ('Guarda booleanos: d["activo"]=true. Imprime d["activo"].',
         'var d = new Dictionary<string, bool> { ["activo"] = true };\nConsole.WriteLine(d["activo"]);'),
        ('Con "hello", imprime cuántas veces aparece "l" (2).',
         'var d = new Dictionary<char, int>();\nforeach (char c in "hello") d[c] = d.GetValueOrDefault(c) + 1;\nConsole.WriteLine(d[\'l\']);'),
        ('Mapea dia->numero: d["lun"]=1. Imprime d["lun"].',
         'var d = new Dictionary<string, int> { ["lun"] = 1 };\nConsole.WriteLine(d["lun"]);'),
        ('Con {5,5,5}, cuenta apariciones de 5 e imprime (3).',
         'var d = new Dictionary<int, int>();\nforeach (int n in new[] { 5, 5, 5 }) d[n] = d.GetValueOrDefault(n) + 1;\nConsole.WriteLine(d[5]);'),
    ]))
    # 24. Patron seen
    sets.append(explicit([
        drill('Con nums {2,3,3}, imprime el primer número repetido usando un HashSet "seen".',
              'var seen = new HashSet<int>();\nforeach (int n in new[] { 2, 3, 3 })\n{\n    if (seen.Contains(n)) { Console.WriteLine(n); break; }\n    seen.Add(n);\n}',
              hint="Guarda lo visto en un HashSet; si vuelve a aparecer, es el repetido."),
        ('Con nums {1,2,3,1}, imprime el primer repetido (1).',
         'var seen = new HashSet<int>();\nforeach (int n in new[] { 1, 2, 3, 1 })\n{\n    if (seen.Contains(n)) { Console.WriteLine(n); break; }\n    seen.Add(n);\n}'),
        ('Con "abca", imprime el primer caracter repetido (a).',
         'var seen = new HashSet<char>();\nforeach (char c in "abca")\n{\n    if (seen.Contains(c)) { Console.WriteLine(c); break; }\n    seen.Add(c);\n}'),
        ('Con nums {5,6,7}, imprime "sin repetidos" si no hay ninguno.',
         'var seen = new HashSet<int>();\nbool hay = false;\nforeach (int n in new[] { 5, 6, 7 }) { if (!seen.Add(n)) { hay = true; break; } }\nConsole.WriteLine(hay ? "hay" : "sin repetidos");'),
        ('Con nums {4,4}, imprime true si existe algún duplicado.',
         'var seen = new HashSet<int>();\nbool dup = false;\nforeach (int n in new[] { 4, 4 }) if (!seen.Add(n)) dup = true;\nConsole.WriteLine(dup);'),
        ('Con "hola", imprime cuántos caracteres únicos hay (4).',
         'var seen = new HashSet<char>();\nforeach (char c in "hola") seen.Add(c);\nConsole.WriteLine(seen.Count);'),
        ('Con nums {1,2,2,3,3,3}, imprime cuántos valores distintos hay (3).',
         'var seen = new HashSet<int>();\nforeach (int n in new[] { 1, 2, 2, 3, 3, 3 }) seen.Add(n);\nConsole.WriteLine(seen.Count);'),
        ('Con "aabbcc", imprime el primer repetido (a).',
         'var seen = new HashSet<char>();\nforeach (char c in "aabbcc")\n{\n    if (!seen.Add(c)) { Console.WriteLine(c); break; }\n}'),
        ('Con nums {10,20,30,20}, imprime el primer repetido (20).',
         'var seen = new HashSet<int>();\nforeach (int n in new[] { 10, 20, 30, 20 })\n{\n    if (!seen.Add(n)) { Console.WriteLine(n); break; }\n}'),
        ('Con "abcdef", imprime "todos unicos" si no hay repetidos.',
         'var seen = new HashSet<char>();\nbool rep = false;\nforeach (char c in "abcdef") if (!seen.Add(c)) rep = true;\nConsole.WriteLine(rep ? "hay repetidos" : "todos unicos");'),
    ]))
    # 25. Two Sum y variantes
    sets.append(explicit([
        drill('Con nums {3,2,4} y target=6, imprime los índices que suman 6 usando un Dictionary (patrón Two Sum).',
              'var nums = new[] { 3, 2, 4 };\nint target = 6;\nvar seen = new Dictionary<int, int>();\nfor (int i = 0; i < nums.Length; i++)\n{\n    int need = target - nums[i];\n    if (seen.ContainsKey(need)) { Console.WriteLine($"[{seen[need]}, {i}]"); break; }\n    seen[nums[i]] = i;\n}',
              hint="Guarda numero->indice; para cada n, busca need=target-n con ContainsKey en O(1)."),
        ('Con nums {2,7,11,15} y target=9, imprime los índices (patrón Two Sum).',
         'var nums = new[] { 2, 7, 11, 15 };\nint target = 9;\nvar seen = new Dictionary<int, int>();\nfor (int i = 0; i < nums.Length; i++)\n{\n    int need = target - nums[i];\n    if (seen.ContainsKey(need)) { Console.WriteLine($"[{seen[need]}, {i}]"); break; }\n    seen[nums[i]] = i;\n}'),
        ('Con nums {1,2,3,4} y target=7, imprime los índices (Two Sum).',
         'var nums = new[] { 1, 2, 3, 4 };\nint target = 7;\nvar seen = new Dictionary<int, int>();\nfor (int i = 0; i < nums.Length; i++)\n{\n    int need = target - nums[i];\n    if (seen.ContainsKey(need)) { Console.WriteLine($"[{seen[need]}, {i}]"); break; }\n    seen[nums[i]] = i;\n}'),
        ('Con nums {5,5} y target=10, imprime true si existen dos que sumen target.',
         'var nums = new[] { 5, 5 };\nint target = 10;\nvar seen = new HashSet<int>();\nbool ok = false;\nforeach (int n in nums) { if (seen.Contains(target - n)) { ok = true; break; } seen.Add(n); }\nConsole.WriteLine(ok);'),
        ('Con nums {1,2,3} y target=100, imprime false (no hay par que sume target).',
         'var nums = new[] { 1, 2, 3 };\nint target = 100;\nvar seen = new HashSet<int>();\nbool ok = false;\nforeach (int n in nums) { if (seen.Contains(target - n)) { ok = true; break; } seen.Add(n); }\nConsole.WriteLine(ok);'),
        ('Con nums {4,1,2,3} y target=5, imprime cuántos pares (i<j) suman 5 (2).',
         'var nums = new[] { 4, 1, 2, 3 };\nint target = 5;\nint count = 0;\nfor (int i = 0; i < nums.Length; i++)\n    for (int j = i + 1; j < nums.Length; j++)\n        if (nums[i] + nums[j] == target) count++;\nConsole.WriteLine(count);'),
        ('Con nums {3,3,3} y target=6, imprime los índices del primer par (Two Sum).',
         'var nums = new[] { 3, 3, 3 };\nint target = 6;\nvar seen = new Dictionary<int, int>();\nfor (int i = 0; i < nums.Length; i++)\n{\n    int need = target - nums[i];\n    if (seen.ContainsKey(need)) { Console.WriteLine($"[{seen[need]}, {i}]"); break; }\n    seen[nums[i]] = i;\n}'),
        ('Con nums {0,4,3,0} y target=0, imprime los índices que suman 0 (Two Sum).',
         'var nums = new[] { 0, 4, 3, 0 };\nint target = 0;\nvar seen = new Dictionary<int, int>();\nfor (int i = 0; i < nums.Length; i++)\n{\n    int need = target - nums[i];\n    if (seen.ContainsKey(need)) { Console.WriteLine($"[{seen[need]}, {i}]"); break; }\n    seen[nums[i]] = i;\n}'),
        ('Con nums {1,-1,2} y target=0, imprime los índices que suman 0 (Two Sum).',
         'var nums = new[] { 1, -1, 2 };\nint target = 0;\nvar seen = new Dictionary<int, int>();\nfor (int i = 0; i < nums.Length; i++)\n{\n    int need = target - nums[i];\n    if (seen.ContainsKey(need)) { Console.WriteLine($"[{seen[need]}, {i}]"); break; }\n    seen[nums[i]] = i;\n}'),
        ('Con nums {6,2,8,4} y target=10, imprime cuántos pares (i<j) suman 10 (2).',
         'var nums = new[] { 6, 2, 8, 4 };\nint target = 10;\nint count = 0;\nfor (int i = 0; i < nums.Length; i++)\n    for (int j = i + 1; j < nums.Length; j++)\n        if (nums[i] + nums[j] == target) count++;\nConsole.WriteLine(count);'),
    ]))

    return sets


# ---------------------------------------------------------------------------
# LEVEL SB — Bucles y métodos
# ---------------------------------------------------------------------------

def level_sb() -> list[list[dict]]:
    sets: list[list[dict]] = []

    # SB.A — for
    sets.append(mapped(
        lambda n: f"Imprime los números del 1 al {n}, uno por línea.",
        lambda n: f"for (int i = 1; i <= {n}; i++)\n    Console.WriteLine(i);",
        [3, 5, 4, 6, 2, 7, 5, 4, 8, 3],
    ))
    sets.append(mapped(
        lambda n: f"Imprime la suma de 1 a {n}.",
        lambda n: f"int total = 0;\nfor (int i = 1; i <= {n}; i++)\n    total += i;\nConsole.WriteLine(total);",
        [5, 10, 3, 7, 100, 4, 6, 8, 20, 15],
    ))
    sets.append(explicit([
        ("Imprime los pares del 2 al 10, uno por línea.", "for (int i = 2; i <= 10; i += 2)\n    Console.WriteLine(i);"),
        ("Imprime los impares del 1 al 9, uno por línea.", "for (int i = 1; i <= 9; i += 2)\n    Console.WriteLine(i);"),
        ("Imprime los múltiplos de 5 del 5 al 25.", "for (int i = 5; i <= 25; i += 5)\n    Console.WriteLine(i);"),
        ("Imprime de 0 a 20 de 4 en 4.", "for (int i = 0; i <= 20; i += 4)\n    Console.WriteLine(i);"),
        ("Imprime de 3 a 30 de 3 en 3.", "for (int i = 3; i <= 30; i += 3)\n    Console.WriteLine(i);"),
        ("Imprime los pares del 0 al 8.", "for (int i = 0; i <= 8; i += 2)\n    Console.WriteLine(i);"),
        ("Imprime de 10 a 100 de 10 en 10.", "for (int i = 10; i <= 100; i += 10)\n    Console.WriteLine(i);"),
        ("Imprime de 1 a 13 de 4 en 4.", "for (int i = 1; i <= 13; i += 4)\n    Console.WriteLine(i);"),
        ("Imprime los múltiplos de 7 del 7 al 35.", "for (int i = 7; i <= 35; i += 7)\n    Console.WriteLine(i);"),
        ("Imprime de 2 a 18 de 2 en 2.", "for (int i = 2; i <= 18; i += 2)\n    Console.WriteLine(i);"),
    ]))
    sets.append(mapped(
        lambda n: f"Cuenta regresiva: imprime de {n} a 1, uno por línea.",
        lambda n: f"for (int i = {n}; i >= 1; i--)\n    Console.WriteLine(i);",
        [3, 5, 4, 6, 2, 7, 5, 4, 3, 8],
    ))
    sets.append(explicit([
        ("Dado el array {4, 8, 15}, imprime cada elemento en su línea con un for.",
         "int[] nums = { 4, 8, 15 };\nfor (int i = 0; i < nums.Length; i++)\n    Console.WriteLine(nums[i]);"),
        ("Dado {1, 2, 3}, imprime la suma con un for.",
         "int[] nums = { 1, 2, 3 };\nint total = 0;\nfor (int i = 0; i < nums.Length; i++)\n    total += nums[i];\nConsole.WriteLine(total);"),
        ("Dado {10, 20, 30}, imprime cada elemento con foreach.",
         "int[] nums = { 10, 20, 30 };\nforeach (int n in nums)\n    Console.WriteLine(n);"),
        ("Dado {2, 4, 6, 8}, imprime la suma con foreach.",
         "int[] nums = { 2, 4, 6, 8 };\nint total = 0;\nforeach (int n in nums)\n    total += n;\nConsole.WriteLine(total);"),
        ('Dado {"a", "b", "c"}, imprime cada string con foreach.',
         'string[] xs = { "a", "b", "c" };\nforeach (string x in xs)\n    Console.WriteLine(x);'),
        ("Dado {5, 3, 9}, imprime el doble de cada uno.",
         "int[] nums = { 5, 3, 9 };\nforeach (int n in nums)\n    Console.WriteLine(n * 2);"),
        ("Dado {1, 2, 3, 4}, imprime cuántos elementos hay (Length).",
         "int[] nums = { 1, 2, 3, 4 };\nConsole.WriteLine(nums.Length);"),
        ("Dado {7, 7, 7}, imprime la suma con foreach.",
         "int[] nums = { 7, 7, 7 };\nint total = 0;\nforeach (int n in nums)\n    total += n;\nConsole.WriteLine(total);"),
        ("Dado {3, 6, 9}, imprime cada elemento más 1.",
         "int[] nums = { 3, 6, 9 };\nforeach (int n in nums)\n    Console.WriteLine(n + 1);"),
        ("Dado {100, 200}, imprime cada elemento con foreach.",
         "int[] nums = { 100, 200 };\nforeach (int n in nums)\n    Console.WriteLine(n);"),
    ]))

    # SB.B — while, break, continue
    sets.append(mapped(
        lambda n: f"Usa un while para imprimir de 1 a {n}.",
        lambda n: f"int i = 1;\nwhile (i <= {n})\n{{\n    Console.WriteLine(i);\n    i++;\n}}",
        [3, 5, 4, 6, 2, 7, 5, 4, 3, 8],
    ))
    sets.append(explicit([
        ("Con un while, imprime la suma de 1 a 5.", "int i = 1;\nint total = 0;\nwhile (i <= 5)\n{\n    total += i;\n    i++;\n}\nConsole.WriteLine(total);"),
        ("Con un while, duplica 1 hasta pasar 100 e imprime el valor final.", "int n = 1;\nwhile (n <= 100)\n    n *= 2;\nConsole.WriteLine(n);"),
        ("Con un while, cuenta cuántas veces divides 100 entre 2 hasta llegar a 1 o menos.", "int n = 100;\nint pasos = 0;\nwhile (n > 1)\n{\n    n /= 2;\n    pasos++;\n}\nConsole.WriteLine(pasos);"),
        ("Con un while, imprime los pares del 2 al 10.", "int i = 2;\nwhile (i <= 10)\n{\n    Console.WriteLine(i);\n    i += 2;\n}"),
        ("Con un while, suma los números del 1 al 10 e imprime el total.", "int i = 1;\nint total = 0;\nwhile (i <= 10)\n{\n    total += i;\n    i++;\n}\nConsole.WriteLine(total);"),
        ("Con un while, imprime de 10 a 1 (regresivo).", "int i = 10;\nwhile (i >= 1)\n{\n    Console.WriteLine(i);\n    i--;\n}"),
        ("Con un while, resta 3 a 20 hasta que sea negativo e imprime el valor final.", "int n = 20;\nwhile (n >= 0)\n    n -= 3;\nConsole.WriteLine(n);"),
        ("Con un while, cuenta los dígitos de 12345 (usa /10).", "int n = 12345;\nint c = 0;\nwhile (n > 0)\n{\n    n /= 10;\n    c++;\n}\nConsole.WriteLine(c);"),
        ("Con un while, imprime la suma de los primeros 3 múltiplos de 5 (5+10+15).", "int i = 5;\nint total = 0;\nwhile (i <= 15)\n{\n    total += i;\n    i += 5;\n}\nConsole.WriteLine(total);"),
        ("Con un while, cuenta cuántas veces multiplicas 3 hasta pasar 50, e imprime el conteo.", "int n = 3;\nint c = 1;\nwhile (n * 3 <= 50)\n{\n    n *= 3;\n    c++;\n}\nConsole.WriteLine(c);"),
    ]))
    sets.append(explicit([
        drill("Con un for de 1 a 10, usa break para detenerte al llegar a 5 e imprime cada número antes.",
              "for (int i = 1; i <= 10; i++)\n{\n    if (i == 5) break;\n    Console.WriteLine(i);\n}",
              hint="break sale del bucle inmediatamente."),
        ("Con un for de 1 a 100, imprime el primer número divisible por 7 y detente.",
         "for (int i = 1; i <= 100; i++)\n{\n    if (i % 7 == 0) { Console.WriteLine(i); break; }\n}"),
        ("Busca en {3, 8, 5, 9} el primer número mayor a 6 e imprímelo (break).",
         "int[] nums = { 3, 8, 5, 9 };\nforeach (int n in nums)\n{\n    if (n > 6) { Console.WriteLine(n); break; }\n}"),
        ("Con un for de 2 a 20, imprime números hasta que la suma acumulada pase 10; imprime esa suma.",
         "int total = 0;\nfor (int i = 2; i <= 20; i++)\n{\n    total += i;\n    if (total > 10) break;\n}\nConsole.WriteLine(total);"),
        ("Recorre {1, 2, 3, 4} e imprime cada uno hasta encontrar el 3 (inclusive, luego break).",
         "int[] nums = { 1, 2, 3, 4 };\nforeach (int n in nums)\n{\n    Console.WriteLine(n);\n    if (n == 3) break;\n}"),
        ("Con un for de 1 a 10, detente en el primer cuadrado perfecto > 1 (i*i coincide) — imprime 4.",
         "for (int i = 1; i <= 10; i++)\n{\n    if (i > 1 && i % 2 == 0) { Console.WriteLine(i * i / i); break; }\n}"),
        ("Busca el primer negativo en {5, 2, -3, 8} e imprímelo (break).",
         "int[] nums = { 5, 2, -3, 8 };\nforeach (int n in nums)\n{\n    if (n < 0) { Console.WriteLine(n); break; }\n}"),
        ("Con un while infinito controlado, imprime i de 1 en 1 y usa break al llegar a 3.",
         "int i = 1;\nwhile (true)\n{\n    Console.WriteLine(i);\n    if (i == 3) break;\n    i++;\n}"),
        ("Recorre {10, 20, 30} e imprime el primero que sea >= 20 (break).",
         "int[] nums = { 10, 20, 30 };\nforeach (int n in nums)\n{\n    if (n >= 20) { Console.WriteLine(n); break; }\n}"),
        ("Con un for de 1 a 50, imprime el primer múltiplo de 13 y detente.",
         "for (int i = 1; i <= 50; i++)\n{\n    if (i % 13 == 0) { Console.WriteLine(i); break; }\n}"),
    ]))
    sets.append(explicit([
        drill("Con un for de 1 a 6, usa continue para saltar el 3 e imprime el resto.",
              "for (int i = 1; i <= 6; i++)\n{\n    if (i == 3) continue;\n    Console.WriteLine(i);\n}",
              hint="continue salta a la siguiente iteración sin ejecutar lo que sigue."),
        ("Con un for de 1 a 10, imprime solo los impares usando continue en los pares.",
         "for (int i = 1; i <= 10; i++)\n{\n    if (i % 2 == 0) continue;\n    Console.WriteLine(i);\n}"),
        ("Recorre {1, -2, 3, -4} e imprime solo los positivos (continue si <= 0).",
         "int[] nums = { 1, -2, 3, -4 };\nforeach (int n in nums)\n{\n    if (n <= 0) continue;\n    Console.WriteLine(n);\n}"),
        ("Con un for de 1 a 15, imprime solo los múltiplos de 3 (continue si no).",
         "for (int i = 1; i <= 15; i++)\n{\n    if (i % 3 != 0) continue;\n    Console.WriteLine(i);\n}"),
        ("Suma de 1 a 10 pero saltando el 5; imprime el total.",
         "int total = 0;\nfor (int i = 1; i <= 10; i++)\n{\n    if (i == 5) continue;\n    total += i;\n}\nConsole.WriteLine(total);"),
        ("Recorre {2, 4, 5, 6} e imprime solo los pares (continue si impar).",
         "int[] nums = { 2, 4, 5, 6 };\nforeach (int n in nums)\n{\n    if (n % 2 != 0) continue;\n    Console.WriteLine(n);\n}"),
        ("Con un for de 1 a 20, imprime solo múltiplos de 5.",
         "for (int i = 1; i <= 20; i++)\n{\n    if (i % 5 != 0) continue;\n    Console.WriteLine(i);\n}"),
        ("Cuenta cuántos positivos hay en {3, -1, 4, -1, 5} usando continue.",
         "int[] nums = { 3, -1, 4, -1, 5 };\nint c = 0;\nforeach (int n in nums)\n{\n    if (n <= 0) continue;\n    c++;\n}\nConsole.WriteLine(c);"),
        ("Imprime de 1 a 10 saltando los múltiplos de 3.",
         "for (int i = 1; i <= 10; i++)\n{\n    if (i % 3 == 0) continue;\n    Console.WriteLine(i);\n}"),
        ("Suma solo los pares de 1 a 8 (continue si impar) e imprime el total.",
         "int total = 0;\nfor (int i = 1; i <= 8; i++)\n{\n    if (i % 2 != 0) continue;\n    total += i;\n}\nConsole.WriteLine(total);"),
    ]))
    sets.append(explicit([
        ("Con un while, acumula la suma de {1,2,3,4} recorriendo por índice; imprime el total.",
         "int[] nums = { 1, 2, 3, 4 };\nint i = 0;\nint total = 0;\nwhile (i < nums.Length)\n{\n    total += nums[i];\n    i++;\n}\nConsole.WriteLine(total);"),
        ("Con un while, cuenta cuántos elementos de {5,0,3,0} son cero.",
         "int[] nums = { 5, 0, 3, 0 };\nint i = 0;\nint c = 0;\nwhile (i < nums.Length)\n{\n    if (nums[i] == 0) c++;\n    i++;\n}\nConsole.WriteLine(c);"),
        ("Con un while, multiplica los elementos de {2,3,4} (producto) e imprime.",
         "int[] nums = { 2, 3, 4 };\nint i = 0;\nint prod = 1;\nwhile (i < nums.Length)\n{\n    prod *= nums[i];\n    i++;\n}\nConsole.WriteLine(prod);"),
        ("Con un while, suma los dígitos de 4321 e imprime.",
         "int n = 4321;\nint suma = 0;\nwhile (n > 0)\n{\n    suma += n % 10;\n    n /= 10;\n}\nConsole.WriteLine(suma);"),
        ("Con un while, invierte los dígitos de 123 (resultado 321) e imprime.",
         "int n = 123;\nint rev = 0;\nwhile (n > 0)\n{\n    rev = rev * 10 + n % 10;\n    n /= 10;\n}\nConsole.WriteLine(rev);"),
        ("Con un while, cuenta cuántas veces cabe 7 en 50 (50/7 entero) sin usar división directa.",
         "int n = 50;\nint c = 0;\nwhile (n >= 7)\n{\n    n -= 7;\n    c++;\n}\nConsole.WriteLine(c);"),
        ("Con un while, acumula 1+2+...+n hasta que el total pase 20; imprime el total.",
         "int i = 1;\nint total = 0;\nwhile (total <= 20)\n{\n    total += i;\n    i++;\n}\nConsole.WriteLine(total);"),
        ("Con un while, encuentra el mayor de {3,9,5,1} recorriendo por índice.",
         "int[] nums = { 3, 9, 5, 1 };\nint i = 1;\nint max = nums[0];\nwhile (i < nums.Length)\n{\n    if (nums[i] > max) max = nums[i];\n    i++;\n}\nConsole.WriteLine(max);"),
        ("Con un while, cuenta cuántos números pares hay en {2,3,4,5,6}.",
         "int[] nums = { 2, 3, 4, 5, 6 };\nint i = 0;\nint c = 0;\nwhile (i < nums.Length)\n{\n    if (nums[i] % 2 == 0) c++;\n    i++;\n}\nConsole.WriteLine(c);"),
        ("Con un while, suma 3+6+9+...+30 e imprime el total.",
         "int i = 3;\nint total = 0;\nwhile (i <= 30)\n{\n    total += i;\n    i += 3;\n}\nConsole.WriteLine(total);"),
    ]))

    # SB.C — Patrones de bucle
    sets.append(explicit([
        drill('Recorre {"a","b","c"} imprimiendo "indice: valor" (0: a, ...).',
              'string[] xs = { "a", "b", "c" };\nfor (int i = 0; i < xs.Length; i++)\n    Console.WriteLine($"{i}: {xs[i]}");',
              hint="Usa el índice i del for para numerar."),
        ('Recorre {10,20,30} imprimiendo "posicion valor" (0 10, ...).',
         'int[] xs = { 10, 20, 30 };\nfor (int i = 0; i < xs.Length; i++)\n    Console.WriteLine($"{i} {xs[i]}");'),
        ('Recorre {"lun","mar"} imprimiendo "dia 1: lun" (1-based).',
         'string[] xs = { "lun", "mar" };\nfor (int i = 0; i < xs.Length; i++)\n    Console.WriteLine($"dia {i + 1}: {xs[i]}");'),
        ('Imprime cada caracter de "abc" con su índice (0 a, ...).',
         'string s = "abc";\nfor (int i = 0; i < s.Length; i++)\n    Console.WriteLine($"{i} {s[i]}");'),
        ('Recorre {5,6,7} imprimiendo "i=indice n=valor".',
         'int[] xs = { 5, 6, 7 };\nfor (int i = 0; i < xs.Length; i++)\n    Console.WriteLine($"i={i} n={xs[i]}");'),
        ('Imprime "1) x" para cada elemento de {"x","y"} (1-based con paréntesis).',
         'string[] xs = { "x", "y" };\nfor (int i = 0; i < xs.Length; i++)\n    Console.WriteLine($"{i + 1}) {xs[i]}");'),
        ('Suma indice+valor para {10,20,30} e imprime cada suma parcial.',
         'int[] xs = { 10, 20, 30 };\nfor (int i = 0; i < xs.Length; i++)\n    Console.WriteLine(i + xs[i]);'),
        ('Imprime el índice del valor 9 en {3,9,7} (busca y muestra 1).',
         'int[] xs = { 3, 9, 7 };\nfor (int i = 0; i < xs.Length; i++)\n    if (xs[i] == 9) Console.WriteLine(i);'),
        ('Recorre "hi" imprimiendo cada caracter con "pos=indice".',
         'string s = "hi";\nfor (int i = 0; i < s.Length; i++)\n    Console.WriteLine($"pos={i} {s[i]}");'),
        ('Recorre {100,200,300} e imprime "item indice: valor".',
         'int[] xs = { 100, 200, 300 };\nfor (int i = 0; i < xs.Length; i++)\n    Console.WriteLine($"item {i}: {xs[i]}");'),
    ]))
    sets.append(explicit([
        drill('Dadas {"Ana","Luis"} y {20,30}, imprime "Ana 20" y "Luis 30" recorriendo por índice.',
              'string[] nombres = { "Ana", "Luis" };\nint[] edades = { 20, 30 };\nfor (int i = 0; i < nombres.Length; i++)\n    Console.WriteLine($"{nombres[i]} {edades[i]}");',
              hint="Usa el mismo índice i para ambos arrays."),
        ('Dadas {1,2,3} y {4,5,6}, imprime la suma de cada par (5,7,9).',
         'int[] a = { 1, 2, 3 };\nint[] b = { 4, 5, 6 };\nfor (int i = 0; i < a.Length; i++)\n    Console.WriteLine(a[i] + b[i]);'),
        ('Dadas {2,3} y {5,7}, imprime el producto de cada par (10, 21).',
         'int[] a = { 2, 3 };\nint[] b = { 5, 7 };\nfor (int i = 0; i < a.Length; i++)\n    Console.WriteLine(a[i] * b[i]);'),
        ('Dadas {"x","y"} y {"1","2"}, imprime "x=1" y "y=2".',
         'string[] k = { "x", "y" };\nstring[] v = { "1", "2" };\nfor (int i = 0; i < k.Length; i++)\n    Console.WriteLine($"{k[i]}={v[i]}");'),
        ('Dadas {10,20,30} y {1,2,3}, imprime a-b de cada par (9,18,27).',
         'int[] a = { 10, 20, 30 };\nint[] b = { 1, 2, 3 };\nfor (int i = 0; i < a.Length; i++)\n    Console.WriteLine(a[i] - b[i]);'),
        ('Dadas {1,1,1} y {2,3,4}, imprime la suma total de sumar cada par (2+... = 12).',
         'int[] a = { 1, 1, 1 };\nint[] b = { 2, 3, 4 };\nint total = 0;\nfor (int i = 0; i < a.Length; i++)\n    total += a[i] + b[i];\nConsole.WriteLine(total);'),
        ('Dadas {"a","b"} y {"c","d"}, imprime "ac" y "bd" (concatenado).',
         'string[] a = { "a", "b" };\nstring[] b = { "c", "d" };\nfor (int i = 0; i < a.Length; i++)\n    Console.WriteLine(a[i] + b[i]);'),
        ('Dadas {5,10} y {2,5}, imprime a/b de cada par (2, 2).',
         'int[] a = { 5, 10 };\nint[] b = { 2, 5 };\nfor (int i = 0; i < a.Length; i++)\n    Console.WriteLine(a[i] / b[i]);'),
        ('Dadas {3,6,9} y {3,3,3}, cuenta cuántos pares son iguales (0).',
         'int[] a = { 3, 6, 9 };\nint[] b = { 3, 3, 3 };\nint c = 0;\nfor (int i = 0; i < a.Length; i++)\n    if (a[i] == b[i]) c++;\nConsole.WriteLine(c);'),
        ('Dadas {1,2,3} y {3,2,1}, imprime el mayor de cada par (3,2,3).',
         'int[] a = { 1, 2, 3 };\nint[] b = { 3, 2, 1 };\nfor (int i = 0; i < a.Length; i++)\n    Console.WriteLine(a[i] > b[i] ? a[i] : b[i]);'),
    ]))
    sets.append(explicit([
        drill("Imprime una tabla 2x3: para i en 1..2, j en 1..3, imprime 'i,j'.",
              'for (int i = 1; i <= 2; i++)\n    for (int j = 1; j <= 3; j++)\n        Console.WriteLine($"{i},{j}");',
              hint="Un bucle dentro de otro: el interno corre completo por cada vuelta del externo."),
        ("Imprime los productos de la tabla del 2 (2x1..2x3), uno por línea.",
         "for (int j = 1; j <= 3; j++)\n    Console.WriteLine(2 * j);"),
        ("Cuenta cuántos pares (i,j) con i en 1..3 y j en 1..3 cumplen i==j (imprime 3).",
         "int c = 0;\nfor (int i = 1; i <= 3; i++)\n    for (int j = 1; j <= 3; j++)\n        if (i == j) c++;\nConsole.WriteLine(c);"),
        ("Suma todos los i*j para i,j en 1..2 e imprime (1+2+2+4=9).",
         "int total = 0;\nfor (int i = 1; i <= 2; i++)\n    for (int j = 1; j <= 2; j++)\n        total += i * j;\nConsole.WriteLine(total);"),
        ("Imprime 'ab', 'ac' recorriendo {\"a\"} x {\"b\",\"c\"}.",
         'string[] xs = { "a" };\nstring[] ys = { "b", "c" };\nforeach (string x in xs)\n    foreach (string y in ys)\n        Console.WriteLine(x + y);'),
        ("Cuenta las celdas de una grilla 3x4 (imprime 12).",
         "int c = 0;\nfor (int i = 0; i < 3; i++)\n    for (int j = 0; j < 4; j++)\n        c++;\nConsole.WriteLine(c);"),
        ("Imprime pares (i,j) con i<j para i,j en 1..3 (1,2 / 1,3 / 2,3).",
         'for (int i = 1; i <= 3; i++)\n    for (int j = i + 1; j <= 3; j++)\n        Console.WriteLine($"{i},{j}");'),
        ("Suma la diagonal de una matriz {{1,2},{3,4}} (1+4=5).",
         "int[][] m = { new[] { 1, 2 }, new[] { 3, 4 } };\nint total = 0;\nfor (int i = 0; i < 2; i++)\n    total += m[i][i];\nConsole.WriteLine(total);"),
        ("Recorre {{1,2},{3,4}} imprimiendo cada elemento (1,2,3,4).",
         "int[][] m = { new[] { 1, 2 }, new[] { 3, 4 } };\nforeach (int[] fila in m)\n    foreach (int x in fila)\n        Console.WriteLine(x);"),
        ("Cuenta cuántos pares (i,j) con i,j en 1..3 suman 4 (imprime 3).",
         "int c = 0;\nfor (int i = 1; i <= 3; i++)\n    for (int j = 1; j <= 3; j++)\n        if (i + j == 4) c++;\nConsole.WriteLine(c);"),
    ]))
    sets.append(explicit([
        drill("Encuentra el máximo de {3,7,2,9,4} con un bucle manual e imprímelo.",
              "int[] nums = { 3, 7, 2, 9, 4 };\nint max = nums[0];\nforeach (int n in nums)\n    if (n > max) max = n;\nConsole.WriteLine(max);",
              hint="Empieza asumiendo que el primero es el máximo y compara."),
        ("Encuentra el mínimo de {5,3,8,1,4} manualmente e imprímelo.",
         "int[] nums = { 5, 3, 8, 1, 4 };\nint min = nums[0];\nforeach (int n in nums)\n    if (n < min) min = n;\nConsole.WriteLine(min);"),
        ("Encuentra el máximo de {-3,-7,-1} manualmente.",
         "int[] nums = { -3, -7, -1 };\nint max = nums[0];\nforeach (int n in nums)\n    if (n > max) max = n;\nConsole.WriteLine(max);"),
        ("Imprime la diferencia entre el máximo y el mínimo de {2,9,4} (7).",
         "int[] nums = { 2, 9, 4 };\nint max = nums[0], min = nums[0];\nforeach (int n in nums)\n{\n    if (n > max) max = n;\n    if (n < min) min = n;\n}\nConsole.WriteLine(max - min);"),
        ("Encuentra el string más largo de {\"a\",\"abc\",\"ab\"} e imprímelo.",
         'string[] xs = { "a", "abc", "ab" };\nstring largo = xs[0];\nforeach (string x in xs)\n    if (x.Length > largo.Length) largo = x;\nConsole.WriteLine(largo);'),
        ("Imprime el índice del máximo de {4,8,2} (1).",
         "int[] nums = { 4, 8, 2 };\nint idx = 0;\nfor (int i = 1; i < nums.Length; i++)\n    if (nums[i] > nums[idx]) idx = i;\nConsole.WriteLine(idx);"),
        ("Encuentra el mínimo de {10,10,10} (10).",
         "int[] nums = { 10, 10, 10 };\nint min = nums[0];\nforeach (int n in nums)\n    if (n < min) min = n;\nConsole.WriteLine(min);"),
        ("Imprime el máximo de {1,2,3,4,5} sin usar Max().",
         "int[] nums = { 1, 2, 3, 4, 5 };\nint max = nums[0];\nforeach (int n in nums)\n    if (n > max) max = n;\nConsole.WriteLine(max);"),
        ("Imprime el promedio entero de {2,4,6} calculando suma con bucle (4).",
         "int[] nums = { 2, 4, 6 };\nint total = 0;\nforeach (int n in nums) total += n;\nConsole.WriteLine(total / nums.Length);"),
        ("Encuentra el segundo elemento más grande NO haría falta; imprime el máximo de {7,3,7,1} (7).",
         "int[] nums = { 7, 3, 7, 1 };\nint max = nums[0];\nforeach (int n in nums)\n    if (n > max) max = n;\nConsole.WriteLine(max);"),
    ]))
    sets.append(explicit([
        drill("Cuenta cuántas veces aparece 'a' en \"banana\" con un bucle.",
              "string s = \"banana\";\nint c = 0;\nforeach (char ch in s)\n    if (ch == 'a') c++;\nConsole.WriteLine(c);",
              hint="Recorre los caracteres y suma 1 cuando coincide."),
        ("Cuenta cuántos números pares hay en {1,2,3,4,5,6} (3).",
         "int[] nums = { 1, 2, 3, 4, 5, 6 };\nint c = 0;\nforeach (int n in nums)\n    if (n % 2 == 0) c++;\nConsole.WriteLine(c);"),
        ("Cuenta cuántos elementos de {5,2,8,1} son mayores a 3 (2).",
         "int[] nums = { 5, 2, 8, 1 };\nint c = 0;\nforeach (int n in nums)\n    if (n > 3) c++;\nConsole.WriteLine(c);"),
        ("Cuenta cuántas vocales hay en \"educacion\".",
         "string s = \"educacion\";\nint c = 0;\nforeach (char ch in s)\n    if (\"aeiou\".Contains(ch)) c++;\nConsole.WriteLine(c);"),
        ("Cuenta cuántos ceros hay en {0,1,0,2,0} (3).",
         "int[] nums = { 0, 1, 0, 2, 0 };\nint c = 0;\nforeach (int n in nums)\n    if (n == 0) c++;\nConsole.WriteLine(c);"),
        ("Cuenta cuántas palabras en \"uno dos tres\" tienen 3 letras (3).",
         'string[] ws = "uno dos tres".Split(" ");\nint c = 0;\nforeach (string w in ws)\n    if (w.Length == 3) c++;\nConsole.WriteLine(c);'),
        ("Cuenta cuántos negativos hay en {-1,2,-3,4,-5} (3).",
         "int[] nums = { -1, 2, -3, 4, -5 };\nint c = 0;\nforeach (int n in nums)\n    if (n < 0) c++;\nConsole.WriteLine(c);"),
        ("Cuenta cuántas veces aparece 'l' en \"hello world\" (3).",
         "string s = \"hello world\";\nint c = 0;\nforeach (char ch in s)\n    if (ch == 'l') c++;\nConsole.WriteLine(c);"),
        ("Cuenta cuántos múltiplos de 3 hay en {3,6,7,9,10} (3).",
         "int[] nums = { 3, 6, 7, 9, 10 };\nint c = 0;\nforeach (int n in nums)\n    if (n % 3 == 0) c++;\nConsole.WriteLine(c);"),
        ("Cuenta cuántos caracteres en mayúscula hay en \"HoLa\" (2).",
         "string s = \"HoLa\";\nint c = 0;\nforeach (char ch in s)\n    if (char.IsUpper(ch)) c++;\nConsole.WriteLine(c);"),
    ]))

    # SB.D — Métodos
    sets.append(explicit([
        drill("Define un método Doble(int n) que retorne n*2 y llámalo con 5, imprimiendo el resultado.",
              "int Doble(int n) => n * 2;\nConsole.WriteLine(Doble(5));",
              hint="Un método con => retorna el valor de la expresión."),
        ("Define Cuadrado(int n) que retorne n*n y llámalo con 4.",
         "int Cuadrado(int n) => n * n;\nConsole.WriteLine(Cuadrado(4));"),
        ("Define Saludo(string nombre) que retorne \"Hola nombre\" y llámalo con \"Ana\".",
         'string Saludo(string nombre) => $"Hola {nombre}";\nConsole.WriteLine(Saludo("Ana"));'),
        ("Define EsPar(int n) que retorne true/false y llámalo con 6.",
         "bool EsPar(int n) => n % 2 == 0;\nConsole.WriteLine(EsPar(6));"),
        ("Define Incrementa(int n) que retorne n+1 y llámalo con 9.",
         "int Incrementa(int n) => n + 1;\nConsole.WriteLine(Incrementa(9));"),
        ("Define Mayuscula(string s) que retorne s en mayúsculas y llámalo con \"hola\".",
         'string Mayuscula(string s) => s.ToUpper();\nConsole.WriteLine(Mayuscula("hola"));'),
        ("Define Triple(int n) que retorne n*3 y llámalo con 7.",
         "int Triple(int n) => n * 3;\nConsole.WriteLine(Triple(7));"),
        ("Define Negativo(int n) que retorne -n y llámalo con 5.",
         "int Negativo(int n) => -n;\nConsole.WriteLine(Negativo(5));"),
        ("Define Largo(string s) que retorne su longitud y llámalo con \"dotnet\".",
         'int Largo(string s) => s.Length;\nConsole.WriteLine(Largo("dotnet"));'),
        ("Define Mitad(int n) que retorne n/2 y llámalo con 10.",
         "int Mitad(int n) => n / 2;\nConsole.WriteLine(Mitad(10));"),
    ]))
    sets.append(explicit([
        drill("Define Suma(int a, int b) y llámalo con 3 y 4.",
              "int Suma(int a, int b) => a + b;\nConsole.WriteLine(Suma(3, 4));",
              hint="Los parámetros van separados por comas."),
        ("Define Area(int b, int h) que retorne b*h y llámalo con 5 y 4.",
         "int Area(int b, int h) => b * h;\nConsole.WriteLine(Area(5, 4));"),
        ("Define Mayor(int a, int b) que retorne el mayor y llámalo con 8 y 3.",
         "int Mayor(int a, int b) => a > b ? a : b;\nConsole.WriteLine(Mayor(8, 3));"),
        ("Define Concat(string a, string b) que una con espacio y llámalo con \"buen\",\"dia\".",
         'string Concat(string a, string b) => a + " " + b;\nConsole.WriteLine(Concat("buen", "dia"));'),
        ("Define Resta(int a, int b) y llámalo con 10 y 6.",
         "int Resta(int a, int b) => a - b;\nConsole.WriteLine(Resta(10, 6));"),
        ("Define Promedio(int a, int b) entero y llámalo con 4 y 8.",
         "int Promedio(int a, int b) => (a + b) / 2;\nConsole.WriteLine(Promedio(4, 8));"),
        ("Define Potencia(int b, int e) usando Math.Pow y (int); llámalo con 2 y 5.",
         "int Potencia(int b, int e) => (int)Math.Pow(b, e);\nConsole.WriteLine(Potencia(2, 5));"),
        ("Define Suma3(int a, int b, int c) y llámalo con 1,2,3.",
         "int Suma3(int a, int b, int c) => a + b + c;\nConsole.WriteLine(Suma3(1, 2, 3));"),
        ("Define Repite(string s, int n) que repita s n veces y llámalo con \"ab\",3.",
         'string Repite(string s, int n) => string.Concat(Enumerable.Repeat(s, n));\nConsole.WriteLine(Repite("ab", 3));'),
        ("Define Distancia(int a, int b) que retorne el valor absoluto de a-b; llámalo con 3 y 9.",
         "int Distancia(int a, int b) => Math.Abs(a - b);\nConsole.WriteLine(Distancia(3, 9));"),
    ]))
    sets.append(explicit([
        drill("Define Saludo(string nombre = \"amigo\") con valor por defecto y llámalo sin argumentos.",
              'string Saludo(string nombre = "amigo") => $"Hola {nombre}";\nConsole.WriteLine(Saludo());',
              hint="Un parámetro con = valor usa ese valor si no lo pasas."),
        ("Define Incrementa(int n, int paso = 1) y llámalo con 5 (usa paso por defecto).",
         "int Incrementa(int n, int paso = 1) => n + paso;\nConsole.WriteLine(Incrementa(5));"),
        ("Define Incrementa(int n, int paso = 1) y llámalo con 5 y 10.",
         "int Incrementa(int n, int paso = 1) => n + paso;\nConsole.WriteLine(Incrementa(5, 10));"),
        ("Define Potencia(int b, int e = 2) y llámalo con 4 (cuadrado por defecto).",
         "int Potencia(int b, int e = 2) => (int)Math.Pow(b, e);\nConsole.WriteLine(Potencia(4));"),
        ("Define Multiplica(int a, int factor = 3) y llámalo con 5.",
         "int Multiplica(int a, int factor = 3) => a * factor;\nConsole.WriteLine(Multiplica(5));"),
        ("Define Linea(char c = '-', int n = 5) que retorne n veces c; llámalo sin argumentos.",
         "string Linea(char c = '-', int n = 5) => new string(c, n);\nConsole.WriteLine(Linea());"),
        ("Define Linea(char c = '-', int n = 5) y llámalo con '*' y 3.",
         "string Linea(char c = '-', int n = 5) => new string(c, n);\nConsole.WriteLine(Linea('*', 3));"),
        ("Define Saluda(string s = \"Hola\", string quien = \"mundo\") y llámalo sin argumentos.",
         'string Saluda(string s = "Hola", string quien = "mundo") => $"{s}, {quien}";\nConsole.WriteLine(Saluda());'),
        ("Define Descuento(int precio, int pct = 10) que reste el pct%; llámalo con 100.",
         "int Descuento(int precio, int pct = 10) => precio - precio * pct / 100;\nConsole.WriteLine(Descuento(100));"),
        ("Define Suma(int a, int b = 0, int c = 0) y llámalo con solo 7.",
         "int Suma(int a, int b = 0, int c = 0) => a + b + c;\nConsole.WriteLine(Suma(7));"),
    ]))
    sets.append(explicit([
        drill("Define Nota(int s) que retorne 'A' si >=90, 'B' si >=80, si no 'F'; llámalo con 85.",
              'string Nota(int s)\n{\n    if (s >= 90) return "A";\n    if (s >= 80) return "B";\n    return "F";\n}\nConsole.WriteLine(Nota(85));',
              hint="Un método puede tener varios return según condiciones."),
        ("Define Signo(int n) que retorne 'positivo'/'cero'/'negativo'; llámalo con -3.",
         'string Signo(int n)\n{\n    if (n > 0) return "positivo";\n    if (n == 0) return "cero";\n    return "negativo";\n}\nConsole.WriteLine(Signo(-3));'),
        ("Define Max(int a, int b) con if; llámalo con 4 y 9.",
         "int Max(int a, int b)\n{\n    if (a > b) return a;\n    return b;\n}\nConsole.WriteLine(Max(4, 9));"),
        ("Define EsPrimo(int n) para n=7 (revisa 2..n-1); imprime true/false.",
         "bool EsPrimo(int n)\n{\n    if (n < 2) return false;\n    for (int i = 2; i < n; i++)\n        if (n % i == 0) return false;\n    return true;\n}\nConsole.WriteLine(EsPrimo(7));"),
        ("Define Abs(int n) que retorne el valor absoluto con if; llámalo con -8.",
         "int Abs(int n)\n{\n    if (n < 0) return -n;\n    return n;\n}\nConsole.WriteLine(Abs(-8));"),
        ("Define FizzBuzz(int n) que retorne texto según divisibilidad; llámalo con 15.",
         'string FizzBuzz(int n)\n{\n    if (n % 15 == 0) return "FizzBuzz";\n    if (n % 3 == 0) return "Fizz";\n    if (n % 5 == 0) return "Buzz";\n    return n.ToString();\n}\nConsole.WriteLine(FizzBuzz(15));'),
        ("Define Categoria(int edad) 'nino'/'adulto'/'mayor'; llámalo con 70.",
         'string Categoria(int edad)\n{\n    if (edad < 18) return "nino";\n    if (edad < 65) return "adulto";\n    return "mayor";\n}\nConsole.WriteLine(Categoria(70));'),
        ("Define ContarPares(int[] nums) que cuente pares; llámalo con {1,2,3,4}.",
         "int ContarPares(int[] nums)\n{\n    int c = 0;\n    foreach (int n in nums)\n        if (n % 2 == 0) c++;\n    return c;\n}\nConsole.WriteLine(ContarPares(new[] { 1, 2, 3, 4 }));"),
        ("Define Factorial(int n) con bucle; llámalo con 5.",
         "int Factorial(int n)\n{\n    int r = 1;\n    for (int i = 2; i <= n; i++)\n        r *= i;\n    return r;\n}\nConsole.WriteLine(Factorial(5));"),
        ("Define Clasifica(int nota) 'aprobado' si >=60 si no 'reprobado'; llámalo con 55.",
         'string Clasifica(int nota)\n{\n    if (nota >= 60) return "aprobado";\n    return "reprobado";\n}\nConsole.WriteLine(Clasifica(55));'),
    ]))
    sets.append(explicit([
        drill("Define Inc(int n)=>n+1 y Doble(int n)=>n*2, imprime Doble(Inc(3)) (8).",
              "int Inc(int n) => n + 1;\nint Doble(int n) => n * 2;\nConsole.WriteLine(Doble(Inc(3)));",
              hint="Puedes pasar el resultado de un método como argumento de otro."),
        ("Define Cuadrado y Suma; imprime Suma(Cuadrado(2), Cuadrado(3)) (13).",
         "int Cuadrado(int n) => n * n;\nint Suma(int a, int b) => a + b;\nConsole.WriteLine(Suma(Cuadrado(2), Cuadrado(3)));"),
        ("Define Inc(int n)=>n+1 y aplica Inc dos veces a 5 (7).",
         "int Inc(int n) => n + 1;\nConsole.WriteLine(Inc(Inc(5)));"),
        ("Define Mayuscula y Repite; imprime Repite(Mayuscula(\"ab\"),2) (ABAB).",
         'string Mayuscula(string s) => s.ToUpper();\nstring Repite(string s, int n) => string.Concat(Enumerable.Repeat(s, n));\nConsole.WriteLine(Repite(Mayuscula("ab"), 2));'),
        ("Define Abs y Resta; imprime Abs(Resta(3,9)) (6).",
         "int Abs(int n) => Math.Abs(n);\nint Resta(int a, int b) => a - b;\nConsole.WriteLine(Abs(Resta(3, 9)));"),
        ("Define Mitad y Doble; imprime Doble(Mitad(10)) (10).",
         "int Mitad(int n) => n / 2;\nint Doble(int n) => n * 2;\nConsole.WriteLine(Doble(Mitad(10)));"),
        ("Define Largo y EsPar; imprime EsPar(Largo(\"dotnet\")) (true).",
         'int Largo(string s) => s.Length;\nbool EsPar(int n) => n % 2 == 0;\nConsole.WriteLine(EsPar(Largo("dotnet")));'),
        ("Define Suma3 usando Suma dos veces; imprime Suma(Suma(1,2),3) (6).",
         "int Suma(int a, int b) => a + b;\nConsole.WriteLine(Suma(Suma(1, 2), 3));"),
        ("Define Triple y Neg; imprime Neg(Triple(4)) (-12).",
         "int Triple(int n) => n * 3;\nint Neg(int n) => -n;\nConsole.WriteLine(Neg(Triple(4)));"),
        ("Define Inc y Cuadrado; imprime Cuadrado(Inc(3)) (16).",
         "int Inc(int n) => n + 1;\nint Cuadrado(int n) => n * n;\nConsole.WriteLine(Cuadrado(Inc(3)));"),
    ]))

    return sets


# ---------------------------------------------------------------------------
# LEVEL SC — Colecciones y strings
# ---------------------------------------------------------------------------

def level_sc() -> list[list[dict]]:
    sets: list[list[dict]] = []

    # SC.A — Arrays y List<T>
    sets.append(explicit([
        drill("Crea un array {10, 20, 30} e imprime el elemento en el índice 1 (20).",
              "int[] nums = { 10, 20, 30 };\nConsole.WriteLine(nums[1]);",
              hint="Los índices empiezan en 0: nums[0] es el primero."),
        ("Crea {5, 15, 25} e imprime el primer elemento.", "int[] nums = { 5, 15, 25 };\nConsole.WriteLine(nums[0]);"),
        ("Crea {1, 2, 3, 4} e imprime el último con nums[nums.Length-1].", "int[] nums = { 1, 2, 3, 4 };\nConsole.WriteLine(nums[nums.Length - 1]);"),
        ('Crea una List<int> con {7, 8, 9} e imprime el elemento 2 (9).', "var nums = new List<int> { 7, 8, 9 };\nConsole.WriteLine(nums[2]);"),
        ('Crea List<string> {"a","b"} e imprime el primero.', 'var xs = new List<string> { "a", "b" };\nConsole.WriteLine(xs[0]);'),
        ("Crea {3, 6, 9} e imprime cuántos elementos hay (Length).", "int[] nums = { 3, 6, 9 };\nConsole.WriteLine(nums.Length);"),
        ("Crea una List<int> {1,2,3} e imprime su Count.", "var nums = new List<int> { 1, 2, 3 };\nConsole.WriteLine(nums.Count);"),
        ("Crea {2, 4, 6, 8} e imprime la suma de nums[0] y nums[3] (10).", "int[] nums = { 2, 4, 6, 8 };\nConsole.WriteLine(nums[0] + nums[3]);"),
        ("Crea {100, 200, 300}, cambia nums[1]=0 e imprímelo.", "int[] nums = { 100, 200, 300 };\nnums[1] = 0;\nConsole.WriteLine(nums[1]);"),
        ("Crea {9, 8, 7} e imprime el elemento del medio (índice 1).", "int[] nums = { 9, 8, 7 };\nConsole.WriteLine(nums[1]);"),
    ]))
    sets.append(explicit([
        drill("Crea una List<int> vacía, agrega 1, 2, 3 con Add e imprime su Count.",
              "var nums = new List<int>();\nnums.Add(1);\nnums.Add(2);\nnums.Add(3);\nConsole.WriteLine(nums.Count);",
              hint="Add agrega al final de la lista."),
        ("Crea List<int> {1,2}, agrega 3 con Add e imprime el último.", "var nums = new List<int> { 1, 2 };\nnums.Add(3);\nConsole.WriteLine(nums[nums.Count - 1]);"),
        ('Crea List<string> {"a"}, agrega "b" e imprime el Count.', 'var xs = new List<string> { "a" };\nxs.Add("b");\nConsole.WriteLine(xs.Count);'),
        ("Crea List<int> {1,3}, inserta 2 en el índice 1 con Insert e imprime nums[1].", "var nums = new List<int> { 1, 3 };\nnums.Insert(1, 2);\nConsole.WriteLine(nums[1]);"),
        ("Crea List<int> vacía, agrega 5 con Add e imprime nums[0].", "var nums = new List<int>();\nnums.Add(5);\nConsole.WriteLine(nums[0]);"),
        ("Crea List<int> {10}, agrega 20 y 30, imprime la suma con Sum().", "var nums = new List<int> { 10 };\nnums.Add(20);\nnums.Add(30);\nConsole.WriteLine(nums.Sum());"),
        ("Crea List<int> {2,4}, inserta 0 al inicio (índice 0) e imprime nums[0].", "var nums = new List<int> { 2, 4 };\nnums.Insert(0, 0);\nConsole.WriteLine(nums[0]);"),
        ('Crea List<string> vacía, agrega "hola" y "mundo", imprime el Count.', 'var xs = new List<string>();\nxs.Add("hola");\nxs.Add("mundo");\nConsole.WriteLine(xs.Count);'),
        ("Crea List<int> {1,2,3}, agrega 4 e imprime el último.", "var nums = new List<int> { 1, 2, 3 };\nnums.Add(4);\nConsole.WriteLine(nums[nums.Count - 1]);"),
        ("Crea List<int> {5,6}, inserta 99 en índice 1 e imprime nums[1].", "var nums = new List<int> { 5, 6 };\nnums.Insert(1, 99);\nConsole.WriteLine(nums[1]);"),
    ]))
    sets.append(explicit([
        drill("Dado {3, 1, 4, 1, 5}, imprime la suma con Sum().",
              "int[] nums = { 3, 1, 4, 1, 5 };\nConsole.WriteLine(nums.Sum());",
              hint="Sum(), Min(), Max() y Count() vienen de LINQ."),
        ("Dado {3, 1, 4, 1, 5}, imprime el máximo con Max().", "int[] nums = { 3, 1, 4, 1, 5 };\nConsole.WriteLine(nums.Max());"),
        ("Dado {3, 1, 4, 1, 5}, imprime el mínimo con Min().", "int[] nums = { 3, 1, 4, 1, 5 };\nConsole.WriteLine(nums.Min());"),
        ("Dado {2, 4, 6}, imprime el promedio entero (suma/Length).", "int[] nums = { 2, 4, 6 };\nConsole.WriteLine(nums.Sum() / nums.Length);"),
        ("Dado {1, 2, 3, 4}, imprime cuántos elementos hay con Count().", "int[] nums = { 1, 2, 3, 4 };\nConsole.WriteLine(nums.Count());"),
        ("Dado {10, 20, 30}, imprime Max - Min (20).", "int[] nums = { 10, 20, 30 };\nConsole.WriteLine(nums.Max() - nums.Min());"),
        ("Dado {5, 5, 5}, imprime la suma (15).", "int[] nums = { 5, 5, 5 };\nConsole.WriteLine(nums.Sum());"),
        ("Dado {-3, 0, 3}, imprime el máximo (3).", "int[] nums = { -3, 0, 3 };\nConsole.WriteLine(nums.Max());"),
        ("Dado {7, 2, 9, 4}, imprime la suma del mínimo y el máximo (11).", "int[] nums = { 7, 2, 9, 4 };\nConsole.WriteLine(nums.Min() + nums.Max());"),
        ("Dado {8, 8}, imprime el promedio (8).", "int[] nums = { 8, 8 };\nConsole.WriteLine(nums.Sum() / nums.Length);"),
    ]))
    sets.append(explicit([
        drill("Crea List<int> {1,2,3}, elimina el valor 2 con Remove e imprime el Count.",
              "var nums = new List<int> { 1, 2, 3 };\nnums.Remove(2);\nConsole.WriteLine(nums.Count);",
              hint="Remove(valor) borra la primera coincidencia; RemoveAt(indice) borra por posición."),
        ("Crea List<int> {10,20,30}, borra el índice 0 con RemoveAt e imprime nums[0].", "var nums = new List<int> { 10, 20, 30 };\nnums.RemoveAt(0);\nConsole.WriteLine(nums[0]);"),
        ("Crea List<int> {5,6,7}, borra el último con RemoveAt(Count-1) e imprime el Count.", "var nums = new List<int> { 5, 6, 7 };\nnums.RemoveAt(nums.Count - 1);\nConsole.WriteLine(nums.Count);"),
        ('Crea List<string> {"a","b","c"}, elimina "b" e imprime el Count.', 'var xs = new List<string> { "a", "b", "c" };\nxs.Remove("b");\nConsole.WriteLine(xs.Count);'),
        ("Crea List<int> {1,2,2,3}, elimina la primera 2 e imprime nums[1].", "var nums = new List<int> { 1, 2, 2, 3 };\nnums.Remove(2);\nConsole.WriteLine(nums[1]);"),
        ("Crea List<int> {9,8,7}, borra índice 1 e imprime nums[1].", "var nums = new List<int> { 9, 8, 7 };\nnums.RemoveAt(1);\nConsole.WriteLine(nums[1]);"),
        ("Crea List<int> {4,5,6}, elimina 4 e imprime nums[0].", "var nums = new List<int> { 4, 5, 6 };\nnums.Remove(4);\nConsole.WriteLine(nums[0]);"),
        ("Crea List<int> {1,2,3}, usa Clear() e imprime el Count (0).", "var nums = new List<int> { 1, 2, 3 };\nnums.Clear();\nConsole.WriteLine(nums.Count);"),
        ("Crea List<int> {3,6,9}, borra el índice 2 e imprime la suma (9).", "var nums = new List<int> { 3, 6, 9 };\nnums.RemoveAt(2);\nConsole.WriteLine(nums.Sum());"),
        ("Crea List<int> {2,4,6,8}, elimina 6 e imprime el Count (3).", "var nums = new List<int> { 2, 4, 6, 8 };\nnums.Remove(6);\nConsole.WriteLine(nums.Count);"),
    ]))
    sets.append(explicit([
        ("Recorre {2, 4, 6} con foreach acumulando la suma; imprime el total.", "int[] nums = { 2, 4, 6 };\nint total = 0;\nforeach (int n in nums) total += n;\nConsole.WriteLine(total);"),
        ("Recorre {1, 2, 3, 4} e imprime solo los pares.", "int[] nums = { 1, 2, 3, 4 };\nforeach (int n in nums)\n    if (n % 2 == 0) Console.WriteLine(n);"),
        ("Recorre {5, 10, 15} imprimiendo cada uno dividido por 5.", "int[] nums = { 5, 10, 15 };\nforeach (int n in nums) Console.WriteLine(n / 5);"),
        ("Acumula el producto de {1, 2, 3, 4} e imprime (24).", "int[] nums = { 1, 2, 3, 4 };\nint prod = 1;\nforeach (int n in nums) prod *= n;\nConsole.WriteLine(prod);"),
        ("Cuenta los positivos de {-1, 2, -3, 4} e imprime.", "int[] nums = { -1, 2, -3, 4 };\nint c = 0;\nforeach (int n in nums) if (n > 0) c++;\nConsole.WriteLine(c);"),
        ("Suma solo los mayores a 10 en {5, 15, 25} e imprime (40).", "int[] nums = { 5, 15, 25 };\nint total = 0;\nforeach (int n in nums) if (n > 10) total += n;\nConsole.WriteLine(total);"),
        ('Une {"a","b","c"} en un solo string acumulando; imprime "abc".', 'string[] xs = { "a", "b", "c" };\nstring r = "";\nforeach (string x in xs) r += x;\nConsole.WriteLine(r);'),
        ("Cuenta cuántos son múltiplos de 3 en {3, 4, 9, 10} e imprime (2).", "int[] nums = { 3, 4, 9, 10 };\nint c = 0;\nforeach (int n in nums) if (n % 3 == 0) c++;\nConsole.WriteLine(c);"),
        ("Acumula la suma de cuadrados de {1, 2, 3} e imprime (14).", "int[] nums = { 1, 2, 3 };\nint total = 0;\nforeach (int n in nums) total += n * n;\nConsole.WriteLine(total);"),
        ("Recorre {10, 20, 30} e imprime la suma acumulada paso a paso (10,30,60).", "int[] nums = { 10, 20, 30 };\nint acc = 0;\nforeach (int n in nums) { acc += n; Console.WriteLine(acc); }"),
    ]))

    # SC.B — Take/Skip, Reverse, orden
    sets.append(explicit([
        drill("Dado {1,2,3,4,5}, imprime los primeros 3 con Take(3) unidos por coma.",
              'int[] nums = { 1, 2, 3, 4, 5 };\nConsole.WriteLine(string.Join(",", nums.Take(3)));',
              hint="Take(n) toma los primeros n; Skip(n) los omite."),
        ("Dado {1,2,3,4,5}, imprime los que quedan tras Skip(2) unidos por coma.", 'int[] nums = { 1, 2, 3, 4, 5 };\nConsole.WriteLine(string.Join(",", nums.Skip(2)));'),
        ("Dado {10,20,30,40}, imprime los primeros 2 (Take) unidos por coma.", 'int[] nums = { 10, 20, 30, 40 };\nConsole.WriteLine(string.Join(",", nums.Take(2)));'),
        ("Dado {5,6,7,8}, imprime todos menos el primero (Skip(1)) unidos por coma.", 'int[] nums = { 5, 6, 7, 8 };\nConsole.WriteLine(string.Join(",", nums.Skip(1)));'),
        ("Dado {1,2,3,4,5,6}, imprime la suma de los primeros 3 (Take(3).Sum()).", "int[] nums = { 1, 2, 3, 4, 5, 6 };\nConsole.WriteLine(nums.Take(3).Sum());"),
        ("Dado {1,2,3,4}, imprime el primero con First().", "int[] nums = { 1, 2, 3, 4 };\nConsole.WriteLine(nums.First());"),
        ("Dado {1,2,3,4}, imprime el último con Last().", "int[] nums = { 1, 2, 3, 4 };\nConsole.WriteLine(nums.Last());"),
        ("Dado {9,8,7,6}, imprime los últimos 2 con Skip(2) unidos por coma.", 'int[] nums = { 9, 8, 7, 6 };\nConsole.WriteLine(string.Join(",", nums.Skip(2)));'),
        ("Dado {2,4,6,8,10}, imprime la suma tras Skip(2) (24).", "int[] nums = { 2, 4, 6, 8, 10 };\nConsole.WriteLine(nums.Skip(2).Sum());"),
        ("Dado {1,2,3,4,5}, imprime los del medio: Skip(1).Take(3) unidos por coma.", 'int[] nums = { 1, 2, 3, 4, 5 };\nConsole.WriteLine(string.Join(",", nums.Skip(1).Take(3)));'),
    ]))
    sets.append(explicit([
        drill("Dado {1,2,3}, imprime la lista invertida con Reverse() unida por coma.",
              'int[] nums = { 1, 2, 3 };\nConsole.WriteLine(string.Join(",", nums.Reverse()));',
              hint="Reverse() de LINQ invierte el orden."),
        ("Dado {5,10,15}, imprime invertido unido por coma.", 'int[] nums = { 5, 10, 15 };\nConsole.WriteLine(string.Join(",", nums.Reverse()));'),
        ('Dado {"a","b","c"}, imprime invertido unido por "-".', 'string[] xs = { "a", "b", "c" };\nConsole.WriteLine(string.Join("-", xs.Reverse()));'),
        ("Dado {1,2,3,4}, imprime el primero tras invertir (4).", "int[] nums = { 1, 2, 3, 4 };\nConsole.WriteLine(nums.Reverse().First());"),
        ("Invierte \"abc\" con Reverse() e imprime 'cba'.", 'string s = "abc";\nConsole.WriteLine(string.Join("", s.Reverse()));'),
        ("Dado {7,8,9}, imprime invertido unido por coma.", 'int[] nums = { 7, 8, 9 };\nConsole.WriteLine(string.Join(",", nums.Reverse()));'),
        ("Dado {1,2}, imprime invertido unido por coma (2,1).", 'int[] nums = { 1, 2 };\nConsole.WriteLine(string.Join(",", nums.Reverse()));'),
        ("Dado {10,20,30,40}, imprime invertido unido por espacio.", 'int[] nums = { 10, 20, 30, 40 };\nConsole.WriteLine(string.Join(" ", nums.Reverse()));'),
        ("Comprueba si {1,2,1} es igual a su reverso; imprime true/false.", "int[] nums = { 1, 2, 1 };\nConsole.WriteLine(nums.SequenceEqual(nums.Reverse()));"),
        ("Dado {3,6,9}, imprime la suma tras invertir (18, igual).", "int[] nums = { 3, 6, 9 };\nConsole.WriteLine(nums.Reverse().Sum());"),
    ]))
    sets.append(explicit([
        drill("Dado {3,1,2}, imprime ordenado ascendente con OrderBy unido por coma.",
              'int[] nums = { 3, 1, 2 };\nConsole.WriteLine(string.Join(",", nums.OrderBy(n => n)));',
              hint="OrderBy(n => n) ordena ascendente; OrderByDescending desc."),
        ("Dado {3,1,2}, imprime ordenado descendente unido por coma.", 'int[] nums = { 3, 1, 2 };\nConsole.WriteLine(string.Join(",", nums.OrderByDescending(n => n)));'),
        ('Dado {"c","a","b"}, imprime ordenado alfabéticamente unido por coma.', 'string[] xs = { "c", "a", "b" };\nConsole.WriteLine(string.Join(",", xs.OrderBy(x => x)));'),
        ("Dado {5,3,8,1}, imprime el menor con OrderBy().First() (1).", "int[] nums = { 5, 3, 8, 1 };\nConsole.WriteLine(nums.OrderBy(n => n).First());"),
        ("Dado {5,3,8,1}, imprime el mayor con OrderByDescending().First() (8).", "int[] nums = { 5, 3, 8, 1 };\nConsole.WriteLine(nums.OrderByDescending(n => n).First());"),
        ("Dado {4,2,7,1}, imprime los 2 menores (OrderBy.Take(2)) unidos por coma.", 'int[] nums = { 4, 2, 7, 1 };\nConsole.WriteLine(string.Join(",", nums.OrderBy(n => n).Take(2)));'),
        ("Dado {10,30,20}, imprime el del medio tras ordenar (20).", "int[] nums = { 10, 30, 20 };\nConsole.WriteLine(nums.OrderBy(n => n).Skip(1).First());"),
        ('Dado {"pera","ana","kiwi"}, imprime ordenado por longitud unido por coma.', 'string[] xs = { "pera", "ana", "kiwi" };\nConsole.WriteLine(string.Join(",", xs.OrderBy(x => x.Length)));'),
        ("Dado {9,9,1}, imprime ordenado ascendente unido por coma.", 'int[] nums = { 9, 9, 1 };\nConsole.WriteLine(string.Join(",", nums.OrderBy(n => n)));'),
        ("Dado {3,1,2}, imprime el segundo menor (OrderBy.Skip(1).First()) (2).", "int[] nums = { 3, 1, 2 };\nConsole.WriteLine(nums.OrderBy(n => n).Skip(1).First());"),
    ]))
    sets.append(explicit([
        drill("Crea una matriz {{1,2},{3,4}} e imprime el elemento [1][0] (3).",
              "int[][] m = { new[] { 1, 2 }, new[] { 3, 4 } };\nConsole.WriteLine(m[1][0]);",
              hint="m[fila][columna] accede a listas anidadas."),
        ("Con {{1,2},{3,4}}, imprime la suma de la primera fila (3).", "int[][] m = { new[] { 1, 2 }, new[] { 3, 4 } };\nConsole.WriteLine(m[0].Sum());"),
        ("Con {{5,6},{7,8}}, imprime el elemento [0][1] (6).", "int[][] m = { new[] { 5, 6 }, new[] { 7, 8 } };\nConsole.WriteLine(m[0][1]);"),
        ("Con {{1,1},{1,1}}, imprime la suma total (4).", "int[][] m = { new[] { 1, 1 }, new[] { 1, 1 } };\nint total = 0;\nforeach (int[] f in m) total += f.Sum();\nConsole.WriteLine(total);"),
        ("Con {{9},{8},{7}}, imprime el número de filas (3).", "int[][] m = { new[] { 9 }, new[] { 8 }, new[] { 7 } };\nConsole.WriteLine(m.Length);"),
        ("Con {{1,2,3}}, imprime la longitud de la primera fila (3).", "int[][] m = { new[] { 1, 2, 3 } };\nConsole.WriteLine(m[0].Length);"),
        ("Con {{2,4},{6,8}}, imprime el máximo de la segunda fila (8).", "int[][] m = { new[] { 2, 4 }, new[] { 6, 8 } };\nConsole.WriteLine(m[1].Max());"),
        ("Con {{1,2},{3,4}}, imprime la diagonal sumada (1+4=5).", "int[][] m = { new[] { 1, 2 }, new[] { 3, 4 } };\nConsole.WriteLine(m[0][0] + m[1][1]);"),
        ("Con {{10,20}}, imprime el segundo elemento de la primera fila (20).", "int[][] m = { new[] { 10, 20 } };\nConsole.WriteLine(m[0][1]);"),
        ("Con {{1},{2},{3}}, imprime la suma de todas las filas (6).", "int[][] m = { new[] { 1 }, new[] { 2 }, new[] { 3 } };\nint total = 0;\nforeach (int[] f in m) total += f.Sum();\nConsole.WriteLine(total);"),
    ]))
    sets.append(explicit([
        drill("Copia {1,2,3} a una nueva List con ToList(), agrega 4 a la copia e imprime el Count original (3).",
              "int[] nums = { 1, 2, 3 };\nvar copia = nums.ToList();\ncopia.Add(4);\nConsole.WriteLine(nums.Length);",
              hint="ToList() crea una copia independiente."),
        ("Copia {5,6} con ToList(), imprime el Count de la copia (2).", "int[] nums = { 5, 6 };\nvar copia = nums.ToList();\nConsole.WriteLine(copia.Count);"),
        ("Crea List<int> {1,2}, cópiala con new List<int>(orig), agrega 3 a la copia e imprime el Count original (2).", "var orig = new List<int> { 1, 2 };\nvar copia = new List<int>(orig);\ncopia.Add(3);\nConsole.WriteLine(orig.Count);"),
        ("Copia {10,20,30} con ToArray() e imprime su Length (3).", "var orig = new List<int> { 10, 20, 30 };\nint[] copia = orig.ToArray();\nConsole.WriteLine(copia.Length);"),
        ("Copia {1,2,3} con ToList(), modifica copia[0]=99 e imprime nums[0] original (1).", "int[] nums = { 1, 2, 3 };\nvar copia = nums.ToList();\ncopia[0] = 99;\nConsole.WriteLine(nums[0]);"),
        ("Duplica los valores de {2,3} en una nueva lista con Select e imprime unido por coma (4,6).", 'int[] nums = { 2, 3 };\nvar doble = nums.Select(n => n * 2).ToList();\nConsole.WriteLine(string.Join(",", doble));'),
        ("Copia solo los pares de {1,2,3,4} a una nueva lista e imprime el Count (2).", "int[] nums = { 1, 2, 3, 4 };\nvar pares = nums.Where(n => n % 2 == 0).ToList();\nConsole.WriteLine(pares.Count);"),
        ("Copia {7,8,9} y ordénala descendente en la copia; imprime el primero de la copia (9).", "int[] nums = { 7, 8, 9 };\nvar copia = nums.OrderByDescending(n => n).ToList();\nConsole.WriteLine(copia[0]);"),
        ("Concatena {1,2} y {3,4} con Concat e imprime el Count (4).", "int[] a = { 1, 2 };\nint[] b = { 3, 4 };\nConsole.WriteLine(a.Concat(b).Count());"),
        ("Copia {5,5,5} y usa Distinct() en la copia; imprime el Count (1).", "int[] nums = { 5, 5, 5 };\nConsole.WriteLine(nums.Distinct().Count());"),
    ]))

    # SC.C — Tuplas y LINQ
    sets.append(explicit([
        drill('Crea una tupla (nombre, edad) = ("Ana", 22) e imprime nombre y edad separados por espacio.',
              'var persona = ("Ana", 22);\nConsole.WriteLine($"{persona.Item1} {persona.Item2}");',
              hint="Accede a los elementos con Item1, Item2 o nombrándolos."),
        ('Crea (x, y) = (3, 4) e imprime la suma (7).', "var punto = (3, 4);\nConsole.WriteLine(punto.Item1 + punto.Item2);"),
        ('Crea tupla con nombres (int a, int b) = (5, 6) e imprime a*b (30).', "(int a, int b) = (5, 6);\nConsole.WriteLine(a * b);"),
        ('Crea ("Lima", "Peru") e imprime "Lima, Peru".', 'var t = ("Lima", "Peru");\nConsole.WriteLine($"{t.Item1}, {t.Item2}");'),
        ('Crea (int min, int max) = (1, 9) e imprime la diferencia (8).', "(int min, int max) = (1, 9);\nConsole.WriteLine(max - min);"),
        ('Crea una tupla (producto, precio) = ("Libro", 25) e imprime "Libro: 25".', 'var t = ("Libro", 25);\nConsole.WriteLine($"{t.Item1}: {t.Item2}");'),
        ('Crea (a, b, c) = (1, 2, 3) e imprime la suma (6).', "(int a, int b, int c) = (1, 2, 3);\nConsole.WriteLine(a + b + c);"),
        ('Crea (bool ok, int code) = (true, 200) e imprime code (200).', "(bool ok, int code) = (true, 200);\nConsole.WriteLine(code);"),
        ('Crea (string dia, int num) = ("lun", 1) e imprime "lun=1".', 'var t = ("lun", 1);\nConsole.WriteLine($"{t.Item1}={t.Item2}");'),
        ('Crea (int x, int y) = (10, 20), intercámbialos con (x,y)=(y,x) e imprime x (20).', "(int x, int y) = (10, 20);\n(x, y) = (y, x);\nConsole.WriteLine(x);"),
    ]))
    sets.append(explicit([
        drill("Desestructura (int a, int b) = (7, 3) e imprime a-b (4).",
              "(int a, int b) = (7, 3);\nConsole.WriteLine(a - b);",
              hint="Puedes asignar varias variables a la vez desde una tupla."),
        ("Con var (nombre, edad) = (\"Luis\", 30), imprime edad (30).", 'var (nombre, edad) = ("Luis", 30);\nConsole.WriteLine(edad);'),
        ("Intercambia a=1, b=2 con (a,b)=(b,a) e imprime a (2).", "int a = 1, b = 2;\n(a, b) = (b, a);\nConsole.WriteLine(a);"),
        ("Desestructura (10, 20, 30) en (x,y,z) e imprime z (30).", "var (x, y, z) = (10, 20, 30);\nConsole.WriteLine(z);"),
        ("Un método que retorne (int, int) MinMax de {3,1,4}; imprime el min.", "(int, int) MinMax(int[] a) => (a.Min(), a.Max());\nvar (mn, mx) = MinMax(new[] { 3, 1, 4 });\nConsole.WriteLine(mn);"),
        ("Desestructura (\"a\", \"b\") e imprime ambos unidos (ab).", 'var (p, q) = ("a", "b");\nConsole.WriteLine(p + q);'),
        ("Con (int suma, int prod) = (2+3, 2*3), imprime suma y prod (5 6).", '(int suma, int prod) = (2 + 3, 2 * 3);\nConsole.WriteLine($"{suma} {prod}");'),
        ("Desestructura una tupla dentro de un método que retorna (bool, string); imprime el string.", '(bool, string) Check() => (true, "ok");\nvar (ok, msg) = Check();\nConsole.WriteLine(msg);'),
        ("Con (a,b)=(5,5), imprime si son iguales (true).", "(int a, int b) = (5, 5);\nConsole.WriteLine(a == b);"),
        ("Desestructura (100, 200) y suma; imprime 300.", "var (a, b) = (100, 200);\nConsole.WriteLine(a + b);"),
    ]))
    sets.append(explicit([
        drill("Dado {1,2,3}, usa Select para duplicar e imprime unido por coma (2,4,6).",
              'int[] nums = { 1, 2, 3 };\nConsole.WriteLine(string.Join(",", nums.Select(n => n * 2)));',
              hint="Select(x => ...) transforma cada elemento."),
        ("Dado {1,2,3}, imprime cada uno al cuadrado unido por coma (1,4,9).", 'int[] nums = { 1, 2, 3 };\nConsole.WriteLine(string.Join(",", nums.Select(n => n * n)));'),
        ('Dado {"a","b"}, imprime cada uno en mayúscula unido por coma (A,B).', 'string[] xs = { "a", "b" };\nConsole.WriteLine(string.Join(",", xs.Select(x => x.ToUpper())));'),
        ("Dado {1,2,3}, imprime cada uno + 10 unido por coma.", 'int[] nums = { 1, 2, 3 };\nConsole.WriteLine(string.Join(",", nums.Select(n => n + 10)));'),
        ('Dado {"pera","kiwi"}, imprime la longitud de cada uno unido por coma (4,4).', 'string[] xs = { "pera", "kiwi" };\nConsole.WriteLine(string.Join(",", xs.Select(x => x.Length)));'),
        ("Dado {1,2,3,4}, imprime la suma de los cuadrados con Select+Sum (30).", "int[] nums = { 1, 2, 3, 4 };\nConsole.WriteLine(nums.Select(n => n * n).Sum());"),
        ("Dado {5,10,15}, imprime cada uno /5 unido por coma (1,2,3).", 'int[] nums = { 5, 10, 15 };\nConsole.WriteLine(string.Join(",", nums.Select(n => n / 5)));'),
        ('Dado {"x","y","z"}, imprime cada uno con "!" unido por coma.', 'string[] xs = { "x", "y", "z" };\nConsole.WriteLine(string.Join(",", xs.Select(x => x + "!")));'),
        ("Dado {1,2,3}, imprime cada uno como negativo unido por coma (-1,-2,-3).", 'int[] nums = { 1, 2, 3 };\nConsole.WriteLine(string.Join(",", nums.Select(n => -n)));'),
        ("Dado {2,4,6}, imprime la mitad de cada uno unido por coma (1,2,3).", 'int[] nums = { 2, 4, 6 };\nConsole.WriteLine(string.Join(",", nums.Select(n => n / 2)));'),
    ]))
    sets.append(explicit([
        drill("Dado {1,2,3,4,5}, usa Where para quedarte con los pares e imprime unido por coma (2,4).",
              'int[] nums = { 1, 2, 3, 4, 5 };\nConsole.WriteLine(string.Join(",", nums.Where(n => n % 2 == 0)));',
              hint="Where(x => condicion) filtra los que cumplen."),
        ("Dado {1,2,3,4,5}, imprime los mayores a 3 unido por coma (4,5).", 'int[] nums = { 1, 2, 3, 4, 5 };\nConsole.WriteLine(string.Join(",", nums.Where(n => n > 3)));'),
        ("Dado {-1,2,-3,4}, imprime los positivos unido por coma (2,4).", 'int[] nums = { -1, 2, -3, 4 };\nConsole.WriteLine(string.Join(",", nums.Where(n => n > 0)));'),
        ("Dado {1,2,3,4,5,6}, imprime cuántos son pares con Where+Count (3).", "int[] nums = { 1, 2, 3, 4, 5, 6 };\nConsole.WriteLine(nums.Where(n => n % 2 == 0).Count());"),
        ('Dado {"ana","bob","al"}, imprime los que tienen 3 letras unido por coma.', 'string[] xs = { "ana", "bob", "al" };\nConsole.WriteLine(string.Join(",", xs.Where(x => x.Length == 3)));'),
        ("Dado {3,6,9,12}, imprime los múltiplos de 6 unido por coma (6,12).", 'int[] nums = { 3, 6, 9, 12 };\nConsole.WriteLine(string.Join(",", nums.Where(n => n % 6 == 0)));'),
        ("Dado {5,10,15,20}, imprime la suma de los > 10 (35).", "int[] nums = { 5, 10, 15, 20 };\nConsole.WriteLine(nums.Where(n => n > 10).Sum());"),
        ("Dado {1,2,3,4}, imprime los impares unido por coma (1,3).", 'int[] nums = { 1, 2, 3, 4 };\nConsole.WriteLine(string.Join(",", nums.Where(n => n % 2 != 0)));'),
        ("Dado {2,4,6,8}, filtra > 4 y duplica (Where+Select) unido por coma (12,16).", 'int[] nums = { 2, 4, 6, 8 };\nConsole.WriteLine(string.Join(",", nums.Where(n => n > 4).Select(n => n * 2)));'),
        ('Dado {"hola","hi","hey"}, imprime cuántos empiezan con "h" y tienen >2 letras (2).', 'string[] xs = { "hola", "hi", "hey" };\nConsole.WriteLine(xs.Where(x => x.StartsWith("h") && x.Length > 2).Count());'),
    ]))
    sets.append(explicit([
        ("Dado {1,2,3}, imprime la suma de (cada uno *10) con Select+Sum (60).", "int[] nums = { 1, 2, 3 };\nConsole.WriteLine(nums.Select(n => n * 10).Sum());"),
        ('Dado {"a","bb","ccc"}, imprime la longitud total con Select+Sum (6).', 'string[] xs = { "a", "bb", "ccc" };\nConsole.WriteLine(xs.Select(x => x.Length).Sum());'),
        ("Dado {1,2,3,4}, imprime el máximo de los cuadrados (16).", "int[] nums = { 1, 2, 3, 4 };\nConsole.WriteLine(nums.Select(n => n * n).Max());"),
        ('Dado {"ana","luis"}, imprime cada uno capitalizado (primera mayúscula) unido por coma.', 'string[] xs = { "ana", "luis" };\nConsole.WriteLine(string.Join(",", xs.Select(x => char.ToUpper(x[0]) + x.Substring(1))));'),
        ("Dado {1,2,3,4,5}, imprime el promedio de los pares (3).", "int[] nums = { 1, 2, 3, 4, 5 };\nvar pares = nums.Where(n => n % 2 == 0);\nConsole.WriteLine(pares.Sum() / pares.Count());"),
        ("Dado {10,20,30}, imprime cada uno como \"$valor\" unido por coma.", 'int[] nums = { 10, 20, 30 };\nConsole.WriteLine(string.Join(",", nums.Select(n => "$" + n)));'),
        ("Dado {5,3,8,1}, imprime los 2 mayores ordenados desc unidos por coma (8,5).", 'int[] nums = { 5, 3, 8, 1 };\nConsole.WriteLine(string.Join(",", nums.OrderByDescending(n => n).Take(2)));'),
        ("Dado {1,2,3,4}, imprime la suma de los cuadrados de los pares (20).", "int[] nums = { 1, 2, 3, 4 };\nConsole.WriteLine(nums.Where(n => n % 2 == 0).Select(n => n * n).Sum());"),
        ('Dado {"perro","gato","pez"}, imprime los que tienen >3 letras en mayúscula unido por coma.', 'string[] xs = { "perro", "gato", "pez" };\nConsole.WriteLine(string.Join(",", xs.Where(x => x.Length > 3).Select(x => x.ToUpper())));'),
        ("Dado {2,4,6,8,10}, imprime cuántos hay tras filtrar > 5 y su suma (24).", "int[] nums = { 2, 4, 6, 8, 10 };\nConsole.WriteLine(nums.Where(n => n > 5).Sum());"),
    ]))

    # SC.D — Métodos de string
    sets.append(explicit([
        drill('Divide "a,b,c" por "," con Split e imprime cuántas partes hay (3).',
              'string s = "a,b,c";\nConsole.WriteLine(s.Split(",").Length);',
              hint="Split(sep) parte el texto; Join une partes."),
        ('Divide "uno dos tres" por espacio e imprime la primera palabra.', 'string s = "uno dos tres";\nConsole.WriteLine(s.Split(" ")[0]);'),
        ('Une {"a","b","c"} con "-" usando string.Join.', 'Console.WriteLine(string.Join("-", new[] { "a", "b", "c" }));'),
        ('Divide "1,2,3" por "," e imprime la suma de sus números (6).', 'string s = "1,2,3";\nConsole.WriteLine(s.Split(",").Select(int.Parse).Sum());'),
        ('Divide "hola mundo" e imprime la última palabra.', 'string s = "hola mundo";\nvar ps = s.Split(" ");\nConsole.WriteLine(ps[ps.Length - 1]);'),
        ('Une {"2024","09","05"} con "-" (formato fecha).', 'Console.WriteLine(string.Join("-", new[] { "2024", "09", "05" }));'),
        ('Divide "a-b-c-d" por "-" e imprime cuántas partes (4).', 'string s = "a-b-c-d";\nConsole.WriteLine(s.Split("-").Length);'),
        ('Cuenta las palabras de "el rapido zorro marron" con Split (4).', 'string s = "el rapido zorro marron";\nConsole.WriteLine(s.Split(" ").Length);'),
        ('Divide "x=5" por "=" e imprime el valor "5".', 'string s = "x=5";\nConsole.WriteLine(s.Split("=")[1]);'),
        ('Une los números {1,2,3} como texto con "," usando string.Join.', 'Console.WriteLine(string.Join(",", new[] { 1, 2, 3 }));'),
    ]))
    sets.append(explicit([
        drill('Dado "  hola  ", quita espacios con Trim e imprime la longitud (4).',
              'string s = "  hola  ";\nConsole.WriteLine(s.Trim().Length);',
              hint="Trim quita espacios en los extremos; Replace reemplaza texto."),
        ('Dado "aaa", reemplaza "a" por "b" e imprime (bbb).', 'string s = "aaa";\nConsole.WriteLine(s.Replace("a", "b"));'),
        ('Dado "hola mundo", quita los espacios con Replace e imprime (holamundo).', 'string s = "hola mundo";\nConsole.WriteLine(s.Replace(" ", ""));'),
        ('Dado "  dato", usa TrimStart e imprime el resultado.', 'string s = "  dato";\nConsole.WriteLine(s.TrimStart());'),
        ('Dado "1-2-3", reemplaza "-" por "/" e imprime (1/2/3).', 'string s = "1-2-3";\nConsole.WriteLine(s.Replace("-", "/"));'),
        ('Dado "banana", reemplaza "a" por "" e imprime (bnn).', 'string s = "banana";\nConsole.WriteLine(s.Replace("a", ""));'),
        ('Dado "hola\\n" (con salto), aplica Trim e imprime la longitud (4).', 'string s = "hola\\n";\nConsole.WriteLine(s.Trim().Length);'),
        ('Dado "  centro  ", aplica Trim e imprime entre corchetes [centro].', 'string s = "  centro  ";\nConsole.WriteLine("[" + s.Trim() + "]");'),
        ('Dado "gato gato", reemplaza "gato" por "perro" e imprime.', 'string s = "gato gato";\nConsole.WriteLine(s.Replace("gato", "perro"));'),
        ('Dado "a.b.c", cuenta los puntos reemplazando y comparando longitudes (2).', 'string s = "a.b.c";\nConsole.WriteLine(s.Length - s.Replace(".", "").Length);'),
    ]))
    sets.append(explicit([
        ('Dado "hola", imprímelo en MAYÚSCULAS.', 'string s = "hola";\nConsole.WriteLine(s.ToUpper());'),
        ('Dado "MUNDO", imprímelo en minúsculas.', 'string s = "MUNDO";\nConsole.WriteLine(s.ToLower());'),
        ('Dado "juan", capitaliza la primera letra e imprime "Juan".', 'string s = "juan";\nConsole.WriteLine(char.ToUpper(s[0]) + s.Substring(1));'),
        ('Dado "hOlA", imprímelo todo en minúsculas.', 'string s = "hOlA";\nConsole.WriteLine(s.ToLower());'),
        ('Dado "ana maria", capitaliza cada palabra e imprime "Ana Maria".', 'string s = "ana maria";\nConsole.WriteLine(string.Join(" ", s.Split(" ").Select(w => char.ToUpper(w[0]) + w.Substring(1))));'),
        ('Dado "Reporte", imprime si es igual a su versión capitalizada (true).', 'string s = "Reporte";\nConsole.WriteLine(s == char.ToUpper(s[0]) + s.Substring(1));'),
        ('Dado "abc", imprime en mayúsculas y su longitud "ABC 3".', 'string s = "abc";\nConsole.WriteLine($"{s.ToUpper()} {s.Length}");'),
        ('Dado "TITULO", pásalo a minúsculas y capitaliza: "Titulo".', 'string s = "TITULO";\ns = s.ToLower();\nConsole.WriteLine(char.ToUpper(s[0]) + s.Substring(1));'),
        ('Dado "hola mundo", imprime la inicial de cada palabra en mayúscula unida (HM).', 'string s = "hola mundo";\nConsole.WriteLine(string.Concat(s.Split(" ").Select(w => char.ToUpper(w[0]))));'),
        ('Dado "python", imprime la primera en mayúscula y el resto igual (Python).', 'string s = "python";\nConsole.WriteLine(char.ToUpper(s[0]) + s.Substring(1));'),
    ]))
    sets.append(explicit([
        drill('Dado "hello", imprime la posición de "l" con IndexOf (2).',
              'string s = "hello";\nConsole.WriteLine(s.IndexOf("l"));',
              hint="IndexOf devuelve -1 si no encuentra; Contains da true/false."),
        ('Dado "dotnet", imprime si contiene "net" (true).', 'string s = "dotnet";\nConsole.WriteLine(s.Contains("net"));'),
        ('Dado "archivo.pdf", imprime si empieza con "archivo".', 'string s = "archivo.pdf";\nConsole.WriteLine(s.StartsWith("archivo"));'),
        ('Dado "foto.png", imprime si termina en ".png".', 'string s = "foto.png";\nConsole.WriteLine(s.EndsWith(".png"));'),
        ('Dado "banana", cuenta las "a" con Count (3).', "string s = \"banana\";\nConsole.WriteLine(s.Count(c => c == 'a'));"),
        ('Dado "mundo", imprime la posición de "z" (no está, -1).', 'string s = "mundo";\nConsole.WriteLine(s.IndexOf("z"));'),
        ('Dado "abcabc", imprime la primera posición de "c" (2).', 'string s = "abcabc";\nConsole.WriteLine(s.IndexOf("c"));'),
        ('Dado "correo@mail.com", imprime si contiene "@" (true).', 'string s = "correo@mail.com";\nConsole.WriteLine(s.Contains("@"));'),
        ('Dado "https://x.com", imprime si empieza con "https" (true).', 'string s = "https://x.com";\nConsole.WriteLine(s.StartsWith("https"));'),
        ('Dado "mississippi", cuenta las "s" (4).', "string s = \"mississippi\";\nConsole.WriteLine(s.Count(c => c == 's'));"),
    ]))
    sets.append(explicit([
        ('Con nombre="Ana" y edad=22, imprime con interpolación "Ana (22)".', 'string nombre = "Ana";\nint edad = 22;\nConsole.WriteLine($"{nombre} ({edad})");'),
        ('Imprime 3.14159 con 2 decimales usando ToString("F2") (3.14).', 'Console.WriteLine((3.14159).ToString("F2"));'),
        ('Imprime el número 42 con 4 dígitos usando ToString("D4") (0042).', 'Console.WriteLine(42.ToString("D4"));'),
        ('Con precio=1000, imprime "Total: $1000" con interpolación.', 'int precio = 1000;\nConsole.WriteLine($"Total: ${precio}");'),
        ('Usa string.Format("{0} y {1}", "sal", "pimienta") e imprime.', 'Console.WriteLine(string.Format("{0} y {1}", "sal", "pimienta"));'),
        ('Con a=7, b=8, imprime "7 + 8 = 15" con interpolación.', 'int a = 7, b = 8;\nConsole.WriteLine($"{a} + {b} = {a + b}");'),
        ('Imprime 0.5 como porcentaje "50%" ((int)(0.5*100)).', 'double r = 0.5;\nConsole.WriteLine($"{(int)(r * 100)}%");'),
        ('Con dia=5, mes=9, imprime "05/09" con ToString("D2").', 'int dia = 5, mes = 9;\nConsole.WriteLine($"{dia.ToString(\"D2\")}/{mes.ToString(\"D2\")}");'),
        ('Imprime 1234.5 con 1 decimal "1234.5" usando ToString("F1").', 'Console.WriteLine((1234.5).ToString("F1"));'),
        ('Con nombre="Bob", imprime alineado a la derecha en 8 espacios usando PadLeft.', 'string nombre = "Bob";\nConsole.WriteLine(nombre.PadLeft(8));'),
    ]))

    return sets


# ---------------------------------------------------------------------------
# LEVEL SD — Diccionarios, sets y errores
# ---------------------------------------------------------------------------

def level_sd() -> list[list[dict]]:
    sets: list[list[dict]] = []

    # SD.A — Dictionary básico
    sets.append(explicit([
        drill('Crea un Dictionary<string,int> {"a":1,"b":2} e imprime d["b"] (2).',
              'var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };\nConsole.WriteLine(d["b"]);',
              hint="Se lee con d[llave]."),
        ('Crea {"edad":30} e imprime d["edad"].', 'var d = new Dictionary<string, int> { ["edad"] = 30 };\nConsole.WriteLine(d["edad"]);'),
        ('Crea {"x":5,"y":9} e imprime la suma d["x"]+d["y"] (14).', 'var d = new Dictionary<string, int> { ["x"] = 5, ["y"] = 9 };\nConsole.WriteLine(d["x"] + d["y"]);'),
        ('Crea un Dictionary<string,string> {"pais":"Peru"} e imprime d["pais"].', 'var d = new Dictionary<string, string> { ["pais"] = "Peru" };\nConsole.WriteLine(d["pais"]);'),
        ('Crea {"uno":1,"dos":2,"tres":3} e imprime d.Count (3).', 'var d = new Dictionary<string, int> { ["uno"] = 1, ["dos"] = 2, ["tres"] = 3 };\nConsole.WriteLine(d.Count);'),
        ('Crea {"a":10} e imprime la longitud de la llave de d["a"] no; imprime d["a"] (10).', 'var d = new Dictionary<string, int> { ["a"] = 10 };\nConsole.WriteLine(d["a"]);'),
        ('Crea {"pan":3,"leche":4} e imprime el precio de "leche".', 'var d = new Dictionary<string, int> { ["pan"] = 3, ["leche"] = 4 };\nConsole.WriteLine(d["leche"]);'),
        ('Crea {"a":1} y usa d.ContainsKey("a") para imprimir true.', 'var d = new Dictionary<string, int> { ["a"] = 1 };\nConsole.WriteLine(d.ContainsKey("a"));'),
        ('Crea {"gato":"miau","perro":"guau"} e imprime d["perro"].', 'var d = new Dictionary<string, string> { ["gato"] = "miau", ["perro"] = "guau" };\nConsole.WriteLine(d["perro"]);'),
        ('Crea {"n":7} e imprime d["n"]*2 (14).', 'var d = new Dictionary<string, int> { ["n"] = 7 };\nConsole.WriteLine(d["n"] * 2);'),
    ]))
    sets.append(explicit([
        drill('Crea un dict vacío, asigna d["a"]=1 y d["b"]=2, imprime d.Count (2).',
              'var d = new Dictionary<string, int>();\nd["a"] = 1;\nd["b"] = 2;\nConsole.WriteLine(d.Count);',
              hint="Asignar una llave nueva la agrega; asignar una existente la actualiza."),
        ('Crea {"a":1}, actualiza d["a"]=100 e imprímelo.', 'var d = new Dictionary<string, int> { ["a"] = 1 };\nd["a"] = 100;\nConsole.WriteLine(d["a"]);'),
        ('Crea {"x":5}, súmale 1 con d["x"]++ e imprímelo (6).', 'var d = new Dictionary<string, int> { ["x"] = 5 };\nd["x"]++;\nConsole.WriteLine(d["x"]);'),
        ('Crea dict vacío, agrega d["hola"]=1 e imprime d["hola"].', 'var d = new Dictionary<string, int>();\nd["hola"] = 1;\nConsole.WriteLine(d["hola"]);'),
        ('Crea {"a":1,"b":2}, agrega d["c"]=3 e imprime d.Count (3).', 'var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };\nd["c"] = 3;\nConsole.WriteLine(d.Count);'),
        ('Crea {"saldo":100}, réstale 30 e imprime el saldo (70).', 'var d = new Dictionary<string, int> { ["saldo"] = 100 };\nd["saldo"] -= 30;\nConsole.WriteLine(d["saldo"]);'),
        ('Crea {"a":1}, quita "a" con Remove e imprime d.Count (0).', 'var d = new Dictionary<string, int> { ["a"] = 1 };\nd.Remove("a");\nConsole.WriteLine(d.Count);'),
        ('Crea dict vacío, agrega 3 llaves e imprime d.Count.', 'var d = new Dictionary<string, int>();\nd["a"] = 1;\nd["b"] = 2;\nd["c"] = 3;\nConsole.WriteLine(d.Count);'),
        ('Crea {"cont":0}, incrementa 3 veces e imprime (3).', 'var d = new Dictionary<string, int> { ["cont"] = 0 };\nfor (int i = 0; i < 3; i++) d["cont"]++;\nConsole.WriteLine(d["cont"]);'),
        ('Crea {"a":5,"b":5}, duplica el valor de "a" e imprímelo (10).', 'var d = new Dictionary<string, int> { ["a"] = 5, ["b"] = 5 };\nd["a"] *= 2;\nConsole.WriteLine(d["a"]);'),
    ]))
    sets.append(explicit([
        drill('Con d={"a":1}, usa GetValueOrDefault("z") para imprimir 0 cuando no existe.',
              'var d = new Dictionary<string, int> { ["a"] = 1 };\nConsole.WriteLine(d.GetValueOrDefault("z"));',
              hint="GetValueOrDefault evita el error de llave inexistente."),
        ('Con d={"a":9}, usa GetValueOrDefault("a") e imprime 9.', 'var d = new Dictionary<string, int> { ["a"] = 9 };\nConsole.WriteLine(d.GetValueOrDefault("a"));'),
        ('Con d={"a":9}, usa GetValueOrDefault("z", -1) e imprime -1.', 'var d = new Dictionary<string, int> { ["a"] = 9 };\nConsole.WriteLine(d.GetValueOrDefault("z", -1));'),
        ('Con d={"k":7}, usa TryGetValue para imprimir el valor si existe.', 'var d = new Dictionary<string, int> { ["k"] = 7 };\nif (d.TryGetValue("k", out int v)) Console.WriteLine(v);'),
        ('Con d vacío, usa TryGetValue("x", out v) e imprime v (0) si falla.', 'var d = new Dictionary<string, int>();\nd.TryGetValue("x", out int v);\nConsole.WriteLine(v);'),
        ('Con d={"a":1,"b":2}, imprime GetValueOrDefault("b") (2).', 'var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };\nConsole.WriteLine(d.GetValueOrDefault("b"));'),
        ('Cuenta "a" en "aaa" usando GetValueOrDefault en el patrón de conteo (3).', "var d = new Dictionary<char, int>();\nforeach (char c in \"aaa\") d[c] = d.GetValueOrDefault(c) + 1;\nConsole.WriteLine(d['a']);"),
        ('Con d={"x":5}, imprime GetValueOrDefault("y", 99) (99).', 'var d = new Dictionary<string, int> { ["x"] = 5 };\nConsole.WriteLine(d.GetValueOrDefault("y", 99));'),
        ('Con d={"a":1}, comprueba y suma: GetValueOrDefault("a")+GetValueOrDefault("b") (1).', 'var d = new Dictionary<string, int> { ["a"] = 1 };\nConsole.WriteLine(d.GetValueOrDefault("a") + d.GetValueOrDefault("b"));'),
        ('Con d={"total":10}, usa TryGetValue e imprime el doble del valor (20).', 'var d = new Dictionary<string, int> { ["total"] = 10 };\nif (d.TryGetValue("total", out int v)) Console.WriteLine(v * 2);'),
    ]))
    sets.append(explicit([
        drill('Con d={"a":1,"b":2}, imprime cuántas llaves hay con d.Keys.Count (2).',
              'var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };\nConsole.WriteLine(d.Keys.Count);',
              hint="d.Keys son las llaves; d.Values los valores."),
        ('Con d={"a":10,"b":20}, imprime la suma de los valores con d.Values.Sum() (30).', 'var d = new Dictionary<string, int> { ["a"] = 10, ["b"] = 20 };\nConsole.WriteLine(d.Values.Sum());'),
        ('Con d={"x":1,"y":2,"z":3}, imprime el máximo de los valores (3).', 'var d = new Dictionary<string, int> { ["x"] = 1, ["y"] = 2, ["z"] = 3 };\nConsole.WriteLine(d.Values.Max());'),
        ('Con d={"a":1,"b":2}, imprime las llaves ordenadas unidas por coma (a,b).', 'var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };\nConsole.WriteLine(string.Join(",", d.Keys.OrderBy(k => k)));'),
        ('Con d={"pan":3,"leche":4}, imprime la suma de los precios (7).', 'var d = new Dictionary<string, int> { ["pan"] = 3, ["leche"] = 4 };\nConsole.WriteLine(d.Values.Sum());'),
        ('Con d={"a":5}, imprime si "a" está en d.Keys (true).', 'var d = new Dictionary<string, int> { ["a"] = 5 };\nConsole.WriteLine(d.Keys.Contains("a"));'),
        ('Con d={"a":1,"b":2,"c":3}, imprime cuántos valores son > 1 (2).', 'var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2, ["c"] = 3 };\nConsole.WriteLine(d.Values.Count(v => v > 1));'),
        ('Con d={"x":10,"y":20}, imprime el mínimo de los valores (10).', 'var d = new Dictionary<string, int> { ["x"] = 10, ["y"] = 20 };\nConsole.WriteLine(d.Values.Min());'),
        ('Con d={"a":1,"b":2}, imprime el promedio de los valores (1).', 'var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };\nConsole.WriteLine(d.Values.Sum() / d.Count);'),
        ('Con d={"uno":1,"dos":2}, imprime cuántas llaves tienen 3 letras (1).', 'var d = new Dictionary<string, int> { ["uno"] = 1, ["dos"] = 2 };\nConsole.WriteLine(d.Keys.Count(k => k.Length == 3));'),
    ]))
    sets.append(explicit([
        drill('Con d={"a":1,"b":2}, recorre con foreach y suma los valores; imprime 3.',
              'var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };\nint total = 0;\nforeach (var kv in d) total += kv.Value;\nConsole.WriteLine(total);',
              hint="foreach (var kv in d) te da kv.Key y kv.Value."),
        ('Con d={"a":1,"b":2}, imprime cada "llave=valor" ordenado por llave.', 'var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };\nforeach (var kv in d.OrderBy(k => k.Key))\n    Console.WriteLine($"{kv.Key}={kv.Value}");'),
        ('Con d={"x":10,"y":5}, imprime la llave con el mayor valor (x).', 'var d = new Dictionary<string, int> { ["x"] = 10, ["y"] = 5 };\nstring mejor = d.OrderByDescending(kv => kv.Value).First().Key;\nConsole.WriteLine(mejor);'),
        ('Con d={"a":2,"b":3}, imprime el producto de los valores (6).', 'var d = new Dictionary<string, int> { ["a"] = 2, ["b"] = 3 };\nint prod = 1;\nforeach (var kv in d) prod *= kv.Value;\nConsole.WriteLine(prod);'),
        ('Con d={"a":1,"b":2,"c":3}, cuenta cuántos valores son pares (1).', 'var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2, ["c"] = 3 };\nint c = 0;\nforeach (var kv in d) if (kv.Value % 2 == 0) c++;\nConsole.WriteLine(c);'),
        ('Con d={"lun":1,"mar":2}, imprime todas las llaves ordenadas unidas por coma.', 'var d = new Dictionary<string, int> { ["lun"] = 1, ["mar"] = 2 };\nConsole.WriteLine(string.Join(",", d.Keys.OrderBy(k => k)));'),
        ('Con d={"a":5,"b":10,"c":15}, imprime la suma solo de valores > 5 (25).', 'var d = new Dictionary<string, int> { ["a"] = 5, ["b"] = 10, ["c"] = 15 };\nint total = 0;\nforeach (var kv in d) if (kv.Value > 5) total += kv.Value;\nConsole.WriteLine(total);'),
        ('Con d={"a":1,"b":2}, imprime la llave del menor valor (a).', 'var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };\nConsole.WriteLine(d.OrderBy(kv => kv.Value).First().Key);'),
        ('Con d={"x":1,"y":2,"z":3}, imprime la concatenación de las llaves ordenadas (xyz).', 'var d = new Dictionary<string, int> { ["x"] = 1, ["y"] = 2, ["z"] = 3 };\nConsole.WriteLine(string.Concat(d.Keys.OrderBy(k => k)));'),
        ('Con d={"a":10,"b":20,"c":30}, imprime el promedio de los valores (20).', 'var d = new Dictionary<string, int> { ["a"] = 10, ["b"] = 20, ["c"] = 30 };\nConsole.WriteLine(d.Values.Sum() / d.Count);'),
    ]))

    # SD.B — Dictionary avanzado
    sets.append(explicit([
        drill('Cuenta la frecuencia de palabras en "a b a" y imprime cuántas veces aparece "a" (2).',
              'var freq = new Dictionary<string, int>();\nforeach (string w in "a b a".Split(" "))\n    freq[w] = freq.GetValueOrDefault(w) + 1;\nConsole.WriteLine(freq["a"]);',
              hint="El patrón de conteo: freq[x] = freq.GetValueOrDefault(x) + 1."),
        ('Cuenta letras en "banana" e imprime cuántas "n" (2).', "var freq = new Dictionary<char, int>();\nforeach (char c in \"banana\") freq[c] = freq.GetValueOrDefault(c) + 1;\nConsole.WriteLine(freq['n']);"),
        ('Cuenta números en {1,2,2,3,3,3} e imprime cuántas veces el 3 (3).', "var freq = new Dictionary<int, int>();\nforeach (int n in new[] { 1, 2, 2, 3, 3, 3 }) freq[n] = freq.GetValueOrDefault(n) + 1;\nConsole.WriteLine(freq[3]);"),
        ('En "el gato y el perro", imprime cuántas veces aparece "el" (2).', 'var freq = new Dictionary<string, int>();\nforeach (string w in "el gato y el perro".Split(" ")) freq[w] = freq.GetValueOrDefault(w) + 1;\nConsole.WriteLine(freq["el"]);'),
        ('Cuenta letras en "mississippi" e imprime la frecuencia de "s" (4).', "var freq = new Dictionary<char, int>();\nforeach (char c in \"mississippi\") freq[c] = freq.GetValueOrDefault(c) + 1;\nConsole.WriteLine(freq['s']);"),
        ('En "a a a b", imprime cuántas palabras distintas hay (2).', 'var freq = new Dictionary<string, int>();\nforeach (string w in "a a a b".Split(" ")) freq[w] = freq.GetValueOrDefault(w) + 1;\nConsole.WriteLine(freq.Count);'),
        ('Cuenta caracteres en "hello" e imprime la frecuencia de "l" (2).', "var freq = new Dictionary<char, int>();\nforeach (char c in \"hello\") freq[c] = freq.GetValueOrDefault(c) + 1;\nConsole.WriteLine(freq['l']);"),
        ('Cuenta números en {5,5,5,5} e imprime la frecuencia de 5 (4).', "var freq = new Dictionary<int, int>();\nforeach (int n in new[] { 5, 5, 5, 5 }) freq[n] = freq.GetValueOrDefault(n) + 1;\nConsole.WriteLine(freq[5]);"),
        ('En "uno dos uno tres uno", imprime la palabra más frecuente (uno).', 'var freq = new Dictionary<string, int>();\nforeach (string w in "uno dos uno tres uno".Split(" ")) freq[w] = freq.GetValueOrDefault(w) + 1;\nConsole.WriteLine(freq.OrderByDescending(kv => kv.Value).First().Key);'),
        ('Cuenta letras en "aabbbc" e imprime la frecuencia máxima (3).', "var freq = new Dictionary<char, int>();\nforeach (char c in \"aabbbc\") freq[c] = freq.GetValueOrDefault(c) + 1;\nConsole.WriteLine(freq.Values.Max());"),
    ]))
    sets.append(explicit([
        drill('Agrupa {1,2,3,4} en "par"/"impar" contando; imprime cuántos pares (2).',
              'var g = new Dictionary<string, int>();\nforeach (int n in new[] { 1, 2, 3, 4 })\n{\n    string k = n % 2 == 0 ? "par" : "impar";\n    g[k] = g.GetValueOrDefault(k) + 1;\n}\nConsole.WriteLine(g["par"]);',
              hint="Usa una llave calculada (categoría) para agrupar."),
        ('Agrupa palabras por longitud en {"a","bb","cc"}; imprime cuántas de longitud 2 (2).', 'var g = new Dictionary<int, int>();\nforeach (string w in new[] { "a", "bb", "cc" }) g[w.Length] = g.GetValueOrDefault(w.Length) + 1;\nConsole.WriteLine(g[2]);'),
        ('Agrupa {5,-3,2,-1} en "pos"/"neg"; imprime cuántos negativos (2).', 'var g = new Dictionary<string, int>();\nforeach (int n in new[] { 5, -3, 2, -1 })\n{\n    string k = n >= 0 ? "pos" : "neg";\n    g[k] = g.GetValueOrDefault(k) + 1;\n}\nConsole.WriteLine(g["neg"]);'),
        ('Agrupa letras por vocal/consonante en "hola"; imprime cuántas vocales (2).', 'var g = new Dictionary<string, int>();\nforeach (char c in "hola")\n{\n    string k = "aeiou".Contains(c) ? "vocal" : "cons";\n    g[k] = g.GetValueOrDefault(k) + 1;\n}\nConsole.WriteLine(g["vocal"]);'),
        ('Agrupa {10,20,5,30} en "grande"(>=20)/"chico"; imprime cuántos grandes (2).', 'var g = new Dictionary<string, int>();\nforeach (int n in new[] { 10, 20, 5, 30 })\n{\n    string k = n >= 20 ? "grande" : "chico";\n    g[k] = g.GetValueOrDefault(k) + 1;\n}\nConsole.WriteLine(g["grande"]);'),
        ('Agrupa por primera letra en {"ana","alba","bob"}; imprime cuántas empiezan con "a" (2).', "var g = new Dictionary<char, int>();\nforeach (string w in new[] { \"ana\", \"alba\", \"bob\" }) g[w[0]] = g.GetValueOrDefault(w[0]) + 1;\nConsole.WriteLine(g['a']);"),
        ('Agrupa {1,2,3,4,5,6} por resto entre 3; imprime cuántos con resto 0 (2).', 'var g = new Dictionary<int, int>();\nforeach (int n in new[] { 1, 2, 3, 4, 5, 6 }) g[n % 3] = g.GetValueOrDefault(n % 3) + 1;\nConsole.WriteLine(g[0]);'),
        ('Agrupa notas {95,82,75,60} por letra (A>=90,B>=80,...); imprime cuántas A (1).', 'var g = new Dictionary<string, int>();\nforeach (int s in new[] { 95, 82, 75, 60 })\n{\n    string k = s >= 90 ? "A" : s >= 80 ? "B" : "C";\n    g[k] = g.GetValueOrDefault(k) + 1;\n}\nConsole.WriteLine(g["A"]);'),
        ('Cuenta cuántas categorías distintas hay al agrupar {1,2,3,4} en par/impar (2).', 'var g = new Dictionary<string, int>();\nforeach (int n in new[] { 1, 2, 3, 4 })\n{\n    string k = n % 2 == 0 ? "par" : "impar";\n    g[k] = g.GetValueOrDefault(k) + 1;\n}\nConsole.WriteLine(g.Count);'),
        ('Agrupa {"rojo","azul","rojo"} y cuenta; imprime cuántos "rojo" (2).', 'var g = new Dictionary<string, int>();\nforeach (string c in new[] { "rojo", "azul", "rojo" }) g[c] = g.GetValueOrDefault(c) + 1;\nConsole.WriteLine(g["rojo"]);'),
    ]))
    sets.append(explicit([
        drill('Crea un dict anidado d["user"]=nuevo dict {"edad":30}; imprime d["user"]["edad"].',
              'var d = new Dictionary<string, Dictionary<string, int>>();\nd["user"] = new Dictionary<string, int> { ["edad"] = 30 };\nConsole.WriteLine(d["user"]["edad"]);',
              hint="El valor de un dict puede ser otro dict."),
        ('Con d anidado {"a":{"x":1}}, imprime d["a"]["x"] (1).', 'var d = new Dictionary<string, Dictionary<string, int>> { ["a"] = new() { ["x"] = 1 } };\nConsole.WriteLine(d["a"]["x"]);'),
        ('Con d anidado, suma d["a"]["x"] + d["a"]["y"] con {"x":2,"y":3} (5).', 'var d = new Dictionary<string, Dictionary<string, int>> { ["a"] = new() { ["x"] = 2, ["y"] = 3 } };\nConsole.WriteLine(d["a"]["x"] + d["a"]["y"]);'),
        ('Con d anidado {"p1":{"gol":2},"p2":{"gol":3}}, imprime los goles de p2 (3).', 'var d = new Dictionary<string, Dictionary<string, int>> { ["p1"] = new() { ["gol"] = 2 }, ["p2"] = new() { ["gol"] = 3 } };\nConsole.WriteLine(d["p2"]["gol"]);'),
        ('Con d anidado {"a":{"n":1}}, actualiza d["a"]["n"]=9 e imprímelo.', 'var d = new Dictionary<string, Dictionary<string, int>> { ["a"] = new() { ["n"] = 1 } };\nd["a"]["n"] = 9;\nConsole.WriteLine(d["a"]["n"]);'),
        ('Con d anidado, imprime cuántas llaves de nivel 1 hay ({"a":{},"b":{}}) (2).', 'var d = new Dictionary<string, Dictionary<string, int>> { ["a"] = new(), ["b"] = new() };\nConsole.WriteLine(d.Count);'),
        ('Con d anidado {"team":{"a":1,"b":2}}, imprime la suma de valores internos (3).', 'var d = new Dictionary<string, Dictionary<string, int>> { ["team"] = new() { ["a"] = 1, ["b"] = 2 } };\nConsole.WriteLine(d["team"].Values.Sum());'),
        ('Con d anidado, imprime cuántas llaves internas tiene d["a"] ({"x":1,"y":2}) (2).', 'var d = new Dictionary<string, Dictionary<string, int>> { ["a"] = new() { ["x"] = 1, ["y"] = 2 } };\nConsole.WriteLine(d["a"].Count);'),
        ('Con d anidado {"a":{"n":5}}, incrementa d["a"]["n"] e imprímelo (6).', 'var d = new Dictionary<string, Dictionary<string, int>> { ["a"] = new() { ["n"] = 5 } };\nd["a"]["n"]++;\nConsole.WriteLine(d["a"]["n"]);'),
        ('Con d anidado {"x":{"a":1},"y":{"a":2}}, imprime d["x"]["a"]+d["y"]["a"] (3).', 'var d = new Dictionary<string, Dictionary<string, int>> { ["x"] = new() { ["a"] = 1 }, ["y"] = new() { ["a"] = 2 } };\nConsole.WriteLine(d["x"]["a"] + d["y"]["a"]);'),
    ]))
    sets.append(explicit([
        drill('Invierte {"a":1,"b":2} para que el valor sea la llave; imprime inv[1] ("a").',
              'var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };\nvar inv = new Dictionary<int, string>();\nforeach (var kv in d) inv[kv.Value] = kv.Key;\nConsole.WriteLine(inv[1]);',
              hint="Recorre el dict y guarda valor -> llave en uno nuevo."),
        ('Invierte {"x":10} e imprime inv[10] ("x").', 'var d = new Dictionary<string, int> { ["x"] = 10 };\nvar inv = new Dictionary<int, string>();\nforeach (var kv in d) inv[kv.Value] = kv.Key;\nConsole.WriteLine(inv[10]);'),
        ('Invierte {"uno":1,"dos":2,"tres":3} e imprime inv[3] ("tres").', 'var d = new Dictionary<string, int> { ["uno"] = 1, ["dos"] = 2, ["tres"] = 3 };\nvar inv = new Dictionary<int, string>();\nforeach (var kv in d) inv[kv.Value] = kv.Key;\nConsole.WriteLine(inv[3]);'),
        ('Invierte {"a":1,"b":2} e imprime cuántas llaves tiene el invertido (2).', 'var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };\nvar inv = new Dictionary<int, string>();\nforeach (var kv in d) inv[kv.Value] = kv.Key;\nConsole.WriteLine(inv.Count);'),
        ('Invierte {"lun":1} e imprime inv[1].', 'var d = new Dictionary<string, int> { ["lun"] = 1 };\nvar inv = new Dictionary<int, string>();\nforeach (var kv in d) inv[kv.Value] = kv.Key;\nConsole.WriteLine(inv[1]);'),
        ('Invierte {"perro":4,"gato":3} e imprime inv[4] ("perro").', 'var d = new Dictionary<string, int> { ["perro"] = 4, ["gato"] = 3 };\nvar inv = new Dictionary<int, string>();\nforeach (var kv in d) inv[kv.Value] = kv.Key;\nConsole.WriteLine(inv[4]);'),
        ('Invierte {"A":90,"B":80} e imprime inv[80] ("B").', 'var d = new Dictionary<string, int> { ["A"] = 90, ["B"] = 80 };\nvar inv = new Dictionary<int, string>();\nforeach (var kv in d) inv[kv.Value] = kv.Key;\nConsole.WriteLine(inv[80]);'),
        ('Invierte {"a":1} y comprueba inv.ContainsKey(1) (true).', 'var d = new Dictionary<string, int> { ["a"] = 1 };\nvar inv = new Dictionary<int, string>();\nforeach (var kv in d) inv[kv.Value] = kv.Key;\nConsole.WriteLine(inv.ContainsKey(1));'),
        ('Invierte {"x":5,"y":6} e imprime la concatenación inv[5]+inv[6] (xy).', 'var d = new Dictionary<string, int> { ["x"] = 5, ["y"] = 6 };\nvar inv = new Dictionary<int, string>();\nforeach (var kv in d) inv[kv.Value] = kv.Key;\nConsole.WriteLine(inv[5] + inv[6]);'),
        ('Invierte {"a":1,"b":2,"c":3} e imprime inv[2] ("b").', 'var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2, ["c"] = 3 };\nvar inv = new Dictionary<int, string>();\nforeach (var kv in d) inv[kv.Value] = kv.Key;\nConsole.WriteLine(inv[2]);'),
    ]))
    sets.append(explicit([
        drill('Combina {"a":1} y {"b":2} en uno nuevo; imprime cuántas llaves tiene (2).',
              'var a = new Dictionary<string, int> { ["a"] = 1 };\nvar b = new Dictionary<string, int> { ["b"] = 2 };\nvar c = new Dictionary<string, int>(a);\nforeach (var kv in b) c[kv.Key] = kv.Value;\nConsole.WriteLine(c.Count);',
              hint="Copia el primero y luego agrega/actualiza con el segundo."),
        ('Combina {"a":1} y {"a":9} (el segundo gana); imprime c["a"] (9).', 'var a = new Dictionary<string, int> { ["a"] = 1 };\nvar b = new Dictionary<string, int> { ["a"] = 9 };\nvar c = new Dictionary<string, int>(a);\nforeach (var kv in b) c[kv.Key] = kv.Value;\nConsole.WriteLine(c["a"]);'),
        ('Combina {"x":1,"y":2} y {"z":3}; imprime la suma de valores (6).', 'var a = new Dictionary<string, int> { ["x"] = 1, ["y"] = 2 };\nvar b = new Dictionary<string, int> { ["z"] = 3 };\nvar c = new Dictionary<string, int>(a);\nforeach (var kv in b) c[kv.Key] = kv.Value;\nConsole.WriteLine(c.Values.Sum());'),
        ('Usa GetValueOrDefault para sumar el valor de "a" en dos dicts {"a":1} y {"a":2} (3).', 'var a = new Dictionary<string, int> { ["a"] = 1 };\nvar b = new Dictionary<string, int> { ["a"] = 2 };\nConsole.WriteLine(a.GetValueOrDefault("a") + b.GetValueOrDefault("a"));'),
        ('Combina {"a":1,"b":2} y {"b":20,"c":30}; imprime c["b"] (20).', 'var a = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };\nvar b = new Dictionary<string, int> { ["b"] = 20, ["c"] = 30 };\nvar c = new Dictionary<string, int>(a);\nforeach (var kv in b) c[kv.Key] = kv.Value;\nConsole.WriteLine(c["b"]);'),
        ('Suma dos inventarios {"pan":2} y {"pan":3} sumando valores; imprime pan (5).', 'var a = new Dictionary<string, int> { ["pan"] = 2 };\nvar b = new Dictionary<string, int> { ["pan"] = 3 };\nvar c = new Dictionary<string, int>(a);\nforeach (var kv in b) c[kv.Key] = c.GetValueOrDefault(kv.Key) + kv.Value;\nConsole.WriteLine(c["pan"]);'),
        ('Combina 3 dicts {"a":1},{"b":2},{"c":3}; imprime el Count (3).', 'var c = new Dictionary<string, int>();\nforeach (var d in new[] { new Dictionary<string, int> { ["a"] = 1 }, new() { ["b"] = 2 }, new() { ["c"] = 3 } })\n    foreach (var kv in d) c[kv.Key] = kv.Value;\nConsole.WriteLine(c.Count);'),
        ('Combina {"a":5} y {} (vacío); imprime c["a"] (5).', 'var a = new Dictionary<string, int> { ["a"] = 5 };\nvar b = new Dictionary<string, int>();\nvar c = new Dictionary<string, int>(a);\nforeach (var kv in b) c[kv.Key] = kv.Value;\nConsole.WriteLine(c["a"]);'),
        ('Con default: para llave nueva usa GetValueOrDefault y suma 10; imprime resultado (10).', 'var d = new Dictionary<string, int>();\nd["x"] = d.GetValueOrDefault("x") + 10;\nConsole.WriteLine(d["x"]);'),
        ('Combina {"a":1,"b":1} y {"a":1,"b":1} sumando; imprime la suma total (4).', 'var a = new Dictionary<string, int> { ["a"] = 1, ["b"] = 1 };\nvar b = new Dictionary<string, int> { ["a"] = 1, ["b"] = 1 };\nvar c = new Dictionary<string, int>(a);\nforeach (var kv in b) c[kv.Key] = c.GetValueOrDefault(kv.Key) + kv.Value;\nConsole.WriteLine(c.Values.Sum());'),
    ]))

    # SD.C — HashSet
    sets.append(explicit([
        drill('Crea un HashSet con {1,2,2,3}; imprime cuántos elementos únicos hay (3).',
              'var s = new HashSet<int> { 1, 2, 2, 3 };\nConsole.WriteLine(s.Count);',
              hint="Un HashSet descarta duplicados automáticamente."),
        ('Crea HashSet de {5,5,5}; imprime su Count (1).', 'var s = new HashSet<int> { 5, 5, 5 };\nConsole.WriteLine(s.Count);'),
        ('Cuenta caracteres únicos en "hola" con un HashSet (4).', 'var s = new HashSet<char>("hola");\nConsole.WriteLine(s.Count);'),
        ('Cuenta números únicos en {1,1,2,3,3,4} (4).', 'var s = new HashSet<int>(new[] { 1, 1, 2, 3, 3, 4 });\nConsole.WriteLine(s.Count);'),
        ('Crea HashSet {"a","b","a"}; imprime su Count (2).', 'var s = new HashSet<string> { "a", "b", "a" };\nConsole.WriteLine(s.Count);'),
        ('Cuenta letras únicas en "banana" (3).', 'var s = new HashSet<char>("banana");\nConsole.WriteLine(s.Count);'),
        ('Convierte {3,3,3,3} a HashSet e imprime el Count (1).', 'var s = new HashSet<int>(new[] { 3, 3, 3, 3 });\nConsole.WriteLine(s.Count);'),
        ('Cuenta caracteres únicos en "mississippi" (4).', 'var s = new HashSet<char>("mississippi");\nConsole.WriteLine(s.Count);'),
        ('Crea HashSet {10,20,30,10}; imprime su Count (3).', 'var s = new HashSet<int> { 10, 20, 30, 10 };\nConsole.WriteLine(s.Count);'),
        ('Cuenta palabras únicas en "a b a c b" con HashSet (3).', 'var s = new HashSet<string>("a b a c b".Split(" "));\nConsole.WriteLine(s.Count);'),
    ]))
    sets.append(explicit([
        drill('Crea un HashSet vacío, agrega 1 y 2 con Add; imprime si Add(1) devuelve false (ya existe).',
              'var s = new HashSet<int>();\ns.Add(1);\ns.Add(2);\nConsole.WriteLine(s.Add(1));',
              hint="Add devuelve false si el elemento ya estaba."),
        ('Crea HashSet {1,2,3}, quita el 2 con Remove; imprime el Count (2).', 'var s = new HashSet<int> { 1, 2, 3 };\ns.Remove(2);\nConsole.WriteLine(s.Count);'),
        ('Crea HashSet vacío, agrega 5 e imprime si Contains(5) (true).', 'var s = new HashSet<int>();\ns.Add(5);\nConsole.WriteLine(s.Contains(5));'),
        ('Crea HashSet {1,2}, agrega 3 e imprime el Count (3).', 'var s = new HashSet<int> { 1, 2 };\ns.Add(3);\nConsole.WriteLine(s.Count);'),
        ('Crea HashSet {"a","b"}, quita "a" e imprime si Contains("a") (false).', 'var s = new HashSet<string> { "a", "b" };\ns.Remove("a");\nConsole.WriteLine(s.Contains("a"));'),
        ('Crea HashSet {1,2,3}, intenta agregar 2 e imprime el resultado de Add (false).', 'var s = new HashSet<int> { 1, 2, 3 };\nConsole.WriteLine(s.Add(2));'),
        ('Crea HashSet vacío, agrega 1,2,3 en bucle e imprime el Count (3).', 'var s = new HashSet<int>();\nfor (int i = 1; i <= 3; i++) s.Add(i);\nConsole.WriteLine(s.Count);'),
        ('Crea HashSet {10}, quita 10 e imprime el Count (0).', 'var s = new HashSet<int> { 10 };\ns.Remove(10);\nConsole.WriteLine(s.Count);'),
        ('Agrega los pares de {1,2,3,4} a un HashSet e imprime el Count (2).', 'var s = new HashSet<int>();\nforeach (int n in new[] { 1, 2, 3, 4 }) if (n % 2 == 0) s.Add(n);\nConsole.WriteLine(s.Count);'),
        ('Crea HashSet {"x"}, agrega "x" de nuevo e imprime el Count (1).', 'var s = new HashSet<string> { "x" };\ns.Add("x");\nConsole.WriteLine(s.Count);'),
    ]))
    sets.append(explicit([
        drill('Une {1,2,3} y {3,4,5} con UnionWith; imprime cuántos elementos hay (5).',
              'var a = new HashSet<int> { 1, 2, 3 };\na.UnionWith(new[] { 3, 4, 5 });\nConsole.WriteLine(a.Count);',
              hint="UnionWith combina; IntersectWith deja solo los comunes."),
        ('Interseca {1,2,3} y {2,3,4} con IntersectWith; imprime el Count (2).', 'var a = new HashSet<int> { 1, 2, 3 };\na.IntersectWith(new[] { 2, 3, 4 });\nConsole.WriteLine(a.Count);'),
        ('Une {1,2} y {2} con Union (LINQ); imprime el Count (2).', 'var a = new[] { 1, 2 };\nConsole.WriteLine(a.Union(new[] { 2 }).Count());'),
        ('Interseca {1,2,3,4} y {2,4,6} con Intersect (LINQ); imprime el Count (2).', 'var a = new[] { 1, 2, 3, 4 };\nConsole.WriteLine(a.Intersect(new[] { 2, 4, 6 }).Count());'),
        ('Une {"a","b"} y {"b","c"}; imprime el Count (3).', 'var a = new HashSet<string> { "a", "b" };\na.UnionWith(new[] { "b", "c" });\nConsole.WriteLine(a.Count);'),
        ('Interseca {5,6,7} y {6,7,8}; imprime la suma de la intersección (13).', 'var a = new HashSet<int> { 5, 6, 7 };\na.IntersectWith(new[] { 6, 7, 8 });\nConsole.WriteLine(a.Sum());'),
        ('Une {1,2,3} y {} (vacío); imprime el Count (3).', 'var a = new HashSet<int> { 1, 2, 3 };\na.UnionWith(new int[] { });\nConsole.WriteLine(a.Count);'),
        ('Interseca {1,2} y {3,4} (sin comunes); imprime el Count (0).', 'var a = new HashSet<int> { 1, 2 };\na.IntersectWith(new[] { 3, 4 });\nConsole.WriteLine(a.Count);'),
        ('Une {1} y {1,2,3,4} e imprime el máximo (4).', 'var a = new HashSet<int> { 1 };\na.UnionWith(new[] { 1, 2, 3, 4 });\nConsole.WriteLine(a.Max());'),
        ('Interseca {"x","y","z"} y {"y","z"} e imprime el Count (2).', 'var a = new HashSet<string> { "x", "y", "z" };\na.IntersectWith(new[] { "y", "z" });\nConsole.WriteLine(a.Count);'),
    ]))
    sets.append(explicit([
        drill('Resta {1,2,3,4} menos {2,4} con ExceptWith; imprime cuántos quedan (2).',
              'var a = new HashSet<int> { 1, 2, 3, 4 };\na.ExceptWith(new[] { 2, 4 });\nConsole.WriteLine(a.Count);',
              hint="ExceptWith quita del conjunto los elementos dados."),
        ('Resta {5,6,7} menos {6} e imprime la suma restante (12).', 'var a = new HashSet<int> { 5, 6, 7 };\na.ExceptWith(new[] { 6 });\nConsole.WriteLine(a.Sum());'),
        ('Diferencia con LINQ: {1,2,3}.Except({2}); imprime el Count (2).', 'Console.WriteLine(new[] { 1, 2, 3 }.Except(new[] { 2 }).Count());'),
        ('Resta {"a","b","c"} menos {"a"} e imprime el Count (2).', 'var a = new HashSet<string> { "a", "b", "c" };\na.ExceptWith(new[] { "a" });\nConsole.WriteLine(a.Count);'),
        ('Resta {1,2,3} menos {1,2,3} e imprime el Count (0).', 'var a = new HashSet<int> { 1, 2, 3 };\na.ExceptWith(new[] { 1, 2, 3 });\nConsole.WriteLine(a.Count);'),
        ('Elementos en {1,2,3,4,5} que no están en {2,4}; imprime la suma (9).', 'var a = new HashSet<int> { 1, 2, 3, 4, 5 };\na.ExceptWith(new[] { 2, 4 });\nConsole.WriteLine(a.Sum());'),
        ('Diferencia {10,20,30} menos {20} e imprime el máximo restante (30).', 'var a = new HashSet<int> { 10, 20, 30 };\na.ExceptWith(new[] { 20 });\nConsole.WriteLine(a.Max());'),
        ('Con LINQ, {"x","y","z"}.Except({"y","z"}) e imprime el Count (1).', 'Console.WriteLine(new[] { "x", "y", "z" }.Except(new[] { "y", "z" }).Count());'),
        ('Resta {1,1,2,2,3} (como set) menos {3} e imprime el Count (2).', 'var a = new HashSet<int>(new[] { 1, 1, 2, 2, 3 });\na.ExceptWith(new[] { 3 });\nConsole.WriteLine(a.Count);'),
        ('Diferencia {4,5,6} menos {} e imprime el Count (3).', 'var a = new HashSet<int> { 4, 5, 6 };\na.ExceptWith(new int[] { });\nConsole.WriteLine(a.Count);'),
    ]))
    sets.append(explicit([
        drill('Elimina duplicados de {1,2,2,3,3,3} y imprime los únicos ordenados unidos por coma.',
              'var nums = new[] { 1, 2, 2, 3, 3, 3 };\nConsole.WriteLine(string.Join(",", new HashSet<int>(nums).OrderBy(n => n)));',
              hint="Convertir a HashSet quita duplicados; luego ordena."),
        ('Imprime si 3 está en {1,2,3} usando Contains (true).', 'var s = new HashSet<int> { 1, 2, 3 };\nConsole.WriteLine(s.Contains(3));'),
        ('Cuenta cuántos únicos hay en {5,5,6,7,7} (3).', 'Console.WriteLine(new HashSet<int>(new[] { 5, 5, 6, 7, 7 }).Count);'),
        ('Imprime si "banana" tiene la letra "z" con un HashSet (false).', 'var s = new HashSet<char>("banana");\nConsole.WriteLine(s.Contains(\'z\'));'),
        ('Quita duplicados de {"a","b","a","c"} e imprime el Count (3).', 'Console.WriteLine(new HashSet<string>(new[] { "a", "b", "a", "c" }).Count);'),
        ('Imprime los únicos de {3,1,2,3,1} ordenados unidos por coma (1,2,3).', 'Console.WriteLine(string.Join(",", new HashSet<int>(new[] { 3, 1, 2, 3, 1 }).OrderBy(n => n)));'),
        ('¿Hay duplicados en {1,2,3,1}? Compara Count del array vs HashSet; imprime true.', 'var nums = new[] { 1, 2, 3, 1 };\nConsole.WriteLine(nums.Length != new HashSet<int>(nums).Count);'),
        ('Imprime cuántas letras distintas tiene "programacion" (10).', 'Console.WriteLine(new HashSet<char>("programacion").Count);'),
        ('Comprueba si {1,2} es subconjunto de {1,2,3} con IsSubsetOf (true).', 'var a = new HashSet<int> { 1, 2 };\nConsole.WriteLine(a.IsSubsetOf(new[] { 1, 2, 3 }));'),
        ('Dedupe {10,10,20,30,30} e imprime la suma de únicos (60).', 'Console.WriteLine(new HashSet<int>(new[] { 10, 10, 20, 30, 30 }).Sum());'),
    ]))

    # SD.D — Manejo de errores
    sets.append(explicit([
        drill('Usa try/catch: divide 10/0 y en el catch imprime "error".',
              'try\n{\n    int cero = 0;\n    int x = 10 / cero;\n    Console.WriteLine(x);\n}\ncatch (DivideByZeroException)\n{\n    Console.WriteLine("error");\n}',
              hint="El código riesgoso va en try; el manejo en catch."),
        ('try/catch: convierte "abc" a int; en el catch imprime "invalido".', 'try\n{\n    int x = int.Parse("abc");\n    Console.WriteLine(x);\n}\ncatch (FormatException)\n{\n    Console.WriteLine("invalido");\n}'),
        ('try/catch: parsea "42" (válido) e imprime el número.', 'try\n{\n    int x = int.Parse("42");\n    Console.WriteLine(x);\n}\ncatch (FormatException)\n{\n    Console.WriteLine("invalido");\n}'),
        ('try/catch: accede a nums[5] en {1,2,3}; en el catch imprime "fuera de rango".', 'try\n{\n    int[] nums = { 1, 2, 3 };\n    Console.WriteLine(nums[5]);\n}\ncatch (IndexOutOfRangeException)\n{\n    Console.WriteLine("fuera de rango");\n}'),
        ('try/catch genérico (catch Exception): divide 5/0 e imprime "fallo".', 'try\n{\n    int cero = 0;\n    int x = 5 / cero;\n}\ncatch (Exception)\n{\n    Console.WriteLine("fallo");\n}'),
        ('try/catch: convierte "10" y súmale 5 (15).', 'try\n{\n    Console.WriteLine(int.Parse("10") + 5);\n}\ncatch (FormatException)\n{\n    Console.WriteLine("invalido");\n}'),
        ('try/catch: si "x" no es número imprime -1.', 'try\n{\n    Console.WriteLine(int.Parse("x"));\n}\ncatch (FormatException)\n{\n    Console.WriteLine(-1);\n}'),
        ('try/catch: divide 20/4 (5) sin error.', 'try\n{\n    Console.WriteLine(20 / 4);\n}\ncatch (DivideByZeroException)\n{\n    Console.WriteLine("error");\n}'),
        ('try/catch: parsea "3.5" como int (falla) e imprime "no es entero".', 'try\n{\n    Console.WriteLine(int.Parse("3.5"));\n}\ncatch (FormatException)\n{\n    Console.WriteLine("no es entero");\n}'),
        ('try/catch: accede a la primera letra de "" e imprime "vacio" si falla.', 'try\n{\n    string s = "";\n    Console.WriteLine(s[0]);\n}\ncatch (IndexOutOfRangeException)\n{\n    Console.WriteLine("vacio");\n}'),
    ]))
    sets.append(explicit([
        drill('Usa int.TryParse("123", out n): si funciona imprime n, si no "invalido".',
              'if (int.TryParse("123", out int n))\n    Console.WriteLine(n);\nelse\n    Console.WriteLine("invalido");',
              hint="TryParse no lanza excepción: devuelve true/false."),
        ('int.TryParse("abc", out n): imprime "invalido" si falla.', 'if (int.TryParse("abc", out int n))\n    Console.WriteLine(n);\nelse\n    Console.WriteLine("invalido");'),
        ('int.TryParse("50", out n) y súmale 10 si funciona (60).', 'if (int.TryParse("50", out int n))\n    Console.WriteLine(n + 10);'),
        ('double.TryParse("2.5", out d): imprime d si funciona.', 'if (double.TryParse("2.5", out double d))\n    Console.WriteLine(d);'),
        ('int.TryParse("", out n): imprime 0 (valor por defecto) si falla.', 'int.TryParse("", out int n);\nConsole.WriteLine(n);'),
        ('Suma "10"+"20" como enteros con TryParse e imprime 30 (o "error").', 'if (int.TryParse("10", out int a) && int.TryParse("20", out int b))\n    Console.WriteLine(a + b);\nelse\n    Console.WriteLine("error");'),
        ('int.TryParse("-5", out n): imprime el valor absoluto (5).', 'if (int.TryParse("-5", out int n))\n    Console.WriteLine(Math.Abs(n));'),
        ('int.TryParse("7x", out n): imprime "no" si falla.', 'if (int.TryParse("7x", out int n))\n    Console.WriteLine(n);\nelse\n    Console.WriteLine("no");'),
        ('Cuenta cuántos de {"1","a","3"} son números con TryParse (2).', 'int c = 0;\nforeach (string s in new[] { "1", "a", "3" }) if (int.TryParse(s, out _)) c++;\nConsole.WriteLine(c);'),
        ('int.TryParse("100", out n): imprime n/4 si funciona (25).', 'if (int.TryParse("100", out int n))\n    Console.WriteLine(n / 4);'),
    ]))
    sets.append(explicit([
        drill('Captura IndexOutOfRangeException al leer nums[10] de {1,2,3}; imprime "indice malo".',
              'int[] nums = { 1, 2, 3 };\ntry\n{\n    Console.WriteLine(nums[10]);\n}\ncatch (IndexOutOfRangeException)\n{\n    Console.WriteLine("indice malo");\n}',
              hint="Cada tipo de error tiene su clase de excepción."),
        ('Captura KeyNotFoundException al leer d["z"] de {"a":1}; imprime "sin llave".', 'var d = new Dictionary<string, int> { ["a"] = 1 };\ntry\n{\n    Console.WriteLine(d["z"]);\n}\ncatch (KeyNotFoundException)\n{\n    Console.WriteLine("sin llave");\n}'),
        ('Lee nums[2] de {1,2,3} (válido) e imprime 3.', 'int[] nums = { 1, 2, 3 };\ntry\n{\n    Console.WriteLine(nums[2]);\n}\ncatch (IndexOutOfRangeException)\n{\n    Console.WriteLine("indice malo");\n}'),
        ('Lee d["a"] de {"a":9} (válido) e imprime 9.', 'var d = new Dictionary<string, int> { ["a"] = 9 };\ntry\n{\n    Console.WriteLine(d["a"]);\n}\ncatch (KeyNotFoundException)\n{\n    Console.WriteLine("sin llave");\n}'),
        ('Evita el error con ContainsKey antes de leer d["z"]; imprime "no existe".', 'var d = new Dictionary<string, int> { ["a"] = 1 };\nif (d.ContainsKey("z"))\n    Console.WriteLine(d["z"]);\nelse\n    Console.WriteLine("no existe");'),
        ('Evita el error de índice comprobando Length antes de leer nums[5].', 'int[] nums = { 1, 2, 3 };\nif (5 < nums.Length)\n    Console.WriteLine(nums[5]);\nelse\n    Console.WriteLine("fuera");'),
        ('Captura el índice malo y luego imprime "seguido" fuera del try.', 'int[] nums = { 1 };\ntry\n{\n    Console.WriteLine(nums[3]);\n}\ncatch (IndexOutOfRangeException)\n{\n    Console.WriteLine("error");\n}\nConsole.WriteLine("seguido");'),
        ('Con d vacío, usa GetValueOrDefault para imprimir 0 sin excepción.', 'var d = new Dictionary<string, int>();\nConsole.WriteLine(d.GetValueOrDefault("x"));'),
        ('Lee el primer caracter de "hola" (válido) e imprime "h".', 'string s = "hola";\ntry\n{\n    Console.WriteLine(s[0]);\n}\ncatch (IndexOutOfRangeException)\n{\n    Console.WriteLine("vacio");\n}'),
        ('Captura cualquier excepción con catch (Exception e) e imprime "capturado".', 'try\n{\n    int[] a = { };\n    Console.WriteLine(a[0]);\n}\ncatch (Exception)\n{\n    Console.WriteLine("capturado");\n}'),
    ]))
    sets.append(explicit([
        drill('Usa try/finally: imprime "trabajo" en try y "listo" en finally.',
              'try\n{\n    Console.WriteLine("trabajo");\n}\nfinally\n{\n    Console.WriteLine("listo");\n}',
              hint="finally siempre se ejecuta, haya error o no."),
        ('try/catch/finally: divide 10/0, catch imprime "error", finally imprime "fin".', 'try\n{\n    int cero = 0;\n    int x = 10 / cero;\n}\ncatch (DivideByZeroException)\n{\n    Console.WriteLine("error");\n}\nfinally\n{\n    Console.WriteLine("fin");\n}'),
        ('try/finally con éxito: imprime 42 y luego "cerrado".', 'try\n{\n    Console.WriteLine(42);\n}\nfinally\n{\n    Console.WriteLine("cerrado");\n}'),
        ('finally se ejecuta tras un parse válido: imprime 5 y "done".', 'try\n{\n    Console.WriteLine(int.Parse("5"));\n}\nfinally\n{\n    Console.WriteLine("done");\n}'),
        ('catch + finally: parsea "x" (falla), catch "malo", finally "siempre".', 'try\n{\n    int.Parse("x");\n}\ncatch (FormatException)\n{\n    Console.WriteLine("malo");\n}\nfinally\n{\n    Console.WriteLine("siempre");\n}'),
        ('Cuenta pasos: imprime "1" en try y "2" en finally.', 'try\n{\n    Console.WriteLine(1);\n}\nfinally\n{\n    Console.WriteLine(2);\n}'),
        ('try/finally: dentro suma 2+3 e imprime; finally imprime "ok".', 'try\n{\n    Console.WriteLine(2 + 3);\n}\nfinally\n{\n    Console.WriteLine("ok");\n}'),
        ('finally tras index error: catch "idx", finally "limpio".', 'int[] a = { 1 };\ntry\n{\n    Console.WriteLine(a[9]);\n}\ncatch (IndexOutOfRangeException)\n{\n    Console.WriteLine("idx");\n}\nfinally\n{\n    Console.WriteLine("limpio");\n}'),
        ('try con return-like: imprime "a", luego finally "b".', 'try\n{\n    Console.WriteLine("a");\n}\nfinally\n{\n    Console.WriteLine("b");\n}'),
        ('finally imprime el total tras sumar 1..3 en try (6) y luego "end".', 'int total = 0;\ntry\n{\n    for (int i = 1; i <= 3; i++) total += i;\n    Console.WriteLine(total);\n}\nfinally\n{\n    Console.WriteLine("end");\n}'),
    ]))
    sets.append(explicit([
        drill('Guard clause: define Raiz(int n) que lance ArgumentException si n<0; captúralo con try/catch imprimiendo "negativo" para -4.',
              'int Raiz(int n)\n{\n    if (n < 0) throw new ArgumentException();\n    return (int)Math.Sqrt(n);\n}\ntry\n{\n    Console.WriteLine(Raiz(-4));\n}\ncatch (ArgumentException)\n{\n    Console.WriteLine("negativo");\n}',
              hint="throw lanza una excepción; una guard clause valida al inicio."),
        ('Raiz(16) válido imprime 4.', 'int Raiz(int n)\n{\n    if (n < 0) throw new ArgumentException();\n    return (int)Math.Sqrt(n);\n}\nConsole.WriteLine(Raiz(16));'),
        ('Divide(a,b) que lance si b==0; captura y imprime "cero" para (5,0).', 'int Divide(int a, int b)\n{\n    if (b == 0) throw new DivideByZeroException();\n    return a / b;\n}\ntry\n{\n    Console.WriteLine(Divide(5, 0));\n}\ncatch (DivideByZeroException)\n{\n    Console.WriteLine("cero");\n}'),
        ('Divide(10,2) válido imprime 5.', 'int Divide(int a, int b)\n{\n    if (b == 0) throw new DivideByZeroException();\n    return a / b;\n}\nConsole.WriteLine(Divide(10, 2));'),
        ('Edad(n) que lance si n<0; para 25 imprime 25.', 'int Edad(int n)\n{\n    if (n < 0) throw new ArgumentException();\n    return n;\n}\nConsole.WriteLine(Edad(25));'),
        ('Primero(int[] a) que lance si está vacío; para {} imprime "vacio".', 'int Primero(int[] a)\n{\n    if (a.Length == 0) throw new InvalidOperationException();\n    return a[0];\n}\ntry\n{\n    Console.WriteLine(Primero(new int[] { }));\n}\ncatch (InvalidOperationException)\n{\n    Console.WriteLine("vacio");\n}'),
        ('Primero({7,8}) imprime 7.', 'int Primero(int[] a)\n{\n    if (a.Length == 0) throw new InvalidOperationException();\n    return a[0];\n}\nConsole.WriteLine(Primero(new[] { 7, 8 }));'),
        ('Descuento(precio,pct) que lance si pct>100; captura "invalido" para (100,150).', 'int Descuento(int precio, int pct)\n{\n    if (pct > 100) throw new ArgumentException();\n    return precio - precio * pct / 100;\n}\ntry\n{\n    Console.WriteLine(Descuento(100, 150));\n}\ncatch (ArgumentException)\n{\n    Console.WriteLine("invalido");\n}'),
        ('Descuento(100,10) válido imprime 90.', 'int Descuento(int precio, int pct)\n{\n    if (pct > 100) throw new ArgumentException();\n    return precio - precio * pct / 100;\n}\nConsole.WriteLine(Descuento(100, 10));'),
        ('ParseaPositivo(s) que lance si el número es <=0; para "5" imprime 5.', 'int ParseaPositivo(string s)\n{\n    int n = int.Parse(s);\n    if (n <= 0) throw new ArgumentException();\n    return n;\n}\nConsole.WriteLine(ParseaPositivo("5"));'),
    ]))

    return sets


# ---------------------------------------------------------------------------
# LEVEL SE — Clases y POO
# ---------------------------------------------------------------------------

def level_se() -> list[list[dict]]:
    sets: list[list[dict]] = []

    # SE.A — Objetos y propiedades
    sets.append(explicit([
        drill('Define una clase Perro con propiedad Nombre; crea uno con Nombre="Fido" e imprime Nombre.',
              'class Perro { public string Nombre; }\nvar p = new Perro();\np.Nombre = "Fido";\nConsole.WriteLine(p.Nombre);',
              hint="Una propiedad guarda un dato del objeto."),
        ('Define Punto con campo X; crea uno con X=5 e imprime X.', 'class Punto { public int X; }\nvar p = new Punto();\np.X = 5;\nConsole.WriteLine(p.X);'),
        ('Define Libro con Titulo; crea uno con "C#" e imprime Titulo.', 'class Libro { public string Titulo; }\nvar l = new Libro();\nl.Titulo = "C#";\nConsole.WriteLine(l.Titulo);'),
        ('Define Caja con Ancho; crea una con 3 e imprime Ancho.', 'class Caja { public int Ancho; }\nvar c = new Caja();\nc.Ancho = 3;\nConsole.WriteLine(c.Ancho);'),
        ('Define Usuario con Edad; crea uno con 30 e imprime Edad.', 'class Usuario { public int Edad; }\nvar u = new Usuario();\nu.Edad = 30;\nConsole.WriteLine(u.Edad);'),
        ('Define Ciudad con Nombre; crea "Lima" e imprime Nombre.', 'class Ciudad { public string Nombre; }\nvar c = new Ciudad();\nc.Nombre = "Lima";\nConsole.WriteLine(c.Nombre);'),
        ('Define Producto con Precio; crea uno con 100 e imprime Precio.', 'class Producto { public int Precio; }\nvar p = new Producto();\np.Precio = 100;\nConsole.WriteLine(p.Precio);'),
        ('Define Gato con Nombre; crea "Michi", cámbialo a "Tom" e imprime Nombre.', 'class Gato { public string Nombre; }\nvar g = new Gato();\ng.Nombre = "Michi";\ng.Nombre = "Tom";\nConsole.WriteLine(g.Nombre);'),
        ('Define Circulo con Radio; crea uno con 7 e imprime Radio.', 'class Circulo { public int Radio; }\nvar c = new Circulo();\nc.Radio = 7;\nConsole.WriteLine(c.Radio);'),
        ('Define Nota con Valor; crea una con 95 e imprime Valor.', 'class Nota { public int Valor; }\nvar n = new Nota();\nn.Valor = 95;\nConsole.WriteLine(n.Valor);'),
    ]))
    sets.append(explicit([
        drill('Define Persona con constructor que reciba nombre; crea "Ana" e imprime Nombre.',
              'class Persona { public string Nombre; public Persona(string n) { Nombre = n; } }\nvar p = new Persona("Ana");\nConsole.WriteLine(p.Nombre);',
              hint="El constructor inicializa el objeto al crearlo."),
        ('Define Punto con constructor(x); crea con 8 e imprime X.', 'class Punto { public int X; public Punto(int x) { X = x; } }\nvar p = new Punto(8);\nConsole.WriteLine(p.X);'),
        ('Define Contador con constructor(inicio); crea con 5 e imprime Valor.', 'class Contador { public int Valor; public Contador(int inicio) { Valor = inicio; } }\nvar c = new Contador(5);\nConsole.WriteLine(c.Valor);'),
        ('Define Libro(titulo); crea "C#" e imprime Titulo.', 'class Libro { public string Titulo; public Libro(string t) { Titulo = t; } }\nvar l = new Libro("C#");\nConsole.WriteLine(l.Titulo);'),
        ('Define Caja(ancho); crea con 4 e imprime Ancho.', 'class Caja { public int Ancho; public Caja(int a) { Ancho = a; } }\nvar c = new Caja(4);\nConsole.WriteLine(c.Ancho);'),
        ('Define Cuenta(saldo); crea con 100 e imprime Saldo.', 'class Cuenta { public int Saldo; public Cuenta(int s) { Saldo = s; } }\nvar c = new Cuenta(100);\nConsole.WriteLine(c.Saldo);'),
        ('Define Ciudad(nombre); crea "Cusco" e imprime Nombre.', 'class Ciudad { public string Nombre; public Ciudad(string n) { Nombre = n; } }\nvar c = new Ciudad("Cusco");\nConsole.WriteLine(c.Nombre);'),
        ('Define Temperatura(grados); crea con 25 e imprime Grados.', 'class Temperatura { public int Grados; public Temperatura(int g) { Grados = g; } }\nvar t = new Temperatura(25);\nConsole.WriteLine(t.Grados);'),
        ('Define Animal(sonido); crea "miau" e imprime Sonido.', 'class Animal { public string Sonido; public Animal(string s) { Sonido = s; } }\nvar a = new Animal("miau");\nConsole.WriteLine(a.Sonido);'),
        ('Define Reloj(hora); crea con 12 e imprime Hora.', 'class Reloj { public int Hora; public Reloj(int h) { Hora = h; } }\nvar r = new Reloj(12);\nConsole.WriteLine(r.Hora);'),
    ]))
    sets.append(explicit([
        drill('Define Persona con constructor(nombre, edad); crea ("Ana",22) e imprime "Ana 22".',
              'class Persona { public string Nombre; public int Edad; public Persona(string n, int e) { Nombre = n; Edad = e; } }\nvar p = new Persona("Ana", 22);\nConsole.WriteLine($"{p.Nombre} {p.Edad}");',
              hint="Un constructor puede recibir varios argumentos."),
        ('Define Punto(x,y); crea (3,4) e imprime la suma X+Y (7).', 'class Punto { public int X; public int Y; public Punto(int x, int y) { X = x; Y = y; } }\nvar p = new Punto(3, 4);\nConsole.WriteLine(p.X + p.Y);'),
        ('Define Rectangulo(ancho,alto); crea (5,4) e imprime el área (20).', 'class Rectangulo { public int Ancho; public int Alto; public Rectangulo(int a, int b) { Ancho = a; Alto = b; } }\nvar r = new Rectangulo(5, 4);\nConsole.WriteLine(r.Ancho * r.Alto);'),
        ('Define Producto(nombre,precio); crea ("Pan",3) e imprime "Pan: 3".', 'class Producto { public string Nombre; public int Precio; public Producto(string n, int p) { Nombre = n; Precio = p; } }\nvar prod = new Producto("Pan", 3);\nConsole.WriteLine($"{prod.Nombre}: {prod.Precio}");'),
        ('Define Fecha(dia,mes); crea (5,9) e imprime "5/9".', 'class Fecha { public int Dia; public int Mes; public Fecha(int d, int m) { Dia = d; Mes = m; } }\nvar f = new Fecha(5, 9);\nConsole.WriteLine($"{f.Dia}/{f.Mes}");'),
        ('Define Rango(min,max); crea (1,10) e imprime la diferencia (9).', 'class Rango { public int Min; public int Max; public Rango(int a, int b) { Min = a; Max = b; } }\nvar r = new Rango(1, 10);\nConsole.WriteLine(r.Max - r.Min);'),
        ('Define Coord(lat,lon); crea (10,20) e imprime lat (10).', 'class Coord { public int Lat; public int Lon; public Coord(int a, int b) { Lat = a; Lon = b; } }\nvar c = new Coord(10, 20);\nConsole.WriteLine(c.Lat);'),
        ('Define Nota(materia,valor); crea ("Mate",95) e imprime "Mate=95".', 'class Nota { public string Materia; public int Valor; public Nota(string m, int v) { Materia = m; Valor = v; } }\nvar n = new Nota("Mate", 95);\nConsole.WriteLine($"{n.Materia}={n.Valor}");'),
        ('Define Par(a,b); crea (6,7) e imprime el producto (42).', 'class Par { public int A; public int B; public Par(int a, int b) { A = a; B = b; } }\nvar p = new Par(6, 7);\nConsole.WriteLine(p.A * p.B);'),
        ('Define Usuario(nombre,activo); crea ("bob",true) e imprime Activo.', 'class Usuario { public string Nombre; public bool Activo; public Usuario(string n, bool a) { Nombre = n; Activo = a; } }\nvar u = new Usuario("bob", true);\nConsole.WriteLine(u.Activo);'),
    ]))
    sets.append(explicit([
        drill('Crea dos objetos Punto(1,2) y Punto(3,4); imprime la suma de sus X (4).',
              'class Punto { public int X; public int Y; public Punto(int x, int y) { X = x; Y = y; } }\nvar a = new Punto(1, 2);\nvar b = new Punto(3, 4);\nConsole.WriteLine(a.X + b.X);',
              hint="Cada objeto tiene sus propios valores."),
        ('Crea Persona("Ana",20) y Persona("Luis",30); imprime la suma de edades (50).', 'class Persona { public string Nombre; public int Edad; public Persona(string n, int e) { Nombre = n; Edad = e; } }\nvar a = new Persona("Ana", 20);\nvar b = new Persona("Luis", 30);\nConsole.WriteLine(a.Edad + b.Edad);'),
        ('Crea dos Cuenta(100) y Cuenta(50); imprime el saldo total (150).', 'class Cuenta { public int Saldo; public Cuenta(int s) { Saldo = s; } }\nvar a = new Cuenta(100);\nvar b = new Cuenta(50);\nConsole.WriteLine(a.Saldo + b.Saldo);'),
        ('Crea Producto("A",10) y Producto("B",20); imprime el más caro (20).', 'class Producto { public string Nombre; public int Precio; public Producto(string n, int p) { Nombre = n; Precio = p; } }\nvar a = new Producto("A", 10);\nvar b = new Producto("B", 20);\nConsole.WriteLine(Math.Max(a.Precio, b.Precio));'),
        ('Crea dos Rectangulo(2,3) y (4,5); imprime la suma de áreas (26).', 'class Rectangulo { public int Ancho; public int Alto; public Rectangulo(int a, int b) { Ancho = a; Alto = b; } }\nvar a = new Rectangulo(2, 3);\nvar b = new Rectangulo(4, 5);\nConsole.WriteLine(a.Ancho * a.Alto + b.Ancho * b.Alto);'),
        ('Crea Persona("Ana",25) y otra "Bea",25; imprime si tienen la misma edad (true).', 'class Persona { public int Edad; public Persona(int e) { Edad = e; } }\nvar a = new Persona(25);\nvar b = new Persona(25);\nConsole.WriteLine(a.Edad == b.Edad);'),
        ('Crea 3 Nota(80),(90),(100) en un array; imprime el promedio (90).', 'class Nota { public int Valor; public Nota(int v) { Valor = v; } }\nvar notas = new[] { new Nota(80), new Nota(90), new Nota(100) };\nConsole.WriteLine(notas.Select(n => n.Valor).Sum() / notas.Length);'),
        ('Crea Punto(0,0) y Punto(3,0); imprime la distancia en X (3).', 'class Punto { public int X; public Punto(int x) { X = x; } }\nvar a = new Punto(0);\nvar b = new Punto(3);\nConsole.WriteLine(b.X - a.X);'),
        ('Crea dos Usuario con Activo true/false; imprime cuántos activos hay (1).', 'class Usuario { public bool Activo; public Usuario(bool a) { Activo = a; } }\nvar us = new[] { new Usuario(true), new Usuario(false) };\nConsole.WriteLine(us.Count(u => u.Activo));'),
        ('Crea Caja(5) y Caja(10); imprime la mayor Ancho (10).', 'class Caja { public int Ancho; public Caja(int a) { Ancho = a; } }\nvar a = new Caja(5);\nvar b = new Caja(10);\nConsole.WriteLine(Math.Max(a.Ancho, b.Ancho));'),
    ]))
    sets.append(explicit([
        drill('Define Persona(nombre,edad) e imprime con interpolación "Ana (22)".',
              'class Persona { public string Nombre; public int Edad; public Persona(string n, int e) { Nombre = n; Edad = e; } }\nvar p = new Persona("Ana", 22);\nConsole.WriteLine($"{p.Nombre} ({p.Edad})");',
              hint="Puedes usar las propiedades dentro de una interpolación."),
        ('Define Producto(nombre,precio) e imprime "Pan cuesta 3".', 'class Producto { public string Nombre; public int Precio; public Producto(string n, int p) { Nombre = n; Precio = p; } }\nvar prod = new Producto("Pan", 3);\nConsole.WriteLine($"{prod.Nombre} cuesta {prod.Precio}");'),
        ('Define Punto(x,y) e imprime "(3, 4)".', 'class Punto { public int X; public int Y; public Punto(int x, int y) { X = x; Y = y; } }\nvar p = new Punto(3, 4);\nConsole.WriteLine($"({p.X}, {p.Y})");'),
        ('Define Libro(titulo,paginas) e imprime "C# - 200 pags".', 'class Libro { public string Titulo; public int Paginas; public Libro(string t, int p) { Titulo = t; Paginas = p; } }\nvar l = new Libro("C#", 200);\nConsole.WriteLine($"{l.Titulo} - {l.Paginas} pags");'),
        ('Define Cuenta(titular,saldo) e imprime "Ana: $100".', 'class Cuenta { public string Titular; public int Saldo; public Cuenta(string t, int s) { Titular = t; Saldo = s; } }\nvar c = new Cuenta("Ana", 100);\nConsole.WriteLine($"{c.Titular}: ${c.Saldo}");'),
        ('Define Rectangulo(a,b) e imprime "Area: 20".', 'class Rectangulo { public int A; public int B; public Rectangulo(int a, int b) { A = a; B = b; } }\nvar r = new Rectangulo(5, 4);\nConsole.WriteLine($"Area: {r.A * r.B}");'),
        ('Define Estudiante(nombre,nota) e imprime "Bob: aprobado" si nota>=60.', 'class Estudiante { public string Nombre; public int Nota; public Estudiante(string n, int x) { Nombre = n; Nota = x; } }\nvar e = new Estudiante("Bob", 75);\nConsole.WriteLine($"{e.Nombre}: {(e.Nota >= 60 ? "aprobado" : "reprobado")}");'),
        ('Define Ciudad(nombre,pais) e imprime "Lima, Peru".', 'class Ciudad { public string Nombre; public string Pais; public Ciudad(string n, string p) { Nombre = n; Pais = p; } }\nvar c = new Ciudad("Lima", "Peru");\nConsole.WriteLine($"{c.Nombre}, {c.Pais}");'),
        ('Define Pelicula(titulo,anio) e imprime "Matrix (1999)".', 'class Pelicula { public string Titulo; public int Anio; public Pelicula(string t, int a) { Titulo = t; Anio = a; } }\nvar p = new Pelicula("Matrix", 1999);\nConsole.WriteLine($"{p.Titulo} ({p.Anio})");'),
        ('Define Temperatura(ciudad,grados) e imprime "Lima: 25C".', 'class Temperatura { public string Ciudad; public int Grados; public Temperatura(string c, int g) { Ciudad = c; Grados = g; } }\nvar t = new Temperatura("Lima", 25);\nConsole.WriteLine($"{t.Ciudad}: {t.Grados}C");'),
    ]))

    # SE.B — Métodos
    sets.append(explicit([
        drill('Define Circulo(radio) con método Area() = radio*radio*3 (aprox); crea radio=2 e imprime Area() (12).',
              'class Circulo { public int Radio; public Circulo(int r) { Radio = r; } public int Area() => Radio * Radio * 3; }\nvar c = new Circulo(2);\nConsole.WriteLine(c.Area());',
              hint="Un método de instancia usa las propiedades del objeto."),
        ('Define Cuadrado(lado) con Area()=lado*lado; crea lado=5 e imprime Area() (25).', 'class Cuadrado { public int Lado; public Cuadrado(int l) { Lado = l; } public int Area() => Lado * Lado; }\nvar c = new Cuadrado(5);\nConsole.WriteLine(c.Area());'),
        ('Define Rectangulo(a,b) con Area(); crea (3,4) e imprime 12.', 'class Rectangulo { public int A; public int B; public Rectangulo(int a, int b) { A = a; B = b; } public int Area() => A * B; }\nvar r = new Rectangulo(3, 4);\nConsole.WriteLine(r.Area());'),
        ('Define Persona(edad) con EsMayor() (>=18); crea edad=20 e imprime true.', 'class Persona { public int Edad; public Persona(int e) { Edad = e; } public bool EsMayor() => Edad >= 18; }\nvar p = new Persona(20);\nConsole.WriteLine(p.EsMayor());'),
        ('Define Cuenta(saldo) con TieneFondos() (>0); crea saldo=0 e imprime false.', 'class Cuenta { public int Saldo; public Cuenta(int s) { Saldo = s; } public bool TieneFondos() => Saldo > 0; }\nvar c = new Cuenta(0);\nConsole.WriteLine(c.TieneFondos());'),
        ('Define Numero(valor) con Doble(); crea 7 e imprime 14.', 'class Numero { public int Valor; public Numero(int v) { Valor = v; } public int Doble() => Valor * 2; }\nvar n = new Numero(7);\nConsole.WriteLine(n.Doble());'),
        ('Define Texto(contenido) con Longitud(); crea "hola" e imprime 4.', 'class Texto { public string Contenido; public Texto(string c) { Contenido = c; } public int Longitud() => Contenido.Length; }\nvar t = new Texto("hola");\nConsole.WriteLine(t.Longitud());'),
        ('Define Triangulo(base,altura) con Area()=base*altura/2; crea (6,4) e imprime 12.', 'class Triangulo { public int Base; public int Altura; public Triangulo(int b, int h) { Base = b; Altura = h; } public int Area() => Base * Altura / 2; }\nvar t = new Triangulo(6, 4);\nConsole.WriteLine(t.Area());'),
        ('Define Nota(valor) con Letra() (A>=90,B>=80,F); crea 85 e imprime "B".', 'class Nota { public int Valor; public Nota(int v) { Valor = v; } public string Letra() => Valor >= 90 ? "A" : Valor >= 80 ? "B" : "F"; }\nvar n = new Nota(85);\nConsole.WriteLine(n.Letra());'),
        ('Define Producto(precio) con ConIva()=precio+precio*18/100; crea 100 e imprime 118.', 'class Producto { public int Precio; public Producto(int p) { Precio = p; } public int ConIva() => Precio + Precio * 18 / 100; }\nvar p = new Producto(100);\nConsole.WriteLine(p.ConIva());'),
    ]))
    sets.append(explicit([
        drill('Define Contador con Valor=0 y método Inc() que suma 1 a this.Valor; incrementa una vez e imprime Valor (1).',
              'class Contador { public int Valor = 0; public void Inc() { Valor++; } }\nvar c = new Contador();\nc.Inc();\nConsole.WriteLine(c.Valor);',
              hint="Un método puede modificar las propiedades del propio objeto."),
        ('Define Contador con Inc(); incrementa 3 veces e imprime Valor (3).', 'class Contador { public int Valor = 0; public void Inc() { Valor++; } }\nvar c = new Contador();\nc.Inc();\nc.Inc();\nc.Inc();\nConsole.WriteLine(c.Valor);'),
        ('Define Cuenta(saldo) con Deposita(n); crea 100, deposita 50 e imprime 150.', 'class Cuenta { public int Saldo; public Cuenta(int s) { Saldo = s; } public void Deposita(int n) { Saldo += n; } }\nvar c = new Cuenta(100);\nc.Deposita(50);\nConsole.WriteLine(c.Saldo);'),
        ('Define Luz con Encendida=false y Toggle(); llama Toggle una vez e imprime Encendida (true).', 'class Luz { public bool Encendida = false; public void Toggle() { Encendida = !Encendida; } }\nvar l = new Luz();\nl.Toggle();\nConsole.WriteLine(l.Encendida);'),
        ('Define Pila con lista interna y Push(x); agrega 5 e imprime el Count (1).', 'class Pila { public List<int> Data = new(); public void Push(int x) { Data.Add(x); } }\nvar p = new Pila();\np.Push(5);\nConsole.WriteLine(p.Data.Count);'),
        ('Define Cuenta con Retira(n); crea 100, retira 40 e imprime 60.', 'class Cuenta { public int Saldo = 100; public void Retira(int n) { Saldo -= n; } }\nvar c = new Cuenta();\nc.Retira(40);\nConsole.WriteLine(c.Saldo);'),
        ('Define Contador con Reset(); incrementa y luego Reset, imprime 0.', 'class Contador { public int Valor = 5; public void Reset() { Valor = 0; } }\nvar c = new Contador();\nc.Reset();\nConsole.WriteLine(c.Valor);'),
        ('Define Termostato con Grados=20 y Sube(); llama 2 veces e imprime 22.', 'class Termostato { public int Grados = 20; public void Sube() { Grados++; } }\nvar t = new Termostato();\nt.Sube();\nt.Sube();\nConsole.WriteLine(t.Grados);'),
        ('Define Carrito con Total=0 y Agrega(precio); agrega 10 y 20 e imprime 30.', 'class Carrito { public int Total = 0; public void Agrega(int p) { Total += p; } }\nvar c = new Carrito();\nc.Agrega(10);\nc.Agrega(20);\nConsole.WriteLine(c.Total);'),
        ('Define Contador con Suma(n); crea, suma 5 y suma 3 e imprime 8.', 'class Contador { public int Valor = 0; public void Suma(int n) { Valor += n; } }\nvar c = new Contador();\nc.Suma(5);\nc.Suma(3);\nConsole.WriteLine(c.Valor);'),
    ]))
    sets.append(explicit([
        drill('Define Calculadora con Suma(a,b); imprime Suma(3,4) (7).',
              'class Calculadora { public int Suma(int a, int b) => a + b; }\nvar c = new Calculadora();\nConsole.WriteLine(c.Suma(3, 4));',
              hint="Un método puede recibir parámetros además de usar this."),
        ('Define Saludador con Saluda(nombre); imprime Saluda("Ana") = "Hola Ana".', 'class Saludador { public string Saluda(string n) => $"Hola {n}"; }\nvar s = new Saludador();\nConsole.WriteLine(s.Saluda("Ana"));'),
        ('Define Cuenta(saldo) con PuedePagar(monto); crea 100 e imprime PuedePagar(50) (true).', 'class Cuenta { public int Saldo; public Cuenta(int s) { Saldo = s; } public bool PuedePagar(int m) => Saldo >= m; }\nvar c = new Cuenta(100);\nConsole.WriteLine(c.PuedePagar(50));'),
        ('Define Multiplicador(factor) con Aplica(n); crea factor=3 e imprime Aplica(5) (15).', 'class Multiplicador { public int Factor; public Multiplicador(int f) { Factor = f; } public int Aplica(int n) => n * Factor; }\nvar m = new Multiplicador(3);\nConsole.WriteLine(m.Aplica(5));'),
        ('Define Caja con Cabe(peso) (<=10); imprime Cabe(8) (true).', 'class Caja { public bool Cabe(int peso) => peso <= 10; }\nvar c = new Caja();\nConsole.WriteLine(c.Cabe(8));'),
        ('Define Texto(base) con Repite(n); crea "ab" e imprime Repite(2) (abab).', 'class Texto { public string Base; public Texto(string b) { Base = b; } public string Repite(int n) => string.Concat(Enumerable.Repeat(Base, n)); }\nvar t = new Texto("ab");\nConsole.WriteLine(t.Repite(2));'),
        ('Define Rango(min,max) con Contiene(n); crea (1,10) e imprime Contiene(5) (true).', 'class Rango { public int Min; public int Max; public Rango(int a, int b) { Min = a; Max = b; } public bool Contiene(int n) => n >= Min && n <= Max; }\nvar r = new Rango(1, 10);\nConsole.WriteLine(r.Contiene(5));'),
        ('Define Descuento(pct) con Aplica(precio); crea 10 e imprime Aplica(100) (90).', 'class Descuento { public int Pct; public Descuento(int p) { Pct = p; } public int Aplica(int precio) => precio - precio * Pct / 100; }\nvar d = new Descuento(10);\nConsole.WriteLine(d.Aplica(100));'),
        ('Define Potencia con Eleva(b,e) usando Math.Pow; imprime Eleva(2,5) (32).', 'class Potencia { public int Eleva(int b, int e) => (int)Math.Pow(b, e); }\nvar p = new Potencia();\nConsole.WriteLine(p.Eleva(2, 5));'),
        ('Define Comparador con Mayor(a,b); imprime Mayor(8,3) (8).', 'class Comparador { public int Mayor(int a, int b) => a > b ? a : b; }\nvar c = new Comparador();\nConsole.WriteLine(c.Mayor(8, 3));'),
    ]))
    sets.append(explicit([
        drill('Define Cuenta con Deposita y Retira; crea saldo=100, deposita 50, retira 30 e imprime 120.',
              'class Cuenta { public int Saldo = 100; public void Deposita(int n) { Saldo += n; } public void Retira(int n) { Saldo -= n; } }\nvar c = new Cuenta();\nc.Deposita(50);\nc.Retira(30);\nConsole.WriteLine(c.Saldo);',
              hint="Una clase puede tener varios métodos que colaboran."),
        ('Define Contador con Inc y Dec; incrementa 3, decrementa 1 e imprime 2.', 'class Contador { public int Valor = 0; public void Inc() { Valor++; } public void Dec() { Valor--; } }\nvar c = new Contador();\nc.Inc();\nc.Inc();\nc.Inc();\nc.Dec();\nConsole.WriteLine(c.Valor);'),
        ('Define Carrito con Agrega y Total(); agrega 10 y 20 e imprime Total() (30).', 'class Carrito { public List<int> Items = new(); public void Agrega(int p) { Items.Add(p); } public int Total() => Items.Sum(); }\nvar c = new Carrito();\nc.Agrega(10);\nc.Agrega(20);\nConsole.WriteLine(c.Total());'),
        ('Define Pila con Push y Top(); agrega 1,2,3 e imprime Top() (3).', 'class Pila { public List<int> Data = new(); public void Push(int x) { Data.Add(x); } public int Top() => Data[Data.Count - 1]; }\nvar p = new Pila();\np.Push(1);\np.Push(2);\np.Push(3);\nConsole.WriteLine(p.Top());'),
        ('Define Luz con On, Off y Estado(); enciende y apaga, imprime Estado() (false).', 'class Luz { public bool E = false; public void On() { E = true; } public void Off() { E = false; } public bool Estado() => E; }\nvar l = new Luz();\nl.On();\nl.Off();\nConsole.WriteLine(l.Estado());'),
        ('Define Cuenta con Deposita y Saldo(); deposita 40 dos veces e imprime 80.', 'class Cuenta { int s = 0; public void Deposita(int n) { s += n; } public int Saldo() => s; }\nvar c = new Cuenta();\nc.Deposita(40);\nc.Deposita(40);\nConsole.WriteLine(c.Saldo());'),
        ('Define Termostato con Sube, Baja y Grados(); sube 3, baja 1 e imprime 22 (base 20).', 'class Termostato { int g = 20; public void Sube() { g++; } public void Baja() { g--; } public int Grados() => g; }\nvar t = new Termostato();\nt.Sube();\nt.Sube();\nt.Sube();\nt.Baja();\nConsole.WriteLine(t.Grados());'),
        ('Define Contador con Suma, Reset y Valor(); suma 5, reset, suma 2 e imprime 2.', 'class Contador { int v = 0; public void Suma(int n) { v += n; } public void Reset() { v = 0; } public int Valor() => v; }\nvar c = new Contador();\nc.Suma(5);\nc.Reset();\nc.Suma(2);\nConsole.WriteLine(c.Valor());'),
        ('Define Lista con Agrega y Cuenta(); agrega dos e imprime 2.', 'class Lista { List<int> xs = new(); public void Agrega(int n) { xs.Add(n); } public int Cuenta() => xs.Count; }\nvar l = new Lista();\nl.Agrega(1);\nl.Agrega(2);\nConsole.WriteLine(l.Cuenta());'),
        ('Define Cuenta con Deposita, Retira, y comprueba fondos: retira 200 de 100 sin permitir negativo (queda 100).', 'class Cuenta { public int Saldo = 100; public void Deposita(int n) { Saldo += n; } public void Retira(int n) { if (Saldo >= n) Saldo -= n; } }\nvar c = new Cuenta();\nc.Retira(200);\nConsole.WriteLine(c.Saldo);'),
    ]))
    sets.append(explicit([
        drill('Define Jugador con Puntos=0 y Anota(p) que suma p; anota 3 y 5 e imprime Puntos (8).',
              'class Jugador { public int Puntos = 0; public void Anota(int p) { Puntos += p; } }\nvar j = new Jugador();\nj.Anota(3);\nj.Anota(5);\nConsole.WriteLine(j.Puntos);',
              hint="Un método puede modificar el estado del objeto varias veces."),
        ('Define Robot con Pos=0 y Avanza(n); avanza 2 y 3 e imprime Pos (5).', 'class Robot { public int Pos = 0; public void Avanza(int n) { Pos += n; } }\nvar r = new Robot();\nr.Avanza(2);\nr.Avanza(3);\nConsole.WriteLine(r.Pos);'),
        ('Define Vaso con Nivel=0 y Llena(ml); llena 100 y 50 e imprime 150.', 'class Vaso { public int Nivel = 0; public void Llena(int ml) { Nivel += ml; } }\nvar v = new Vaso();\nv.Llena(100);\nv.Llena(50);\nConsole.WriteLine(v.Nivel);'),
        ('Define Bateria con Nivel=0 y Carga(n); carga 20 dos veces e imprime 40.', 'class Bateria { public int Nivel = 0; public void Carga(int n) { Nivel += n; } }\nvar b = new Bateria();\nb.Carga(20);\nb.Carga(20);\nConsole.WriteLine(b.Nivel);'),
        ('Define Termometro con Grados=0, Sube(n) y Baja(n); sube 5, baja 2 e imprime 3.', 'class Termometro { public int Grados = 0; public void Sube(int n) { Grados += n; } public void Baja(int n) { Grados -= n; } }\nvar t = new Termometro();\nt.Sube(5);\nt.Baja(2);\nConsole.WriteLine(t.Grados);'),
        ('Define Score con Add(n) y Reset(); add 10, reset, add 3 e imprime 3.', 'class Score { public int V = 0; public void Add(int n) { V += n; } public void Reset() { V = 0; } }\nvar s = new Score();\ns.Add(10);\ns.Reset();\ns.Add(3);\nConsole.WriteLine(s.V);'),
        ('Define Tareas con Agrega(t); agrega 2 e imprime cuántas hay (2).', 'class Tareas { public List<string> Items = new(); public void Agrega(string t) { Items.Add(t); } }\nvar x = new Tareas();\nx.Agrega("a");\nx.Agrega("b");\nConsole.WriteLine(x.Items.Count);'),
        ('Define Contador con Valor=1 y Multiplica(n); multiplica por 2 tres veces e imprime 8.', 'class Contador { public int Valor = 1; public void Multiplica(int n) { Valor *= n; } }\nvar c = new Contador();\nc.Multiplica(2);\nc.Multiplica(2);\nc.Multiplica(2);\nConsole.WriteLine(c.Valor);'),
        ('Define Acumulador con Agrega(n); en un bucle suma 1..3 e imprime 6.', 'class Acumulador { public int Total = 0; public void Agrega(int n) { Total += n; } }\nvar a = new Acumulador();\nfor (int i = 1; i <= 3; i++) a.Agrega(i);\nConsole.WriteLine(a.Total);'),
        ('Define Cuenta con Saldo=0, Deposita(n) y Retira(n) sin negativo; deposita 100, retira 30 e imprime 70.', 'class Cuenta { public int Saldo = 0; public void Deposita(int n) { Saldo += n; } public void Retira(int n) { if (Saldo >= n) Saldo -= n; } }\nvar c = new Cuenta();\nc.Deposita(100);\nc.Retira(30);\nConsole.WriteLine(c.Saldo);'),
    ]))

    # SE.C — ToString y composición
    sets.append(explicit([
        drill('Define Punto(x,y) con override ToString() que retorne "(x, y)"; imprime new Punto(1,2).',
              'class Punto { public int X; public int Y; public Punto(int x, int y) { X = x; Y = y; } public override string ToString() => $"({X}, {Y})"; }\nConsole.WriteLine(new Punto(1, 2));',
              hint="Console.WriteLine usa ToString() del objeto automáticamente."),
        ('Define Persona(nombre) con ToString()=nombre; imprime new Persona("Ana").', 'class Persona { public string Nombre; public Persona(string n) { Nombre = n; } public override string ToString() => Nombre; }\nConsole.WriteLine(new Persona("Ana"));'),
        ('Define Dinero(monto) con ToString()="$monto"; imprime new Dinero(50).', 'class Dinero { public int Monto; public Dinero(int m) { Monto = m; } public override string ToString() => $"${Monto}"; }\nConsole.WriteLine(new Dinero(50));'),
        ('Define Fraccion(a,b) con ToString()="a/b"; imprime new Fraccion(1,2).', 'class Fraccion { public int A; public int B; public Fraccion(int a, int b) { A = a; B = b; } public override string ToString() => $"{A}/{B}"; }\nConsole.WriteLine(new Fraccion(1, 2));'),
        ('Define Producto(nombre,precio) con ToString()="nombre: $precio"; imprime new Producto("Pan",3).', 'class Producto { public string Nombre; public int Precio; public Producto(string n, int p) { Nombre = n; Precio = p; } public override string ToString() => $"{Nombre}: ${Precio}"; }\nConsole.WriteLine(new Producto("Pan", 3));'),
        ('Define Temperatura(g) con ToString()="gC"; imprime new Temperatura(25).', 'class Temperatura { public int G; public Temperatura(int g) { G = g; } public override string ToString() => $"{G}C"; }\nConsole.WriteLine(new Temperatura(25));'),
        ('Define Rango(a,b) con ToString()="[a, b]"; imprime new Rango(1,9).', 'class Rango { public int A; public int B; public Rango(int a, int b) { A = a; B = b; } public override string ToString() => $"[{A}, {B}]"; }\nConsole.WriteLine(new Rango(1, 9));'),
        ('Define Libro(titulo,anio) con ToString()="titulo (anio)"; imprime new Libro("C#",2020).', 'class Libro { public string T; public int A; public Libro(string t, int a) { T = t; A = a; } public override string ToString() => $"{T} ({A})"; }\nConsole.WriteLine(new Libro("C#", 2020));'),
        ('Define Coord(lat,lon) con ToString()="lat,lon"; imprime new Coord(10,20).', 'class Coord { public int Lat; public int Lon; public Coord(int a, int b) { Lat = a; Lon = b; } public override string ToString() => $"{Lat},{Lon}"; }\nConsole.WriteLine(new Coord(10, 20));'),
        ('Define Usuario(nombre) con ToString()="@nombre"; imprime new Usuario("bob").', 'class Usuario { public string N; public Usuario(string n) { N = n; } public override string ToString() => $"@{N}"; }\nConsole.WriteLine(new Usuario("bob"));'),
    ]))
    sets.append(explicit([
        drill('Define Circulo(r) con propiedad calculada Area (=r*r*3); crea r=2 e imprime Area (12).',
              'class Circulo { public int R; public Circulo(int r) { R = r; } public int Area => R * R * 3; }\nvar c = new Circulo(2);\nConsole.WriteLine(c.Area);',
              hint="Una propiedad calculada usa => y no se asigna."),
        ('Define Rectangulo(a,b) con propiedad Area; crea (3,4) e imprime 12.', 'class Rectangulo { public int A; public int B; public Rectangulo(int a, int b) { A = a; B = b; } public int Area => A * B; }\nvar r = new Rectangulo(3, 4);\nConsole.WriteLine(r.Area);'),
        ('Define Persona(nombre) con propiedad Inicial (primera letra); crea "Ana" e imprime "A".', 'class Persona { public string Nombre; public Persona(string n) { Nombre = n; } public char Inicial => Nombre[0]; }\nvar p = new Persona("Ana");\nConsole.WriteLine(p.Inicial);'),
        ('Define Cuenta(saldo) con propiedad EnRojo (saldo<0); crea -5 e imprime true.', 'class Cuenta { public int Saldo; public Cuenta(int s) { Saldo = s; } public bool EnRojo => Saldo < 0; }\nvar c = new Cuenta(-5);\nConsole.WriteLine(c.EnRojo);'),
        ('Define Cuadrado(lado) con propiedad Perimetro (=4*lado); crea 5 e imprime 20.', 'class Cuadrado { public int Lado; public Cuadrado(int l) { Lado = l; } public int Perimetro => 4 * Lado; }\nvar c = new Cuadrado(5);\nConsole.WriteLine(c.Perimetro);'),
        ('Define Persona(edad) con propiedad EsMayor; crea 20 e imprime true.', 'class Persona { public int Edad; public Persona(int e) { Edad = e; } public bool EsMayor => Edad >= 18; }\nvar p = new Persona(20);\nConsole.WriteLine(p.EsMayor);'),
        ('Define Texto(valor) con propiedad Largo; crea "hola" e imprime 4.', 'class Texto { public string Valor; public Texto(string v) { Valor = v; } public int Largo => Valor.Length; }\nvar t = new Texto("hola");\nConsole.WriteLine(t.Largo);'),
        ('Define Producto(precio) con propiedad ConIva (+18%); crea 100 e imprime 118.', 'class Producto { public int Precio; public Producto(int p) { Precio = p; } public int ConIva => Precio + Precio * 18 / 100; }\nvar p = new Producto(100);\nConsole.WriteLine(p.ConIva);'),
        ('Define Numero(valor) con propiedad EsPar; crea 6 e imprime true.', 'class Numero { public int Valor; public Numero(int v) { Valor = v; } public bool EsPar => Valor % 2 == 0; }\nvar n = new Numero(6);\nConsole.WriteLine(n.EsPar);'),
        ('Define Rango(a,b) con propiedad Tamano (=b-a); crea (2,10) e imprime 8.', 'class Rango { public int A; public int B; public Rango(int a, int b) { A = a; B = b; } public int Tamano => B - A; }\nvar r = new Rango(2, 10);\nConsole.WriteLine(r.Tamano);'),
    ]))
    sets.append(explicit([
        drill('Define un campo estático Contador.Total; crea 3 objetos que lo incrementen e imprime Total (3).',
              'class Item { public static int Total = 0; public Item() { Total++; } }\nnew Item();\nnew Item();\nnew Item();\nConsole.WriteLine(Item.Total);',
              hint="Un campo static es compartido por todas las instancias."),
        ('Define static Contador.N; incrementa en 2 constructores e imprime N (2).', 'class C { public static int N = 0; public C() { N++; } }\nnew C();\nnew C();\nConsole.WriteLine(C.N);'),
        ('Define un campo static Config.Version="1.0"; imprime Config.Version sin crear objeto.', 'class Config { public static string Version = "1.0"; }\nConsole.WriteLine(Config.Version);'),
        ('Define static Mate.Pi=3; imprime Mate.Pi.', 'class Mate { public static int Pi = 3; }\nConsole.WriteLine(Mate.Pi);'),
        ('Diferencia instancia vs estático: cada objeto tiene su Id, pero Total es compartido; crea 2 e imprime Total (2).', 'class U { public static int Total = 0; public int Id; public U() { Total++; Id = Total; } }\nnew U();\nvar b = new U();\nConsole.WriteLine(U.Total);'),
        ('Define static Banco.Tasa=5; imprime Banco.Tasa.', 'class Banco { public static int Tasa = 5; }\nConsole.WriteLine(Banco.Tasa);'),
        ('Cuenta objetos creados con static: crea 5 en un bucle e imprime el conteo.', 'class Obj { public static int Count = 0; public Obj() { Count++; } }\nfor (int i = 0; i < 5; i++) new Obj();\nConsole.WriteLine(Obj.Count);'),
        ('Define un método estático Util.Doble(n); imprime Util.Doble(7) (14).', 'class Util { public static int Doble(int n) => n * 2; }\nConsole.WriteLine(Util.Doble(7));'),
        ('Define un método estático Mate.Max(a,b); imprime Mate.Max(3,9) (9).', 'class Mate { public static int Max(int a, int b) => a > b ? a : b; }\nConsole.WriteLine(Mate.Max(3, 9));'),
        ('Un id autoincremental: cada objeto toma el siguiente Id estático; crea 3, imprime el Id del último (3).', 'class Ticket { public static int Sig = 0; public int Id; public Ticket() { Sig++; Id = Sig; } }\nnew Ticket();\nnew Ticket();\nvar c = new Ticket();\nConsole.WriteLine(c.Id);'),
    ]))
    sets.append(explicit([
        drill('Define Equipo con lista de Jugadores (strings) y Agrega(nombre); agrega 2 e imprime cuántos hay (2).',
              'class Equipo { public List<string> Jugadores = new(); public void Agrega(string n) { Jugadores.Add(n); } }\nvar e = new Equipo();\ne.Agrega("Ana");\ne.Agrega("Bob");\nConsole.WriteLine(e.Jugadores.Count);',
              hint="Un objeto puede contener una lista de otros datos u objetos."),
        ('Define Carrito con List<int> Precios y Total(); agrega 10,20,30 e imprime 60.', 'class Carrito { public List<int> Precios = new(); public void Agrega(int p) { Precios.Add(p); } public int Total() => Precios.Sum(); }\nvar c = new Carrito();\nc.Agrega(10);\nc.Agrega(20);\nc.Agrega(30);\nConsole.WriteLine(c.Total());'),
        ('Define Biblioteca con List<string> Libros; agrega 3 e imprime el Count.', 'class Biblioteca { public List<string> Libros = new(); }\nvar b = new Biblioteca();\nb.Libros.Add("a");\nb.Libros.Add("b");\nb.Libros.Add("c");\nConsole.WriteLine(b.Libros.Count);'),
        ('Define Aula con List<int> Notas y Promedio(); agrega 80,90,100 e imprime 90.', 'class Aula { public List<int> Notas = new(); public int Promedio() => Notas.Sum() / Notas.Count; }\nvar a = new Aula();\na.Notas.Add(80);\na.Notas.Add(90);\na.Notas.Add(100);\nConsole.WriteLine(a.Promedio());'),
        ('Define Pila con List<int> y Pop() que quita y devuelve el último; push 1,2,3, pop e imprime 3.', 'class Pila { public List<int> Data = new(); public void Push(int x) { Data.Add(x); } public int Pop() { int x = Data[Data.Count - 1]; Data.RemoveAt(Data.Count - 1); return x; } }\nvar p = new Pila();\np.Push(1);\np.Push(2);\np.Push(3);\nConsole.WriteLine(p.Pop());'),
        ('Define Equipo con jugadores; imprime el primero agregado ("Ana").', 'class Equipo { public List<string> J = new(); public void Add(string n) { J.Add(n); } }\nvar e = new Equipo();\ne.Add("Ana");\ne.Add("Bob");\nConsole.WriteLine(e.J[0]);'),
        ('Define Inventario con List<int> y Max(); agrega 5,9,2 e imprime 9.', 'class Inventario { public List<int> Stock = new(); public int Max() => Stock.Max(); }\nvar i = new Inventario();\ni.Stock.Add(5);\ni.Stock.Add(9);\ni.Stock.Add(2);\nConsole.WriteLine(i.Max());'),
        ('Define Cola con List<int>, Enqueue y Peek() (primero); agrega 1,2 e imprime 1.', 'class Cola { public List<int> Data = new(); public void Enqueue(int x) { Data.Add(x); } public int Peek() => Data[0]; }\nvar c = new Cola();\nc.Enqueue(1);\nc.Enqueue(2);\nConsole.WriteLine(c.Peek());'),
        ('Define Grupo con List<string> y Contiene(nombre); agrega "Ana" e imprime Contiene("Ana") (true).', 'class Grupo { public List<string> M = new(); public void Add(string n) { M.Add(n); } public bool Contiene(string n) => M.Contains(n); }\nvar g = new Grupo();\ng.Add("Ana");\nConsole.WriteLine(g.Contiene("Ana"));'),
        ('Define Playlist con List<string> y Cantidad(); agrega 4 canciones e imprime 4.', 'class Playlist { public List<string> S = new(); public void Add(string c) { S.Add(c); } public int Cantidad() => S.Count; }\nvar pl = new Playlist();\nfor (int i = 0; i < 4; i++) pl.Add("song");\nConsole.WriteLine(pl.Cantidad());'),
    ]))
    sets.append(explicit([
        drill('Define Rectangulo(a,b) con Area() y Perimetro(); crea (3,4) e imprime "12 14".',
              'class Rectangulo { public int A; public int B; public Rectangulo(int a, int b) { A = a; B = b; } public int Area() => A * B; public int Perimetro() => 2 * (A + B); }\nvar r = new Rectangulo(3, 4);\nConsole.WriteLine($"{r.Area()} {r.Perimetro()}");',
              hint="Una clase puede tener varios métodos que calculan resultados distintos."),
        ('Define Circulo(r) con Area()=r*r*3 y Diametro()=2*r; crea r=2 e imprime "12 4".', 'class Circulo { public int R; public Circulo(int r) { R = r; } public int Area() => R * R * 3; public int Diametro() => 2 * R; }\nvar c = new Circulo(2);\nConsole.WriteLine($"{c.Area()} {c.Diametro()}");'),
        ('Define Cuenta(saldo) con ConInteres()=saldo+10%; crea 100 e imprime 110.', 'class Cuenta { public int Saldo; public Cuenta(int s) { Saldo = s; } public int ConInteres() => Saldo + Saldo * 10 / 100; }\nvar c = new Cuenta(100);\nConsole.WriteLine(c.ConInteres());'),
        ('Define Persona(nacimiento) con Edad(actual)=actual-nacimiento; crea 2000 e imprime Edad(2020) (20).', 'class Persona { public int Nacimiento; public Persona(int n) { Nacimiento = n; } public int Edad(int actual) => actual - Nacimiento; }\nvar p = new Persona(2000);\nConsole.WriteLine(p.Edad(2020));'),
        ('Define Notas(a,b) con Promedio()=(a+b)/2; crea (80,90) e imprime 85.', 'class Notas { public int A; public int B; public Notas(int a, int b) { A = a; B = b; } public int Promedio() => (A + B) / 2; }\nvar n = new Notas(80, 90);\nConsole.WriteLine(n.Promedio());'),
        ('Define Triangulo(b,h) con Area()=b*h/2; crea (6,4) e imprime 12.', 'class Triangulo { public int B; public int H; public Triangulo(int b, int h) { B = b; H = h; } public int Area() => B * H / 2; }\nvar t = new Triangulo(6, 4);\nConsole.WriteLine(t.Area());'),
        ('Define Caja(l,a,p) con Volumen()=l*a*p; crea (2,3,4) e imprime 24.', 'class Caja { public int L; public int A; public int P; public Caja(int l, int a, int p) { L = l; A = a; P = p; } public int Volumen() => L * A * P; }\nvar c = new Caja(2, 3, 4);\nConsole.WriteLine(c.Volumen());'),
        ('Define Temperatura(c) con AFahrenheit()=c*9/5+32; crea 100 e imprime 212.', 'class Temperatura { public int C; public Temperatura(int c) { C = c; } public int AFahrenheit() => C * 9 / 5 + 32; }\nvar t = new Temperatura(100);\nConsole.WriteLine(t.AFahrenheit());'),
        ('Define Segmento(x1,x2) con Longitud()=|x2-x1|; crea (3,10) e imprime 7.', 'class Segmento { public int X1; public int X2; public Segmento(int a, int b) { X1 = a; X2 = b; } public int Longitud() => Math.Abs(X2 - X1); }\nvar s = new Segmento(3, 10);\nConsole.WriteLine(s.Longitud());'),
        ('Define Producto(precio,cant) con Total()=precio*cant; crea (5,3) e imprime 15.', 'class Producto { public int Precio; public int Cant; public Producto(int p, int c) { Precio = p; Cant = c; } public int Total() => Precio * Cant; }\nvar p = new Producto(5, 3);\nConsole.WriteLine(p.Total());'),
    ]))

    # SE.D — Herencia
    sets.append(explicit([
        drill('Define Animal con método Come() que imprime "come"; Perro : Animal; crea Perro y llama Come().',
              'class Animal { public void Come() { Console.WriteLine("come"); } }\nclass Perro : Animal { }\nnew Perro().Come();',
              hint="Una subclase hereda los métodos de la base con ':'."),
        ('Define Vehiculo con Arranca()="arranca"; Auto : Vehiculo; crea Auto y llama Arranca().', 'class Vehiculo { public void Arranca() { Console.WriteLine("arranca"); } }\nclass Auto : Vehiculo { }\nnew Auto().Arranca();'),
        ('Define Base con propiedad Nombre; Derivada : Base; crea Derivada, Nombre="X" e imprime Nombre.', 'class Base { public string Nombre; }\nclass Derivada : Base { }\nvar d = new Derivada();\nd.Nombre = "X";\nConsole.WriteLine(d.Nombre);'),
        ('Define Forma con Describe()="soy forma"; Circulo : Forma; crea y llama Describe().', 'class Forma { public void Describe() { Console.WriteLine("soy forma"); } }\nclass Circulo : Forma { }\nnew Circulo().Describe();'),
        ('Define Empleado con Trabaja()="trabaja"; Gerente : Empleado; crea Gerente y llama Trabaja().', 'class Empleado { public void Trabaja() { Console.WriteLine("trabaja"); } }\nclass Gerente : Empleado { }\nnew Gerente().Trabaja();'),
        ('Define Animal con propiedad Patas; Gato : Animal; crea Gato con Patas=4 e imprime 4.', 'class Animal { public int Patas; }\nclass Gato : Animal { }\nvar g = new Gato();\ng.Patas = 4;\nConsole.WriteLine(g.Patas);'),
        ('Define Base con Saluda()="hola"; Hija : Base; llama Saluda() desde Hija.', 'class Base { public void Saluda() { Console.WriteLine("hola"); } }\nclass Hija : Base { }\nnew Hija().Saluda();'),
        ('Define Instrumento con Suena()="suena"; Guitarra : Instrumento; crea y llama.', 'class Instrumento { public void Suena() { Console.WriteLine("suena"); } }\nclass Guitarra : Instrumento { }\nnew Guitarra().Suena();'),
        ('Define Figura con Area()=0; Cuadrado : Figura hereda; crea Cuadrado e imprime Area() (0).', 'class Figura { public virtual int Area() => 0; }\nclass Cuadrado : Figura { }\nConsole.WriteLine(new Cuadrado().Area());'),
        ('Define Persona con Nombre; Estudiante : Persona; crea Estudiante con Nombre="Ana" e imprime.', 'class Persona { public string Nombre; }\nclass Estudiante : Persona { }\nvar e = new Estudiante();\ne.Nombre = "Ana";\nConsole.WriteLine(e.Nombre);'),
    ]))
    sets.append(explicit([
        drill('Define Animal con virtual Sonido()="..."; Perro override Sonido()="guau"; crea Perro e imprime Sonido().',
              'class Animal { public virtual string Sonido() => "..."; }\nclass Perro : Animal { public override string Sonido() => "guau"; }\nConsole.WriteLine(new Perro().Sonido());',
              hint="override redefine un método virtual de la base."),
        ('Define Animal Sonido() virtual; Gato override "miau"; imprime.', 'class Animal { public virtual string Sonido() => "..."; }\nclass Gato : Animal { public override string Sonido() => "miau"; }\nConsole.WriteLine(new Gato().Sonido());'),
        ('Define Figura Area() virtual =0; Cuadrado(lado) override lado*lado; crea 5 e imprime 25.', 'class Figura { public virtual int Area() => 0; }\nclass Cuadrado : Figura { public int L; public Cuadrado(int l) { L = l; } public override int Area() => L * L; }\nConsole.WriteLine(new Cuadrado(5).Area());'),
        ('Define Saludo virtual "hola"; Formal override "buenos dias"; imprime Formal.', 'class Saludo { public virtual string Di() => "hola"; }\nclass Formal : Saludo { public override string Di() => "buenos dias"; }\nConsole.WriteLine(new Formal().Di());'),
        ('Define Empleado Sueldo() virtual=1000; Gerente override=2000; imprime 2000.', 'class Empleado { public virtual int Sueldo() => 1000; }\nclass Gerente : Empleado { public override int Sueldo() => 2000; }\nConsole.WriteLine(new Gerente().Sueldo());'),
        ('Define Forma Nombre() virtual "forma"; Circulo override "circulo"; imprime.', 'class Forma { public virtual string Nombre() => "forma"; }\nclass Circulo : Forma { public override string Nombre() => "circulo"; }\nConsole.WriteLine(new Circulo().Nombre());'),
        ('Define Figura Area() virtual; Rectangulo(a,b) override a*b; crea (3,4) e imprime 12.', 'class Figura { public virtual int Area() => 0; }\nclass Rectangulo : Figura { public int A; public int B; public Rectangulo(int a, int b) { A = a; B = b; } public override int Area() => A * B; }\nConsole.WriteLine(new Rectangulo(3, 4).Area());'),
        ('Usa polimorfismo: Figura f = new Cuadrado(4); imprime f.Area() (16).', 'class Figura { public virtual int Area() => 0; }\nclass Cuadrado : Figura { public int L; public Cuadrado(int l) { L = l; } public override int Area() => L * L; }\nFigura f = new Cuadrado(4);\nConsole.WriteLine(f.Area());'),
        ('Define Animal Habla() virtual "..."; Vaca override "muu"; imprime Vaca.', 'class Animal { public virtual string Habla() => "..."; }\nclass Vaca : Animal { public override string Habla() => "muu"; }\nConsole.WriteLine(new Vaca().Habla());'),
        ('Define Pago virtual Monto()=0; Efectivo override 100; imprime 100.', 'class Pago { public virtual int Monto() => 0; }\nclass Efectivo : Pago { public override int Monto() => 100; }\nConsole.WriteLine(new Efectivo().Monto());'),
    ]))
    sets.append(explicit([
        drill('Define Animal(nombre) con constructor; Perro : Animal usa base(nombre); crea Perro("Fido") e imprime Nombre.',
              'class Animal { public string Nombre; public Animal(string n) { Nombre = n; } }\nclass Perro : Animal { public Perro(string n) : base(n) { } }\nConsole.WriteLine(new Perro("Fido").Nombre);',
              hint="base(...) llama al constructor de la clase base."),
        ('Define Vehiculo(ruedas); Auto : Vehiculo con base(4); crea Auto e imprime Ruedas (4).', 'class Vehiculo { public int Ruedas; public Vehiculo(int r) { Ruedas = r; } }\nclass Auto : Vehiculo { public Auto() : base(4) { } }\nConsole.WriteLine(new Auto().Ruedas);'),
        ('Define Persona(nombre); Estudiante : Persona con base(nombre); crea "Ana" e imprime.', 'class Persona { public string Nombre; public Persona(string n) { Nombre = n; } }\nclass Estudiante : Persona { public Estudiante(string n) : base(n) { } }\nConsole.WriteLine(new Estudiante("Ana").Nombre);'),
        ('Define Forma(lados); Triangulo : Forma con base(3); crea e imprime Lados (3).', 'class Forma { public int Lados; public Forma(int l) { Lados = l; } }\nclass Triangulo : Forma { public Triangulo() : base(3) { } }\nConsole.WriteLine(new Triangulo().Lados);'),
        ('Define Empleado(sueldo); Gerente : Empleado con base(sueldo) y bono; crea sueldo=1000 e imprime Sueldo.', 'class Empleado { public int Sueldo; public Empleado(int s) { Sueldo = s; } }\nclass Gerente : Empleado { public Gerente(int s) : base(s) { } }\nConsole.WriteLine(new Gerente(1000).Sueldo);'),
        ('Define Base(x); Sub : Base pasa base(x*2); crea Sub(5) e imprime X (10).', 'class Base { public int X; public Base(int x) { X = x; } }\nclass Sub : Base { public Sub(int x) : base(x * 2) { } }\nConsole.WriteLine(new Sub(5).X);'),
        ('Define Animal(patas); Araña : Animal base(8); crea e imprime Patas (8).', 'class Animal { public int Patas; public Animal(int p) { Patas = p; } }\nclass Arana : Animal { public Arana() : base(8) { } }\nConsole.WriteLine(new Arana().Patas);'),
        ('Define Cuenta(saldo); CuentaAhorro : Cuenta base(saldo); crea 100 e imprime Saldo.', 'class Cuenta { public int Saldo; public Cuenta(int s) { Saldo = s; } }\nclass CuentaAhorro : Cuenta { public CuentaAhorro(int s) : base(s) { } }\nConsole.WriteLine(new CuentaAhorro(100).Saldo);'),
        ('Define Producto(precio); Descuento : Producto base(precio-10); crea 100 e imprime Precio (90).', 'class Producto { public int Precio; public Producto(int p) { Precio = p; } }\nclass Descuento : Producto { public Descuento(int p) : base(p - 10) { } }\nConsole.WriteLine(new Descuento(100).Precio);'),
        ('Define Ciudad(nombre); Capital : Ciudad base(nombre); crea "Lima" e imprime Nombre.', 'class Ciudad { public string Nombre; public Ciudad(string n) { Nombre = n; } }\nclass Capital : Ciudad { public Capital(string n) : base(n) { } }\nConsole.WriteLine(new Capital("Lima").Nombre);'),
    ]))
    sets.append(explicit([
        drill('Define Animal con virtual Sonido()="..."; Perro override llama base y agrega: retorna base.Sonido()+"guau"; imprime "...guau".',
              'class Animal { public virtual string Sonido() => "..."; }\nclass Perro : Animal { public override string Sonido() => base.Sonido() + "guau"; }\nConsole.WriteLine(new Perro().Sonido());',
              hint="base.Metodo() llama la versión de la clase base."),
        ('Define Base Saluda()="hola"; Sub override base.Saluda()+" mundo"; imprime "hola mundo".', 'class Base { public virtual string Saluda() => "hola"; }\nclass Sub : Base { public override string Saluda() => base.Saluda() + " mundo"; }\nConsole.WriteLine(new Sub().Saluda());'),
        ('Define Figura Area()=10 virtual; Especial override base.Area()+5; imprime 15.', 'class Figura { public virtual int Area() => 10; }\nclass Especial : Figura { public override int Area() => base.Area() + 5; }\nConsole.WriteLine(new Especial().Area());'),
        ('Define Empleado Sueldo()=1000; Gerente override base.Sueldo()+500; imprime 1500.', 'class Empleado { public virtual int Sueldo() => 1000; }\nclass Gerente : Empleado { public override int Sueldo() => base.Sueldo() + 500; }\nConsole.WriteLine(new Gerente().Sueldo());'),
        ('Define Base Nombre()="base"; Sub override "sub-"+base.Nombre(); imprime "sub-base".', 'class Base { public virtual string Nombre() => "base"; }\nclass Sub : Base { public override string Nombre() => "sub-" + base.Nombre(); }\nConsole.WriteLine(new Sub().Nombre());'),
        ('Define Contador Valor()=1; Doble override base.Valor()*2; imprime 2.', 'class Contador { public virtual int Valor() => 1; }\nclass Doble : Contador { public override int Valor() => base.Valor() * 2; }\nConsole.WriteLine(new Doble().Valor());'),
        ('Define Animal Describe()="animal"; Perro override base+" perro"; imprime "animal perro".', 'class Animal { public virtual string Describe() => "animal"; }\nclass Perro : Animal { public override string Describe() => base.Describe() + " perro"; }\nConsole.WriteLine(new Perro().Describe());'),
        ('Define Producto Precio()=100 virtual; ConEnvio override base.Precio()+20; imprime 120.', 'class Producto { public virtual int Precio() => 100; }\nclass ConEnvio : Producto { public override int Precio() => base.Precio() + 20; }\nConsole.WriteLine(new ConEnvio().Precio());'),
        ('Define Base Lista()="a"; Sub override base.Lista()+"b"; imprime "ab".', 'class Base { public virtual string Lista() => "a"; }\nclass Sub : Base { public override string Lista() => base.Lista() + "b"; }\nConsole.WriteLine(new Sub().Lista());'),
        ('Define Vehiculo Velocidad()=50; Deportivo override base.Velocidad()*2; imprime 100.', 'class Vehiculo { public virtual int Velocidad() => 50; }\nclass Deportivo : Vehiculo { public override int Velocidad() => base.Velocidad() * 2; }\nConsole.WriteLine(new Deportivo().Velocidad());'),
    ]))
    sets.append(explicit([
        drill('Usa is: Figura f = new Cuadrado(); imprime "es cuadrado" si f is Cuadrado.',
              'class Figura { }\nclass Cuadrado : Figura { }\nFigura f = new Cuadrado();\nif (f is Cuadrado)\n    Console.WriteLine("es cuadrado");',
              hint="'is' comprueba el tipo real de un objeto."),
        ('Figura f = new Circulo(); imprime true si f is Circulo.', 'class Figura { }\nclass Circulo : Figura { }\nFigura f = new Circulo();\nConsole.WriteLine(f is Circulo);'),
        ('Animal a = new Perro(); imprime false si a is Gato.', 'class Animal { }\nclass Perro : Animal { }\nclass Gato : Animal { }\nAnimal a = new Perro();\nConsole.WriteLine(a is Gato);'),
        ('Polimorfismo en array: {Cuadrado(2),Cuadrado(3)} como Figura[]; suma áreas (13).', 'class Figura { public virtual int Area() => 0; }\nclass Cuadrado : Figura { public int L; public Cuadrado(int l) { L = l; } public override int Area() => L * L; }\nFigura[] fs = { new Cuadrado(2), new Cuadrado(3) };\nConsole.WriteLine(fs.Sum(f => f.Area()));'),
        ('Cuenta cuántos Perro hay en un Animal[] con is (2).', 'class Animal { }\nclass Perro : Animal { }\nclass Gato : Animal { }\nAnimal[] xs = { new Perro(), new Gato(), new Perro() };\nConsole.WriteLine(xs.Count(x => x is Perro));'),
        ('Usa as: Animal a = new Perro(); (a as Perro) no es null -> imprime "perro".', 'class Animal { }\nclass Perro : Animal { }\nAnimal a = new Perro();\nvar p = a as Perro;\nConsole.WriteLine(p != null ? "perro" : "no");'),
        ('Con pattern: if (f is Cuadrado c) imprime c.Area() (9) para Cuadrado(3).', 'class Figura { public virtual int Area() => 0; }\nclass Cuadrado : Figura { public int L; public Cuadrado(int l) { L = l; } public override int Area() => L * L; }\nFigura f = new Cuadrado(3);\nif (f is Cuadrado c)\n    Console.WriteLine(c.Area());'),
        ('Polimorfismo con Sonido(): recorre {Perro,Gato} e imprime cada sonido.', 'class Animal { public virtual string Sonido() => "..."; }\nclass Perro : Animal { public override string Sonido() => "guau"; }\nclass Gato : Animal { public override string Sonido() => "miau"; }\nAnimal[] xs = { new Perro(), new Gato() };\nforeach (var x in xs) Console.WriteLine(x.Sonido());'),
        ('Suma sueldos polimórficos de {Empleado(1000),Gerente()} (Gerente=2000) -> 3000.', 'class Empleado { public virtual int Sueldo() => 1000; }\nclass Gerente : Empleado { public override int Sueldo() => 2000; }\nEmpleado[] es = { new Empleado(), new Gerente() };\nConsole.WriteLine(es.Sum(e => e.Sueldo()));'),
        ('Base b = new Sub(); imprime true si b is Base (siempre) para cualquier Sub.', 'class Base { }\nclass Sub : Base { }\nBase b = new Sub();\nConsole.WriteLine(b is Base);'),
    ]))

    return sets


LEVEL_BUILDERS = {
    "SA": level_sa,
    "SB": level_sb,
    "SC": level_sc,
    "SD": level_sd,
    "SE": level_se,
}


# ---------------------------------------------------------------------------
# write Kumon pages
# ---------------------------------------------------------------------------

def _load_schedule() -> dict:
    with open(SCHEDULE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _level_blocks(level: str) -> list[tuple[str, dict]]:
    sched = _load_schedule()
    lvl = sched["levels"][level]
    return list(lvl["blocks"].items())


def _set_standards(level: str) -> list[int]:
    out: list[int] = []
    for _bl, bdata in _level_blocks(level):
        for s in bdata.get("sets", []):
            out.append(s.get("standard_seconds", 600))
    return out


def generate_kumon(levels: list[str] | None = None) -> int:
    count = 0
    targets = levels or list(LEVEL_BUILDERS.keys())
    for level in targets:
        builder = LEVEL_BUILDERS[level]
        sets = builder()
        blocks = _level_blocks(level)
        expected_sets = sum(len(b.get("sets", [])) for _n, b in blocks)
        if len(sets) != expected_sets:
            raise SystemExit(f"Level {level}: expected {expected_sets} sets, got {len(sets)}")
        std = _set_standards(level)
        set_idx = 0
        for block_letter, bdata in blocks:
            for _si in range(len(bdata.get("sets", []))):
                drills = sets[set_idx]
                if len(drills) != PAGES_PER_SET:
                    raise SystemExit(f"Level {level} set {set_idx + 1}: expected 10 drills, got {len(drills)}")
                set_number = set_idx + 1
                std_seconds = std[set_idx] if set_idx < len(std) else 600
                per_page = max(20, std_seconds // PAGES_PER_SET)
                page_base = bdata["page_start"] + _si * PAGES_PER_SET
                for j, d in enumerate(drills):
                    order = j + 1
                    page = page_base + j
                    code = d["code"]
                    expected_out = run_capture(code)
                    scaff = scaffolding_for(order)
                    data: dict = {
                        "id": f"{level}{page}",
                        "level": level,
                        "page": page,
                        "set": set_number,
                        "block": block_letter,
                        "block_id": f"{level}.{block_letter}",
                        "order": order,
                        "scaffolding": scaff,
                        "time_estimate_seconds": per_page,
                        "prompt": d["prompt"],
                        "hints": [hint_for(d["prompt"], code, d.get("hint"))] if scaff != "none" else [],
                        "validation": {"type": "run_and_match_stdout", "expected": expected_out},
                        "starter_code": safe_starter(code, order) if scaff == "full" else "",
                    }
                    if scaff == "full":
                        data["reference_code"] = code
                    write_yaml(CONTENT / f"level-{level.lower()}" / "kumon" / f"{data['id']}.yaml", data)
                    count += 1
                set_idx += 1
    return count


# ---------------------------------------------------------------------------
# LeetCode checkpoints + exams (C#)
# ---------------------------------------------------------------------------

def lc(pid, title, fn, desc, cases, starter1, *, solution_code="", hints=None):
    return {
        "id": pid, "title": title, "fn_name": fn, "description": desc,
        "test_cases": cases,
        "hints": hints or [
            "Identifica qué operación pide el enunciado.",
            "Empieza con el caso más simple y luego los casos borde.",
            "Prueba con los ejemplos del enunciado.",
        ],
        "approach": "Lee el enunciado, identifica entradas/salida y resuélvelo paso a paso.",
        "learning": ["Traducir el enunciado a C#", "Probar con los ejemplos", "Manejar casos borde"],
        "interview_questions": [
            "¿Cuál es la complejidad de tu solución?",
            "¿Qué casos borde consideraste?",
            "¿Hay una forma más eficiente?",
        ],
        "solution_code": solution_code,
        "tiers": {
            1: {"starter_code": starter1, "explain_checklist": [
                "Lee el enunciado y los ejemplos",
                "Identifica entradas, salida y casos borde",
                "Piensa en el patrón antes de escribir código",
            ], "hints_allowed": True},
            2: {"starter_code": starter1, "narration_prompts": [
                "Explica tu enfoque en voz alta paso a paso",
                "¿Cuál es la complejidad temporal y espacial?",
            ], "hints_allowed": True},
            3: {"starter_code": starter1, "narration_prompts": [], "hints_allowed": False},
        },
    }


CSHARP_LEETCODE = {
    "level-sa": [
        lc("sa-cp-sum-pair", "Suma de dos números", "Suma", "Retorna a + b.",
           [{"args": [2, 3], "expected": 5}, {"args": [10, 90], "expected": 100}],
           "int Suma(int a, int b)\n{\n    return 0; // reemplaza\n}",
           solution_code="int Suma(int a, int b) => a + b;"),
        lc("sa-cp-reverse-string", "Invertir texto", "Invertir", "Retorna el texto al revés.",
           [{"args": ["csharp"], "expected": "prahsc"}, {"args": ["ana"], "expected": "ana"}],
           "string Invertir(string s)\n{\n    return s; // reemplaza\n}",
           solution_code="string Invertir(string s) => new string(s.Reverse().ToArray());"),
        lc("sa-cp-fizzbuzz", "FizzBuzz de un número", "FizzBuzz", "Retorna 'Fizz','Buzz','FizzBuzz' o el número como texto.",
           [{"args": [3], "expected": "Fizz"}, {"args": [5], "expected": "Buzz"}, {"args": [15], "expected": "FizzBuzz"}, {"args": [7], "expected": "7"}],
           "string FizzBuzz(int n)\n{\n    // usa n % 3 y n % 5\n    return n.ToString();\n}",
           solution_code="string FizzBuzz(int n)\n{\n    if (n % 15 == 0) return \"FizzBuzz\";\n    if (n % 3 == 0) return \"Fizz\";\n    if (n % 5 == 0) return \"Buzz\";\n    return n.ToString();\n}"),
        lc("sa-cp-grade", "Nota a letra", "Nota", "Retorna 'A','B','C' o 'F' según el score.",
           [{"args": [95], "expected": "A"}, {"args": [82], "expected": "B"}, {"args": [71], "expected": "C"}, {"args": [50], "expected": "F"}],
           "string Nota(int score)\n{\n    return \"F\"; // reemplaza\n}",
           solution_code="string Nota(int score)\n{\n    if (score >= 90) return \"A\";\n    if (score >= 80) return \"B\";\n    if (score >= 70) return \"C\";\n    return \"F\";\n}"),
        lc("sa-exam-temperature", "Celsius a Fahrenheit", "CtoF", "Convierte celsius a fahrenheit (c*9/5+32).",
           [{"args": [0], "expected": 32.0}, {"args": [100], "expected": 212.0}],
           "double CtoF(int c)\n{\n    return 0; // reemplaza\n}",
           solution_code="double CtoF(int c) => c * 9.0 / 5 + 32;"),
        lc("sa-exam-leap-year", "Año bisiesto", "Bisiesto", "Retorna true si el año es bisiesto.",
           [{"args": [2024], "expected": True}, {"args": [1900], "expected": False}, {"args": [2000], "expected": True}],
           "bool Bisiesto(int a)\n{\n    return false; // reemplaza\n}",
           solution_code="bool Bisiesto(int a) => a % 400 == 0 || (a % 4 == 0 && a % 100 != 0);"),
    ],
    "level-sb": [
        lc("sb-cp-sum-range", "Suma de 1 a n", "SumRange", "Retorna la suma de 1..n con un bucle.",
           [{"args": [5], "expected": 15}, {"args": [10], "expected": 55}],
           "int SumRange(int n)\n{\n    int total = 0;\n    // bucle for\n    return total;\n}",
           solution_code="int SumRange(int n)\n{\n    int total = 0;\n    for (int i = 1; i <= n; i++) total += i;\n    return total;\n}"),
        lc("sb-cp-count-positive", "Contar positivos", "CountPositive", "Cuenta cuántos números son > 0.",
           [{"args": [[1, -2, 3, 0, 5]], "expected": 3}, {"args": [[-1, -2]], "expected": 0}],
           "int CountPositive(int[] nums)\n{\n    int c = 0;\n    // recorre nums\n    return c;\n}",
           solution_code="int CountPositive(int[] nums)\n{\n    int c = 0;\n    foreach (int n in nums) if (n > 0) c++;\n    return c;\n}"),
        lc("sb-cp-pair-sums", "Sumas por pares", "PairSums", "Suma elemento a elemento de dos arrays.",
           [{"args": [[1, 2, 3], [4, 5, 6]], "expected": [5, 7, 9]}],
           "int[] PairSums(int[] a, int[] b)\n{\n    return new int[0];\n}",
           solution_code="int[] PairSums(int[] a, int[] b)\n{\n    var r = new int[a.Length];\n    for (int i = 0; i < a.Length; i++) r[i] = a[i] + b[i];\n    return r;\n}"),
        lc("sb-cp-apply-twice", "Aplicar dos veces", "ApplyTwice", "Aplica +1 dos veces al número.",
           [{"args": [3], "expected": 5}, {"args": [10], "expected": 12}],
           "int ApplyTwice(int x)\n{\n    return x;\n}",
           solution_code="int Inc(int n) => n + 1;\nint ApplyTwice(int x) => Inc(Inc(x));"),
        lc("sb-exam-factorial", "Factorial", "Factorial", "Retorna n! con un bucle.",
           [{"args": [5], "expected": 120}, {"args": [0], "expected": 1}],
           "int Factorial(int n)\n{\n    int r = 1;\n    // bucle\n    return r;\n}",
           solution_code="int Factorial(int n)\n{\n    int r = 1;\n    for (int i = 2; i <= n; i++) r *= i;\n    return r;\n}"),
        lc("sb-exam-collatz", "Pasos de Collatz", "Collatz", "Cuenta pasos hasta llegar a 1 (par->/2, impar->*3+1).",
           [{"args": [1], "expected": 0}, {"args": [8], "expected": 3}],
           "int Collatz(int n)\n{\n    int pasos = 0;\n    while (n > 1)\n    {\n        // ...\n        pasos++;\n    }\n    return pasos;\n}",
           solution_code="int Collatz(int n)\n{\n    int pasos = 0;\n    while (n > 1)\n    {\n        if (n % 2 == 0) n /= 2; else n = n * 3 + 1;\n        pasos++;\n    }\n    return pasos;\n}"),
    ],
    "level-sc": [
        lc("sc-cp-list-sum", "Suma de lista", "SumList", "Suma todos los elementos.",
           [{"args": [[1, 2, 3, 4]], "expected": 10}, {"args": [[]], "expected": 0}],
           "int SumList(int[] nums)\n{\n    return 0;\n}",
           solution_code="int SumList(int[] nums) => nums.Sum();"),
        lc("sc-cp-reverse-list", "Invertir lista", "ReverseList", "Retorna el array invertido.",
           [{"args": [[1, 2, 3]], "expected": [3, 2, 1]}],
           "int[] ReverseList(int[] nums)\n{\n    return new int[0];\n}",
           solution_code="int[] ReverseList(int[] nums) => nums.Reverse().ToArray();"),
        lc("sc-cp-evens", "Filtrar pares", "Evens", "Retorna solo los números pares.",
           [{"args": [[1, 2, 3, 4, 5, 6]], "expected": [2, 4, 6]}],
           "int[] Evens(int[] nums)\n{\n    return new int[0];\n}",
           solution_code="int[] Evens(int[] nums) => nums.Where(n => n % 2 == 0).ToArray();"),
        lc("sc-cp-word-count", "Contar palabras", "WordCount", "Cuenta cuántas palabras tiene el texto.",
           [{"args": ["hola mundo python"], "expected": 3}, {"args": [""], "expected": 0}],
           "int WordCount(string s)\n{\n    return 0;\n}",
           solution_code="int WordCount(string s) => string.IsNullOrWhiteSpace(s) ? 0 : s.Split(' ').Length;"),
        lc("sc-exam-second-largest", "Segundo mayor", "SecondLargest", "Retorna el segundo número más grande (distintos).",
           [{"args": [[3, 1, 4, 1, 5]], "expected": 4}, {"args": [[10, 20]], "expected": 10}],
           "int SecondLargest(int[] nums)\n{\n    return 0;\n}",
           solution_code="int SecondLargest(int[] nums) => nums.Distinct().OrderByDescending(n => n).Skip(1).First();"),
        lc("sc-exam-anagram", "Anagrama", "IsAnagram", "True si t es anagrama de s.",
           [{"args": ["roma", "amor"], "expected": True}, {"args": ["abc", "abd"], "expected": False}],
           "bool IsAnagram(string s, string t)\n{\n    return false;\n}",
           solution_code="bool IsAnagram(string s, string t) => string.Concat(s.OrderBy(c => c)) == string.Concat(t.OrderBy(c => c));"),
    ],
    "level-sd": [
        lc("sd-cp-merge-dicts", "Combinar conteos", "Combinar", "Cuenta las palabras de dos arrays combinados y retorna un diccionario.",
           [{"args": [["a", "b"], ["a"]], "expected": {"a": 2, "b": 1}}],
           "Dictionary<string, int> Combinar(string[] a, string[] b)\n{\n    return new Dictionary<string, int>();\n}",
           solution_code="Dictionary<string, int> Combinar(string[] a, string[] b)\n{\n    var d = new Dictionary<string, int>();\n    foreach (string w in a.Concat(b)) d[w] = d.GetValueOrDefault(w) + 1;\n    return d;\n}"),
        lc("sd-cp-word-freq", "Frecuencia de palabras", "Frecuencia", "Cuenta cada palabra y retorna un diccionario.",
           [{"args": ["a b a"], "expected": {"a": 2, "b": 1}}],
           "Dictionary<string, int> Frecuencia(string texto)\n{\n    var freq = new Dictionary<string, int>();\n    // recorre texto.Split(' ')\n    return freq;\n}",
           solution_code="Dictionary<string, int> Frecuencia(string texto)\n{\n    var freq = new Dictionary<string, int>();\n    foreach (string w in texto.Split(' ')) freq[w] = freq.GetValueOrDefault(w) + 1;\n    return freq;\n}"),
        lc("sd-cp-unique", "Elementos únicos", "Unicos", "Retorna la cantidad de elementos únicos.",
           [{"args": [[1, 1, 2, 3, 3]], "expected": 3}],
           "int Unicos(int[] nums)\n{\n    return 0;\n}",
           solution_code="int Unicos(int[] nums) => new HashSet<int>(nums).Count;"),
        lc("sd-cp-safe-div", "División segura", "SafeDiv", "Retorna a/b (entero) o 0 si b es 0.",
           [{"args": [10, 2], "expected": 5}, {"args": [5, 0], "expected": 0}],
           "int SafeDiv(int a, int b)\n{\n    // usa try/catch o comprueba b\n    return 0;\n}",
           solution_code="int SafeDiv(int a, int b) => b == 0 ? 0 : a / b;"),
        lc("sd-exam-group-by", "Agrupar y contar", "Agrupar", "Cuenta la frecuencia de cada elemento y retorna un diccionario.",
           [{"args": [["x", "y", "x", "z", "x"]], "expected": {"x": 3, "y": 1, "z": 1}}],
           "Dictionary<string, int> Agrupar(string[] items)\n{\n    var d = new Dictionary<string, int>();\n    return d;\n}",
           solution_code="Dictionary<string, int> Agrupar(string[] items)\n{\n    var d = new Dictionary<string, int>();\n    foreach (string x in items) d[x] = d.GetValueOrDefault(x) + 1;\n    return d;\n}"),
        lc("sd-exam-two-sum", "Two Sum", "TwoSum", "Retorna los índices de los dos números que suman target.",
           [{"args": [[2, 7, 11, 15], 9], "expected": [0, 1]}],
           "int[] TwoSum(int[] nums, int target)\n{\n    // usa un Dictionary de vistos\n    return new int[0];\n}",
           solution_code="int[] TwoSum(int[] nums, int target)\n{\n    var seen = new Dictionary<int, int>();\n    for (int i = 0; i < nums.Length; i++)\n    {\n        int need = target - nums[i];\n        if (seen.ContainsKey(need)) return new[] { seen[need], i };\n        seen[nums[i]] = i;\n    }\n    return new int[0];\n}"),
    ],
    "level-se": [
        lc("se-cp-counter", "Contador con clase", "RunCounter", "Crea una clase Counter, incrementa n veces y retorna el conteo.",
           [{"args": [3], "expected": 3}, {"args": [0], "expected": 0}],
           "int RunCounter(int n)\n{\n    // crea un contador, incrementa n veces y retorna\n    return 0;\n}",
           solution_code="class Counter { public int C; public void Inc() { C++; } }\nint RunCounter(int n)\n{\n    var c = new Counter();\n    for (int i = 0; i < n; i++) c.Inc();\n    return c.C;\n}"),
        lc("se-cp-bank", "Saldo final", "FinalBalance", "Suma todos los depósitos y retorna el saldo final.",
           [{"args": [[10, 20, 5]], "expected": 35}, {"args": [[]], "expected": 0}],
           "int FinalBalance(int[] deps)\n{\n    return 0;\n}",
           solution_code="class Cuenta { public int S; public void Deposita(int n) { S += n; } }\nint FinalBalance(int[] deps)\n{\n    var c = new Cuenta();\n    foreach (int d in deps) c.Deposita(d);\n    return c.S;\n}"),
        lc("se-cp-point-str", "Punto como texto", "PointStr", "Retorna un punto como texto '(x, y)'.",
           [{"args": [1, 2], "expected": "(1, 2)"}],
           "string PointStr(int x, int y)\n{\n    return \"\";\n}",
           solution_code="class Punto { public int X; public int Y; public Punto(int x, int y) { X = x; Y = y; } public override string ToString() => $\"({X}, {Y})\"; }\nstring PointStr(int x, int y) => new Punto(x, y).ToString();"),
        lc("se-cp-shape-area", "Área por herencia", "SquareArea", "Define Shape base y Square que sobrescribe Area(); retorna el área.",
           [{"args": [4], "expected": 16}, {"args": [3], "expected": 9}],
           "int SquareArea(int side)\n{\n    return 0;\n}",
           solution_code="class Shape { public virtual int Area() => 0; }\nclass Square : Shape { public int L; public Square(int l) { L = l; } public override int Area() => L * L; }\nint SquareArea(int side) => new Square(side).Area();"),
        lc("se-exam-stack", "Pila (Stack)", "StackTop", "Crea una pila con Push; aplica los valores y retorna el tope.",
           [{"args": [[1, 2, 3]], "expected": 3}, {"args": [[5]], "expected": 5}],
           "int StackTop(int[] valores)\n{\n    return 0;\n}",
           solution_code="class Stack { public List<int> Data = new(); public void Push(int x) { Data.Add(x); } public int Top() => Data[Data.Count - 1]; }\nint StackTop(int[] valores)\n{\n    var s = new Stack();\n    foreach (int v in valores) s.Push(v);\n    return s.Top();\n}"),
        lc("se-exam-shapes", "Suma de áreas (polimorfismo)", "TotalArea", "Dada una lista de lados de cuadrados, suma sus áreas.",
           [{"args": [[2, 3]], "expected": 13}, {"args": [[1, 1, 1]], "expected": 3}],
           "int TotalArea(int[] lados)\n{\n    return 0;\n}",
           solution_code="class Cuadrado { public int L; public Cuadrado(int l) { L = l; } public int Area() => L * L; }\nint TotalArea(int[] lados) => lados.Select(l => new Cuadrado(l).Area()).Sum();"),
    ],
}


def generate_leetcode(levels: list[str] | None = None) -> int:
    count = 0
    for level, probs in CSHARP_LEETCODE.items():
        lvl_letter = level.replace("level-", "").upper()
        if levels and lvl_letter not in levels:
            continue
        for p in probs:
            write_yaml(CONTENT / level / "leetcode" / f"{p['id']}.yaml", p)
            count += 1
    return count


# ---------------------------------------------------------------------------
# Interview questions
# ---------------------------------------------------------------------------

CSHARP_INTERVIEW = {
    "level-sa": [
        {"id": "sa-int-1",
         "question": "¿Cuál es la diferencia entre int y string en C#? Da un ejemplo de cada uno.",
         "rubric": ["int representa números enteros", "string representa texto entre comillas dobles", "se convierten con int.Parse / .ToString()"],
         "sample_answer": "Un int es un número entero (ej. 42) con el que puedes hacer aritmética; un string es texto entre comillas dobles (ej. \"42\"). Conviertes con int.Parse(\"42\") o 42.ToString()."},
        {"id": "sa-int-2",
         "question": "¿Qué es la interpolación de strings ($\"\") en C# y por qué es útil? Muestra un ejemplo.",
         "rubric": ["inserta variables/expresiones dentro del texto", "sintaxis $\"...{var}...\"", "más legible que concatenar con +"],
         "sample_answer": "La interpolación inserta el valor de variables o expresiones dentro de un texto: $\"{nombre} tiene {edad} anios\". Es más legible que concatenar con +."},
    ],
    "level-sb": [
        {"id": "sb-int-1",
         "question": "¿Cuál es la diferencia entre un bucle for y un bucle while en C#? ¿Cuándo usarías cada uno?",
         "rubric": ["for cuando conoces el número de iteraciones", "while cuando dependes de una condición", "for combina init/condición/incremento"],
         "sample_answer": "El for reúne inicialización, condición e incremento en una línea y es ideal cuando sabes cuántas veces iterar. El while repite mientras una condición sea verdadera, útil cuando no conoces el número de vueltas de antemano."},
        {"id": "sb-int-2",
         "question": "¿Qué hacen break y continue dentro de un bucle? Da un ejemplo de cada uno.",
         "rubric": ["break termina el bucle", "continue salta a la siguiente iteración", "ejemplos concretos"],
         "sample_answer": "break sale por completo del bucle (ej. al encontrar un valor). continue omite el resto de la iteración actual y pasa a la siguiente (ej. saltar números pares)."},
    ],
    "level-sc": [
        {"id": "sc-int-1",
         "question": "¿Qué es LINQ en C# y para qué sirve? Menciona métodos como Where, Select y Sum.",
         "rubric": ["consultas sobre colecciones", "Where filtra, Select transforma, Sum agrega", "estilo declarativo"],
         "sample_answer": "LINQ permite consultar colecciones de forma declarativa: Where filtra elementos, Select los transforma y Sum/Count/Max agregan. Ej: nums.Where(n => n % 2 == 0).Sum()."},
        {"id": "sc-int-2",
         "question": "¿Cuál es la diferencia entre un array (int[]) y una List<int> en C#?",
         "rubric": ["array tamaño fijo", "List redimensionable con Add/Remove", "elegir según necesidad"],
         "sample_answer": "Un array tiene tamaño fijo al crearse; una List<int> crece y encoge dinámicamente con Add/Remove. Usa array si el tamaño es fijo y List si necesitas modificar la colección."},
    ],
    "level-sd": [
        {"id": "sd-int-1",
         "question": "¿Qué es un Dictionary<TKey, TValue> en C# y cuándo lo usarías?",
         "rubric": ["mapea claves a valores", "búsqueda rápida por clave", "claves únicas"],
         "sample_answer": "Un Dictionary asocia claves únicas a valores y permite búsquedas rápidas por clave. Se usa para conteos de frecuencia, cachés o cualquier mapeo clave->valor."},
        {"id": "sd-int-2",
         "question": "¿Cómo manejas errores en C# con try/catch? ¿Por qué es útil?",
         "rubric": ["try envuelve código riesgoso", "catch captura la excepción", "evita que el programa se caiga"],
         "sample_answer": "Envuelves el código riesgoso en try y capturas la excepción en catch para manejarla sin que el programa termine abruptamente, por ejemplo una división por cero o parseo inválido."},
    ],
    "level-se": [
        {"id": "se-int-1",
         "question": "¿Qué es una clase en C# y en qué se diferencia de un objeto? Da un ejemplo.",
         "rubric": ["clase es la plantilla", "objeto es una instancia", "ejemplo con new"],
         "sample_answer": "Una clase es una plantilla que define campos y métodos; un objeto es una instancia concreta creada con new. Ej: class Perro {...} y var p = new Perro();."},
        {"id": "se-int-2",
         "question": "¿Qué es la herencia y el polimorfismo en C#? Menciona virtual y override.",
         "rubric": ["herencia reutiliza una clase base", "override redefine métodos virtual", "polimorfismo: mismo método, comportamiento distinto"],
         "sample_answer": "La herencia permite que una clase derive de otra y reutilice su código. Con virtual/override una subclase redefine un método, y el polimorfismo hace que el mismo método se comporte distinto según el tipo real del objeto."},
    ],
}


def generate_interview(levels: list[str] | None = None) -> int:
    count = 0
    for level, qs in CSHARP_INTERVIEW.items():
        lvl_letter = level.replace("level-", "").upper()
        if levels and lvl_letter not in levels:
            continue
        for q in qs:
            q = dict(q)
            q["category"] = "csharp"
            write_yaml(CONTENT / level / "interview" / f"{q['id']}.yaml", q)
            count += 1
    return count


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    global RUNNER
    parser = argparse.ArgumentParser(description="Generate the C# Kumon track.")
    parser.add_argument("--level", action="append", help="Regenerate only these levels (e.g. SA). May repeat.")
    parser.add_argument("--kumon-only", action="store_true", help="Only regenerate Kumon YAML pages.")
    args = parser.parse_args()

    targets = [lv.upper() for lv in args.level] if args.level else None

    RUNNER = Runner()
    try:
        if targets:
            for lv in targets:
                shutil.rmtree(CONTENT / f"level-{lv.lower()}", ignore_errors=True)
            print(f"Regenerating C# level(s): {', '.join(targets)}...")
            k = generate_kumon(levels=targets)
            print(f"  -> {k} Kumon pages")
            if not args.kumon_only:
                print(f"  -> {generate_leetcode(targets)} LeetCode problems")
                print(f"  -> {generate_interview(targets)} interview questions")
            return

        if CONTENT.exists():
            print("Cleaning old C# content...")
            shutil.rmtree(CONTENT)
        print("Generating C# Kumon pages...")
        k = generate_kumon()
        print(f"  -> {k} Kumon pages")
        print(f"  -> {generate_leetcode()} LeetCode problems")
        print(f"  -> {generate_interview()} interview questions")
    finally:
        RUNNER.close()


if __name__ == "__main__":
    main()
