"""Generate SDE program YAML: theory sections, algorithm sheets, SQL drills."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sde_algo_sheets import build_all_algos, sde_algo_ids  # noqa: E402
from sde_theory import theory_weeks  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "content" / "sde"

TWO_SUM_TESTS = [
    {"args": [[2, 7, 11, 15], 9], "expected": [0, 1]},
    {"args": [[3, 2, 4], 6], "expected": [1, 2]},
    {"args": [[3, 3], 6], "expected": [0, 1]},
]
DUP_TESTS = [
    {"args": [[1, 2, 3, 1]], "expected": True},
    {"args": [[1, 2, 3, 4]], "expected": False},
]
ANAGRAM_TESTS = [
    {"args": ["anagram", "nagaram"], "expected": True},
    {"args": ["rat", "car"], "expected": False},
]
TWO_SUM_II_TESTS = [
    {"args": [[2, 7, 11, 15], 9], "expected": [1, 2]},
    {"args": [[2, 3, 4], 6], "expected": [1, 3]},
]

PY_VARS = [
    ("nums", "target"),
    ("arr", "k"),
    ("xs", "need"),
    ("values", "goal"),
    ("items", "sum_to"),
]
CS_VARS = [
    ("nums", "target"),
    ("arr", "k"),
    ("xs", "need"),
    ("values", "goal"),
    ("items", "sumTo"),
]


def dump(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )


def py_two_sum_full(a: str, t: str) -> str:
    return (
        f"def two_sum({a}, {t}):\n"
        f"    seen = {{}}\n"
        f"    for i, n in enumerate({a}):\n"
        f"        want = {t} - n\n"
        f"        if want in seen:\n"
        f"            return [seen[want], i]\n"
        f"        seen[n] = i\n"
        f"    return []\n"
    )


def py_two_sum_r1(a: str, t: str) -> str:
    return py_two_sum_full(a, t).replace("    seen = {}\n", "    seen = ___\n")


def py_two_sum_r2(a: str, t: str) -> str:
    return (
        f"def two_sum({a}, {t}):\n"
        f"    seen = {{}}\n"
        f"    ___\n"
        f"    return []\n"
    )


def py_two_sum_r3(a: str, t: str) -> str:
    return (
        f"def two_sum({a}, {t}):\n"
        f"    seen = {{}}\n"
        f"    for i, n in enumerate({a}):\n"
        f"        want = {t} - n\n"
        f"        if want in seen:\n"
        f"            ___\n"
        f"        seen[n] = i\n"
        f"    ___\n"
    )


def py_two_sum_stub(a: str, t: str) -> str:
    return f"def two_sum({a}, {t}):\n    # arma el algoritmo completo\n    return []\n"


def cs_two_sum_full(a: str, t: str) -> str:
    return (
        f"int[] TwoSum(int[] {a}, int {t})\n"
        "{\n"
        "    var seen = new Dictionary<int, int>();\n"
        f"    for (int i = 0; i < {a}.Length; i++)\n"
        "    {\n"
        f"        int want = {t} - {a}[i];\n"
        "        if (seen.ContainsKey(want))\n"
        "            return new[] { seen[want], i };\n"
        f"        seen[{a}[i]] = i;\n"
        "    }\n"
        "    return new int[] {};\n"
        "}\n"
    )


def cs_two_sum_r1(a: str, t: str) -> str:
    return cs_two_sum_full(a, t).replace(
        "    var seen = new Dictionary<int, int>();\n",
        "    var seen = ___;\n",
    )


def cs_two_sum_r2(a: str, t: str) -> str:
    return (
        f"int[] TwoSum(int[] {a}, int {t})\n"
        "{\n"
        "    var seen = new Dictionary<int, int>();\n"
        "    ___\n"
        "    return new int[] {};\n"
        "}\n"
    )


def cs_two_sum_r3(a: str, t: str) -> str:
    return (
        f"int[] TwoSum(int[] {a}, int {t})\n"
        "{\n"
        "    var seen = new Dictionary<int, int>();\n"
        f"    for (int i = 0; i < {a}.Length; i++)\n"
        "    {\n"
        f"        int want = {t} - {a}[i];\n"
        "        if (seen.ContainsKey(want))\n"
        "            ___;\n"
        f"        seen[{a}[i]] = i;\n"
        "    }\n"
        "    ___\n"
        "}\n"
    )


def cs_two_sum_stub(a: str, t: str) -> str:
    return (
        f"int[] TwoSum(int[] {a}, int {t})\n"
        "{\n"
        "    // arma el algoritmo completo\n"
        "    return new int[] {};\n"
        "}\n"
    )


def sheets_two_sum(lang: str) -> list[dict]:
    pairs = CS_VARS if lang == "csharp" else PY_VARS
    fn = "TwoSum" if lang == "csharp" else "two_sum"
    out: list[dict] = []
    makers = {
        "csharp": (cs_two_sum_r1, cs_two_sum_r2, cs_two_sum_r3, cs_two_sum_stub, cs_two_sum_full),
        "python": (py_two_sum_r1, py_two_sum_r2, py_two_sum_r3, py_two_sum_stub, py_two_sum_full),
    }[lang]
    r1, r2, r3, stub, full = makers
    prompts = {
        1: "Peldaño 1: crea el mapa (diccionario vacío). Variables distintas.",
        2: "Peldaño 2: el recorrido y la búsqueda del complemento.",
        3: "Peldaño 3: qué regresas cuando hay pareja y cuando no.",
        4: "Algoritmo completo. Ármalo a la primera.",
    }
    for rung, maker in ((1, r1), (2, r2), (3, r3)):
        for i, (a, t) in enumerate(pairs, start=1):
            out.append({
                "id": f"r{rung}-{i:02d}",
                "rung": rung,
                "kind": "rung",
                "fn_name": fn,
                "prompt": prompts[rung],
                "starter_code": maker(a, t),
            })
    for i, (a, t) in enumerate(pairs[:2], start=1):
        out.append({
            "id": f"full-{i:02d}",
            "rung": 4,
            "kind": "full",
            "fn_name": fn,
            "prompt": prompts[4],
            "starter_code": stub(a, t),
        })
    a, t = pairs[2]
    out.append({
        "id": "full-recall",
        "rung": 4,
        "kind": "full",
        "fn_name": fn,
        "prompt": "Día 2 / pool: el entero, a la primera.",
        "starter_code": stub(a, t),
    })
    return out


def py_dup_full(a: str) -> str:
    return (
        f"def contains_duplicate({a}):\n"
        f"    seen = set()\n"
        f"    for n in {a}:\n"
        f"        if n in seen:\n"
        f"            return True\n"
        f"        seen.add(n)\n"
        f"    return False\n"
    )


def cs_dup_full(a: str) -> str:
    return (
        f"bool ContainsDuplicate(int[] {a})\n"
        "{\n"
        "    var seen = new HashSet<int>();\n"
        f"    foreach (var n in {a})\n"
        "    {\n"
        "        if (!seen.Add(n)) return true;\n"
        "    }\n"
        "    return false;\n"
        "}\n"
    )


def sheets_simple(
    lang: str,
    fn_py: str,
    fn_cs: str,
    py_full,
    cs_full,
    py_stub: str,
    cs_stub: str,
    names: list[str],
    prompts: dict[int, str],
    r1_replace: tuple[str, str],
) -> list[dict]:
    fn = fn_cs if lang == "csharp" else fn_py
    full_fn = cs_full if lang == "csharp" else py_full
    stub_fn = cs_stub if lang == "csharp" else py_stub
    out = []
    for rung in (1, 2, 3):
        for i, a in enumerate(names, start=1):
            code = full_fn(a)
            if rung == 1:
                code = code.replace(r1_replace[0], r1_replace[1], 1)
            elif rung == 2:
                if lang == "python":
                    code = f"def {fn_py}({a}):\n    seen = set()\n    ___\n    return False\n"
                else:
                    code = (
                        f"bool {fn_cs}(int[] {a})\n{{\n    var seen = new HashSet<int>();\n"
                        f"    ___\n    return false;\n}}\n"
                    )
            elif rung == 3:
                if lang == "python":
                    code = (
                        f"def {fn_py}({a}):\n    seen = set()\n    for n in {a}:\n"
                        f"        if n in seen:\n            ___\n        seen.add(n)\n    ___\n"
                    )
                else:
                    code = (
                        f"bool {fn_cs}(int[] {a})\n{{\n    var seen = new HashSet<int>();\n"
                        f"    foreach (var n in {a})\n    {{\n        if (!seen.Add(n)) ___;\n"
                        f"    }}\n    ___\n}}\n"
                    )
            out.append({
                "id": f"r{rung}-{i:02d}",
                "rung": rung,
                "kind": "rung",
                "fn_name": fn,
                "prompt": prompts[rung],
                "starter_code": code,
            })
    for i, a in enumerate(names[:2], start=1):
        out.append({
            "id": f"full-{i:02d}",
            "rung": 4,
            "kind": "full",
            "fn_name": fn,
            "prompt": prompts[4],
            "starter_code": stub_fn(a),
        })
    out.append({
        "id": "full-recall",
        "rung": 4,
        "kind": "full",
        "fn_name": fn,
        "prompt": "Día 2 / pool: el entero, a la primera.",
        "starter_code": stub_fn(names[2]),
    })
    return out


def sql_drills() -> list[dict]:
    return [
        {
            "id": "sql-01",
            "prompt": "INNER JOIN orders and customers on customer_id. Select order_id and name.",
            "prompt_es": "INNER JOIN orders y customers por customer_id. Selecciona order_id y name.",
            "expected": "select o.order_id, c.name from orders o inner join customers c on o.customer_id = c.customer_id",
        },
        {
            "id": "sql-02",
            "prompt": "LEFT JOIN for customers with no orders.",
            "prompt_es": "LEFT JOIN para clientes sin órdenes.",
            "expected": "select c.name, o.order_id from customers c left join orders o on c.id = o.customer_id",
        },
        {
            "id": "sql-03",
            "prompt": "Index on orders(customer_id).",
            "prompt_es": "Índice en orders(customer_id).",
            "expected": "create index ix_orders_customer_id on orders(customer_id)",
        },
        {
            "id": "sql-04",
            "prompt": "Orders with more than 3 lines (GROUP BY HAVING).",
            "prompt_es": "Pedidos con más de 3 líneas (GROUP BY HAVING).",
            "expected": "select order_id from order_lines group by order_id having count(*) > 3",
        },
        {
            "id": "sql-05",
            "prompt": "Transaction: insert order + lines or nothing.",
            "prompt_es": "Transacción: insert order + lines o nada.",
            "expected": "begin transaction; insert into orders; insert into order_lines; commit;",
        },
        {
            "id": "sql-06",
            "prompt": "N+1: rewrite as 1 query with a join instead of a loop.",
            "prompt_es": "N+1: reescribe 1 query con join en vez de loop.",
            "expected": "select o.id, l.sku from orders o join order_lines l on l.order_id = o.id",
        },
        {
            "id": "sql-07",
            "prompt": "Idempotent stock UPDATE by sku.",
            "prompt_es": "UPDATE idempotente de stock por sku.",
            "expected": "update inventory set qty = qty - 1 where sku = @sku and qty >= 1",
        },
        {
            "id": "sql-08",
            "prompt": "Keyset pagination: WHERE id > @last ORDER BY id FETCH 50.",
            "prompt_es": "Cursor de paginación: WHERE id > @last ORDER BY id FETCH 50.",
            "expected": "select * from listings where id > @last order by id fetch next 50 rows only",
        },
    ]


def write_algo(algo_id: str, title: str, leetcode_id: str, tests, py_fn: str, cs_fn: str, sheets_cs, sheets_py, voice: dict) -> None:
    dump(OUT / "algos" / f"{algo_id}.yaml", {
        "id": algo_id,
        "title": title,
        "leetcode_id": leetcode_id,
        "test_cases": tests,
        "voice": voice,
        "languages": {
            "csharp": {"fn_name": cs_fn, "sheets": sheets_cs},
            "python": {"fn_name": py_fn, "sheets": sheets_py},
        },
    })


def main() -> None:
    sections = theory_weeks()
    algo_ids = sde_algo_ids()
    dump(OUT / "program.yaml", {
        "track": "sde",
        "algos": algo_ids,
        "first_lang": "csharp",
        "second_lang": "python",
        "card_cap": 40,
        "card_cap_light": 12,
        "inactivity_days": 3,
        "sections": [{"id": s["id"], "title": s["title"], "week_id": s["week_id"]} for s in sections],
    })
    dump(OUT / "sections.yaml", {"sections": sections})
    dump(OUT / "sql.yaml", {"drills": sql_drills()})
    written = build_all_algos()
    print(f"Generated ladders for {len(written)} algos; keeping hand-crafted first four")

    dup_names = ["nums", "arr", "xs", "values", "items"]
    dup_prompts = {
        1: "Peldaño 1: crea el set.",
        2: "Peldaño 2: recorre y detecta el repetido.",
        3: "Peldaño 3: true / false.",
        4: "Completo.",
    }
    write_algo(
        "two-sum", "Two Sum", "lc-two-sum", TWO_SUM_TESTS, "two_sum", "TwoSum",
        sheets_two_sum("csharp"), sheets_two_sum("python"),
        {
            "prompt": "¿Qué guarda el diccionario y por qué Two Sum es O(n)?",
            "prompt_en": "What does the dictionary store and why is Two Sum O(n)?",
            "keywords": ["diccionario", "dictionary", "mapa", "complemento", "índice", "index", "o(n)", "hash"],
        },
    )
    write_algo(
        "contains-duplicate", "Contains Duplicate", "lc-contains-duplicate", DUP_TESTS,
        "contains_duplicate", "ContainsDuplicate",
        sheets_simple(
            "csharp", "contains_duplicate", "ContainsDuplicate",
            py_dup_full, cs_dup_full,
            lambda a: f"def contains_duplicate({a}):\n    return False\n",
            lambda a: f"bool ContainsDuplicate(int[] {a})\n{{\n    return false;\n}}\n",
            dup_names, dup_prompts,
            ("    var seen = new HashSet<int>();\n", "    var seen = ___;\n"),
        ),
        sheets_simple(
            "python", "contains_duplicate", "ContainsDuplicate",
            py_dup_full, cs_dup_full,
            lambda a: f"def contains_duplicate({a}):\n    return False\n",
            lambda a: f"bool ContainsDuplicate(int[] {a})\n{{\n    return false;\n}}\n",
            dup_names, dup_prompts,
            ("    seen = set()\n", "    seen = ___\n"),
        ),
        {
            "prompt": "¿Por qué un set y no un loop O(n²)?",
            "prompt_en": "Why a set instead of an O(n²) loop?",
            "keywords": ["set", "hash", "o(n)", "visto", "duplicado"],
        },
    )

    # anagram + two-sum-ii: reuse two-sum style generators lightly via stubs that still run tests
    write_algo(
        "valid-anagram", "Valid Anagram", "lc-valid-anagram", ANAGRAM_TESTS,
        "is_anagram", "IsAnagram",
        _anagram_sheets("csharp"), _anagram_sheets("python"),
        {
            "prompt": "¿Qué comparas para saber si es anagrama?",
            "prompt_en": "What do you compare to know it is an anagram?",
            "keywords": ["frecuencia", "count", "longitud", "letra", "o(n)"],
        },
    )
    write_algo(
        "two-sum-ii", "Two Sum II", "lc-two-sum-ii", TWO_SUM_II_TESTS,
        "two_sum_ii", "TwoSumII",
        _two_sum_ii_sheets("csharp"), _two_sum_ii_sheets("python"),
        {
            "prompt": "¿Por qué dos punteros y no un diccionario aquí?",
            "prompt_en": "Why two pointers and not a dictionary here?",
            "keywords": ["ordenado", "puntero", "left", "right", "o(1)", "espacio"],
        },
    )
    print(f"Wrote SDE content under {OUT}")


def _anagram_sheets(lang: str) -> list[dict]:
    pairs = [("s", "t"), ("a", "b"), ("left", "right"), ("src", "dst"), ("x", "y")]
    out = []
    if lang == "python":
        def full(s, t):
            return (
                f"def is_anagram({s}, {t}):\n"
                f"    if len({s}) != len({t}):\n        return False\n"
                f"    count = {{}}\n"
                f"    for c in {s}:\n        count[c] = count.get(c, 0) + 1\n"
                f"    for c in {t}:\n"
                f"        if c not in count or count[c] == 0:\n            return False\n"
                f"        count[c] -= 1\n"
                f"    return True\n"
            )
        def stub(s, t):
            return f"def is_anagram({s}, {t}):\n    return False\n"
        fn = "is_anagram"
    else:
        def full(s, t):
            return (
                f"bool IsAnagram(string {s}, string {t})\n{{\n"
                f"    if ({s}.Length != {t}.Length) return false;\n"
                f"    var count = new int[26];\n"
                f"    foreach (var c in {s}) count[c - 'a']++;\n"
                f"    foreach (var c in {t})\n    {{\n"
                f"        if (--count[c - 'a'] < 0) return false;\n    }}\n"
                f"    return true;\n}}\n"
            )
        def stub(s, t):
            return f"bool IsAnagram(string {s}, string {t})\n{{\n    return false;\n}}\n"
        fn = "IsAnagram"
    for rung in (1, 2, 3):
        for i, (s, t) in enumerate(pairs, start=1):
            code = full(s, t)
            if rung == 1:
                code = stub(s, t).replace("    return False\n", "    if len(" + s + ") != len(" + t + "):\n        ___\n    return False\n") if lang == "python" else code.replace(
                    f"    if ({s}.Length != {t}.Length) return false;\n",
                    f"    if ({s}.Length != {t}.Length) ___;\n",
                )
            elif rung == 2:
                code = stub(s, t)
                code = code.replace("    return False\n", "    ___\n    return False\n") if lang == "python" else code.replace(
                    "    return false;\n", "    ___\n    return false;\n"
                )
            elif rung == 3:
                if lang == "python":
                    code = code.replace("return False", "___").replace("return True", "___")
                else:
                    code = code.replace("return false;", "___").replace("return true;", "___")
            out.append({"id": f"r{rung}-{i:02d}", "rung": rung, "kind": "rung", "fn_name": fn, "prompt": f"Peldaño {rung}.", "starter_code": code})
    for i, (s, t) in enumerate(pairs[:2], start=1):
        out.append({"id": f"full-{i:02d}", "rung": 4, "kind": "full", "fn_name": fn, "prompt": "Completo.", "starter_code": stub(s, t)})
    s, t = pairs[2]
    out.append({"id": "full-recall", "rung": 4, "kind": "full", "fn_name": fn, "prompt": "Día 2 / pool.", "starter_code": stub(s, t)})
    return out


def _two_sum_ii_sheets(lang: str) -> list[dict]:
    pairs = PY_VARS if lang == "python" else CS_VARS
    out = []
    if lang == "python":
        fn = "two_sum_ii"
        def full(a, t):
            return (
                f"def two_sum_ii({a}, {t}):\n"
                f"    left, right = 0, len({a}) - 1\n"
                f"    while left < right:\n"
                f"        s = {a}[left] + {a}[right]\n"
                f"        if s == {t}:\n            return [left + 1, right + 1]\n"
                f"        if s < {t}:\n            left += 1\n"
                f"        else:\n            right -= 1\n"
                f"    return []\n"
            )
        def stub(a, t):
            return f"def two_sum_ii({a}, {t}):\n    return []\n"
    else:
        fn = "TwoSumII"
        def full(a, t):
            return (
                f"int[] TwoSumII(int[] {a}, int {t})\n{{\n"
                f"    int left = 0, right = {a}.Length - 1;\n"
                f"    while (left < right)\n    {{\n"
                f"        int s = {a}[left] + {a}[right];\n"
                f"        if (s == {t}) return new[] {{ left + 1, right + 1 }};\n"
                f"        if (s < {t}) left++;\n        else right--;\n"
                f"    }}\n    return new int[] {{}};\n}}\n"
            )
        def stub(a, t):
            return f"int[] TwoSumII(int[] {a}, int {t})\n{{\n    return new int[] {{}};\n}}\n"
    for rung, maker in ((1, None), (2, None), (3, None)):
        for i, (a, t) in enumerate(pairs, start=1):
            code = full(a, t)
            if rung == 1:
                code = stub(a, t).replace("    return []\n", "    left, right = ___\n    return []\n") if lang == "python" else code.replace(
                    f"    int left = 0, right = {a}.Length - 1;\n",
                    "    int left = ___, right = ___;\n",
                )
            elif rung == 2:
                if lang == "python":
                    code = f"def two_sum_ii({a}, {t}):\n    left, right = 0, len({a}) - 1\n    ___\n    return []\n"
                else:
                    code = (
                        f"int[] TwoSumII(int[] {a}, int {t})\n{{\n"
                        f"    int left = 0, right = {a}.Length - 1;\n    ___\n"
                        f"    return new int[] {{}};\n}}\n"
                    )
            elif rung == 3:
                if lang == "python":
                    code = code.replace("            return [left + 1, right + 1]\n", "            ___\n").replace(
                        "    return []\n", "    ___\n"
                    )
                else:
                    code = code.replace(
                        f"        if (s == {t}) return new[] {{ left + 1, right + 1 }};\n",
                        f"        if (s == {t}) ___;\n",
                    ).replace("    return new int[] {};\n", "    ___\n")
            out.append({"id": f"r{rung}-{i:02d}", "rung": rung, "kind": "rung", "fn_name": fn, "prompt": f"Peldaño {rung}.", "starter_code": code})
    for i, (a, t) in enumerate(pairs[:2], start=1):
        out.append({"id": f"full-{i:02d}", "rung": 4, "kind": "full", "fn_name": fn, "prompt": "Completo.", "starter_code": stub(a, t)})
    a, t = pairs[2]
    out.append({"id": "full-recall", "rung": 4, "kind": "full", "fn_name": fn, "prompt": "Día 2 / pool.", "starter_code": stub(a, t)})
    return out


if __name__ == "__main__":
    main()
