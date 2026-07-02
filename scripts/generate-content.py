#!/usr/bin/env python3
"""Generate Kumon pages (Levels A-E, 200 each), LeetCode checkpoints/exams and
interview questions for the Python track.

Model: each level = 4 blocks x 50 pages = 20 sets x 10 pages. Each *set* drills
ONE micro-skill with 10 incremental variations. Scaffolding ramps down inside
the set (full -> minimal -> none). The expected stdout for every drill is
computed by actually executing the reference solution, so content can't drift
out of sync with its answers.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import re
import shutil
from pathlib import Path

import yaml

from kumon_starters import safe_starter

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "levels"
PAGES_PER_SET = 10
STD_PATH = ROOT / "content" / "schedule" / "kumon-levels.yaml"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def run_capture(code: str) -> str:
    """Execute a reference solution and capture its stdout."""
    buf = io.StringIO()
    g: dict = {}
    with contextlib.redirect_stdout(buf):
        exec(compile(code, "<drill>", "exec"), g)  # noqa: S102 (trusted content)
    return buf.getvalue().rstrip("\n")


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
# LEVEL A — Fundamentos
# ---------------------------------------------------------------------------

def level_a() -> list[list[dict]]:
    sets: list[list[dict]] = []

    # A.A — Variables y tipos
    sets.append(mapped(
        lambda v: f"Imprime exactamente el texto: {v}",
        lambda v: f"print({v!r})",
        ["Hola, mundo", "Python", "Odoo", "Codenda", "Bienvenido",
         "Aprendiendo", "Listo", "Codigo", "Practica", "Avanzando"],
    ))
    sets.append(mapped(
        lambda t: f"Crea la variable {t[0]} con el valor '{t[1]}' e imprime la variable.",
        lambda t: f"{t[0]} = {t[1]!r}\nprint({t[0]})",
        [("ciudad", "Lima"), ("pais", "Peru"), ("color", "azul"), ("animal", "gato"),
         ("fruta", "mango"), ("lenguaje", "Python"), ("equipo", "Odoo"), ("mes", "enero"),
         ("dia", "lunes"), ("plato", "ceviche")],
    ))
    _arith_notes = {
        "20 // 3": " (division entera, sin decimales)",
        "20 % 3": " (resto de la division)",
        "2 ** 5": " (potencia)",
    }
    sets.append(mapped(
        lambda e: f"Calcula e imprime el resultado de {e}{_arith_notes.get(e, '')}",
        lambda e: f"print({e})",
        ["7 + 5", "20 // 3", "20 % 3", "10 - 3", "4 * 6", "2 ** 5",
         "8 + 9", "15 - 7", "3 * 9", "100 // 7"],
    ))
    sets.append(explicit([
        (
            "Asigna name='Ana' y age=22. Usa f-string para presentarla "
            "(formato: nombre tiene edad años).",
            "name = 'Ana'\nage = 22\nprint(f'{name} tiene {age} años')",
        ),
        (
            "Asigna city='Lima' y country='Perú'. Imprime la ubicación con f-string "
            "(formato: ciudad, país).",
            "city = 'Lima'\ncountry = 'Perú'\nprint(f'{city}, {country}')",
        ),
        (
            "Asigna producto='Libro' y precio=25. Con f-string muestra qué producto es "
            "y cuánto cuesta (formato: producto cuesta precio).",
            "producto = 'Libro'\nprecio = 25\nprint(f'{producto} cuesta {precio}')",
        ),
        (
            "Asigna lenguaje='Python' y anio=1991. Imprime con f-string en qué año "
            "apareció (formato: lenguaje nació en anio).",
            "lenguaje = 'Python'\nanio = 1991\nprint(f'{lenguaje} nació en {anio}')",
        ),
        (
            "Asigna animal='gato' y sonido='miau'. Usa f-string para describir el animal "
            "(formato: El animal dice sonido).",
            "animal = 'gato'\nsonido = 'miau'\nprint(f'El {animal} dice {sonido}')",
        ),
        (
            "Asigna equipo='Odoo' e integrantes=5. Imprime con f-string cuántas personas "
            "hay en el equipo (formato: equipo tiene N integrantes).",
            "equipo = 'Odoo'\nintegrantes = 5\nprint(f'{equipo} tiene {integrantes} integrantes')",
        ),
        (
            "Con a=4 y b=6, calcula la suma en una variable y usa f-string "
            "(formato: Suma: resultado).",
            "a = 4\nb = 6\ntotal = a + b\nprint(f'Suma: {total}')",
        ),
        (
            "Con nombre='Mia', saluda con f-string (formato: Hola, nombre).",
            "nombre = 'Mia'\nprint(f'Hola, {nombre}')",
        ),
        (
            "Asigna color='azul' y objeto='cielo'. Describe con f-string "
            "(formato: El objeto es color).",
            "color = 'azul'\nobjeto = 'cielo'\nprint(f'El {objeto} es {color}')",
        ),
        (
            "Presenta a Pablo, 29 años, con f-string (formato: nombre tiene edad años). "
            "Crea las variables que necesites.",
            "name = 'Pablo'\nage = 29\nprint(f'{name} tiene {age} años')",
        ),
    ]))
    sets.append(explicit([
        drill("Convierte '5' a entero con int() y sumale 3", "print(int('5') + 3)",
              hint="int(texto) convierte texto a entero. Imprime el resultado con print()."),
        drill("Imprime el booleano de bool(1)", "print(bool(1))",
              hint="bool(valor) convierte un valor a True o False. Imprime con print()."),
        drill("Convierte el numero 42 a texto con str() y agrega '!'", "print(str(42) + '!')",
              hint="str(numero) convierte un numero a texto."),
        drill("Convierte '2.5' a flotante con float() y sumale 0.5", "print(float('2.5') + 0.5)",
              hint="float(texto) convierte texto a numero decimal."),
        ("Convierte 3.9 a entero (trunca los decimales)", "print(int(3.9))"),
        ("Imprime el booleano de bool(0)", "print(bool(0))"),
        drill("Redondea 3.14159 a 2 decimales con round()", "print(round(3.14159, 2))",
              hint="round(numero, decimales) redondea un flotante. Imprime con print()."),
        ("Suma int('12') + int('8')", "print(int('12') + int('8'))"),
        ("Convierte '100' a entero y dividelo entre 4 (division entera)", "print(int('100') // 4)"),
        ("Convierte True a entero con int() y sumale 1", "print(int(True) + 1)"),
    ]))

    # A.B — Strings
    sets.append(explicit([
        ("Une las palabras 'Hola' y 'mundo' con un espacio e imprime el resultado.",
         "a = 'Hola'\nb = 'mundo'\nprint(a + ' ' + b)"),
        ("Une las palabras 'buen' y 'dia' con un espacio e imprime el resultado.",
         "a = 'buen'\nb = 'dia'\nprint(a + ' ' + b)"),
        ("Une las palabras 'Odoo' y 'ERP' con un espacio e imprime el resultado.",
         "a = 'Odoo'\nb = 'ERP'\nprint(a + ' ' + b)"),
        ("Une las palabras 'Python' y 'rocks' con un espacio e imprime el resultado.",
         "a = 'Python'\nb = 'rocks'\nprint(a + ' ' + b)"),
        ("Une las palabras 'hasta' y 'luego' con un espacio e imprime el resultado.",
         "a = 'hasta'\nb = 'luego'\nprint(a + ' ' + b)"),
        drill("Dada s='interview', imprime cuantos caracteres tiene con len()",
              "s = 'interview'\nprint(len(s))",
              hint="len(texto) devuelve cuantos caracteres tiene una cadena."),
        ("Dada s='odoo', imprime la longitud de s", "s = 'odoo'\nprint(len(s))"),
        ("Une 'muy' y 'bien' con espacio e imprime la longitud del resultado",
         "a = 'muy'\nb = 'bien'\nprint(len(a + ' ' + b))"),
        ("Dada palabra='python', imprime len(palabra)", "palabra = 'python'\nprint(len(palabra))"),
        ("Dada frase='buen dia', imprime cuantos caracteres tiene (incluye el espacio)",
         "frase = 'buen dia'\nprint(len(frase))"),
    ]))
    sets.append(explicit([
        drill("Dada s='python', imprime el primer caracter con s[0]",
              "s = 'python'\nprint(s[0])",
              hint="s[0] es el primer caracter; s[-1] es el ultimo."),
        drill("Dada s='odoo', imprime el ultimo caracter con s[-1]",
              "s = 'odoo'\nprint(s[-1])",
              hint="Los indices negativos cuentan desde el final: s[-1] es el ultimo."),
        ("Dada s='kumon', imprime el primer y ultimo caracter separados por un guion",
         "s = 'kumon'\nprint(s[0] + '-' + s[-1])"),
        drill("Dada s='python', imprime los primeros 3 caracteres con s[:3]",
              "s = 'python'\nprint(s[:3])",
              hint="s[inicio:fin] extrae una parte del texto; s[:3] toma los primeros 3."),
        drill("Dada s='abc', invierte el texto con s[::-1]",
              "s = 'abc'\nprint(s[::-1])",
              hint="s[::-1] invierte el texto completo."),
    ] + [
        drill(f"Dada s={w!r}, imprime el primer y ultimo caracter separados por un guion.",
              f"s = {w!r}\nprint(s[0] + '-' + s[-1])")
        for w in ["variable", "funcion", "objeto", "cadena", "entero"]
    ]))
    sets.append(explicit([
        drill("Imprime 'hola' en mayusculas con .upper()", "print('hola'.upper())",
              hint="Los metodos de string van despues del punto: texto.upper()."),
        drill("Imprime 'PYTHON' en minusculas con .lower()", "print('PYTHON'.lower())",
              hint="texto.lower() convierte todas las letras a minusculas."),
        drill("Capitaliza 'odoo developer' con .capitalize()", "print('odoo developer'.capitalize())",
              hint=".capitalize() pone en mayuscula solo la primera letra."),
        ("Pon en formato titulo 'soporte tecnico' con .title()", "print('soporte tecnico'.title())"),
        ("Quita espacios de '  hola  ' con .strip()", "print('  hola  '.strip())"),
        ("Reemplaza 'l' por 'L' en 'hello' con .replace()", "print('hello'.replace('l', 'L'))"),
        ("Cuenta cuantas 'a' hay en 'banana' con .count()", "print('banana'.count('a'))"),
        ("Verifica si 'python' empieza con 'py' (.startswith)", "print('python'.startswith('py'))"),
        drill("Dado s='hola mundo', divide en palabras con .split() e imprime cuantas hay",
              "s = 'hola mundo'\nprint(len(s.split()))",
              hint=".split() divide un texto en palabras usando espacios."),
        ("Dado s='ana perez', imprime la primera palabra con .split()[0]",
         "s = 'ana perez'\nprint(s.split()[0])"),
    ]))
    sets.append(mapped(
        lambda t: f"Declara a={t[0]} y b={t[1]}, luego imprime: 'La suma de {t[0]} y {t[1]} es {t[0]+t[1]}'",
        lambda t: f"a = {t[0]}\nb = {t[1]}\nprint(f'La suma de {{a}} y {{b}} es {{a + b}}')",
        [(2, 3), (10, 5), (7, 8), (12, 4), (9, 1), (6, 6), (15, 5), (20, 13), (3, 19), (11, 7)],
    ))
    sets.append(explicit([
        drill("Repite el texto 'ab' 4 veces con el operador *", "print('ab' * 4)",
              hint="texto * n repite el texto n veces."),
        drill("Repite 'o' 5 veces", "print('o' * 5)",
              hint="texto * n repite el texto n veces."),
        ("Con n=3, imprime 'o' repetido (n+1) veces", "n = 3\nprint('o' * (n + 1))"),
        drill("Imprime el numero 3.5 con 1 decimal usando f-string (formato: 3.5)",
              "x = 3.5\nprint(f'{x:.1f}')",
              hint="En f-strings, {x:.1f} muestra un decimal."),
        drill("Imprime 42 con 3 digitos rellenando ceros (formato: 042)", "print(f'{42:03d}')",
              hint="{numero:03d} rellena con ceros hasta 3 digitos."),
        drill("Rellena '5' a 4 caracteres con ceros a la izquierda usando .zfill(4)",
              "print('5'.zfill(4))",
              hint=".zfill(n) rellena con ceros a la izquierda hasta n caracteres."),
        ("Imprime 'Total: $1500' usando monto=1500 (formato exacto)",
         "monto = 1500\nprint(f'Total: ${monto}')"),
        drill("Centra 'ok' en 6 caracteres con guiones usando .center(6, '-')",
              "print('ok'.center(6, '-'))",
              hint=".center(ancho, relleno) centra el texto rellenando a los lados."),
        drill("Une 'rojo', 'verde', 'azul' con ', ' usando .join (formato: rojo, verde, azul)",
              "print(', '.join(['rojo', 'verde', 'azul']))",
              hint="', '.join(lista) une palabras separadas por comas."),
        drill("Imprime monto=1234.5 como '$1,234.50' con f-string",
              "monto = 1234.5\nprint(f'${monto:,.2f}')",
              hint="{monto:,.2f} formatea con comas y dos decimales."),
    ]))

    # A.C — Operadores y condicionales
    sets.append(mapped(
        lambda e: (
            f"Imprime el resultado (True/False) de: {e}"
            + (" (comparacion encadenada)" if e == "3 < 5 < 9" else "")
        ),
        lambda e: f"print({e})",
        ["7 > 3", "3 < 5 < 9", "5 == 5", "10 < 2", "8 >= 8", "4 != 4",
         "100 > 99", "bool(0) == False", "7 % 2 == 1", "15 <= 10"],
    ))
    sets.append(mapped(
        lambda n: f"Dado n={n}, imprime 'par' si es par o 'impar' si es impar.",
        lambda n: f"n = {n}\nif n % 2 == 0:\n    print('par')\nelse:\n    print('impar')",
        [4, 7, 10, 3, 0, 15, 22, 9, 100, 1],
    ))
    sets.append(mapped(
        lambda s: f"Dado score={s}, imprime la letra: >=90 'A', >=80 'B', >=70 'C', si no 'F'.",
        lambda s: (f"score = {s}\n"
                   "if score >= 90:\n    print('A')\n"
                   "elif score >= 80:\n    print('B')\n"
                   "elif score >= 70:\n    print('C')\n"
                   "else:\n    print('F')"),
        [95, 85, 75, 60, 90, 80, 70, 99, 64, 88],
    ))
    sets.append(explicit([
        drill("Dado a=5, b=3: imprime True si AMBOS son positivos (usa and)",
              "a, b = 5, 3\nprint(a > 0 and b > 0)",
              hint="and exige que las dos condiciones sean True."),
        drill("Dado a=-1, b=4: imprime True si ALGUNO es positivo (usa or)",
              "a, b = -1, 4\nprint(a > 0 or b > 0)",
              hint="or es True si al menos una condicion lo es."),
        drill("Dado letra='a', imprime True si la letra esta en 'aeiou' (usa in)",
              "letra = 'a'\nprint(letra in 'aeiou')",
              hint="x in texto comprueba si x aparece dentro del texto."),
        ("Dado activo=False: imprime el valor de not activo", "activo = False\nprint(not activo)"),
        ("Dado edad=20: imprime True si edad>=18 and edad<65", "edad = 20\nprint(edad >= 18 and edad < 65)"),
        ("Dado x=0: imprime True si x==0 or x>100", "x = 0\nprint(x == 0 or x > 100)"),
        ("Dado dia='sabado': imprime True si es sabado o domingo", "dia = 'sabado'\nprint(dia == 'sabado' or dia == 'domingo')"),
        ("Dado n=12: imprime True si es divisible por 3 Y por 4", "n = 12\nprint(n % 3 == 0 and n % 4 == 0)"),
        ("Dado temp=30: imprime True si NO (temp<10 o temp>40)", "temp = 30\nprint(not (temp < 10 or temp > 40))"),
        ("Dado saldo=0: imprime True si saldo es igual a 0", "saldo = 0\nprint(saldo == 0)"),
    ]))

    def _nested_fizzbuzz(n: int) -> str:
        return (
            f"n = {n}\n"
            "if n % 3 == 0:\n"
            "    if n % 5 == 0:\n"
            "        print('FizzBuzz')\n"
            "    else:\n"
            "        print('Fizz')\n"
            "elif n % 5 == 0:\n"
            "    print('Buzz')\n"
            "else:\n"
            "    print(n)"
        )

    sets.append(explicit([
        drill(
            "Dado n=3: si es multiplo de 3 imprime 'Fizz', si no el numero (usa if anidado)",
            _nested_fizzbuzz(3),
            hint="Anida un if dentro de otro para combinar condiciones.",
        ),
        drill(
            "Dado n=5: aplica FizzBuzz con if anidado (multiplo de 3, de 5, o el numero)",
            _nested_fizzbuzz(5),
            hint="Primero verifica multiplo de 3; dentro, verifica multiplo de 5.",
        ),
        drill(
            "Dado n=15: aplica FizzBuzz con if anidado",
            _nested_fizzbuzz(15),
            hint="15 es multiplo de 3 y de 5, asi que imprime 'FizzBuzz'.",
        ),
    ] + [
        drill(
            f"Dado n={n}: aplica FizzBuzz con if anidado",
            _nested_fizzbuzz(n),
        )
        for n in [7, 9, 10, 30, 11, 45, 8]
    ]))

    # A.D — Repaso de fundamentos
    sets.append(mapped(
        lambda t: f"Declara producto={t[0]!r} y precio={t[1]}, imprime: '{t[0]} cuesta {t[1]}'",
        lambda t: f"producto = {t[0]!r}\nprecio = {t[1]}\nprint(f'{{producto}} cuesta {{precio}}')",
        [("Libro", 25), ("Mouse", 15), ("Teclado", 45), ("Monitor", 300), ("Cable", 8),
         ("Silla", 120), ("Lampara", 33), ("Taza", 12), ("Cuaderno", 6), ("Mochila", 80)],
    ))
    sets.append(explicit([
        ("Calcula el area de un rectangulo base=8, altura=5", "base, altura = 8, 5\nprint(base * altura)"),
        ("Calcula el promedio de 10, 20 y 30", "print((10 + 20 + 30) / 3)"),
        ("Convierte 100 cm a metros (divide entre 100)", "print(100 / 100)"),
        ("Calcula el 20% de 250", "print(250 * 0.20)"),
        ("Calcula el perimetro de un cuadrado de lado 7", "lado = 7\nprint(lado * 4)"),
        ("Suma 3 horas + 45 min en minutos (3*60+45)", "print(3 * 60 + 45)"),
        ("Calcula cuantos minutos hay en 2.5 horas (resultado puede ser decimal)",
         "print(2.5 * 60)"),
        ("Calcula el total de 3 articulos de 19.99 cada uno", "print(round(3 * 19.99, 2))"),
        ("Calcula el cambio de pagar 50 por algo de 32", "print(50 - 32)"),
        ("Calcula el area de un circulo r=2 (usa 3.1416, redondea a 4 decimales)",
         "r = 2\nprint(round(3.1416 * r ** 2, 4))"),
    ]))
    sets.append(mapped(
        lambda w: f"Dado nombre={w!r}: imprime '{w} (corto)' si tiene menos de 5 letras, si no '{w} (largo)'.",
        lambda w: (f"nombre = {w!r}\n"
                   "if len(nombre) < 5:\n    print(f'{nombre} (corto)')\n"
                   "else:\n    print(f'{nombre} (largo)')"),
        ["Ana", "Carlos", "Ivan", "Sebastian", "Leo", "Valentina", "Sara", "Maximiliano", "Noa", "Gabriela"],
    ))
    sets.append(explicit([
        ("Dado num=7: usa if/elif/else para imprimir 'positivo', 'negativo' o 'cero'",
         "num = 7\nif num > 0:\n    print('positivo')\nelif num < 0:\n    print('negativo')\nelse:\n    print('cero')"),
        ("Dado edad=16: usa if/else para imprimir 'menor' o 'adulto'",
         "edad = 16\nif edad < 18:\n    print('menor')\nelse:\n    print('adulto')"),
        ("Dado nota=70: imprime 'aprobado' si nota>=61, si no 'reprobado'",
         "nota = 70\nif nota >= 61:\n    print('aprobado')\nelse:\n    print('reprobado')"),
        ("Dado total=120: si total>100 imprime total con 10% descuento, si no el total",
         "total = 120\nif total > 100:\n    print(total * 0.9)\nelse:\n    print(total)"),
        ("Dado hora=14: imprime 'tarde' si 12<=hora<19, si no 'otro'",
         "hora = 14\nif 12 <= hora < 19:\n    print('tarde')\nelse:\n    print('otro')"),
        ("Dado a=10,b=10: imprime 'iguales' o 'distintos'",
         "a, b = 10, 10\nif a == b:\n    print('iguales')\nelse:\n    print('distintos')"),
        ("Dado pwd='abc12': True si len>=5 AND contiene el digito '1'",
         "pwd = 'abc12'\nprint(len(pwd) >= 5 and '1' in pwd)"),
        ("Dado temp=38: imprime 'fiebre' si temp>=37.5, si no 'normal'",
         "temp = 38\nif temp >= 37.5:\n    print('fiebre')\nelse:\n    print('normal')"),
        ("Dado dia='domingo': True si es sabado o domingo",
         "dia = 'domingo'\nprint(dia == 'sabado' or dia == 'domingo')"),
        ("Dado n=12: True si es divisible por 3 y por 4",
         "n = 12\nprint(n % 3 == 0 and n % 4 == 0)"),
    ]))
    sets.append(explicit([
        ("Imprime '2 4 6 8 10' (numeros pares del 1 al 10, separados por espacio)",
         "print('2 4 6 8 10')"),
        ("Dado precio=80, calcula precio con IVA 16% redondeado a 2 decimales",
         "precio = 80\nprint(round(precio * 1.16, 2))"),
        ("Dado s='Hola Mundo', imprime cuantas palabras tiene con .split()",
         "s = 'Hola Mundo'\nprint(len(s.split()))"),
        ("Dado n=5: imprime 'n es 5 y es impar' usando f-string e if/else",
         "n = 5\nif n % 2 == 0:\n    tipo = 'par'\nelse:\n    tipo = 'impar'\nprint(f'n es {n} y es {tipo}')"),
        ("Dado celsius=25: convierte a Fahrenheit (c*9/5+32)", "c = 25\nprint(c * 9 / 5 + 32)"),
        ("Calcula el promedio de las notas 80, 90 y 70 sin usar listas",
         "print((80 + 90 + 70) / 3)"),
        ("Dado nombre='ana perez', imprime 'AP' (iniciales en mayuscula con .split())",
         "nombre = 'ana perez'\nparts = nombre.split()\nprint(parts[0][0].upper() + parts[1][0].upper())"),
        ("Dado monto=1234.5: imprime con formato '$1,234.50'",
         "monto = 1234.5\nprint(f'${monto:,.2f}')"),
        ("Dado n=3: imprime 'oooo' (n+1 letras o)", "n = 3\nprint('o' * (n + 1))"),
        ("Dado edad=30: imprime 'Tienes 30 anios' o 'Tienes 1 anio' segun corresponda",
         "edad = 30\nprint(f'Tienes {edad} anio' + ('' if edad == 1 else 's'))"),
    ]))

    sets.extend(level_a_extra_hashmaps())
    return sets


def level_a_extra_hashmaps() -> list[list[dict]]:
    """Block Extra — hashmaps O(1), always-available practice (sets 21–25)."""
    sets: list[list[dict]] = []

    # Extra.1 — par llave → valor
    sets.append(explicit([
        (
            "Crea un diccionario llamado d donde la clave 2 guarda el valor 0. Imprime el valor asociado a la clave 2.",
            "d = {2: 0}\nprint(d[2])",
        ),
        (
            "Crea un diccionario donde la clave 7 guarda el texto 'Marco'. Imprime lo que hay guardado bajo la clave 7.",
            "d = {7: 'Marco'}\nprint(d[7])",
        ),
        (
            "Crea un diccionario vacio llamado seen. Guarda en la clave 5 el valor 3. Imprime el valor de la clave 5.",
            "seen = {}\nseen[5] = 3\nprint(seen[5])",
        ),
        (
            "Crea un diccionario vacio llamado seen. Registra que el numero 10 aparecio en el indice 4 "
            "(el numero es la clave, el indice es el valor). Imprime el diccionario completo.",
            "seen = {}\nseen[10] = 4\nprint(seen)",
        ),
        (
            "Tienes un diccionario seen que mapea numeros a indices: el 2 esta en el indice 0 y el 7 en el 1. "
            "Imprime en que indice viste el 2.",
            "seen = {2: 0, 7: 1}\nprint(seen[2])",
        ),
        (
            "Mismo diccionario: el 2 esta en el indice 0 y el 7 en el 1. Imprime en que indice viste el 7.",
            "seen = {2: 0, 7: 1}\nprint(seen[7])",
        ),
        (
            "Crea un diccionario vacio. Primero guarda 14 bajo la clave 7, luego sobrescribe esa misma clave "
            "con el texto 'Marco'. Imprime el diccionario (debe quedar una sola entrada).",
            "seen = {}\nseen[7] = 14\nseen[7] = 'Marco'\nprint(seen)",
        ),
        (
            "Si escribes un diccionario con la clave 7 dos veces (primero valor 14, luego 'Marco'), "
            "cuantas claves distintas quedan? Imprime ese numero.",
            "print(len({7: 14, 7: 'Marco'}))",
        ),
        (
            "Tienes seen con el 3 en el indice 0 y el 5 en el indice 1. "
            "Imprime ambos indices separados por un espacio.",
            "seen = {3: 0, 5: 1}\nprint(seen[3], seen[5])",
        ),
        (
            "Tienes un diccionario d con 'a' -> 1 y 'b' -> 2. Imprime la suma de ambos valores.",
            "d = {'a': 1, 'b': 2}\nprint(d['a'] + d['b'])",
        ),
    ]))

    # Extra.2 — buscar por llave (in)
    sets.append(explicit([
        (
            "Tienes el diccionario {'a': 1, 'b': 2}. Imprime True o False segun si 'a' es una de sus claves.",
            "print('a' in {'a': 1, 'b': 2})",
        ),
        (
            "Tienes el diccionario {1: 99, 2: 88}. Imprime True o False segun si 99 es una clave "
            "(ojo: 99 es un valor, no una clave).",
            "print(99 in {1: 99, 2: 88})",
        ),
        (
            "Tienes el diccionario {0: 2, 1: 7} (indices como claves, numeros como valores). "
            "Imprime True o False segun si 2 es una clave.",
            "print(2 in {0: 2, 1: 7})",
        ),
        (
            "Mismo diccionario {0: 2, 1: 7}. Ahora imprime True o False segun si 2 aparece entre los valores.",
            "d = {0: 2, 1: 7}\nprint(2 in d.values())",
        ),
        (
            "Tienes seen = {2: 0} y necesitas el numero 2. Imprime True o False segun si ese numero "
            "ya esta registrado como clave.",
            "seen = {2: 0}\nneed = 2\nprint(need in seen)",
        ),
        (
            "Tienes seen = {2: 0} y necesitas el numero 7. Imprime True o False segun si ese numero "
            "ya esta registrado como clave.",
            "seen = {2: 0}\nneed = 7\nprint(need in seen)",
        ),
        (
            "Tienes seen = {4: 1} y need = 4. Si need ya esta en seen, imprime el valor guardado para esa clave.",
            "seen = {4: 1}\nneed = 4\nif need in seen:\n    print(seen[need])",
        ),
        (
            "Tienes el diccionario {5: 'x', 9: 'y'}. Imprime True o False segun si 5 es una clave.",
            "print(5 in {5: 'x', 9: 'y'})",
        ),
        (
            "Tienes el diccionario {'a': 1}. Imprime True o False segun si 'z' es una clave.",
            "print('z' in {'a': 1})",
        ),
        (
            "Tienes el diccionario {3: 10}. En dos lineas, imprime: (1) si 3 es clave, (2) si 10 es clave.",
            "d = {3: 10}\nprint(3 in d)\nprint(10 in d)",
        ),
    ]))

    # Extra.3 — que va como llave
    sets.append(explicit([
        (
            "Tienes la lista [2, 7, 11, 15]. Guarda solo el primer elemento en un diccionario seen "
            "mapeando numero -> indice. Imprime seen.",
            "nums = [2, 7, 11, 15]\nseen = {}\nfor i, num in enumerate(nums[:1]):\n    seen[num] = i\nprint(seen)",
        ),
        (
            "Tienes la lista [2, 7, 11, 15]. Guarda los dos primeros elementos en seen "
            "(cada numero como clave, su indice como valor). Imprime seen.",
            "nums = [2, 7, 11, 15]\nseen = {}\nfor i, num in enumerate(nums[:2]):\n    seen[num] = i\nprint(seen)",
        ),
        (
            "El numero actual es 7 y el target es 9. Imprime cuanto falta para llegar al target "
            "(el complemento: target menos el numero).",
            "num = 7\ntarget = 9\nneed = target - num\nprint(need)",
        ),
        (
            "Ya viste el 2 en el indice 0 (seen = {2: 0}). El complemento que buscas es 2. "
            "Imprime el indice donde lo viste.",
            "seen = {2: 0}\nneed = 2\nprint(seen[need])",
        ),
        (
            "Recorre la lista [3, 5] y construye seen donde cada NUMERO es la clave y su INDICE es el valor "
            "(no al reves). Imprime seen.",
            "nums = [3, 5]\nseen = {}\nfor i, num in enumerate(nums):\n    seen[num] = i\nprint(seen)",
        ),
        (
            "Imprime en dos lineas: primero el diccionario correcto numero->indice para 2 en 0 y 7 en 1; "
            "luego el incorrecto indice->numero (0: 2, 1: 7).",
            "print({2: 0, 7: 1})\nprint({0: 2, 1: 7})",
        ),
        (
            "Recorre [2, 7] guardando cada numero como clave y su indice como valor. "
            "Imprime el diccionario y, en la siguiente linea, si el 2 ya esta registrado.",
            "nums = [2, 7]\nseen = {}\nfor i, num in enumerate(nums):\n    seen[num] = i\nprint(seen)\nprint(2 in seen)",
        ),
        (
            "Ya viste el 2 en el indice 0. El numero actual es 7 y el target es 9. "
            "Calcula el complemento; si ya lo viste, imprime su indice.",
            "seen = {2: 0}\nnum = 7\ntarget = 9\nneed = target - num\nif need in seen:\n    print(seen[need])",
        ),
        (
            "Para poder preguntar rapido '¿ya vi el 7?', el 7 debe ser llave o valor? "
            "Imprime la palabra 'llave' o 'valor'.",
            "print('llave' if 7 in {7: 1} else 'valor')",
        ),
        (
            "Recorre [4, 5, 4] guardando numero -> indice (si un numero se repite, queda el ultimo indice). "
            "Imprime el diccionario.",
            "nums = [4, 5, 4]\nseen = {}\nfor i, num in enumerate(nums):\n    seen[num] = i\nprint(seen)",
        ),
    ]))

    # Extra.4 — patron seen
    sets.append(explicit([
        (
            "Recorre la lista [1, 2, 3] y construye un diccionario que mapee cada numero a su indice. "
            "Imprime el diccionario.",
            "nums = [1, 2, 3]\nseen = {}\nfor i, num in enumerate(nums):\n    seen[num] = i\nprint(seen)",
        ),
        (
            "Tienes seen = {1: 0, 2: 1, 3: 2}. Imprime True o False segun si el numero 2 ya esta registrado.",
            "seen = {1: 0, 2: 1, 3: 2}\nprint(2 in seen)",
        ),
        (
            "En la lista [1, 2, 2, 3], encuentra el indice de la primera repeticion "
            "(el segundo 2) usando un diccionario de vistos. Imprime ese indice.",
            "nums = [1, 2, 2, 3]\nseen = {}\nfor i, num in enumerate(nums):\n    if num in seen:\n        print(i)\n        break\n    seen[num] = i",
        ),
        (
            "Cuenta cuantas veces aparece cada letra en 'aabbc'. Imprime el diccionario de frecuencias.",
            "texto = 'aabbc'\nfreq = {}\nfor ch in texto:\n    freq[ch] = freq.get(ch, 0) + 1\nprint(freq)",
        ),
        (
            "Recorre [1, 2, 3, 1] una sola vez. Imprime True si hay algun numero repetido, False si no.",
            "nums = [1, 2, 3, 1]\nseen = set()\ndup = False\nfor n in nums:\n    if n in seen:\n        dup = True\n        break\n    seen.add(n)\nprint(dup)",
        ),
        (
            "El target es 6 y el numero actual es 2. Imprime cuanto falta para llegar al target.",
            "num = 2\ntarget = 6\nprint(target - num)",
        ),
        (
            "Ya viste el 2 en el indice 1. Estas en el indice 2 con el numero 4 y el target es 6. "
            "Si el complemento ya esta en seen, imprime la lista [indice_viejo, indice_actual].",
            "seen = {2: 1}\nnum = 4\ntarget = 6\ni = 2\nneed = target - num\nif need in seen:\n    print([seen[need], i])",
        ),
        (
            "Encuentra dos numeros en [3, 2, 4] que sumen 6. Imprime la lista de sus indices "
            "(usa un diccionario de vistos en un solo recorrido).",
            "nums = [3, 2, 4]\ntarget = 6\nseen = {}\nfor i, num in enumerate(nums):\n    need = target - num\n    if need in seen:\n        print([seen[need], i])\n        break\n    seen[num] = i",
        ),
        (
            "En la lista [4, 9, 9], imprime el indice de la primera vez que aparece el 9 "
            "(usa un diccionario que solo guarda la primera aparicion de cada numero).",
            "nums = [4, 9, 9]\nseen = {}\nfor i, num in enumerate(nums):\n    if num not in seen:\n        seen[num] = i\nprint(seen[9])",
        ),
        (
            "Cuenta cuantas veces aparece cada letra en 'hello'. Imprime el diccionario de frecuencias.",
            "texto = 'hello'\nfreq = {}\nfor ch in texto:\n    freq[ch] = freq.get(ch, 0) + 1\nprint(freq)",
        ),
    ]))

    # Extra.5 — Two Sum y variantes
    sets.append(explicit([
        (
            "En [2, 7, 11, 15], encuentra dos numeros que sumen 9. Imprime la lista de sus indices.",
            "nums = [2, 7, 11, 15]\ntarget = 9\nseen = {}\nfor i, num in enumerate(nums):\n    need = target - num\n    if need in seen:\n        print([seen[need], i])\n        break\n    seen[num] = i",
        ),
        (
            "En [3, 2, 4], encuentra dos numeros que sumen 6. Imprime la lista de sus indices.",
            "nums = [3, 2, 4]\ntarget = 6\nseen = {}\nfor i, num in enumerate(nums):\n    need = target - num\n    if need in seen:\n        print([seen[need], i])\n        break\n    seen[num] = i",
        ),
        (
            "En [3, 3], encuentra dos numeros que sumen 6. Imprime la lista de sus indices.",
            "nums = [3, 3]\ntarget = 6\nseen = {}\nfor i, num in enumerate(nums):\n    need = target - num\n    if need in seen:\n        print([seen[need], i])\n        break\n    seen[num] = i",
        ),
        (
            "Ya viste el 2 en el indice 0. El complemento es 2 y el indice actual es 1. "
            "Imprime la lista [indice_viejo, indice_actual] (no el diccionario entero).",
            "seen = {2: 0}\nneed = 2\ni = 1\nprint([seen[need], i])",
        ),
        (
            "En [3, 3] busca dos que sumen 6. Importante: revisa si el complemento ya esta en seen "
            "ANTES de registrar el numero actual. Imprime los indices.",
            "nums = [3, 3]\ntarget = 6\nseen = {}\nfor i, num in enumerate(nums):\n    need = target - num\n    if need in seen:\n        print([seen[need], i])\n        break\n    seen[num] = i",
        ),
        (
            "En [10, 20, 30], encuentra dos numeros que sumen 50. Imprime la lista de esos dos valores "
            "(no los indices).",
            "nums = [10, 20, 30]\ntarget = 50\nseen = {}\nfor num in nums:\n    need = target - num\n    if need in seen:\n        print([need, num])\n        break\n    seen[num] = True",
        ),
        (
            "En [1, 5, 3, 7], encuentra dos numeros que sumen 8. Imprime la lista de sus indices.",
            "nums = [1, 5, 3, 7]\ntarget = 8\nseen = {}\nfor i, num in enumerate(nums):\n    need = target - num\n    if need in seen:\n        print([seen[need], i])\n        break\n    seen[num] = i",
        ),
        (
            "En [0, 4, 3, 0], encuentra dos numeros que sumen 0. Imprime la lista de sus indices.",
            "nums = [0, 4, 3, 0]\ntarget = 0\nseen = {}\nfor i, num in enumerate(nums):\n    need = target - num\n    if need in seen:\n        print([seen[need], i])\n        break\n    seen[num] = i",
        ),
        (
            "En [5, 1, 7], encuentra dos numeros que sumen 6. Imprime la lista de sus indices.",
            "nums = [5, 1, 7]\ntarget = 6\nseen = {}\nfor i, num in enumerate(nums):\n    need = target - num\n    if need in seen:\n        print([seen[need], i])\n        break\n    seen[num] = i",
        ),
        (
            "En [4, 6, 1, 9], encuentra dos numeros que sumen 10. Imprime la lista de sus indices.",
            "nums = [4, 6, 1, 9]\ntarget = 10\nseen = {}\nfor i, num in enumerate(nums):\n    need = target - num\n    if need in seen:\n        print([seen[need], i])\n        break\n    seen[num] = i",
        ),
    ]))

    return sets


# ---------------------------------------------------------------------------
# LEVEL B — Bucles y funciones
# ---------------------------------------------------------------------------

def level_b() -> list[list[dict]]:
    sets: list[list[dict]] = []

    # B.A — for y range
    sets.append(mapped(
        lambda t: f"Imprime los numeros de {t[0]} a {t[1]} separados por espacio.",
        lambda t: f"for i in range({t[0]}, {t[1] + 1}):\n    print(i, end=' ')",
        [(1, 5), (0, 4), (1, 3), (5, 9), (1, 10), (2, 6), (3, 8), (1, 7), (4, 9), (1, 6)],
    ))
    sets.append(mapped(
        lambda n: f"Suma los numeros de 1 a {n} e imprime el total.",
        lambda n: f"total = 0\nfor i in range(1, {n + 1}):\n    total += i\nprint(total)",
        [5, 10, 3, 7, 100, 4, 6, 8, 9, 20],
    ))
    sets.append(mapped(
        lambda t: f"Imprime de {t[0]} a {t[1]} de {t[2]} en {t[2]} separados por espacio.",
        lambda t: f"for i in range({t[0]}, {t[1]}, {t[2]}):\n    print(i, end=' ')",
        [(2, 21, 2), (1, 20, 3), (0, 51, 5), (3, 31, 3), (10, 101, 10),
         (1, 30, 4), (5, 26, 5), (0, 19, 2), (2, 17, 3), (1, 22, 7)],
    ))
    sets.append(mapped(
        lambda n: f"Imprime una cuenta regresiva de {n} a 1 separada por espacio.",
        lambda n: f"for i in range({n}, 0, -1):\n    print(i, end=' ')",
        [5, 10, 3, 8, 6, 4, 7, 9, 2, 12],
    ))
    sets.append(explicit([
        ("Imprime cada letra de 'python' separada por espacio", "for c in 'python':\n    print(c, end=' ')"),
        ("Imprime cada elemento de [10, 20, 30] en su propia linea", "for n in [10, 20, 30]:\n    print(n)"),
        ("Imprime la longitud de cada palabra en ['sol','luna','mar']", "for w in ['sol', 'luna', 'mar']:\n    print(len(w))"),
        ("Cuenta cuantos caracteres tiene 'odoo' usando un bucle", "c = 0\nfor _ in 'odoo':\n    c += 1\nprint(c)"),
        ("Imprime cada caracter de 'abc' en mayuscula", "for c in 'abc':\n    print(c.upper(), end='')"),
        ("Suma los elementos de [3, 1, 4, 1, 5] con un bucle", "total = 0\nfor n in [3, 1, 4, 1, 5]:\n    total += n\nprint(total)"),
        ("Imprime el doble de cada numero en [1, 2, 3, 4]", "for n in [1, 2, 3, 4]:\n    print(n * 2, end=' ')"),
        ("Imprime las vocales de 'murcielago'", "for c in 'murcielago':\n    if c in 'aeiou':\n        print(c, end='')"),
        ("Cuenta cuantas 'o' hay en 'odoo' con un bucle", "c = 0\nfor ch in 'odoo':\n    if ch == 'o':\n        c += 1\nprint(c)"),
        ("Imprime cada par (precio) de [5, 8, 2] con signo $", "for p in [5, 8, 2]:\n    print(f'${p}', end=' ')"),
    ]))

    # B.B — while, break, continue
    sets.append(mapped(
        lambda n: f"Usa while para imprimir de 1 a {n} separados por espacio.",
        lambda n: f"i = 1\nwhile i <= {n}:\n    print(i, end=' ')\n    i += 1",
        [5, 3, 8, 10, 6, 4, 7, 9, 2, 12],
    ))
    sets.append(explicit([
        ("Empieza en 100 y mientras sea >1 divide entre 2, imprime cuantos pasos", "n = 100\nc = 0\nwhile n > 1:\n    n //= 2\n    c += 1\nprint(c)"),
        ("Suma 1+2+3+... hasta que la suma supere 50, imprime la suma", "s, i = 0, 1\nwhile s <= 50:\n    s += i\n    i += 1\nprint(s)"),
        ("Empieza en 1 y duplica mientras sea <100, imprime el valor final", "n = 1\nwhile n < 100:\n    n *= 2\nprint(n)"),
        ("Resta 7 a 40 mientras sea positivo, imprime el ultimo valor positivo o cero", "n = 40\nwhile n - 7 >= 0:\n    n -= 7\nprint(n)"),
        ("Cuenta cuantas veces cabe 3 en 20 (sin usar //)", "n, c = 20, 0\nwhile n >= 3:\n    n -= 3\n    c += 1\nprint(c)"),
        ("Imprime las potencias de 2 menores a 50 separadas por espacio", "n = 1\nwhile n < 50:\n    print(n, end=' ')\n    n *= 2"),
        ("Suma los digitos de 1234 usando while (modulo y //)", "n, s = 1234, 0\nwhile n > 0:\n    s += n % 10\n    n //= 10\nprint(s)"),
        ("Cuenta los digitos de 98765 con while", "n, c = 98765, 0\nwhile n > 0:\n    n //= 10\n    c += 1\nprint(c)"),
        ("Invierte el numero 123 usando while", "n, r = 123, 0\nwhile n > 0:\n    r = r * 10 + n % 10\n    n //= 10\nprint(r)"),
        ("Empieza en 50, resta 5 e imprime cada valor hasta llegar a 0", "n = 50\nwhile n >= 0:\n    print(n, end=' ')\n    n -= 5"),
    ]))
    sets.append(mapped(
        lambda k: f"Recorre de 1 a 10 e imprime los numeros, pero DETENTE (break) al llegar a {k}.",
        lambda k: f"for i in range(1, 11):\n    if i == {k}:\n        break\n    print(i, end=' ')",
        [6, 4, 8, 3, 5, 7, 9, 2, 10, 6],
    ))
    sets.append(mapped(
        lambda m: f"Recorre de 1 a 10 e imprime solo los numeros que NO sean multiplos de {m} (usa continue).",
        lambda m: f"for i in range(1, 11):\n    if i % {m} == 0:\n        continue\n    print(i, end=' ')",
        [2, 3, 4, 5, 2, 3, 6, 7, 2, 3],
    ))
    sets.append(mapped(
        lambda n: f"Calcula el factorial de {n} usando un bucle while.",
        lambda n: f"n, r = {n}, 1\nwhile n > 1:\n    r *= n\n    n -= 1\nprint(r)",
        [5, 3, 6, 4, 7, 2, 8, 1, 9, 10],
    ))

    # B.C — patrones de bucle
    sets.append(mapped(
        lambda lst: f"Dado {lst}, imprime 'indice:valor' por cada elemento usando enumerate.",
        lambda lst: f"for i, v in enumerate({lst}):\n    print(f'{{i}}:{{v}}', end=' ')",
        [['a', 'b', 'c'], ['x', 'y'], [10, 20, 30], ['rojo', 'azul'], ['p', 'q', 'r', 's'],
         ['uno'], ['a', 'e', 'i', 'o', 'u'], [5, 6], ['si', 'no'], ['lun', 'mar', 'mie']],
    ))
    sets.append(mapped(
        lambda t: f"Dadas las listas {t[0]} y {t[1]}, imprime cada par unido usando zip.",
        lambda t: f"for a, b in zip({t[0]}, {t[1]}):\n    print(f'{{a}}{{b}}', end=' ')",
        [([1, 2, 3], ['x', 'y', 'z']), (['a', 'b'], [1, 2]), ([10, 20], ['kg', 'm']),
         (['Ana', 'Leo'], [22, 30]), ([1, 2, 3], [4, 5, 6]), (['+', '-'], [1, 2]),
         (['r', 'g', 'b'], [255, 0, 128]), ([1], ['a']), (['p', 'q'], ['1', '2']),
         (['lun', 'mar'], ['L', 'M'])],
    ))
    sets.append(mapped(
        lambda n: f"Usa dos bucles anidados para contar cuantas parejas (i,j) hay con i,j en range({n}). Imprime el total.",
        lambda n: f"c = 0\nfor i in range({n}):\n    for j in range({n}):\n        c += 1\nprint(c)",
        [3, 2, 4, 5, 1, 6, 3, 2, 4, 5],
    ))
    sets.append(mapped(
        lambda lst: f"Dado {lst}, encuentra e imprime el valor MAXIMO sin usar max().",
        lambda lst: f"nums = {lst}\nm = nums[0]\nfor n in nums:\n    if n > m:\n        m = n\nprint(m)",
        [[3, 9, 2, 7], [1, 5, 4], [10, 2, 30, 4], [8], [-3, -1, -7],
         [100, 50, 75], [2, 2, 3], [9, 8, 7, 6], [4, 4, 4, 9], [11, 22, 5]],
    ))
    sets.append(mapped(
        lambda t: f"Dado {t[0]}, cuenta cuantas veces aparece {t[1]!r} e imprime el conteo.",
        lambda t: f"data = {t[0]}\nc = 0\nfor x in data:\n    if x == {t[1]!r}:\n        c += 1\nprint(c)",
        [(['a', 'b', 'a', 'c', 'a'], 'a'), ([1, 2, 2, 3], 2), (['si', 'no', 'si'], 'si'),
         ([5, 5, 5], 5), (['x'], 'y'), ([1, 1, 2, 1], 1), (['p', 'q', 'p'], 'p'),
         ([0, 0, 1, 0], 0), (['ok', 'no'], 'ok'), ([9, 8, 9, 9], 9)],
    ))

    # B.D — funciones
    sets.append(explicit([
        ("Define saludar(nombre) que retorne 'Hola, <nombre>!' y llamala con 'Ana'", "def saludar(nombre):\n    return f'Hola, {nombre}!'\nprint(saludar('Ana'))"),
        ("Define cuadrado(n) que retorne n*n y llamala con 6", "def cuadrado(n):\n    return n * n\nprint(cuadrado(6))"),
        ("Define doble(n) que retorne n*2 y llamala con 21", "def doble(n):\n    return n * 2\nprint(doble(21))"),
        ("Define es_par(n) que retorne True/False y llamala con 8", "def es_par(n):\n    return n % 2 == 0\nprint(es_par(8))"),
        ("Define incrementar(n) que retorne n+1 y llamala con 99", "def incrementar(n):\n    return n + 1\nprint(incrementar(99))"),
        ("Define longitud(s) que retorne len(s) y llamala con 'odoo'", "def longitud(s):\n    return len(s)\nprint(longitud('odoo'))"),
        ("Define negativo(n) que retorne -n y llamala con 7", "def negativo(n):\n    return -n\nprint(negativo(7))"),
        ("Define mayuscula(s) que retorne s en mayuscula y llamala con 'hola'", "def mayuscula(s):\n    return s.upper()\nprint(mayuscula('hola'))"),
        ("Define triple(n) que retorne n*3 y llamala con 5", "def triple(n):\n    return n * 3\nprint(triple(5))"),
        ("Define cubo(n) que retorne n**3 y llamala con 3", "def cubo(n):\n    return n ** 3\nprint(cubo(3))"),
    ]))
    sets.append(mapped(
        lambda t: f"Define sumar(a, b) que retorne a+b y llamala con {t[0]} y {t[1]}.",
        lambda t: f"def sumar(a, b):\n    return a + b\nprint(sumar({t[0]}, {t[1]}))",
        [(3, 4), (10, 20), (7, 8), (100, 1), (5, 5), (12, 13), (0, 9), (50, 50), (8, 17), (6, 6)],
    ))
    sets.append(explicit([
        ("Define saludo(nombre='Invitado') y llamala SIN argumentos", "def saludo(nombre='Invitado'):\n    return f'Hola, {nombre}'\nprint(saludo())"),
        ("Define potencia(base, exp=2) y llamala con 5", "def potencia(base, exp=2):\n    return base ** exp\nprint(potencia(5))"),
        ("Define unir(a, b, sep='-') y llamala con 'x','y'", "def unir(a, b, sep='-'):\n    return a + sep + b\nprint(unir('x', 'y'))"),
        ("Define multiplicar(a, b=10) y llamala con 4", "def multiplicar(a, b=10):\n    return a * b\nprint(multiplicar(4))"),
        ("Define repetir(texto, veces=3) y llamala con 'ab'", "def repetir(texto, veces=3):\n    return texto * veces\nprint(repetir('ab'))"),
        ("Define iva(monto, tasa=0.16) y llamala con 100", "def iva(monto, tasa=0.16):\n    return monto * (1 + tasa)\nprint(iva(100))"),
        ("Define contar(items=None) que devuelva 0 si es None", "def contar(items=None):\n    if items is None:\n        items = []\n    return len(items)\nprint(contar())"),
        ("Define despedida(nombre='amigo') y llamala con 'Leo'", "def despedida(nombre='amigo'):\n    return f'Adios, {nombre}'\nprint(despedida('Leo'))"),
        ("Define precio(base, envio=0) y llamala con 200", "def precio(base, envio=0):\n    return base + envio\nprint(precio(200))"),
        ("Define inicial(nombre, sufijo='.') y llamala con 'Ana'", "def inicial(nombre, sufijo='.'):\n    return nombre[0] + sufijo\nprint(inicial('Ana'))"),
    ]))
    sets.append(mapped(
        lambda s: f"Define nota_letra(score) (>=90 'A', >=80 'B', >=70 'C', si no 'F') y llamala con {s}.",
        lambda s: ("def nota_letra(score):\n"
                   "    if score >= 90:\n        return 'A'\n"
                   "    if score >= 80:\n        return 'B'\n"
                   "    if score >= 70:\n        return 'C'\n"
                   "    return 'F'\n"
                   f"print(nota_letra({s}))"),
        [95, 85, 75, 60, 91, 80, 70, 100, 55, 88],
    ))
    sets.append(explicit([
        ("Define aplicar(f, x) que retorne f(x); llamala con (lambda n: n+1, 10)", "def aplicar(f, x):\n    return f(x)\nprint(aplicar(lambda n: n + 1, 10))"),
        ("Define dos_veces(f, x) que retorne f(f(x)); llamala con (lambda n: n*2, 3)", "def dos_veces(f, x):\n    return f(f(x))\nprint(dos_veces(lambda n: n * 2, 3))"),
        ("Usa una lambda para ordenar [3,1,2] y mostrar el resultado", "print(sorted([3, 1, 2], key=lambda x: x))"),
        ("Define componer aplicando cuadrado luego +1 sobre 4", "def sq(n):\n    return n * n\ndef inc(n):\n    return n + 1\nprint(inc(sq(4)))"),
        ("Usa una lambda que multiplique por 10 sobre el valor 7", "f = lambda x: x * 10\nprint(f(7))"),
        ("Filtra los pares de [1,2,3,4,5,6] con una lambda", "print([n for n in [1, 2, 3, 4, 5, 6] if (lambda x: x % 2 == 0)(n)])"),
        ("Define maximo(a, b) usando un if y llamala con (9, 4)", "def maximo(a, b):\n    return a if a > b else b\nprint(maximo(9, 4))"),
        ("Aplica una lambda de suma a 5 y 8", "suma = lambda a, b: a + b\nprint(suma(5, 8))"),
        ("Define total(precios) que sume una lista; llamala con [10,20,30]", "def total(precios):\n    return sum(precios)\nprint(total([10, 20, 30]))"),
        ("Mapea el cuadrado sobre [1,2,3,4] con una lambda y muestralo", "print([(lambda x: x * x)(n) for n in [1, 2, 3, 4]])"),
    ]))

    return sets


# ---------------------------------------------------------------------------
# LEVEL C — Listas, tuplas y strings
# ---------------------------------------------------------------------------

def level_c() -> list[list[dict]]:
    sets: list[list[dict]] = []

    # C.A — listas basicas
    sets.append(mapped(
        lambda t: f"Dada la lista {t[0]}, imprime el elemento en el indice {t[1]}.",
        lambda t: f"items = {t[0]}\nprint(items[{t[1]}])",
        [([10, 20, 30], 1), (['a', 'b', 'c'], 0), ([5, 6, 7, 8], -1), ([100], 0),
         (['x', 'y', 'z'], 2), ([9, 8, 7], -2), ([1, 2, 3, 4], 3), (['rojo', 'azul'], 1),
         ([0, 1, 2], 0), ([4, 5, 6, 7, 8], -1)],
    ))
    sets.append(explicit([
        ("Crea [1,2,3], agrega 4 con append e imprime la lista", "items = [1, 2, 3]\nitems.append(4)\nprint(items)"),
        ("Crea [10,20] y agrega 30 al final", "items = [10, 20]\nitems.append(30)\nprint(items)"),
        ("Crea [2,3] e inserta 1 al inicio con insert", "items = [2, 3]\nitems.insert(0, 1)\nprint(items)"),
        ("Crea ['b','c'] e inserta 'a' en posicion 0", "items = ['b', 'c']\nitems.insert(0, 'a')\nprint(items)"),
        ("Crea [1,2] y extiendela con [3,4]", "a = [1, 2]\na.extend([3, 4])\nprint(a)"),
        ("Crea una lista vacia y agrega 'x','y' con append", "items = []\nitems.append('x')\nitems.append('y')\nprint(items)"),
        ("Crea [5] y agrega los numeros 6,7 en un bucle", "items = [5]\nfor n in [6, 7]:\n    items.append(n)\nprint(items)"),
        ("Crea [1,2,3] e inserta 99 en la posicion 1", "items = [1, 2, 3]\nitems.insert(1, 99)\nprint(items)"),
        ("Concatena [1,2] + [3,4] e imprime", "print([1, 2] + [3, 4])"),
        ("Crea [3] y agrega su doble (6) con append", "items = [3]\nitems.append(items[0] * 2)\nprint(items)"),
    ]))
    sets.append(mapped(
        lambda lst: f"Dada {lst}, imprime su longitud, suma, minimo y maximo separados por espacio.",
        lambda lst: f"n = {lst}\nprint(len(n), sum(n), min(n), max(n))",
        [[3, 1, 4, 1, 5], [10, 20, 30], [7], [9, 2, 6, 4], [100, 50],
         [1, 2, 3, 4, 5], [8, 8, 8], [2, 9, 1], [15, 3, 27, 6], [4, 4, 9, 1]],
    ))
    sets.append(explicit([
        ("Dada [1,2,3], quita el ultimo con pop e imprime la lista", "items = [1, 2, 3]\nitems.pop()\nprint(items)"),
        ("Dada [1,2,3], elimina el valor 2 con remove", "items = [1, 2, 3]\nitems.remove(2)\nprint(items)"),
        ("Dada ['a','b','c'], quita el indice 0 con pop(0)", "items = ['a', 'b', 'c']\nitems.pop(0)\nprint(items)"),
        ("Dada [5,6,7], imprime el valor que devuelve pop()", "items = [5, 6, 7]\nprint(items.pop())"),
        ("Dada [1,2,2,3], elimina la primera 2 con remove", "items = [1, 2, 2, 3]\nitems.remove(2)\nprint(items)"),
        ("Dada [10,20,30,40], quita el indice 1", "items = [10, 20, 30, 40]\nitems.pop(1)\nprint(items)"),
        ("Dada [1,2,3], vaciala con clear", "items = [1, 2, 3]\nitems.clear()\nprint(items)"),
        ("Dada ['x','y'], elimina 'x' e imprime", "items = ['x', 'y']\nitems.remove('x')\nprint(items)"),
        ("Dada [9,8,7,6], quita los dos ultimos con pop dos veces", "items = [9, 8, 7, 6]\nitems.pop()\nitems.pop()\nprint(items)"),
        ("Dada [1,2,3,4], imprime la longitud despues de un pop", "items = [1, 2, 3, 4]\nitems.pop()\nprint(len(items))"),
    ]))
    sets.append(mapped(
        lambda lst: f"Dada {lst}, recorre con un bucle y acumula la suma; imprime el total.",
        lambda lst: f"nums = {lst}\ntotal = 0\nfor n in nums:\n    total += n\nprint(total)",
        [[1, 2, 3], [10, 10, 10], [5, 4, 3, 2, 1], [100], [7, 7],
         [2, 4, 6, 8], [9, 1], [3, 3, 3, 3], [11, 22, 33], [6, 5, 4]],
    ))

    # C.B — slicing y orden
    sets.append(mapped(
        lambda t: f"Dada {t[0]}, imprime el slice [{t[1]}:{t[2]}].",
        lambda t: f"items = {t[0]}\nprint(items[{t[1]}:{t[2]}])",
        [([1, 2, 3, 4, 5], 0, 2), ([1, 2, 3, 4, 5], 2, 4), (['a', 'b', 'c', 'd'], 1, 3),
         ([10, 20, 30, 40], 0, 3), ([5, 6, 7, 8, 9], 1, 4), ([1, 2, 3], 0, 1),
         (['p', 'q', 'r', 's'], 2, 4), ([0, 1, 2, 3, 4, 5], 3, 6), ([9, 8, 7, 6], 0, 2),
         ([1, 2, 3, 4, 5, 6], 2, 5)],
    ))
    sets.append(explicit([
        ("Dada [1,2,3,4,5], imprime uno de cada dos con [::2]", "print([1, 2, 3, 4, 5][::2])"),
        ("Invierte [1,2,3,4] con [::-1]", "print([1, 2, 3, 4][::-1])"),
        ("Invierte el texto 'python' con slicing", "print('python'[::-1])"),
        ("Dada [10,20,30,40,50], imprime los ultimos 2 con [-2:]", "print([10, 20, 30, 40, 50][-2:])"),
        ("Dada [1,2,3,4,5], imprime todo menos el primero con [1:]", "print([1, 2, 3, 4, 5][1:])"),
        ("Dada [1,2,3,4,5], imprime todo menos el ultimo con [:-1]", "print([1, 2, 3, 4, 5][:-1])"),
        ("Dada [0,1,2,3,4,5,6], imprime de 1 a 6 de 2 en 2", "print([0, 1, 2, 3, 4, 5, 6][1:7:2])"),
        ("Dada 'abcdef', imprime cada tercer caracter", "print('abcdef'[::3])"),
        ("Invierte la lista ['a','b','c'] y muestrala", "print(['a', 'b', 'c'][::-1])"),
        ("Dada [1,2,3,4,5,6], imprime el centro [2:4]", "print([1, 2, 3, 4, 5, 6][2:4])"),
    ]))
    sets.append(explicit([
        ("Ordena [3,1,2] de menor a mayor con sorted", "print(sorted([3, 1, 2]))"),
        ("Ordena [5,2,9,1] descendente", "print(sorted([5, 2, 9, 1], reverse=True))"),
        ("Ordena la lista ['banana','ana','sol'] alfabeticamente", "print(sorted(['banana', 'ana', 'sol']))"),
        ("Ordena [3,1,2] in-place con .sort() e imprime", "items = [3, 1, 2]\nitems.sort()\nprint(items)"),
        ("Ordena ['Leo','ana','Zoe'] sin distinguir mayusculas", "print(sorted(['Leo', 'ana', 'Zoe'], key=str.lower))"),
        ("Ordena [10,2,33,4] por su numero de digitos", "print(sorted([10, 2, 33, 4], key=lambda x: len(str(x))))"),
        ("Ordena ['aaa','b','cc'] por longitud", "print(sorted(['aaa', 'b', 'cc'], key=len))"),
        ("Ordena [-3,2,-1,5] por valor absoluto", "print(sorted([-3, 2, -1, 5], key=abs))"),
        ("Ordena [3,1,2] descendente con .sort(reverse=True)", "items = [3, 1, 2]\nitems.sort(reverse=True)\nprint(items)"),
        ("Imprime el menor de [7,3,9,1] usando sorted()[0]", "print(sorted([7, 3, 9, 1])[0])"),
    ]))
    sets.append(mapped(
        lambda t: f"Dada la matriz {t[0]}, imprime el elemento fila {t[1]}, columna {t[2]}.",
        lambda t: f"m = {t[0]}\nprint(m[{t[1]}][{t[2]}])",
        [([[1, 2], [3, 4]], 1, 0), ([[5, 6, 7], [8, 9, 10]], 0, 2), ([[1], [2], [3]], 2, 0),
         ([['a', 'b'], ['c', 'd']], 0, 1), ([[10, 20], [30, 40]], 1, 1),
         ([[1, 2, 3]], 0, 1), ([[9, 8], [7, 6], [5, 4]], 2, 1), ([[0, 0], [1, 1]], 1, 0),
         ([[2, 4], [6, 8]], 0, 0), ([['x'], ['y']], 1, 0)],
    ))
    sets.append(explicit([
        ("Copia [1,2,3] con .copy(), agrega 4 a la copia, imprime la ORIGINAL", "a = [1, 2, 3]\nb = a.copy()\nb.append(4)\nprint(a)"),
        ("Copia [5,6] con list(), modifica la copia e imprime la original", "a = [5, 6]\nb = list(a)\nb.append(7)\nprint(a)"),
        ("Copia [1,2,3] con slicing [:] y muestra la copia", "a = [1, 2, 3]\nb = a[:]\nprint(b)"),
        ("Demuestra que b=a comparte la lista: modifica b e imprime a", "a = [1, 2]\nb = a\nb.append(3)\nprint(a)"),
        ("Crea una copia de ['x','y'] y agrega 'z' solo a la copia", "a = ['x', 'y']\nb = a.copy()\nb.append('z')\nprint(b)"),
        ("Duplica [1,2,3] en una nueva lista con comprehension", "a = [1, 2, 3]\nb = [x for x in a]\nprint(b)"),
        ("Copia [10,20,30] e invierte solo la copia", "a = [10, 20, 30]\nb = a.copy()\nb.reverse()\nprint(b)"),
        ("Copia [1,2] y concatena [3] a la copia", "a = [1, 2]\nb = a.copy() + [3]\nprint(b)"),
        ("Muestra la longitud de una copia de [1,2,3,4]", "a = [1, 2, 3, 4]\nb = a.copy()\nprint(len(b))"),
        ("Copia [9,8,7] y ordena solo la copia", "a = [9, 8, 7]\nb = sorted(a)\nprint(b)"),
    ]))

    # C.C — tuplas y comprehensions
    sets.append(explicit([
        ("Crea la tupla (1,2,3) e imprime el primer elemento", "t = (1, 2, 3)\nprint(t[0])"),
        ("Crea ('Ana', 22) e imprime el ultimo elemento", "t = ('Ana', 22)\nprint(t[-1])"),
        ("Imprime la longitud de la tupla (4,5,6,7)", "print(len((4, 5, 6, 7)))"),
        ("Crea (10,20,30) e imprime la suma", "t = (10, 20, 30)\nprint(sum(t))"),
        ("Crea una tupla de un solo elemento (5,) e imprimela", "t = (5,)\nprint(t)"),
        ("Convierte la lista [1,2,3] en tupla e imprimela", "print(tuple([1, 2, 3]))"),
        ("Cuenta cuantos 2 hay en (2,3,2,2)", "print((2, 3, 2, 2).count(2))"),
        ("Imprime el indice de 'b' en ('a','b','c')", "print(('a', 'b', 'c').index('b'))"),
        ("Concatena (1,2) + (3,4) e imprime", "print((1, 2) + (3, 4))"),
        ("Crea (1,2,3) e imprime el slice [1:]", "print((1, 2, 3)[1:])"),
    ]))
    sets.append(explicit([
        ("Desempaqueta a,b = (1,2) e imprime a y b", "a, b = (1, 2)\nprint(a, b)"),
        ("Desempaqueta x,y,z = (10,20,30) e imprime la suma", "x, y, z = (10, 20, 30)\nprint(x + y + z)"),
        ("Intercambia a,b = 1,2 con a,b=b,a e imprimelos", "a, b = 1, 2\na, b = b, a\nprint(a, b)"),
        ("Desempaqueta nombre,edad=('Leo',30) e imprime con f-string", "nombre, edad = ('Leo', 30)\nprint(f'{nombre}-{edad}')"),
        ("Usa primero,*resto = [1,2,3,4] e imprime resto", "primero, *resto = [1, 2, 3, 4]\nprint(resto)"),
        ("Usa *inicio,ultimo = [1,2,3,4] e imprime ultimo", "*inicio, ultimo = [1, 2, 3, 4]\nprint(ultimo)"),
        ("Recorre [(1,'a'),(2,'b')] desempaquetando cada par", "for n, l in [(1, 'a'), (2, 'b')]:\n    print(f'{n}{l}', end=' ')"),
        ("Desempaqueta (1,(2,3)) en a,(b,c) e imprime b+c", "a, (b, c) = (1, (2, 3))\nprint(b + c)"),
        ("Asigna a=b=c=0 e imprime los tres", "a = b = c = 0\nprint(a, b, c)"),
        ("Desempaqueta coords=(4,5); imprime 'x=4 y=5'", "x, y = (4, 5)\nprint(f'x={x} y={y}')"),
    ]))
    sets.append(mapped(
        lambda n: f"Usa una list comprehension para crear los cuadrados de 1 a {n} e imprimelos.",
        lambda n: f"print([i * i for i in range(1, {n + 1})])",
        [5, 3, 6, 4, 7, 2, 8, 1, 9, 10],
    ))
    sets.append(mapped(
        lambda lst: f"Dada {lst}, usa una comprehension para quedarte solo con los pares.",
        lambda lst: f"print([n for n in {lst} if n % 2 == 0])",
        [[1, 2, 3, 4, 5, 6], [10, 15, 20, 25], [7, 8, 9], [2, 4, 6], [1, 3, 5],
         [11, 12, 13, 14], [100, 101, 102], [5, 10, 15, 20], [3, 6, 9, 12], [8, 7, 6, 5]],
    ))
    sets.append(explicit([
        ("Usa comprehension para poner en mayuscula ['a','b','c']", "print([c.upper() for c in ['a', 'b', 'c']])"),
        ("Crea una lista con la longitud de cada palabra en ['sol','luna','mar']", "print([len(w) for w in ['sol', 'luna', 'mar']])"),
        ("Crea [n*10 for n in 1..5]", "print([n * 10 for n in range(1, 6)])"),
        ("Convierte ['1','2','3'] a enteros con comprehension", "print([int(x) for x in ['1', '2', '3']])"),
        ("Crea pares (n, n*n) para n en 1..4", "print([(n, n * n) for n in range(1, 5)])"),
        ("Filtra palabras de >3 letras en [' a','casa','sol','arbol'] (usa strip)", "print([w for w in ['casa', 'sol', 'arbol'] if len(w) > 3])"),
        ("Suma 1 a cada elemento de [10,20,30]", "print([n + 1 for n in [10, 20, 30]])"),
        ("Crea la primera letra de cada palabra en ['Ana','Beto','Caro']", "print([w[0] for w in ['Ana', 'Beto', 'Caro']])"),
        ("Genera los multiplos de 3 menores a 20 con comprehension", "print([n for n in range(20) if n % 3 == 0])"),
        ("Convierte [1,2,3] en sus negativos", "print([-n for n in [1, 2, 3]])"),
    ]))

    # C.D — metodos de string
    sets.append(explicit([
        ("Separa 'a,b,c' por comas en una lista", "print('a,b,c'.split(','))"),
        ("Une ['a','b','c'] con comas", "print(','.join(['a', 'b', 'c']))"),
        ("Separa 'hola mundo python' por espacios", "print('hola mundo python'.split())"),
        ("Une ['2024','06','25'] con guiones (fecha)", "print('-'.join(['2024', '06', '25']))"),
        ("Cuenta cuantas palabras hay en 'uno dos tres cuatro'", "print(len('uno dos tres cuatro'.split()))"),
        ("Separa 'a-b-c-d' por guiones e imprime el primero", "print('a-b-c-d'.split('-')[0])"),
        ("Une los caracteres de 'abc' con '.'", "print('.'.join('abc'))"),
        ("Separa 'clave=valor' por '=' e imprime la lista", "print('clave=valor'.split('='))"),
        ("Une ['Hola','Mundo'] con un espacio", "print(' '.join(['Hola', 'Mundo']))"),
        ("Separa 'a, b, c' por ', ' (con espacio)", "print('a, b, c'.split(', '))"),
    ]))
    sets.append(explicit([
        ("Quita espacios de '  hola  '", "print('  hola  '.strip())"),
        ("Reemplaza 'gato' por 'perro' en 'mi gato'", "print('mi gato'.replace('gato', 'perro'))"),
        ("Quita solo los espacios de la izquierda de '  hi'", "print('  hi'.lstrip())"),
        ("Reemplaza todas las 'a' por '@' en 'banana'", "print('banana'.replace('a', '@'))"),
        ("Quita los '*' de '**texto**'", "print('**texto**'.strip('*'))"),
        ("Reemplaza espacios por '_' en 'hola mundo'", "print('hola mundo'.replace(' ', '_'))"),
        ("Quita el salto de linea de 'linea\\n'", "print('linea\\n'.strip())"),
        ("Reemplaza 'http' por 'https' en 'http://x'", "print('http://x'.replace('http', 'https'))"),
        ("Quita los espacios de la derecha de 'hi   '", "print(repr('hi   '.rstrip()))"),
        ("Elimina las comas de '1,000,000'", "print('1,000,000'.replace(',', ''))"),
    ]))
    sets.append(explicit([
        ("Pon 'hola' en mayusculas", "print('hola'.upper())"),
        ("Pon 'MUNDO' en minusculas", "print('MUNDO'.lower())"),
        ("Pon 'odoo developer' en formato titulo", "print('odoo developer'.title())"),
        ("Capitaliza 'soporte tecnico'", "print('soporte tecnico'.capitalize())"),
        ("Intercambia mayus/minus de 'Hola Mundo' con swapcase", "print('Hola Mundo'.swapcase())"),
        ("Verifica si 'PYTHON' esta todo en mayusculas", "print('PYTHON'.isupper())"),
        ("Verifica si 'hola' esta todo en minusculas", "print('hola'.islower())"),
        ("Pon en mayuscula solo la primera letra de 'python'", "print('python'.capitalize())"),
        ("Pon 'el gran libro' en titulo", "print('el gran libro'.title())"),
        ("Convierte 'Mixed Case' a mayusculas", "print('Mixed Case'.upper())"),
    ]))
    sets.append(explicit([
        ("Encuentra el indice de 'll' en 'hello'", "print('hello'.find('ll'))"),
        ("Cuenta cuantas 'l' hay en 'hello'", "print('hello'.count('l'))"),
        ("Verifica si 'python' empieza con 'py'", "print('python'.startswith('py'))"),
        ("Verifica si 'reporte.pdf' termina con '.pdf'", "print('reporte.pdf'.endswith('.pdf'))"),
        ("Verifica si 'sol' esta dentro de 'girasol'", "print('sol' in 'girasol')"),
        ("Encuentra el indice de '@' en 'a@b.com'", "print('a@b.com'.find('@'))"),
        ("Cuenta cuantas palabras 'la' hay en 'la la la'", "print('la la la'.count('la'))"),
        ("Verifica si '12345'.isdigit()", "print('12345'.isdigit())"),
        ("Verifica si 'abc'.isalpha()", "print('abc'.isalpha())"),
        ("Devuelve -1 si 'xyz' no esta en 'hello'", "print('hello'.find('xyz'))"),
    ]))
    sets.append(explicit([
        ("Imprime 3.14159 con 2 decimales usando format()", "print('{:.2f}'.format(3.14159))"),
        ("Imprime 42 con 5 digitos (ceros) usando f-string", "print(f'{42:05d}')"),
        ("Formatea 1234567 con separador de miles", "print(f'{1234567:,}')"),
        ("Imprime 0.25 como porcentaje (25.00%)", "print(f'{0.25:.2%}')"),
        ("Alinea 'ok' a la derecha en 10 espacios", "print(f'{\"ok\":>10}')"),
        ("Usa format posicional: '{0} y {1}' con 'a','b'", "print('{0} y {1}'.format('a', 'b'))"),
        ("Usa format con nombre: '{n}!' con n='Hola'", "print('{n}!'.format(n='Hola'))"),
        ("Imprime el binario de 10 con f-string", "print(f'{10:b}')"),
        ("Imprime 255 en hexadecimal con f-string", "print(f'{255:x}')"),
        ("Imprime 'Total: $99.90' con un float 99.9", "t = 99.9\nprint(f'Total: ${t:.2f}')"),
    ]))

    return sets


# ---------------------------------------------------------------------------
# LEVEL D — Diccionarios, sets y errores
# ---------------------------------------------------------------------------

def level_d() -> list[list[dict]]:
    sets: list[list[dict]] = []

    # D.A — diccionarios basicos
    sets.append(mapped(
        lambda t: f"Crea el dict {t[0]} e imprime el valor de la clave {t[1]!r}.",
        lambda t: f"d = {t[0]}\nprint(d[{t[1]!r}])",
        [({'a': 1, 'b': 2}, 'a'), ({'nombre': 'Ana', 'edad': 22}, 'nombre'),
         ({'x': 10, 'y': 20}, 'y'), ({'pais': 'Peru'}, 'pais'),
         ({'r': 255, 'g': 0, 'b': 128}, 'g'), ({'uno': 1, 'dos': 2}, 'dos'),
         ({'fruta': 'mango', 'precio': 5}, 'precio'), ({'k': 'v'}, 'k'),
         ({'a': 'x', 'b': 'y', 'c': 'z'}, 'c'), ({'activo': True}, 'activo')],
    ))
    sets.append(explicit([
        ("Crea {'a':1}, agrega la clave 'b' con 2 e imprime el dict", "d = {'a': 1}\nd['b'] = 2\nprint(d)"),
        ("Crea un dict vacio, agrega 'x':10 e imprimelo", "d = {}\nd['x'] = 10\nprint(d)"),
        ("Crea {'n':1} y actualiza 'n' a 99", "d = {'n': 1}\nd['n'] = 99\nprint(d)"),
        ("Crea {'a':1,'b':2} y borra 'a' con del", "d = {'a': 1, 'b': 2}\ndel d['a']\nprint(d)"),
        ("Crea {'x':1} e incrementa 'x' en 1", "d = {'x': 1}\nd['x'] += 1\nprint(d)"),
        ("Crea {'lista':[]} y agrega 5 a la lista interna", "d = {'lista': []}\nd['lista'].append(5)\nprint(d)"),
        ("Crea {'a':1,'b':2} y saca 'a' con pop e imprime el dict", "d = {'a': 1, 'b': 2}\nd.pop('a')\nprint(d)"),
        ("Crea {'c':3} y agrega dos claves mas", "d = {'c': 3}\nd['d'] = 4\nd['e'] = 5\nprint(d)"),
        ("Actualiza el precio de {'precio':10} a 12", "d = {'precio': 10}\nd['precio'] = 12\nprint(d)"),
        ("Crea {'on':False} y cambialo a True", "d = {'on': False}\nd['on'] = True\nprint(d)"),
    ]))
    sets.append(mapped(
        lambda t: f"Dado {t[0]}, usa .get({t[1]!r}, {t[2]!r}) y muestra el resultado (la clave puede no existir).",
        lambda t: f"d = {t[0]}\nprint(d.get({t[1]!r}, {t[2]!r}))",
        [({'a': 1}, 'b', 0), ({'x': 10}, 'x', -1), ({}, 'k', 'NA'),
         ({'nombre': 'Ana'}, 'edad', 'desconocida'), ({'p': 5}, 'q', 99),
         ({'on': True}, 'off', False), ({'a': 1, 'b': 2}, 'c', 3),
         ({'total': 100}, 'total', 0), ({}, 'x', 0), ({'k': 'v'}, 'z', 'sin valor')],
    ))
    sets.append(explicit([
        ("Dado {'a':1,'b':2}, imprime la lista de claves", "d = {'a': 1, 'b': 2}\nprint(list(d.keys()))"),
        ("Dado {'a':1,'b':2}, imprime la lista de valores", "d = {'a': 1, 'b': 2}\nprint(list(d.values()))"),
        ("Dado {'a':1,'b':2,'c':3}, imprime la suma de los valores", "d = {'a': 1, 'b': 2, 'c': 3}\nprint(sum(d.values()))"),
        ("Dado {'x':10,'y':20}, imprime cuantas claves tiene", "d = {'x': 10, 'y': 20}\nprint(len(d))"),
        ("Dado {'a':1,'b':2}, imprime la lista de items (pares)", "d = {'a': 1, 'b': 2}\nprint(list(d.items()))"),
        ("Verifica si 'a' esta en {'a':1,'b':2}", "d = {'a': 1, 'b': 2}\nprint('a' in d)"),
        ("Dado {'p':3,'q':7}, imprime el valor maximo", "d = {'p': 3, 'q': 7}\nprint(max(d.values()))"),
        ("Dado {'a':1,'b':2,'c':3}, imprime las claves ordenadas", "d = {'c': 3, 'a': 1, 'b': 2}\nprint(sorted(d.keys()))"),
        ("Verifica si el valor 2 esta en {'a':1,'b':2}", "d = {'a': 1, 'b': 2}\nprint(2 in d.values())"),
        ("Dado {'a':5,'b':5}, imprime True si todos los valores son 5", "d = {'a': 5, 'b': 5}\nprint(all(v == 5 for v in d.values()))"),
    ]))
    sets.append(mapped(
        lambda d: f"Dado {d}, recorre items() e imprime 'clave:valor' por cada par.",
        lambda d: f"d = {d}\nfor k, v in d.items():\n    print(f'{{k}}:{{v}}', end=' ')",
        [{'a': 1, 'b': 2}, {'x': 10}, {'uno': 1, 'dos': 2, 'tres': 3}, {'k': 'v'},
         {'r': 1, 'g': 2}, {'p': 9, 'q': 8}, {'nombre': 'Ana'}, {'a': 1, 'b': 2, 'c': 3},
         {'on': 1}, {'m': 5, 'n': 6}],
    ))

    # D.B — diccionarios avanzados
    sets.append(mapped(
        lambda n: f"Usa un dict comprehension para mapear cada numero de 1 a {n} con su cuadrado.",
        lambda n: f"print({{i: i * i for i in range(1, {n + 1})}})",
        [3, 4, 5, 2, 6, 1, 7, 8, 3, 4],
    ))
    sets.append(mapped(
        lambda s: f"Cuenta la frecuencia de cada palabra en {s!r} e imprime el dict.",
        lambda s: (f"texto = {s!r}\nfreq = {{}}\n"
                   "for w in texto.split():\n    freq[w] = freq.get(w, 0) + 1\nprint(freq)"),
        ["a b a", "sol luna sol sol", "x y z", "uno uno dos", "hola hola hola",
         "p q p q p", "ana ana beto", "si no si", "a a a b b", "rojo azul rojo"],
    ))
    sets.append(explicit([
        ("Dado {'user':{'name':'Bob'}}, imprime el name interno", "d = {'user': {'name': 'Bob'}}\nprint(d['user']['name'])"),
        ("Dado {'a':{'b':{'c':42}}}, imprime 42", "d = {'a': {'b': {'c': 42}}}\nprint(d['a']['b']['c'])"),
        ("Crea {'cliente':{'pedidos':2}} y aumenta pedidos a 3", "d = {'cliente': {'pedidos': 2}}\nd['cliente']['pedidos'] = 3\nprint(d)"),
        ("Dado {'p':{'precio':10,'stock':5}}, imprime el stock", "d = {'p': {'precio': 10, 'stock': 5}}\nprint(d['p']['stock'])"),
        ("Crea un dict con una lista de dicts y cuenta los elementos", "d = {'items': [{'x': 1}, {'x': 2}]}\nprint(len(d['items']))"),
        ("Dado {'a':[1,2,3]}, imprime la suma de la lista interna", "d = {'a': [1, 2, 3]}\nprint(sum(d['a']))"),
        ("Dado un dict anidado, agrega una clave al sub-dict", "d = {'cfg': {'on': True}}\nd['cfg']['nivel'] = 5\nprint(d)"),
        ("Dado {'team':{'a':1,'b':2}}, imprime la suma de valores internos", "d = {'team': {'a': 1, 'b': 2}}\nprint(sum(d['team'].values()))"),
        ("Dado {'x':{'y':[10,20]}}, imprime el ultimo de la lista", "d = {'x': {'y': [10, 20]}}\nprint(d['x']['y'][-1])"),
        ("Recorre {'a':1,'b':2} dentro de {'datos':...} e imprime claves", "d = {'datos': {'a': 1, 'b': 2}}\nprint(list(d['datos'].keys()))"),
    ]))
    sets.append(mapped(
        lambda d: f"Dado {d}, invierte el dict (valor->clave) e imprime el resultado.",
        lambda d: f"d = {d}\nprint({{v: k for k, v in d.items()}})",
        [{'a': 1, 'b': 2}, {'x': 10, 'y': 20}, {'uno': 1}, {'r': 'rojo', 'a': 'azul'},
         {'k1': 'v1', 'k2': 'v2'}, {'p': 100}, {'a': 'x', 'b': 'y'}, {'on': 1, 'off': 0},
         {'m': 5}, {'i': 'j', 'k': 'l'}],
    ))
    sets.append(explicit([
        ("Usa setdefault para inicializar 'lista':[] y agrega 1", "d = {}\nd.setdefault('lista', []).append(1)\nprint(d)"),
        ("Combina {'a':1} y {'b':2} con update", "a = {'a': 1}\na.update({'b': 2})\nprint(a)"),
        ("Combina dos dicts con {**a, **b}", "a = {'x': 1}\nb = {'y': 2}\nprint({**a, **b})"),
        ("Usa setdefault en {'a':1} para 'a' (ya existe)", "d = {'a': 1}\nprint(d.setdefault('a', 99))"),
        ("Agrupa: setdefault para acumular [1,2] bajo 'nums'", "d = {}\nfor n in [1, 2]:\n    d.setdefault('nums', []).append(n)\nprint(d)"),
        ("Combina {'a':1,'b':2} con {'b':9} (b se sobreescribe)", "a = {'a': 1, 'b': 2}\na.update({'b': 9})\nprint(a)"),
        ("Crea dict desde pares [('a',1),('b',2)]", "print(dict([('a', 1), ('b', 2)]))"),
        ("Usa setdefault para contar: 'x' a 0 luego +1", "d = {}\nd.setdefault('x', 0)\nd['x'] += 1\nprint(d)"),
        ("Une tres dicts con {**a,**b,**c}", "a, b, c = {'a': 1}, {'b': 2}, {'c': 3}\nprint({**a, **b, **c})"),
        ("Crea dict con zip(['a','b'],[1,2])", "print(dict(zip(['a', 'b'], [1, 2])))"),
    ]))

    # D.C — sets
    sets.append(mapped(
        lambda lst: f"Dada {lst}, conviertela en set y muestra cuantos elementos UNICOS tiene.",
        lambda lst: f"print(len(set({lst})))",
        [[1, 2, 2, 3], [1, 1, 1], ['a', 'b', 'a'], [5, 5, 6, 7, 7], [1, 2, 3, 4],
         [9, 9, 9, 8], ['x', 'y', 'z', 'x'], [0, 0, 0, 0], [1, 2, 3, 2, 1], ['p', 'p', 'q']],
    ))
    sets.append(explicit([
        ("Crea un set {1,2}, agrega 3 e imprime ordenado", "s = {1, 2}\ns.add(3)\nprint(sorted(s))"),
        ("Crea {1,2,3}, quita el 2 con discard e imprime ordenado", "s = {1, 2, 3}\ns.discard(2)\nprint(sorted(s))"),
        ("Crea un set vacio, agrega 'a','b','a' e imprime su tamano", "s = set()\nfor x in ['a', 'b', 'a']:\n    s.add(x)\nprint(len(s))"),
        ("Crea {10,20} y agrega 20 de nuevo (no cambia); imprime tamano", "s = {10, 20}\ns.add(20)\nprint(len(s))"),
        ("Crea {1,2,3} y quita el 1 con remove; imprime ordenado", "s = {1, 2, 3}\ns.remove(1)\nprint(sorted(s))"),
        ("Crea un set desde 'banana' e imprime sus letras ordenadas", "print(sorted(set('banana')))"),
        ("Agrega los numeros 1,2,3 a un set y muestra el total", "s = set()\ns.update([1, 2, 3])\nprint(len(s))"),
        ("Crea {5}, usa discard(99) (no existe) e imprime ordenado", "s = {5}\ns.discard(99)\nprint(sorted(s))"),
        ("Crea {1,2,3,4} y quita los pares; imprime ordenado", "s = {1, 2, 3, 4}\nfor n in [2, 4]:\n    s.discard(n)\nprint(sorted(s))"),
        ("Convierte [3,3,2,1] a set y de regreso a lista ordenada", "print(sorted(set([3, 3, 2, 1])))"),
    ]))
    sets.append(mapped(
        lambda t: f"Dados los sets {t[0]} y {t[1]}, imprime su UNION ordenada y su INTERSECCION ordenada.",
        lambda t: f"a, b = set({t[0]}), set({t[1]})\nprint(sorted(a | b), sorted(a & b))",
        [([1, 2, 3], [2, 3, 4]), ([1, 2], [3, 4]), (['a', 'b'], ['b', 'c']),
         ([5, 6, 7], [7, 8]), ([1], [1]), ([10, 20], [20, 30]), ([1, 2, 3], [1, 2, 3]),
         (['x'], ['y']), ([2, 4, 6], [4, 6, 8]), ([9], [8, 9])],
    ))
    sets.append(mapped(
        lambda t: f"Dados {t[0]} y {t[1]}, imprime los elementos de A que NO estan en B (diferencia, ordenada).",
        lambda t: f"a, b = set({t[0]}), set({t[1]})\nprint(sorted(a - b))",
        [([1, 2, 3], [2]), ([1, 2, 3, 4], [3, 4]), (['a', 'b', 'c'], ['a']),
         ([5, 6, 7], [6]), ([1, 2], [1, 2]), ([10, 20, 30], [20]), ([1, 2, 3], []),
         (['x', 'y'], ['y']), ([4, 5, 6], [4, 5, 6]), ([7, 8, 9], [8])],
    ))
    sets.append(explicit([
        ("Verifica si 3 esta en el set {1,2,3}", "print(3 in {1, 2, 3})"),
        ("Elimina duplicados de [1,2,2,3,3,3] conservando orden de aparicion", "seen = set()\nout = []\nfor n in [1, 2, 2, 3, 3, 3]:\n    if n not in seen:\n        seen.add(n)\n        out.append(n)\nprint(out)"),
        ("Verifica si {1,2} es subconjunto de {1,2,3}", "print({1, 2} <= {1, 2, 3})"),
        ("Cuenta elementos unicos en 'mississippi'", "print(len(set('mississippi')))"),
        ("Verifica si dos listas tienen algun elemento en comun", "print(bool(set([1, 2, 3]) & set([3, 4])))"),
        ("Imprime True si 'z' NO esta en {'a','b'}", "print('z' not in {'a', 'b'})"),
        ("Quita duplicados de ['a','b','a','c'] y ordena", "print(sorted(set(['a', 'b', 'a', 'c'])))"),
        ("Verifica si {1,2,3} y {4,5} son disjuntos", "print({1, 2, 3}.isdisjoint({4, 5}))"),
        ("Cuenta cuantos numeros unicos hay en [1,1,2,3,3,3,4]", "print(len(set([1, 1, 2, 3, 3, 3, 4])))"),
        ("Verifica si {1,2,3} es superconjunto de {2}", "print({1, 2, 3} >= {2})"),
    ]))

    # D.D — manejo de errores
    sets.append(explicit([
        ("Divide 10/2 dentro de try/except ZeroDivisionError", "try:\n    print(10 / 2)\nexcept ZeroDivisionError:\n    print('error')"),
        ("Divide 10/0 y captura ZeroDivisionError imprimiendo 'error'", "try:\n    print(10 / 0)\nexcept ZeroDivisionError:\n    print('error')"),
        ("Intenta 5/0, en except imprime 'infinito'", "try:\n    x = 5 / 0\nexcept ZeroDivisionError:\n    print('infinito')"),
        ("Divide 9/3 (no falla) e imprime el resultado", "try:\n    print(9 / 3)\nexcept ZeroDivisionError:\n    print('error')"),
        ("Captura el error de 1/0 e imprime el tipo del error", "try:\n    1 / 0\nexcept ZeroDivisionError as e:\n    print(type(e).__name__)"),
        ("Suma 8/4 y 6/2 en un try, imprime ambos", "try:\n    print(8 / 4)\n    print(6 / 2)\nexcept ZeroDivisionError:\n    print('error')"),
        ("Maneja division por cero devolviendo 0", "def safe(a, b):\n    try:\n        return a / b\n    except ZeroDivisionError:\n        return 0\nprint(safe(10, 0))"),
        ("Captura ZeroDivisionError dentro de un bucle sobre [2,0,4] (10/n)", "for n in [2, 0, 4]:\n    try:\n        print(10 / n, end=' ')\n    except ZeroDivisionError:\n        print('x', end=' ')"),
        ("Intenta 100/5 e imprime 'ok' al final con else", "try:\n    100 / 5\nexcept ZeroDivisionError:\n    print('no')\nelse:\n    print('ok')"),
        ("Maneja 7/0 imprimiendo un mensaje personalizado", "try:\n    print(7 / 0)\nexcept ZeroDivisionError:\n    print('No se puede dividir entre cero')"),
    ]))
    sets.append(explicit([
        ("Convierte 'abc' a int y captura ValueError imprimiendo 'invalido'", "try:\n    int('abc')\nexcept ValueError:\n    print('invalido')"),
        ("Convierte '42' a int (no falla) e imprime el doble", "try:\n    print(int('42') * 2)\nexcept ValueError:\n    print('invalido')"),
        ("Convierte 'x' a float capturando ValueError -> 0.0", "def to_float(s):\n    try:\n        return float(s)\n    except ValueError:\n        return 0.0\nprint(to_float('x'))"),
        ("Recorre ['1','dos','3'] sumando los que sean numeros", "total = 0\nfor s in ['1', 'dos', '3']:\n    try:\n        total += int(s)\n    except ValueError:\n        pass\nprint(total)"),
        ("Convierte '3.14' a float e imprimelo", "try:\n    print(float('3.14'))\nexcept ValueError:\n    print('error')"),
        ("Captura ValueError de int('1,000') e imprime el nombre del error", "try:\n    int('1,000')\nexcept ValueError as e:\n    print(type(e).__name__)"),
        ("Pide int de '07' (valido) e imprime +1", "try:\n    print(int('07') + 1)\nexcept ValueError:\n    print('error')"),
        ("Convierte 'NaN' a float (valido en Python) e imprime su tipo", "try:\n    x = float('nan')\n    print(type(x).__name__)\nexcept ValueError:\n    print('error')"),
        ("Maneja int('') con ValueError devolviendo -1", "def parse(s):\n    try:\n        return int(s)\n    except ValueError:\n        return -1\nprint(parse(''))"),
        ("Suma int('10')+int('20') protegido con try", "try:\n    print(int('10') + int('20'))\nexcept ValueError:\n    print('error')"),
    ]))
    sets.append(explicit([
        ("Accede al indice 5 de [1,2] capturando IndexError -> 'fuera'", "try:\n    [1, 2][5]\nexcept IndexError:\n    print('fuera')"),
        ("Accede a la clave 'x' de {} capturando KeyError -> 'sin clave'", "try:\n    {}['x']\nexcept KeyError:\n    print('sin clave')"),
        ("Accede a [10,20,30][1] (valido) e imprimelo", "try:\n    print([10, 20, 30][1])\nexcept IndexError:\n    print('error')"),
        ("Accede a {'a':1}['a'] (valido) e imprime el valor", "try:\n    print({'a': 1}['a'])\nexcept KeyError:\n    print('error')"),
        ("Captura IndexError de una lista vacia devolviendo None", "def first(lst):\n    try:\n        return lst[0]\n    except IndexError:\n        return None\nprint(first([]))"),
        ("Captura KeyError e imprime el nombre del error", "try:\n    {'a': 1}['z']\nexcept KeyError as e:\n    print(type(e).__name__)"),
        ("Maneja IndexError accediendo al ultimo de []", "try:\n    print([][-1])\nexcept IndexError:\n    print('vacia')"),
        ("Usa get() para evitar KeyError en {} con clave 'k'", "print({}.get('k', 'default'))"),
        ("Recorre indices 0..3 de [1,2] capturando IndexError", "data = [1, 2]\nfor i in range(4):\n    try:\n        print(data[i], end=' ')\n    except IndexError:\n        print('-', end=' ')"),
        ("Captura (IndexError, KeyError) juntos accediendo a {}['a']", "try:\n    {}['a']\nexcept (IndexError, KeyError):\n    print('faltante')"),
    ]))
    sets.append(explicit([
        ("Usa try/finally: imprime 1 en try y 2 en finally", "try:\n    print(1)\nfinally:\n    print(2)"),
        ("Usa try/except/else: si 5/1 funciona, imprime 'sin error'", "try:\n    5 / 1\nexcept ZeroDivisionError:\n    print('error')\nelse:\n    print('sin error')"),
        ("Usa finally para imprimir 'fin' aunque haya error 1/0", "try:\n    1 / 0\nexcept ZeroDivisionError:\n    print('error')\nfinally:\n    print('fin')"),
        ("Else solo corre si no hay excepcion: int('5') -> imprime 'ok'", "try:\n    int('5')\nexcept ValueError:\n    print('mal')\nelse:\n    print('ok')"),
        ("Combina except + else + finally con 10/2", "try:\n    r = 10 / 2\nexcept ZeroDivisionError:\n    print('error')\nelse:\n    print(r)\nfinally:\n    print('listo')"),
        ("finally se ejecuta tras el return de una funcion", "def f():\n    try:\n        return 'valor'\n    finally:\n        print('cerrando')\nprint(f())"),
        ("else imprime el resultado de una conversion exitosa", "try:\n    n = int('100')\nexcept ValueError:\n    print('mal')\nelse:\n    print(n)"),
        ("finally cierra un recurso simulado tras un error capturado", "try:\n    raise ValueError('x')\nexcept ValueError:\n    print('manejado')\nfinally:\n    print('recurso cerrado')"),
        ("Usa else para sumar tras un acceso valido a lista", "try:\n    v = [1, 2, 3][0]\nexcept IndexError:\n    print('mal')\nelse:\n    print(v + 10)"),
        ("Demuestra el orden: try->else->finally con prints 1,2,3", "try:\n    print(1)\nexcept Exception:\n    pass\nelse:\n    print(2)\nfinally:\n    print(3)"),
    ]))
    sets.append(explicit([
        ("Define f(n) con guard clause: si n es None retorna 0, si no n*2; llamala con None", "def f(n):\n    if n is None:\n        return 0\n    return n * 2\nprint(f(None))"),
        ("Define f(n) con guard: None->0; llamala con 5", "def f(n):\n    if n is None:\n        return 0\n    return n * 2\nprint(f(5))"),
        ("Lanza ValueError('negativo') si x<0 y capturalo; llama con -1", "def check(x):\n    if x < 0:\n        raise ValueError('negativo')\n    return x\ntry:\n    check(-1)\nexcept ValueError as e:\n    print(e)"),
        ("Guard clause: lista vacia -> 'vacia', si no su primer elemento", "def first(lst):\n    if not lst:\n        return 'vacia'\n    return lst[0]\nprint(first([]))"),
        ("Usa raise para validar edad>=0; captura y muestra el mensaje", "def edad(x):\n    if x < 0:\n        raise ValueError('edad invalida')\n    return x\ntry:\n    edad(-5)\nexcept ValueError as e:\n    print(e)"),
        ("Guard: si el texto esta vacio retorna 'N/A'; llama con ''", "def saludo(s):\n    if not s:\n        return 'N/A'\n    return f'Hola {s}'\nprint(saludo(''))"),
        ("Usa assert para verificar que 2+2==4 e imprime 'ok'", "assert 2 + 2 == 4\nprint('ok')"),
        ("Lanza y captura un KeyError personalizado", "try:\n    raise KeyError('falta')\nexcept KeyError as e:\n    print(e)"),
        ("Guard: divisor 0 -> retorna None; llama con (10,0)", "def div(a, b):\n    if b == 0:\n        return None\n    return a / b\nprint(div(10, 0))"),
        ("Valida con guard que el numero sea par, si no lanza error; llama con 4", "def solo_par(n):\n    if n % 2 != 0:\n        raise ValueError('impar')\n    return n\nprint(solo_par(4))"),
    ]))

    return sets


# ---------------------------------------------------------------------------
# LEVEL E — Clases y OOP (rampa gradual)
# ---------------------------------------------------------------------------

def level_e() -> list[list[dict]]:
    sets: list[list[dict]] = []

    # E.A — objetos y atributos
    sets.append(explicit([
        ("Define una clase vacia Perro (usa pass) e imprime type(Perro()).__name__", "class Perro:\n    pass\nprint(type(Perro()).__name__)"),
        ("Crea una clase Caja, una instancia, asigna c.valor=5 e imprimelo", "class Caja:\n    pass\nc = Caja()\nc.valor = 5\nprint(c.valor)"),
        ("Crea clase Punto, instancia, asigna x=3 y=4, imprime x+y", "class Punto:\n    pass\np = Punto()\np.x = 3\np.y = 4\nprint(p.x + p.y)"),
        ("Crea clase Usuario, asigna nombre='Ana' e imprimelo", "class Usuario:\n    pass\nu = Usuario()\nu.nombre = 'Ana'\nprint(u.nombre)"),
        ("Crea clase Coche, asigna marca='Toyota' y annio=2020, imprime con f-string", "class Coche:\n    pass\nc = Coche()\nc.marca = 'Toyota'\nc.annio = 2020\nprint(f'{c.marca} {c.annio}')"),
        ("Crea dos instancias de Animal y asignales nombres distintos; imprime ambos", "class Animal:\n    pass\na = Animal()\nb = Animal()\na.n = 'gato'\nb.n = 'perro'\nprint(a.n, b.n)"),
        ("Crea clase Producto, asigna precio=100, aplicale 10% e imprime", "class Producto:\n    pass\np = Producto()\np.precio = 100\nprint(p.precio * 0.9)"),
        ("Crea clase Contador, asigna n=0, sumale 1 tres veces, imprime n", "class Contador:\n    pass\nc = Contador()\nc.n = 0\nfor _ in range(3):\n    c.n += 1\nprint(c.n)"),
        ("Crea clase Libro, asigna paginas=200 e imprime cuantas faltan para 250", "class Libro:\n    pass\nl = Libro()\nl.paginas = 200\nprint(250 - l.paginas)"),
        ("Crea clase Punto con atributos x=1,y=2; imprime la tupla (x,y)", "class Punto:\n    pass\np = Punto()\np.x = 1\np.y = 2\nprint((p.x, p.y))"),
    ]))
    sets.append(mapped(
        lambda v: f"Define clase Perro con __init__(self, nombre); crea Perro({v!r}) e imprime su .nombre.",
        lambda v: f"class Perro:\n    def __init__(self, nombre):\n        self.nombre = nombre\nd = Perro({v!r})\nprint(d.nombre)",
        ['Rex', 'Toby', 'Luna', 'Max', 'Kira', 'Bobby', 'Nina', 'Zeus', 'Lola', 'Rocky'],
    ))
    sets.append(mapped(
        lambda t: f"Define Producto con __init__(self, nombre, precio); crea Producto({t[0]!r}, {t[1]}) e imprime el precio.",
        lambda t: ("class Producto:\n    def __init__(self, nombre, precio):\n"
                   "        self.nombre = nombre\n        self.precio = precio\n"
                   f"p = Producto({t[0]!r}, {t[1]})\nprint(p.precio)"),
        [('Libro', 25), ('Mouse', 15), ('Teclado', 45), ('Monitor', 300), ('Cable', 8),
         ('Silla', 120), ('Lampara', 33), ('Taza', 12), ('Cuaderno', 6), ('Mochila', 80)],
    ))
    sets.append(mapped(
        lambda t: f"Define Persona con nombre y edad; crea Persona({t[0]!r}, {t[1]}) e imprime ambos atributos separados por espacio.",
        lambda t: ("class Persona:\n    def __init__(self, nombre, edad):\n"
                   "        self.nombre = nombre\n        self.edad = edad\n"
                   f"p = Persona({t[0]!r}, {t[1]})\nprint(p.nombre, p.edad)"),
        [('Ana', 22), ('Leo', 30), ('Mia', 19), ('Sam', 41), ('Eva', 27),
         ('Tom', 35), ('Zoe', 24), ('Ian', 18), ('Ola', 33), ('Ben', 29)],
    ))
    sets.append(mapped(
        lambda t: f"Define Ticket con titulo y estado; crea Ticket({t[0]!r}, {t[1]!r}) e imprime: '<titulo> [<estado>]'.",
        lambda t: ("class Ticket:\n    def __init__(self, titulo, estado):\n"
                   "        self.titulo = titulo\n        self.estado = estado\n"
                   f"t = Ticket({t[0]!r}, {t[1]!r})\nprint(f'{{t.titulo}} [{{t.estado}}]')"),
        [('Bug login', 'abierto'), ('Error pago', 'cerrado'), ('Mejora UI', 'abierto'),
         ('Crash app', 'en progreso'), ('Typo', 'cerrado'), ('Lentitud', 'abierto'),
         ('Falla email', 'en progreso'), ('Permiso', 'abierto'), ('Reporte', 'cerrado'),
         ('Caida', 'abierto')],
    ))

    # E.B — metodos
    sets.append(mapped(
        lambda t: f"Define Calc con metodo sumar(self, a, b) que retorne a+b; crea Calc() e imprime sumar({t[0]}, {t[1]}).",
        lambda t: ("class Calc:\n    def sumar(self, a, b):\n        return a + b\n"
                   f"c = Calc()\nprint(c.sumar({t[0]}, {t[1]}))"),
        [(2, 3), (10, 5), (7, 8), (100, 1), (4, 4), (9, 6), (12, 13), (0, 7), (15, 5), (8, 8)],
    ))
    sets.append(mapped(
        lambda v: f"Define Circulo con radio en __init__ y metodo diametro(self) que retorne radio*2; crea Circulo({v}) e imprime su diametro.",
        lambda v: ("class Circulo:\n    def __init__(self, radio):\n        self.radio = radio\n"
                   "    def diametro(self):\n        return self.radio * 2\n"
                   f"c = Circulo({v})\nprint(c.diametro())"),
        [3, 5, 1, 10, 7, 2, 8, 4, 6, 9],
    ))
    sets.append(mapped(
        lambda t: f"Define Saludo con nombre en __init__ y metodo saludar(self, otro) que retorne 'Hola <otro>, soy <nombre>'; usa nombre={t[0]!r}, otro={t[1]!r}.",
        lambda t: ("class Saludo:\n    def __init__(self, nombre):\n        self.nombre = nombre\n"
                   "    def saludar(self, otro):\n        return f'Hola {otro}, soy {self.nombre}'\n"
                   f"s = Saludo({t[0]!r})\nprint(s.saludar({t[1]!r}))"),
        [('Ana', 'Leo'), ('Bot', 'Sam'), ('Eva', 'Tom'), ('Mia', 'Zoe'), ('Ivan', 'Ola'),
         ('Noa', 'Ben'), ('Sara', 'Pia'), ('Hugo', 'Lia'), ('Caro', 'Dani'), ('Beto', 'Ana')],
    ))
    sets.append(mapped(
        lambda t: f"Define Rectangulo con base y altura; agrega area() y perimetro(); crea Rectangulo({t[0]}, {t[1]}) e imprime area y perimetro separados por espacio.",
        lambda t: ("class Rectangulo:\n    def __init__(self, base, altura):\n"
                   "        self.base = base\n        self.altura = altura\n"
                   "    def area(self):\n        return self.base * self.altura\n"
                   "    def perimetro(self):\n        return 2 * (self.base + self.altura)\n"
                   f"r = Rectangulo({t[0]}, {t[1]})\nprint(r.area(), r.perimetro())"),
        [(3, 4), (5, 2), (10, 1), (6, 6), (8, 3), (7, 5), (2, 9), (4, 4), (12, 2), (1, 1)],
    ))
    sets.append(mapped(
        lambda ops: f"Define Cuenta con saldo=0; metodo depositar(self, n) suma al saldo; metodo saldo_actual(self) lo retorna. Deposita {ops} e imprime el saldo final.",
        lambda ops: ("class Cuenta:\n    def __init__(self):\n        self.saldo = 0\n"
                     "    def depositar(self, n):\n        self.saldo += n\n"
                     "    def saldo_actual(self):\n        return self.saldo\n"
                     "c = Cuenta()\n"
                     + "".join(f"c.depositar({n})\n" for n in ops)
                     + "print(c.saldo_actual())"),
        [[100, 50], [10, 20, 30], [5], [100, 100, 100], [7, 3],
         [40, 60], [1, 1, 1, 1], [200], [33, 67], [25, 25, 25, 25]],
    ))

    # E.C — dunder y composicion
    sets.append(mapped(
        lambda t: f"Define Punto con x,y y __str__ que devuelva '(x, y)'; imprime el objeto Punto({t[0]}, {t[1]}).",
        lambda t: ("class Punto:\n    def __init__(self, x, y):\n        self.x = x\n        self.y = y\n"
                   "    def __str__(self):\n        return f'({self.x}, {self.y})'\n"
                   f"print(Punto({t[0]}, {t[1]}))"),
        [(1, 2), (3, 4), (0, 0), (5, 9), (10, 20), (7, 7), (2, 8), (4, 1), (6, 3), (9, 5)],
    ))
    sets.append(mapped(
        lambda v: f"Define Item con id en __init__ y __repr__ que devuelva 'Item(<id>)'; imprime repr(Item({v})).",
        lambda v: ("class Item:\n    def __init__(self, id):\n        self.id = id\n"
                   "    def __repr__(self):\n        return f'Item({self.id})'\n"
                   f"print(repr(Item({v})))"),
        [5, 1, 10, 42, 7, 99, 3, 8, 21, 100],
    ))
    sets.append(mapped(
        lambda n: f"Define Contador con atributo de CLASE total=0 que aumenta en cada __init__; crea {n} instancias e imprime Contador.total.",
        lambda n: ("class Contador:\n    total = 0\n    def __init__(self):\n        Contador.total += 1\n"
                   + "".join("Contador()\n" for _ in range(n))
                   + "print(Contador.total)"),
        [2, 3, 1, 5, 4, 6, 2, 7, 3, 8],
    ))
    sets.append(mapped(
        lambda t: f"Define Temperatura con celsius en __init__ y metodo fahrenheit() (c*9/5+32); imprime la fahrenheit de Temperatura({t}).",
        lambda t: ("class Temperatura:\n    def __init__(self, celsius):\n        self.celsius = celsius\n"
                   "    def fahrenheit(self):\n        return self.celsius * 9 / 5 + 32\n"
                   f"print(Temperatura({t}).fahrenheit())"),
        [0, 100, 25, 37, 10, 40, 5, 30, 20, 15],
    ))
    sets.append(mapped(
        lambda nums: f"Define Carrito con una lista interna; metodo agregar(p) y total() que sume los precios. Agrega {nums} e imprime el total.",
        lambda nums: ("class Carrito:\n    def __init__(self):\n        self.items = []\n"
                      "    def agregar(self, p):\n        self.items.append(p)\n"
                      "    def total(self):\n        return sum(self.items)\n"
                      "c = Carrito()\n"
                      + "".join(f"c.agregar({n})\n" for n in nums)
                      + "print(c.total())"),
        [[10, 20, 30], [5, 5], [100], [1, 2, 3, 4], [50, 50],
         [7, 8, 9], [200, 300], [15, 25, 10], [9, 9, 9], [40]],
    ))

    # E.D — herencia
    sets.append(mapped(
        lambda t: f"Define Animal con metodo hablar() que retorne 'sonido'; define {t[0]}(Animal) que sobrescriba hablar() para retornar {t[1]!r}; imprime {t[0]}().hablar().",
        lambda t: ("class Animal:\n    def hablar(self):\n        return 'sonido'\n"
                   f"class {t[0]}(Animal):\n    def hablar(self):\n        return {t[1]!r}\n"
                   f"print({t[0]}().hablar())"),
        [('Perro', 'guau'), ('Gato', 'miau'), ('Vaca', 'muu'), ('Pato', 'cuac'),
         ('Leon', 'roar'), ('Oveja', 'bee'), ('Rana', 'croac'), ('Buho', 'uhu'),
         ('Lobo', 'auu'), ('Pollo', 'pio')],
    ))
    sets.append(mapped(
        lambda t: f"Define Empleado con metodo rol() -> 'empleado'; define {t[0]}(Empleado) que sobrescriba rol() -> {t[1]!r}; imprime {t[0]}().rol().",
        lambda t: ("class Empleado:\n    def rol(self):\n        return 'empleado'\n"
                   f"class {t[0]}(Empleado):\n    def rol(self):\n        return {t[1]!r}\n"
                   f"print({t[0]}().rol())"),
        [('Gerente', 'gerente'), ('Soporte', 'soporte'), ('Dev', 'desarrollador'),
         ('QA', 'tester'), ('Lider', 'lider'), ('Becario', 'becario'), ('Admin', 'admin'),
         ('Ventas', 'ventas'), ('RH', 'recursos humanos'), ('CEO', 'director')],
    ))
    sets.append(mapped(
        lambda t: f"Define Base con __init__(self, x) que guarde self.x; define Hija(Base) con __init__(self, x, y) que llame super().__init__(x) y guarde self.y; crea Hija({t[0]}, {t[1]}) e imprime x+y.",
        lambda t: ("class Base:\n    def __init__(self, x):\n        self.x = x\n"
                   "class Hija(Base):\n    def __init__(self, x, y):\n"
                   "        super().__init__(x)\n        self.y = y\n"
                   f"h = Hija({t[0]}, {t[1]})\nprint(h.x + h.y)"),
        [(1, 2), (10, 5), (3, 7), (4, 4), (8, 1), (6, 9), (2, 2), (5, 5), (12, 3), (7, 8)],
    ))
    sets.append(mapped(
        lambda t: f"Define A con metodo saludo() -> 'Hola'; define B(A) cuyo saludo() retorne super().saludo() + {t!r}; imprime B().saludo().",
        lambda t: ("class A:\n    def saludo(self):\n        return 'Hola'\n"
                   f"class B(A):\n    def saludo(self):\n        return super().saludo() + {t!r}\n"
                   "print(B().saludo())"),
        [' a todos', ' mundo', ' equipo', '!', ' Odoo', ' Ana', ' de nuevo',
         ' amigos', ' Python', ' :)'],
    ))
    sets.append(explicit([
        ("Define Animal y Perro(Animal); imprime isinstance(Perro(), Animal)", "class Animal:\n    pass\nclass Perro(Animal):\n    pass\nprint(isinstance(Perro(), Animal))"),
        ("Define A y B(A); imprime issubclass(B, A)", "class A:\n    pass\nclass B(A):\n    pass\nprint(issubclass(B, A))"),
        ("Polimorfismo: lista de figuras con area(), imprime la suma de areas", "class Cuadrado:\n    def __init__(self, l):\n        self.l = l\n    def area(self):\n        return self.l * self.l\nfiguras = [Cuadrado(2), Cuadrado(3)]\nprint(sum(f.area() for f in figuras))"),
        ("Define Gato(Animal); imprime isinstance de un int como Animal (False)", "class Animal:\n    pass\nclass Gato(Animal):\n    pass\nprint(isinstance(5, Animal))"),
        ("Polimorfismo: dos clases con hablar(); recorre e imprime cada sonido", "class Perro:\n    def hablar(self):\n        return 'guau'\nclass Gato:\n    def hablar(self):\n        return 'miau'\nfor a in [Perro(), Gato()]:\n    print(a.hablar(), end=' ')"),
        ("Verifica issubclass(bool, int) (True en Python)", "print(issubclass(bool, int))"),
        ("Define Vehiculo y Auto(Vehiculo); imprime el nombre de la clase base", "class Vehiculo:\n    pass\nclass Auto(Vehiculo):\n    pass\nprint(Auto.__bases__[0].__name__)"),
        ("Recorre figuras [Cuadrado(2),Cuadrado(4)] e imprime areas separadas", "class Cuadrado:\n    def __init__(self, l):\n        self.l = l\n    def area(self):\n        return self.l ** 2\nfor f in [Cuadrado(2), Cuadrado(4)]:\n    print(f.area(), end=' ')"),
        ("isinstance con herencia de 2 niveles: C(B), B(A) -> isinstance(C(),A)", "class A:\n    pass\nclass B(A):\n    pass\nclass C(B):\n    pass\nprint(isinstance(C(), A))"),
        ("Define Forma base con area()=0 y Circulo que la sobrescribe; imprime ambas", "class Forma:\n    def area(self):\n        return 0\nclass Circulo(Forma):\n    def __init__(self, r):\n        self.r = r\n    def area(self):\n        return round(3.1416 * self.r ** 2, 2)\nprint(Forma().area(), Circulo(1).area())"),
    ]))

    return sets


LEVEL_BUILDERS = {"A": level_a, "B": level_b, "C": level_c, "D": level_d, "E": level_e}
EXPECTED_CORE_SETS = 20


def load_level_blocks(level: str) -> list[tuple[str, dict]]:
    """Return ordered (block_letter, block_data) pairs from kumon-levels.yaml."""
    with open(STD_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    level_data = data["levels"][level.upper()]
    return [(k.upper(), v) for k, v in level_data.get("blocks", {}).items()]


def expected_set_count(level: str) -> int:
    return sum(len(b[1].get("sets", [])) for b in load_level_blocks(level))


# ---------------------------------------------------------------------------
# Standard times (read back from kumon-levels.yaml for per-page estimates)
# ---------------------------------------------------------------------------

def load_set_standards() -> dict[str, list[int]]:
    with open(STD_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    out: dict[str, list[int]] = {}
    for level, ldata in data["levels"].items():
        stds: list[int] = []
        for _bl, block_data in ldata.get("blocks", {}).items():
            for s in block_data.get("sets", []):
                stds.append(s.get("standard_seconds", 600))
        out[level.upper()] = stds
    return out


def _code_uses(code: str, name: str) -> bool:
    return bool(re.search(rf"\b{re.escape(name)}\s*\(", code))


def _has_membership_in(code: str) -> bool:
    """True for `x in y` membership, not `for x in y` loops."""
    stripped = re.sub(r"\bfor\s+[^:\n]+\s+in\b", " ", code)
    return bool(re.search(r"\bin\b", stripped))


def hint_for_drill(prompt: str, code: str, custom: str | None = None) -> str:
    if custom:
        return custom
    p = prompt.lower()
    c = code.lower()
    if "break" in c or "detente" in p:
        return "Usa break para salir del bucle cuando se cumple la condicion."
    if "continue" in c:
        return "Usa continue para saltar a la siguiente iteracion."
    uses_conditional = (
        "if/elif" in p or "si no" in p or " elif " in c
        or bool(re.search(r"(?m)^\s*if\s+", code))
    )
    if uses_conditional and "f-string" not in p:
        return "Usa if/elif/else con sangria de 4 espacios. Imprime dentro de cada rama."
    if "f-string" in p or "f'" in c or 'f"' in c:
        return (
            "Pon f delante de las comillas e inserta variables con {nombre}. "
            "Puedes calcular expresiones dentro de { }."
        )
    if _code_uses(code, "int") and not _code_uses(code, "bool"):
        return "int(valor) convierte a entero. Imprime el resultado con print()."
    if _code_uses(code, "str"):
        return "str(valor) convierte a texto. Imprime el resultado con print()."
    if _code_uses(code, "float"):
        return "float(valor) convierte a numero decimal. Imprime el resultado con print()."
    if _code_uses(code, "bool"):
        return "bool(valor) convierte un valor a True o False. Imprime con print()."
    if _code_uses(code, "round"):
        return "round(numero, decimales) redondea un flotante. Imprime con print()."
    if _code_uses(code, "len"):
        return "len(x) devuelve cuantos elementos tiene x."
    if ".upper()" in c or ".lower()" in c:
        return "Los metodos de string van despues del punto: texto.upper(), texto.lower()."
    if ".split(" in c:
        return ".split(sep) divide un texto usando el separador (espacio por defecto)."
    if " * " in c and "'" in c:
        return "texto * n repite el texto n veces."
    if _has_membership_in(code) and "print(" in c:
        if "seen" in c or "dict" in p or "clave" in p or "diccionario" in p or "{" in code:
            return (
                "x in d busca por LLAVE en O(1). Lo que necesitas encontrar rapido "
                "debe ser la llave (ej. el numero), no el indice."
            )
        return "x in coleccion comprueba si x aparece en la coleccion."
    if "seen[" in c or ".get(" in c:
        return (
            "La llave es lo que buscas despues (ej. el numero). "
            "El valor es informacion extra (ej. el indice): seen[num] = i."
        )
    if re.search(r"\b(and|or|not)\b", code):
        return "Combina condiciones con and, or y not. Imprime True o False."
    if "s[0]" in c or "s[-1]" in c or "s[:" in c:
        return "s[i] accede a un caracter; s[:n] toma los primeros n; s[::-1] invierte."
    if "//" in code or "**" in code or re.search(r"\d\s*%\s*\d", code):
        return "Calcula la expresion dentro de print() e imprime el resultado."
    return "Lee con atención lo que se pide imprimir y construye el código paso a paso."


# ---------------------------------------------------------------------------
# write pages
# ---------------------------------------------------------------------------

def generate_kumon(*, levels: list[str] | None = None) -> int:
    standards = load_set_standards()
    count = 0
    targets = levels or list(LEVEL_BUILDERS.keys())
    for level in targets:
        builder = LEVEL_BUILDERS[level]
        sets = builder()
        expected = expected_set_count(level)
        if len(sets) != expected:
            raise SystemExit(f"Level {level}: expected {expected} sets, got {len(sets)}")
        level_std = standards[level]
        blocks = load_level_blocks(level)
        set_idx = 0
        for block_letter, _block_data in blocks:
            block_sets = _block_data.get("sets", [])
            for set_i, _set_data in enumerate(block_sets):
                drills = sets[set_idx]
                if len(drills) != PAGES_PER_SET:
                    raise SystemExit(
                        f"Level {level} set {set_idx + 1}: expected 10 drills, got {len(drills)}"
                    )
                set_number = set_idx + 1
                std_seconds = level_std[set_idx] if set_idx < len(level_std) else 600
                per_page = max(20, std_seconds // PAGES_PER_SET)
                for j, d in enumerate(drills):
                    order = j + 1
                    page = set_idx * PAGES_PER_SET + order
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
                        "hints": [hint_for_drill(d["prompt"], code, d.get("hint"))] if scaff != "none" else [],
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
# LeetCode checkpoints + level exams
# ---------------------------------------------------------------------------

def lc(pid, title, fn, desc, cases, starter1, *, hints=None, approach="", learning=None, interview_questions=None, solution_code=""):
    default_hints = {
        "suma": ["Suma directa: return a + b.", "No necesitas bucles ni estructuras extra."],
        "invertir": ["Los strings son secuencias: prueba s[::-1] o un bucle.", "¿Qué pasa con string vacío?"],
        "fizzbuzz": ["Divisible por 15 → FizzBuzz; por 3 → Fizz; por 5 → Buzz.", "Usa if/elif en ese orden."],
        "nota": ["Define rangos: A >= 90, B >= 80, etc.", "Compara de mayor a menor con if/elif."],
        "c_a_f": ["Fórmula: c * 9/5 + 32.", "Cuidado con enteros vs float."],
        "bisiesto": ["Divisible por 400 → sí; por 100 (no 400) → no; por 4 → sí.", "Orden de las condiciones importa."],
    }
    default_solutions = {
        "suma": "def suma(a, b):\n    return a + b",
        "invertir": "def invertir(s):\n    return s[::-1]",
        "fizzbuzz": "def fizzbuzz(n):\n    if n % 15 == 0:\n        return 'FizzBuzz'\n    if n % 3 == 0:\n        return 'Fizz'\n    if n % 5 == 0:\n        return 'Buzz'\n    return str(n)",
        "nota": "def nota(score):\n    if score >= 90:\n        return 'A'\n    if score >= 80:\n        return 'B'\n    if score >= 70:\n        return 'C'\n    return 'F'",
        "c_a_f": "def c_a_f(c):\n    return c * 9 / 5 + 32",
        "bisiesto": "def bisiesto(a):\n    if a % 400 == 0:\n        return True\n    if a % 100 == 0:\n        return False\n    return a % 4 == 0",
        "suma_rango": "def suma_rango(n):\n    total = 0\n    for i in range(1, n + 1):\n        total += i\n    return total",
        "contar_pos": "def contar_pos(nums):\n    c = 0\n    for n in nums:\n        if n > 0:\n            c += 1\n    return c",
        "pares": "def pares(a, b):\n    return [x + y for x, y in zip(a, b)]",
        "doble_func": "def inc(n):\n    return n + 1\n\ndef doble_func(x):\n    return inc(inc(x))",
        "factorial": "def factorial(n):\n    r = 1\n    for i in range(2, n + 1):\n        r *= i\n    return r",
        "collatz": "def collatz(n):\n    pasos = 0\n    while n > 1:\n        if n % 2 == 0:\n            n //= 2\n        else:\n            n = n * 3 + 1\n        pasos += 1\n    return pasos",
        "suma_lista": "def suma_lista(nums):\n    return sum(nums)",
        "invertir_lista": "def invertir_lista(nums):\n    return nums[::-1]",
        "contar_palabras": "def contar_palabras(s):\n    return len(s.split()) if s.strip() else 0",
        "segundo_mayor": "def segundo_mayor(nums):\n    uniq = sorted(set(nums), reverse=True)\n    return uniq[1]",
        "es_anagrama": "def es_anagrama(s, t):\n    return sorted(s) == sorted(t)",
        "combinar": "def combinar(a, b):\n    out = dict(a)\n    out.update(b)\n    return out",
        "frecuencia": "def frecuencia(texto):\n    freq = {}\n    for w in texto.split():\n        freq[w] = freq.get(w, 0) + 1\n    return freq",
        "unicos": "def unicos(nums):\n    return len(set(nums))",
        "div_segura": "def div_segura(a, b):\n    try:\n        return a / b\n    except ZeroDivisionError:\n        return 0",
        "agrupar": "def agrupar(items):\n    d = {}\n    for x in items:\n        d[x] = d.get(x, 0) + 1\n    return d",
        "two_sum": "def two_sum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        need = target - n\n        if need in seen:\n            return [seen[need], i]\n        seen[n] = i\n    return []",
        "run_counter": "def run_counter(n):\n    class Counter:\n        def __init__(self):\n            self.c = 0\n        def inc(self):\n            self.c += 1\n    c = Counter()\n    for _ in range(n):\n        c.inc()\n    return c.c",
        "final_balance": "def final_balance(deps):\n    class Cuenta:\n        def __init__(self):\n            self.s = 0\n        def deposito(self, n):\n            self.s += n\n    c = Cuenta()\n    for d in deps:\n        c.deposito(d)\n    return c.s",
        "point_str": "def point_str(x, y):\n    class Punto:\n        def __init__(self, x, y):\n            self.x = x\n            self.y = y\n        def __str__(self):\n            return f'({self.x}, {self.y})'\n    return str(Punto(x, y))",
        "square_area": "def square_area(side):\n    class Shape:\n        def area(self):\n            return 0\n    class Square(Shape):\n        def __init__(self, s):\n            self.s = s\n        def area(self):\n            return self.s * self.s\n    return Square(side).area()",
        "stack_top": "def stack_top(valores):\n    class Stack:\n        def __init__(self):\n            self.data = []\n        def push(self, x):\n            self.data.append(x)\n        def top(self):\n            return self.data[-1]\n    s = Stack()\n    for v in valores:\n        s.push(v)\n    return s.top()",
        "total_area": "def total_area(lados):\n    class Cuadrado:\n        def __init__(self, l):\n            self.l = l\n        def area(self):\n            return self.l * self.l\n    return sum(Cuadrado(l).area() for l in lados)",
    }
    fn_hints = hints or default_hints.get(fn, [
        "Identifica qué operación pide el enunciado.",
        "Empieza con el caso más simple y luego casos borde.",
        "Prueba con los ejemplos del enunciado.",
    ])
    return {
        "id": pid, "title": title, "fn_name": fn, "description": desc,
        "test_cases": cases,
        "hints": fn_hints,
        "approach": approach or "Lee el enunciado, identifica entradas/salida y resuelve paso a paso con la lógica que ya conoces.",
        "learning": learning or [
            "Traducir enunciado a código Python",
            "Probar con los ejemplos dados",
            "Manejar casos borde antes de enviar",
        ],
        "interview_questions": interview_questions or [
            "¿Cuál es la complejidad de tu solución?",
            "¿Qué casos borde consideraste?",
            "¿Hay una forma más eficiente?",
        ],
        "solution_code": solution_code or default_solutions.get(fn, ""),
        "tiers": {
            1: {
                "starter_code": starter1,
                "explain_checklist": [
                    "Lee el enunciado y los ejemplos",
                    "Identifica entradas, salida y casos borde",
                    "Piensa en el patrón antes de escribir código",
                ],
                "hints_allowed": True,
            },
            2: {
                "starter_code": f"def {fn}(*args):\n    pass",
                "narration_prompts": [
                    "Explica tu enfoque en voz alta paso a paso",
                    "¿Cuál es la complejidad temporal y espacial?",
                ],
                "hints_allowed": True,
            },
            3: {
                "starter_code": f"def {fn}(*args):\n    pass",
                "narration_prompts": [],
                "hints_allowed": False,
            },
        },
    }


def generate_leetcode() -> int:
    problems = {
        "level-a": [
            lc("a-cp-sum-pair", "Suma de dos numeros", "suma", "Retorna a + b.",
               [{"args": [2, 3], "expected": 5}, {"args": [10, 90], "expected": 100}],
               "def suma(a, b):\n    return ___"),
            lc("a-cp-reverse-string", "Invertir texto", "invertir", "Retorna el texto al reves.",
               [{"args": ["python"], "expected": "nohtyp"}, {"args": ["ana"], "expected": "ana"}],
               "def invertir(s):\n    return ___"),
            lc("a-cp-fizzbuzz", "FizzBuzz de un numero", "fizzbuzz", "Retorna 'Fizz','Buzz','FizzBuzz' o el numero como texto.",
               [{"args": [3], "expected": "Fizz"}, {"args": [5], "expected": "Buzz"}, {"args": [15], "expected": "FizzBuzz"}, {"args": [7], "expected": "7"}],
               "def fizzbuzz(n):\n    # usa n % 3 y n % 5\n    return ___"),
            lc("a-cp-grade", "Nota a letra", "nota", "Retorna 'A','B','C' o 'F' segun el score.",
               [{"args": [95], "expected": "A"}, {"args": [82], "expected": "B"}, {"args": [71], "expected": "C"}, {"args": [50], "expected": "F"}],
               "def nota(score):\n    return ___"),
            lc("a-exam-temperature", "Celsius a Fahrenheit", "c_a_f", "Convierte celsius a fahrenheit (c*9/5+32).",
               [{"args": [0], "expected": 32.0}, {"args": [100], "expected": 212.0}],
               "def c_a_f(c):\n    return ___"),
            lc("a-exam-leap-year", "Anio bisiesto", "bisiesto", "Retorna True si el anio es bisiesto.",
               [{"args": [2024], "expected": True}, {"args": [1900], "expected": False}, {"args": [2000], "expected": True}],
               "def bisiesto(a):\n    return ___"),
        ],
        "level-b": [
            lc("b-cp-sum-range", "Suma de 1 a n", "suma_rango", "Retorna la suma de 1..n con un bucle.",
               [{"args": [5], "expected": 15}, {"args": [10], "expected": 55}],
               "def suma_rango(n):\n    total = 0\n    # bucle for\n    return total"),
            lc("b-cp-count-positive", "Contar positivos", "contar_pos", "Cuenta cuantos numeros son > 0.",
               [{"args": [[1, -2, 3, 0, 5]], "expected": 3}, {"args": [[-1, -2]], "expected": 0}],
               "def contar_pos(nums):\n    c = 0\n    # recorre nums\n    return c"),
            lc("b-cp-pair-sums", "Sumas por pares", "pares", "Con zip, suma elemento a elemento de dos listas.",
               [{"args": [[1, 2, 3], [4, 5, 6]], "expected": [5, 7, 9]}],
               "def pares(a, b):\n    # usa zip\n    return ___"),
            lc("b-cp-apply-twice", "Aplicar dos veces", "doble_func", "Aplica f(f(x)).",
               [{"args": [3], "expected": 5}, {"args": [10], "expected": 12}],
               "def inc(n):\n    return n + 1\n\ndef doble_func(x):\n    # aplica inc dos veces\n    return ___"),
            lc("b-exam-factorial", "Factorial", "factorial", "Retorna n! con un bucle.",
               [{"args": [5], "expected": 120}, {"args": [0], "expected": 1}],
               "def factorial(n):\n    r = 1\n    # bucle\n    return r"),
            lc("b-exam-collatz", "Pasos de Collatz", "collatz", "Cuenta pasos hasta llegar a 1 (par->/2, impar->*3+1).",
               [{"args": [1], "expected": 0}, {"args": [8], "expected": 3}],
               "def collatz(n):\n    pasos = 0\n    while n > 1:\n        # ...\n        pasos += 1\n    return pasos"),
        ],
        "level-c": [
            lc("c-cp-list-sum", "Suma de lista", "suma_lista", "Suma todos los elementos.",
               [{"args": [[1, 2, 3, 4]], "expected": 10}, {"args": [[]], "expected": 0}],
               "def suma_lista(nums):\n    return ___"),
            lc("c-cp-reverse-list", "Invertir lista", "invertir_lista", "Retorna la lista invertida.",
               [{"args": [[1, 2, 3]], "expected": [3, 2, 1]}],
               "def invertir_lista(nums):\n    return ___"),
            lc("c-cp-evens", "Filtrar pares", "pares", "Retorna solo los numeros pares.",
               [{"args": [[1, 2, 3, 4, 5, 6]], "expected": [2, 4, 6]}],
               "def pares(nums):\n    return ___",
               solution_code="def pares(nums):\n    return [n for n in nums if n % 2 == 0]"),
            lc("c-cp-word-count", "Contar palabras", "contar_palabras", "Cuenta cuantas palabras tiene el texto.",
               [{"args": ["hola mundo python"], "expected": 3}, {"args": [""], "expected": 0}],
               "def contar_palabras(s):\n    return ___"),
            lc("c-exam-second-largest", "Segundo mayor", "segundo_mayor", "Retorna el segundo numero mas grande (distintos).",
               [{"args": [[3, 1, 4, 1, 5]], "expected": 4}, {"args": [[10, 20]], "expected": 10}],
               "def segundo_mayor(nums):\n    return ___"),
            lc("c-exam-anagram", "Anagrama", "es_anagrama", "True si t es anagrama de s.",
               [{"args": ["roma", "amor"], "expected": True}, {"args": ["abc", "abd"], "expected": False}],
               "def es_anagrama(s, t):\n    return ___"),
        ],
        "level-d": [
            lc("d-cp-merge-dicts", "Combinar dicts", "combinar", "Combina dos dicts (b sobreescribe a).",
               [{"args": [{"a": 1}, {"b": 2}], "expected": {"a": 1, "b": 2}}],
               "def combinar(a, b):\n    return ___"),
            lc("d-cp-word-freq", "Frecuencia de palabras", "frecuencia", "Cuenta cada palabra y retorna un dict.",
               [{"args": ["a b a"], "expected": {"a": 2, "b": 1}}],
               "def frecuencia(texto):\n    freq = {}\n    # recorre texto.split()\n    return freq"),
            lc("d-cp-unique", "Elementos unicos", "unicos", "Retorna la cantidad de elementos unicos.",
               [{"args": [[1, 1, 2, 3, 3]], "expected": 3}],
               "def unicos(nums):\n    return ___"),
            lc("d-cp-safe-div", "Division segura", "div_segura", "Retorna a/b o 0 si b es 0.",
               [{"args": [10, 2], "expected": 5.0}, {"args": [5, 0], "expected": 0}],
               "def div_segura(a, b):\n    # usa try/except\n    return ___"),
            lc("d-exam-group-by", "Agrupar y contar", "agrupar", "Cuenta la frecuencia de cada elemento.",
               [{"args": [["x", "y", "x", "z", "x"]], "expected": {"x": 3, "y": 1, "z": 1}}],
               "def agrupar(items):\n    d = {}\n    return d"),
            lc("d-exam-two-sum", "Two Sum", "two_sum", "Retorna los indices de los dos numeros que suman target.",
               [{"args": [[2, 7, 11, 15], 9], "expected": [0, 1]}],
               "def two_sum(nums, target):\n    # usa un dict de vistos\n    return ___"),
        ],
        "level-e": [
            lc("e-cp-counter", "Contador con clase", "run_counter", "Crea una clase Counter, incrementa n veces y retorna el conteo.",
               [{"args": [3], "expected": 3}, {"args": [0], "expected": 0}],
               "def run_counter(n):\n    class Counter:\n        def __init__(self):\n            self.c = 0\n        def inc(self):\n            self.c += 1\n    # crea, incrementa n veces y retorna\n    return ___"),
            lc("e-cp-bank", "Saldo final", "final_balance", "Crea una clase Cuenta con deposito y retorna el saldo final.",
               [{"args": [[10, 20, 5]], "expected": 35}, {"args": [[]], "expected": 0}],
               "def final_balance(deps):\n    class Cuenta:\n        def __init__(self):\n            self.s = 0\n        def deposito(self, n):\n            self.s += n\n    return ___"),
            lc("e-cp-point-str", "Punto como texto", "point_str", "Crea Punto con __str__ '(x, y)' y retorna str(Punto).",
               [{"args": [1, 2], "expected": "(1, 2)"}],
               "def point_str(x, y):\n    class Punto:\n        def __init__(self, x, y):\n            self.x = x\n            self.y = y\n        def __str__(self):\n            return f'({self.x}, {self.y})'\n    return ___"),
            lc("e-cp-shape-area", "Area por herencia", "square_area", "Define Shape base y Square(Shape) que sobrescribe area(); retorna el area.",
               [{"args": [4], "expected": 16}, {"args": [3], "expected": 9}],
               "def square_area(side):\n    class Shape:\n        def area(self):\n            return 0\n    class Square(Shape):\n        def __init__(self, s):\n            self.s = s\n        def area(self):\n            return ___\n    return Square(side).area()"),
            lc("e-exam-stack", "Pila (Stack)", "stack_top", "Crea una Stack con push/pop; aplica las operaciones y retorna el tope.",
               [{"args": [[1, 2, 3]], "expected": 3}, {"args": [[5]], "expected": 5}],
               "def stack_top(valores):\n    class Stack:\n        def __init__(self):\n            self.data = []\n        def push(self, x):\n            self.data.append(x)\n        def top(self):\n            return self.data[-1]\n    return ___"),
            lc("e-exam-shapes", "Suma de areas (polimorfismo)", "total_area", "Dada una lista de lados de cuadrados, suma sus areas usando una clase.",
               [{"args": [[2, 3]], "expected": 13}, {"args": [[1, 1, 1]], "expected": 3}],
               "def total_area(lados):\n    class Cuadrado:\n        def __init__(self, l):\n            self.l = l\n        def area(self):\n            return self.l * self.l\n    return ___"),
        ],
    }
    count = 0
    for level, probs in problems.items():
        for p in probs:
            write_yaml(CONTENT / level / "leetcode" / f"{p['id']}.yaml", p)
            count += 1
    return count


# ---------------------------------------------------------------------------
# Interview questions (level completion exam)
# ---------------------------------------------------------------------------

def generate_interview() -> int:
    questions = {
        "level-a": [
            {"id": "a-int-1", "question": "Cual es la diferencia entre un entero (int) y una cadena (str)? Da un ejemplo de cada uno.",
             "rubric": ["int representa numeros", "str representa texto entre comillas", "se pueden convertir con int()/str()"],
             "sample_answer": "Un int es un numero (ej. 42) con el que puedes hacer aritmetica; un str es texto entre comillas (ej. '42'). Puedes convertir con int('42') o str(42)."},
            {"id": "a-int-2", "question": "Que hace una f-string y por que es util? Muestra un ejemplo.",
             "rubric": ["interpola variables dentro del texto", "sintaxis f'...{var}...'", "mas legible que concatenar"],
             "sample_answer": "Una f-string inserta el valor de variables o expresiones dentro de un texto: f'{nombre} tiene {edad} anios'. Es mas legible que concatenar con +."},
        ],
        "level-b": [
            {"id": "b-int-1", "question": "Cual es la diferencia entre un bucle for y un while? Cuando usarias cada uno?",
             "rubric": ["for itera sobre una secuencia o rango conocido", "while repite mientras una condicion sea verdadera", "for cuando sabes cuantas veces; while cuando depende de una condicion"],
             "sample_answer": "for se usa cuando recorres una secuencia o sabes el numero de iteraciones (range). while se usa cuando repites hasta que se cumpla/deje de cumplir una condicion, sin saber cuantas veces."},
            {"id": "b-int-2", "question": "Que hace la palabra return en una funcion y en que se diferencia de print?",
             "rubric": ["return devuelve un valor al que llama", "print solo muestra en pantalla", "el valor retornado se puede reutilizar"],
             "sample_answer": "return entrega un valor a quien llamo la funcion para poder usarlo despues; print solo muestra texto en consola y no devuelve nada utilizable."},
        ],
        "level-c": [
            {"id": "c-int-1", "question": "Cual es la diferencia entre una lista y una tupla en Python?",
             "rubric": ["la lista es mutable", "la tupla es inmutable", "tuplas para datos fijos, listas para datos que cambian"],
             "sample_answer": "Una lista es mutable (puedes agregar/quitar/cambiar elementos); una tupla es inmutable (no cambia tras crearse). Usas tuplas para datos fijos como coordenadas y listas para colecciones que cambian."},
            {"id": "c-int-2", "question": "Que es slicing y como obtendrias los ultimos dos elementos de una lista?",
             "rubric": ["slicing extrae una porcion con [inicio:fin:paso]", "indices negativos cuentan desde el final", "lista[-2:] da los ultimos dos"],
             "sample_answer": "Slicing extrae una sublista con lista[inicio:fin:paso]. Para los ultimos dos: lista[-2:], usando indices negativos que cuentan desde el final."},
        ],
        "level-d": [
            {"id": "d-int-1", "question": "Cuando usarias un diccionario y cuando un set? Da un ejemplo de cada uno.",
             "rubric": ["dict mapea claves a valores", "set guarda elementos unicos sin orden", "dict para asociaciones; set para unicidad/pertenencia"],
             "sample_answer": "Un dict asocia claves con valores (ej. {'precio': 100}); un set guarda elementos unicos y permite comprobar pertenencia rapido (ej. quitar duplicados). Uso dict para mapear datos y set para unicidad."},
            {"id": "d-int-2", "question": "Para que sirve try/except y por que es mejor que dejar que el programa falle?",
             "rubric": ["captura errores en tiempo de ejecucion", "permite manejar el fallo con gracia", "evita que el programa se caiga"],
             "sample_answer": "try/except captura excepciones para manejarlas (mostrar un mensaje, usar un valor por defecto) en lugar de que el programa se detenga abruptamente, haciendolo mas robusto."},
        ],
        "level-e": [
            {"id": "e-int-1", "question": "Que es __init__ y que significa self en una clase?",
             "rubric": ["__init__ es el constructor", "self es la instancia actual", "los atributos se guardan en self"],
             "sample_answer": "__init__ es el metodo que se ejecuta al crear un objeto e inicializa sus atributos. self es la referencia a la instancia actual, por eso guardamos datos como self.nombre."},
            {"id": "e-int-2", "question": "Explica que es la herencia y para que sirve sobrescribir un metodo.",
             "rubric": ["una subclase hereda de una clase base", "reutiliza y extiende comportamiento", "sobrescribir cambia el comportamiento heredado"],
             "sample_answer": "La herencia permite que una subclase reutilice atributos y metodos de una clase base. Sobrescribir un metodo redefine su comportamiento en la subclase, logrando polimorfismo."},
        ],
    }
    count = 0
    for level, qs in questions.items():
        for q in qs:
            q["category"] = "python"
            write_yaml(CONTENT / level / "interview" / f"{q['id']}.yaml", q)
            count += 1
    return count


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Kumon and related content.")
    parser.add_argument(
        "--level",
        action="append",
        choices=list(LEVEL_BUILDERS.keys()),
        help="Regenerate only these Kumon levels (may repeat). Omit to rebuild all levels.",
    )
    parser.add_argument(
        "--kumon-only",
        action="store_true",
        help="Only regenerate Kumon YAML pages.",
    )
    args = parser.parse_args()

    if args.level:
        print(f"Regenerating Kumon level(s): {', '.join(args.level)}...")
        k = generate_kumon(levels=[lv.upper() for lv in args.level])
        print(f"  -> {k} Kumon pages")
        return

    if CONTENT.exists():
        print("Cleaning old Python content...")
        shutil.rmtree(CONTENT)
    print("Generating Kumon pages (A-E, 200 each)...")
    k = generate_kumon()
    print(f"  -> {k} Kumon pages")
    print("Generating LeetCode checkpoints + exams...")
    lc_count = generate_leetcode()
    print(f"  -> {lc_count} LeetCode problems")
    print("Generating Interview exam questions...")
    iv = generate_interview()
    print(f"  -> {iv} interview questions")
    print("Done.")


if __name__ == "__main__":
    main()
