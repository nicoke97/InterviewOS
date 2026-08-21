#!/usr/bin/env python3
"""Generate backend/app/schedule_i18n.py from Python, C#, and Odoo schedules."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEDULE_DIR = ROOT / "content" / "schedule"
YAML_PATHS = [
    SCHEDULE_DIR / "kumon-levels.yaml",
    SCHEDULE_DIR / "csharp-levels.yaml",
    SCHEDULE_DIR / "odoo-levels.yaml",
]
OUT = ROOT / "backend" / "app" / "schedule_i18n.py"

TITLE_EN: dict[str, str] = {
    "Imprimir valores": "Print values",
    "Variables y asignación": "Variables and assignment",
    "Aritmética con enteros": "Integer arithmetic",
    "f-strings básicas": "Basic f-strings",
    "Tipos y conversion": "Types and conversion",
    "Tipos y conversión": "Types and conversion",
    "Concatenación y longitud": "Concatenation and length",
    "Índices de string": "String indices",
    "Métodos básicos de string": "Basic string methods",
    "f-strings con calculo": "f-strings with calculations",
    "f-strings con cálculo": "f-strings with calculations",
    "Repeticion y formato": "Repetition and formatting",
    "Repetición y formato": "Repetition and formatting",
    "Comparaciones": "Comparisons",
    "if / else": "if / else",
    "if / elif / else": "if / elif / else",
    "Operadores lógicos": "Logical operators",
    "Condicionales anidados": "Nested conditionals",
    "Variables y f-strings (repaso)": "Variables and f-strings (review)",
    "Aritmética aplicada": "Applied arithmetic",
    "Strings y condicionales": "Strings and conditionals",
    "Condicionales combinados": "Combined conditionals",
    "Mini-retos integrados": "Integrated mini-challenges",
    "for sobre range": "for over range",
    "Suma acumulada": "Running sum",
    "range con paso": "range with step",
    "Cuenta regresiva": "Countdown",
    "Iterar strings y listas": "Iterate strings and lists",
    "while básico": "Basic while",
    "while con condición": "while with condition",
    "break": "break",
    "continue": "continue",
    "enumerate": "enumerate",
    "zip": "zip",
    "Bucles anidados": "Nested loops",
    "Patrones de bucle": "Loop patterns",
    "def y return": "def and return",
    "Parámetros múltiples": "Multiple parameters",
    "Valores por defecto": "Default values",
    "Funciones con condicionales": "Functions with conditionals",
    "Componer funciones": "Compose functions",
    "Crear e indexar listas": "Create and index lists",
    "append e insert": "append and insert",
    "Slicing básico": "Basic slicing",
    "sort y sorted": "sort and sorted",
    "List comprehension": "List comprehension",
    "Listas anidadas": "Nested lists",
    "Tuplas": "Tuples",
    "Desempaquetado": "Unpacking",
    "Comprehension con filtro": "Comprehension with filter",
    "Comprehension con transformacion": "Comprehension with transform",
    "Comprehension con transformación": "Comprehension with transform",
    "split y join": "split and join",
    "strip y replace": "strip and replace",
    "find, count, startswith": "find, count, startswith",
    "Mayúsculas y título": "Uppercase and title case",
    "format y f-strings": "format and f-strings",
    "Métodos de string": "String methods",
    "Crear y acceder": "Create and access",
    "get con default": "get with default",
    "keys, values, items": "keys, values, items",
    "Recorrer items": "Iterate items",
    "setdefault y merge": "setdefault and merge",
    "Diccionarios anidados": "Nested dictionaries",
    "dict comprehension": "dict comprehension",
    "Invertir un dict": "Invert a dict",
    "Contar frecuencias": "Count frequencies",
    "Diccionarios avanzados": "Advanced dictionaries",
    "Crear sets y unicidad": "Create sets and uniqueness",
    "add y remove": "add and remove",
    "Union e interseccion": "Union and intersection",
    "Unión e intersección": "Union and intersection",
    "Diferencia": "Difference",
    "Membership y dedupe": "Membership and dedupe",
    "Contar coincidencias": "Count matches",
    "try / except": "try / except",
    "ValueError y casting": "ValueError and casting",
    "IndexError y KeyError": "IndexError and KeyError",
    "Guard clauses y raise": "Guard clauses and raise",
    "finally y else": "finally and else",
    "Manejo de errores": "Error handling",
    "Clase y atributo": "Class and attribute",
    "__init__ con un atributo": "__init__ with one attribute",
    "__init__ con dos atributos": "__init__ with two attributes",
    "Atributos e impresion": "Attributes and printing",
    "Atributos e impresión": "Attributes and printing",
    "Metodo que usa self": "Method that uses self",
    "Método que usa self": "Method that uses self",
    "Metodo que retorna": "Method that returns",
    "Método que retorna": "Method that returns",
    "Metodo con parametro": "Method with parameter",
    "Método con parámetro": "Method with parameter",
    "Metodo que cambia estado": "Method that changes state",
    "Método que cambia estado": "Method that changes state",
    "Métodos básicos": "Basic methods",
    "Métodos": "Methods",
    "Metodos": "Methods",
    "Múltiples métodos": "Multiple methods",
    "Métodos que calculan": "Methods that compute",
    "Metodos que calculan": "Methods that compute",
    "__str__": "__str__",
    "__repr__": "__repr__",
    "Objetos y atributos": "Objects and attributes",
    "Objeto que contiene una lista": "Object containing a list",
    "Herencia básica": "Basic inheritance",
    "super().__init__": "super().__init__",
    "Override de método": "Method override",
    "Herencia": "Inheritance",
    "super() en métodos": "super() in methods",
    "Acceder atributos": "Access attributes",
    "Atributo de clase vs instancia": "Class vs instance attribute",
    "Dunder y composicion": "Dunder and composition",
    "Dunder y composición": "Dunder and composition",
    "isinstance y polimorfismo": "isinstance and polymorphism",
    "Variables y tipos": "Variables and types",
    "Strings": "Strings",
    "Operadores y condicionales": "Operators and conditionals",
    "Repaso de fundamentos": "Fundamentals review",
    "for y range": "for and range",
    "while, break y continue": "while, break and continue",
    "Funciones": "Functions",
    "Listas básicas": "Basic lists",
    "Slicing y orden": "Slicing and sorting",
    "Tuplas y comprehensions": "Tuples and comprehensions",
    "Diccionarios básicos": "Basic dictionaries",
    "Sets": "Sets",
    "Recorrer y acumular": "Iterate and accumulate",
    "Acumuladores con while": "Accumulators with while",
    "Agregar y actualizar": "Add and update",
    "Copiar listas": "Copy lists",
    "Paso e inversion": "Step and reverse",
    "Paso e inversión": "Step and reverse",
    "pop y remove": "pop and remove",
    "len, sum, min, max": "len, sum, min, max",
    "Maximo y minimo manual": "Manual max and min",
    "Máximo y mínimo manual": "Manual max and min",
    "Hashmaps O(1)": "Hashmaps O(1)",
    "Par llave → valor": "Key → value pairs",
    "Buscar por llave (in)": "Lookup by key (in)",
    "Qué va como llave": "What goes as the key",
    "Patrón seen": "The seen pattern",
    "Two Sum y variantes": "Two Sum and variants",
    "Level A — Fundamentos": "Level A — Fundamentals",
    "Level B — Bucles y funciones": "Level B — Loops and functions",
    "Level C — Listas, tuplas y strings": "Level C — Lists, tuples, and strings",
    "Level D — Diccionarios, sets y errores": "Level D — Dictionaries, sets, and errors",
    "Level E — Clases y OOP": "Level E — Classes and OOP",
    "Nivel A — Fundamentos de C#": "Level A — C# Fundamentals",
    "Nivel B — Bucles y métodos": "Level B — Loops and methods",
    "Nivel C — Colecciones y strings": "Level C — Collections and strings",
    "Nivel D — Diccionarios, sets y errores": "Level D — Dictionaries, sets, and errors",
    "Nivel E — Clases y POO": "Level E — Classes and OOP",
    "Odoo A — Registros y dominios": "Odoo A — Records and domains",
    "Odoo B — ORM y modelos": "Odoo B — ORM and models",
    "Odoo C — Flujos y soporte": "Odoo C — Workflows and support",
    "Recordsets, dominios y mapped": "Recordsets, domains, and mapped",
    "create, write, search y relaciones": "create, write, search, and relations",
    "Estados, validaciones y reportes": "States, validations, and reports",
    "Un registro como dict": "A record as a dict",
    "Recordset (lista de registros)": "Recordset (list of records)",
    "filtered: dominios": "filtered: domains",
    "mapped: extraer un campo": "mapped: extract a field",
    "Agregar y sumar campos": "Add and sum fields",
    "Definir un modelo (campos)": "Define a model (fields)",
    "create: nuevo registro": "create: new record",
    "write: actualizar registro": "write: update record",
    "search: filtrar por dominio": "search: filter by domain",
    "Relaciones many2one": "many2one relations",
    "Estados de un ticket": "Ticket states",
    "Validaciones y guard clauses": "Validations and guard clauses",
    "Prioridades y SLA (orden)": "Priorities and SLA (order)",
    "Reportes: agrupar y contar": "Reports: group and count",
    "Integrar varias fuentes": "Integrate multiple sources",
    "Dictionaries O(1)": "Dictionaries O(1)",
    "Arrays y List<T>": "Arrays and List<T>",
    "Rebanado y orden": "Slicing and sorting",
    "Tuplas y LINQ": "Tuples and LINQ",
    "Dictionary básico": "Basic Dictionary",
    "Dictionary avanzado": "Advanced Dictionary",
    "HashSet": "HashSet",
    "Objetos y propiedades": "Objects and properties",
    "ToString y composición": "ToString and composition",
    "Console.WriteLine": "Console.WriteLine",
    "Interpolación $\"\"": "Interpolation $\"\"",
    "Concatenación y Length": "Concatenation and Length",
    "Índices y Substring": "Indices and Substring",
    "Interpolación con cálculo": "Interpolation with calculations",
    "if / else if / else": "if / else if / else",
    "Variables e interpolación (repaso)": "Variables and interpolation (review)",
    "Buscar por llave (ContainsKey)": "Lookup by key (ContainsKey)",
    "for": "for",
    "for básico": "Basic for",
    "for con paso": "for with step",
    "Recorrer arrays": "Iterate arrays",
    "foreach con índice": "foreach with index",
    "Recorrer dos listas": "Iterate two lists",
    "Método con return": "Method with return",
    "Métodos con condicionales": "Methods with conditionals",
    "Componer métodos": "Compose methods",
    "Crear e indexar": "Create and index",
    "Add e Insert": "Add and Insert",
    "Count, Sum, Min, Max": "Count, Sum, Min, Max",
    "Remove y RemoveAt": "Remove and RemoveAt",
    "Take y Skip": "Take and Skip",
    "Reverse": "Reverse",
    "Sort y OrderBy": "Sort and OrderBy",
    "Desestructuración": "Deconstruction",
    "Select": "Select",
    "Where": "Where",
    "Select con transformación": "Select with transform",
    "Split y Join": "Split and Join",
    "Trim y Replace": "Trim and Replace",
    "ToUpper y Title": "ToUpper and Title",
    "IndexOf, Contains, StartsWith": "IndexOf, Contains, StartsWith",
    "Format e interpolación": "Format and interpolation",
    "TryGetValue / GetValueOrDefault": "TryGetValue / GetValueOrDefault",
    "Keys, Values": "Keys, Values",
    "Recorrer con foreach": "Iterate with foreach",
    "Agrupar": "Group",
    "Merge y default": "Merge and default",
    "Add y Remove": "Add and Remove",
    "Union e Intersect": "Union and Intersect",
    "Except (diferencia)": "Except (difference)",
    "Contains y dedupe": "Contains and dedupe",
    "try / catch": "try / catch",
    "FormatException y parseo": "FormatException and parsing",
    "IndexOutOfRange y KeyNotFound": "IndexOutOfRange and KeyNotFound",
    "finally": "finally",
    "Guard clauses y throw": "Guard clauses and throw",
    "Clase y propiedad": "Class and property",
    "Constructor con un campo": "Constructor with one field",
    "Constructor con dos campos": "Constructor with two fields",
    "Acceder propiedades": "Access properties",
    "Propiedades e impresión": "Properties and printing",
    "Método que usa this": "Method that uses this",
    "ToString()": "ToString()",
    "Propiedades calculadas": "Computed properties",
    "Campo estático vs instancia": "Static vs instance field",
    "override de método": "Method override",
    "base(...) en constructor": "base(...) in constructor",
    "base en métodos": "base in methods",
    "is y polimorfismo": "is and polymorphism",
}

TITLE_ES: dict[str, str] = {
    "Level A — Fundamentos": "Nivel A — Fundamentos",
    "Level B — Bucles y funciones": "Nivel B — Bucles y funciones",
    "Level C — Listas, tuplas y strings": "Nivel C — Listas, tuplas y strings",
    "Level D — Diccionarios, sets y errores": "Nivel D — Diccionarios, sets y errores",
    "Level E — Clases y OOP": "Nivel E — Clases y POO",
}

INSTRUCTION_EN: dict[str, str] = {
    "A.A": "Declare variables and print values. Write the code for each problem.",
    "A.B": "Work with strings. Write Python for each problem.",
    "A.C": "Use comparisons and if/elif/else. Write your code below each question.",
    "A.D": "Fundamentals review. Solve each problem in order.",
    "A.Extra": "Extra practice — hashmaps. Look up by key (x in d); store extra data as the value. Always available.",
    "B.A": "Use for loops and range(). Write code that produces the expected output.",
    "B.B": "Use while with break and continue. Solve each problem.",
    "B.C": "Apply loop patterns: enumerate, zip, and nested loops.",
    "B.D": "Write a function for each problem and call it to print the result.",
    "C.A": "Work with lists: create, index, and modify.",
    "C.B": "Use list slicing and sorting.",
    "C.C": "Use tuples and comprehensions.",
    "C.D": "Use string methods to solve each problem.",
    "D.A": "Work with dictionaries: create, access, and iterate.",
    "D.B": "Apply advanced dictionary techniques.",
    "D.C": "Use sets for uniqueness and set operations.",
    "D.D": "Handle errors with try/except and guard clauses.",
    "E.A": "Define classes and work with attributes.",
    "E.B": "Add methods to your classes.",
    "E.C": "Use dunder methods and object composition.",
    "E.D": "Apply inheritance and polymorphism.",
    "SA.A": "Declare variables and print values with Console.WriteLine. Write the code for each problem.",
    "SA.B": "Work with strings. Write C# for each problem.",
    "SA.C": "Use comparisons and if/else if/else. Write your code below each question.",
    "SA.D": "Fundamentals review. Solve each problem in order.",
    "SA.Extra": "Extra practice — Dictionary. Look up by key (ContainsKey); store extra data as the value. Always available.",
    "SB.A": "Use for loops. Write code that produces the expected output.",
    "SB.B": "Use while with break and continue. Solve each problem.",
    "SB.C": "Apply loop patterns: indexes, two lists, and nested loops.",
    "SB.D": "Write a method for each problem and call it to print the result.",
    "SC.A": "Work with arrays and List<T>: create, index, and modify.",
    "SC.B": "Use Take/Skip, Reverse, and sorting.",
    "SC.C": "Use tuples and LINQ (Select, Where).",
    "SC.D": "Use string methods to solve each problem.",
    "SD.A": "Work with Dictionary: create, access, and iterate.",
    "SD.B": "Apply advanced Dictionary techniques.",
    "SD.C": "Use HashSet for uniqueness and set operations.",
    "SD.D": "Handle errors with try/catch and guard clauses.",
    "SE.A": "Define classes and work with properties.",
    "SE.B": "Add methods to your classes.",
    "SE.C": "Use ToString() and object composition.",
    "SE.D": "Apply inheritance and polymorphism.",
    "OA.A": "Work with Odoo records represented as dictionaries and lists (recordsets).",
    "OB.A": "Simulate the Odoo ORM: create, write, and search on a list of records.",
    "OC.A": "Model support workflows: states, validations, priorities, and reports.",
}

DEFAULT_INSTRUCTION_EN = "Solve each problem. Review all your answers when finished."


def collect_schedule_titles() -> set[str]:
    titles: set[str] = set()
    for path in YAML_PATHS:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for ld in (data.get("levels") or {}).values():
            if ld.get("title"):
                titles.add(ld["title"])
            for bd in (ld.get("blocks") or {}).values():
                if bd.get("title"):
                    titles.add(bd["title"])
                for s in bd.get("sets") or []:
                    if s.get("title"):
                        titles.add(s["title"])
    return titles


def main() -> None:
    missing = sorted(collect_schedule_titles() - set(TITLE_EN))
    if missing:
        raise SystemExit(f"Missing EN titles: {missing}")

    body = f'''"""Schedule title and block instruction localization."""
from __future__ import annotations

TITLE_EN: dict[str, str] = {json.dumps(TITLE_EN, ensure_ascii=False, indent=4)}

TITLE_ES: dict[str, str] = {json.dumps(TITLE_ES, ensure_ascii=False, indent=4)}

INSTRUCTION_EN: dict[str, str] = {json.dumps(INSTRUCTION_EN, ensure_ascii=False, indent=4)}

DEFAULT_INSTRUCTION_EN = {json.dumps(DEFAULT_INSTRUCTION_EN)}


def localize_title(title: str, locale: str = "en") -> str:
    if locale == "es":
        return TITLE_ES.get(title, title)
    return TITLE_EN.get(title, title)


def localize_instruction(bid: str, instruction: str, locale: str = "en") -> str:
    if locale == "es":
        return instruction
    return INSTRUCTION_EN.get(bid, DEFAULT_INSTRUCTION_EN)
'''
    OUT.write_text(body, encoding="utf-8")
    print(f"Wrote {OUT} ({len(TITLE_EN)} titles, {len(INSTRUCTION_EN)} instructions)")


if __name__ == "__main__":
    main()
