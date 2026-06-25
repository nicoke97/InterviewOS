#!/usr/bin/env python3
"""Generate all Kumon, LeetCode, and Interview YAML content for Levels A, B, C."""
from __future__ import annotations

import textwrap
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "levels"


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def scaffolding(order: int) -> str:
    if order <= 3:
        return "full"
    if order <= 10:
        return "minimal"
    return "none"


def gen_a1_drills() -> None:
    names = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack",
             "Kate", "Leo", "Mia", "Noah", "Olivia", "Paul", "Quinn", "Rose", "Sam", "Tina"]
    ages = [22, 25, 30, 19, 35, 28, 31, 24, 27, 33, 21, 29, 26, 32, 23, 34, 20, 36, 18, 37]
    for i in range(20):
        order = i + 1
        name, age = names[i], ages[i]
        drill_id = f"a1-{order:03d}"
        expected = f"{name} is {age} years old"
        data = {
            "id": drill_id,
            "block": "a1-variables",
            "order": order,
            "scaffolding": scaffolding(order),
            "prompt": f"Declare name='{name}' and age={age}, then print: '{expected}'",
            "hints": [
                f"Use f-string: f'{{name}} is {{age}} years old'",
                "Remember: strings use quotes, ints do not",
            ] if order <= 3 else ([] if order > 10 else ["Use an f-string"]),
            "validation": {"type": "run_and_match_stdout", "expected": expected},
        }
        if order <= 3:
            data["starter_code"] = textwrap.dedent(f"""\
                name = ___  # str
                age = ___   # int
                print(___)
            """)
            data["csharp_note"] = "In C#: string name = \"Alice\"; int age = 30;"
        elif order <= 10:
            data["starter_code"] = f"# Print: '{expected}'\n"
        else:
            data["starter_code"] = ""
        write_yaml(CONTENT / "level-a" / "kumon" / f"{drill_id}.yaml", data)


def gen_a2_drills() -> None:
    specs = [
        ("even", 4, "even", "if n % 2 == 0: print('even') else: print('odd')", "even"),
        ("odd", 7, "odd", "if n % 2 == 0: print('even') else: print('odd')", "odd"),
        ("grade_A", 95, "A", "if score >= 90: print('A') elif score >= 80: print('B') elif score >= 70: print('C') else: print('F')", "A"),
        ("grade_B", 85, "B", "if score >= 90: print('A') elif score >= 80: print('B') elif score >= 70: print('C') else: print('F')", "B"),
        ("grade_C", 75, "C", "if score >= 90: print('A') elif score >= 80: print('B') elif score >= 70: print('C') else: print('F')", "C"),
        ("grade_F", 55, "F", "if score >= 90: print('A') elif score >= 80: print('B') elif score >= 70: print('C') else: print('F')", "F"),
        ("adult", 20, "adult", "if age >= 18: print('adult') else: print('minor')", "adult"),
        ("minor", 15, "minor", "if age >= 18: print('adult') else: print('minor')", "minor"),
        ("positive", 5, "positive", "if n > 0: print('positive') elif n < 0: print('negative') else: print('zero')", "positive"),
        ("negative", -3, "negative", "if n > 0: print('positive') elif n < 0: print('negative') else: print('zero')", "negative"),
        ("zero", 0, "zero", "if n > 0: print('positive') elif n < 0: print('negative') else: print('zero')", "zero"),
        ("fizz", 9, "Fizz", "if n % 15 == 0: print('FizzBuzz') elif n % 3 == 0: print('Fizz') elif n % 5 == 0: print('Buzz') else: print(n)", "Fizz"),
        ("buzz", 10, "Buzz", "if n % 15 == 0: print('FizzBuzz') elif n % 3 == 0: print('Fizz') elif n % 5 == 0: print('Buzz') else: print(n)", "Buzz"),
        ("fizzbuzz", 15, "FizzBuzz", "if n % 15 == 0: print('FizzBuzz') elif n % 3 == 0: print('Fizz') elif n % 5 == 0: print('Buzz') else: print(n)", "FizzBuzz"),
        ("fizzbuzz_num", 7, "7", "if n % 15 == 0: print('FizzBuzz') elif n % 3 == 0: print('Fizz') elif n % 5 == 0: print('Buzz') else: print(n)", "7"),
        ("and_true", 1, "yes", "if a > 0 and b > 0: print('yes') else: print('no')", "yes"),
        ("and_false", 1, "no", "if a > 0 and b > 0: print('yes') else: print('no')", "no"),
        ("or_true", 1, "yes", "if a > 0 or b > 0: print('yes') else: print('no')", "yes"),
        ("not_gate", 1, "inactive", "if not active: print('inactive') else: print('active')", "inactive"),
        ("nested", 1, "big", "if x > 10: print('big') elif x > 5: print('medium') else: print('small')", "big"),
    ]
    for i, (label, val, expected, logic, _) in enumerate(specs):
        order = i + 1
        drill_id = f"a2-{order:03d}"
        if "score" in logic:
            setup = f"score = {val}"
            prompt = f"Given score={val}, print the letter grade ({expected})"
        elif "age" in logic:
            setup = f"age = {val}"
            prompt = f"Given age={val}, print '{expected}'"
        elif "a >" in logic:
            setup = f"a = {val}\nb = {-1 if expected == 'no' and 'and' in logic else 1}"
            prompt = f"Given a and b, print '{expected}'"
        elif "active" in logic:
            setup = f"active = False"
            prompt = "Given active=False, print 'inactive'"
        elif "x >" in logic:
            setup = f"x = 15"
            prompt = "Given x=15, print 'big'"
        else:
            setup = f"n = {val}"
            prompt = f"Given n={val}, evaluate and print '{expected}'"

        code_template = f"{setup}\n{logic}"
        data = {
            "id": drill_id, "block": "a2-conditionals", "order": order,
            "scaffolding": scaffolding(order),
            "prompt": prompt,
            "hints": ["Use if/elif/else chains", "Remember % for modulo"] if order <= 3 else [],
            "validation": {"type": "run_and_match_stdout", "expected": expected, "setup": setup},
        }
        if order <= 3:
            data["starter_code"] = f"{setup}\n# Write if/elif/else\nprint(___)"
        elif order <= 10:
            data["starter_code"] = f"# {prompt}\n"
        else:
            data["starter_code"] = ""
        write_yaml(CONTENT / "level-a" / "kumon" / f"{drill_id}.yaml", data)


def gen_a3_drills() -> None:
    specs = [
        ("sum_1_5", "total = 0\nfor i in range(1, 6):\n    total += i\nprint(total)", "15"),
        ("count_1_10", "for i in range(1, 11):\n    print(i, end=' ')", "1 2 3 4 5 6 7 8 9 10"),
        ("mult_3", "for i in range(3, 31, 3):\n    print(i, end=' ')", "3 6 9 12 15 18 21 24 27 30"),
        ("countdown", "for i in range(5, 0, -1):\n    print(i, end=' ')", "5 4 3 2 1"),
        ("while_sum", "n = 5\ntotal = 0\nwhile n > 0:\n    total += n\n    n -= 1\nprint(total)", "15"),
        ("break_at", "for i in range(1, 11):\n    if i == 6:\n        break\n    print(i, end=' ')", "1 2 3 4 5"),
        ("continue_even", "for i in range(1, 6):\n    if i % 2 != 0:\n        continue\n    print(i, end=' ')", "2 4"),
        ("table_2", "for i in range(1, 6):\n    print(i * 2, end=' ')", "2 4 6 8 10"),
        ("vowels", "s = 'hello'\ncount = 0\nfor c in s:\n    if c in 'aeiou':\n        count += 1\nprint(count)", "2"),
        ("factorial", "n = 5\nresult = 1\nfor i in range(1, n + 1):\n    result *= i\nprint(result)", "120"),
        ("nested_sum", "total = 0\nfor i in range(1, 4):\n    for j in range(1, 4):\n        total += 1\nprint(total)", "9"),
        ("enumerate_demo", "items = ['a', 'b', 'c']\nfor i, v in enumerate(items):\n    print(f'{i}:{v}', end=' ')", "0:a 1:b 2:c"),
        ("zip_demo", "a = [1, 2, 3]\nb = ['x', 'y', 'z']\nfor x, y in zip(a, b):\n    print(f'{x}{y}', end=' ')", "1x 2y 3z"),
        ("list_comp", "squares = [i*i for i in range(1, 6)]\nprint(squares)", "[1, 4, 9, 16, 25]"),
        ("filter_even", "nums = [1, 2, 3, 4, 5, 6]\nevens = [n for n in nums if n % 2 == 0]\nprint(evens)", "[2, 4, 6]"),
        ("while_count", "count = 0\nn = 10\nwhile n > 0:\n    count += 1\n    n //= 2\nprint(count)", "4"),
        ("sum_list", "nums = [3, 1, 4, 1, 5]\ntotal = 0\nfor n in nums:\n    total += n\nprint(total)", "14"),
        ("max_manual", "nums = [3, 9, 2, 7]\nm = nums[0]\nfor n in nums:\n    if n > m:\n        m = n\nprint(m)", "9"),
        ("char_count", "s = 'aaa'\nprint(s.count('a'))", "3"),
        ("range_len", "items = [10, 20, 30]\nfor i in range(len(items)):\n    print(items[i], end=' ')", "10 20 30"),
    ]
    for i, (label, code, expected) in enumerate(specs):
        order = i + 1
        drill_id = f"a3-{order:03d}"
        data = {
            "id": drill_id, "block": "a3-loops", "order": order,
            "scaffolding": scaffolding(order),
            "prompt": f"Write code that outputs: {expected!r}",
            "hints": ["Use for i in range(...)", "end=' ' keeps output on same line"] if order <= 3 else [],
            "validation": {"type": "run_and_match_stdout", "expected": expected},
        }
        if order <= 3:
            data["starter_code"] = "# Use a for loop\nfor ___ in ___:\n    ___\nprint(___)"
        elif order <= 10:
            data["starter_code"] = f"# Output: {expected!r}\n"
        else:
            data["starter_code"] = ""
        write_yaml(CONTENT / "level-a" / "kumon" / f"{drill_id}.yaml", data)


def gen_a4_drills() -> None:
    specs = [
        ("greet", "def greet(name):\n    return f'Hello, {name}!'\nprint(greet('World'))", "Hello, World!"),
        ("add", "def add(a, b):\n    return a + b\nprint(add(3, 4))", "7"),
        ("square", "def square(n):\n    return n * n\nprint(square(5))", "25"),
        ("is_even", "def is_even(n):\n    return n % 2 == 0\nprint(is_even(4))", "True"),
        ("default_greet", "def greet(name='Guest'):\n    return f'Hi, {name}'\nprint(greet())", "Hi, Guest"),
        ("max3", "def max3(a, b, c):\n    return max(a, b, c)\nprint(max3(1, 9, 3))", "9"),
        ("count_vowels", "def count_vowels(s):\n    return sum(1 for c in s if c in 'aeiou')\nprint(count_vowels('hello'))", "2"),
        ("reverse_str", "def reverse_str(s):\n    return s[::-1]\nprint(reverse_str('abc'))", "cba"),
        ("factorial_fn", "def factorial(n):\n    r = 1\n    for i in range(1, n + 1):\n        r *= i\n    return r\nprint(factorial(5))", "120"),
        ("fizzbuzz_fn", "def fizzbuzz(n):\n    if n % 15 == 0: return 'FizzBuzz'\n    if n % 3 == 0: return 'Fizz'\n    if n % 5 == 0: return 'Buzz'\n    return str(n)\nprint(fizzbuzz(9))", "Fizz"),
        ("sum_list_fn", "def sum_list(nums):\n    return sum(nums)\nprint(sum_list([1, 2, 3]))", "6"),
        ("first_last", "def first_last(items):\n    return (items[0], items[-1])\nresult = first_last([1, 2, 3])\nprint(result)", "(1, 3)"),
        ("grade_fn", "def grade(score):\n    if score >= 90: return 'A'\n    if score >= 80: return 'B'\n    return 'C'\nprint(grade(85))", "B"),
        ("twice", "def twice(f, x):\n    return f(f(x))\nprint(twice(lambda n: n + 1, 3))", "5"),
        ("apply", "def apply(f, x):\n    return f(x)\nprint(apply(lambda n: n * 2, 7))", "14"),
        ("power", "def power(base, exp=2):\n    return base ** exp\nprint(power(3))", "9"),
        ("clamp", "def clamp(n, lo, hi):\n    return max(lo, min(n, hi))\nprint(clamp(15, 0, 10))", "10"),
        ("palindrome_fn", "def is_palindrome(s):\n    return s == s[::-1]\nprint(is_palindrome('aba'))", "True"),
        ("word_count", "def word_count(s):\n    return len(s.split())\nprint(word_count('one two three'))", "3"),
        ("safe_div", "def safe_div(a, b):\n    if b == 0:\n        return None\n    return a / b\nprint(safe_div(10, 2))", "5.0"),
    ]
    for i, (label, code, expected) in enumerate(specs):
        order = i + 1
        drill_id = f"a4-{order:03d}"
        data = {
            "id": drill_id, "block": "a4-functions", "order": order,
            "scaffolding": scaffolding(order),
            "prompt": f"Write a function and call it to output: {expected!r}",
            "hints": ["Use def name(params):", "return sends a value back"] if order <= 3 else [],
            "validation": {"type": "run_and_match_stdout", "expected": expected},
        }
        if order <= 3:
            data["starter_code"] = "def greet(name):\n    ___\n\nprint(greet(___))"
        elif order <= 10:
            data["starter_code"] = f"# Output: {expected!r}\n"
        else:
            data["starter_code"] = ""
        write_yaml(CONTENT / "level-a" / "kumon" / f"{drill_id}.yaml", data)


def gen_block_drills(prefix: str, block: str, level: str, specs: list[tuple[str, str, str]]) -> None:
    for i, (prompt, code, expected) in enumerate(specs):
        order = i + 1
        drill_id = f"{prefix}-{order:03d}"
        vtype = "exact_match" if prefix == "c4" else "run_and_match_stdout"
        validation = {"type": vtype, "expected": expected}
        if vtype == "run_and_match_stdout" and "\n" in code:
            validation = {"type": "run_and_match_stdout", "expected": expected}
        data = {
            "id": drill_id, "block": block, "order": order,
            "scaffolding": scaffolding(order),
            "prompt": prompt,
            "hints": ["Think step by step"] if order <= 3 else [],
            "validation": validation,
        }
        if order <= 3:
            data["starter_code"] = "# Fill in\n___"
        elif order <= 10:
            data["starter_code"] = f"# {prompt}\n"
        else:
            data["starter_code"] = ""
        if prefix != "c4":
            data["validation"] = {"type": "run_and_match_stdout", "expected": expected}
        write_yaml(CONTENT / f"level-{level}" / "kumon" / f"{drill_id}.yaml", data)


def gen_b_blocks() -> None:
    b1 = [
        ("Reverse [1,2,3] without reverse()", "nums = [1, 2, 3]\nresult = []\nfor i in range(len(nums) - 1, -1, -1):\n    result.append(nums[i])\nprint(result)", "[3, 2, 1]"),
        ("Print last element of [10,20,30]", "items = [10, 20, 30]\nprint(items[-1])", "30"),
        ("Slice first 2 of [1,2,3,4]", "items = [1, 2, 3, 4]\nprint(items[:2])", "[1, 2]"),
        ("Append 4 to [1,2,3]", "items = [1, 2, 3]\nitems.append(4)\nprint(items)", "[1, 2, 3, 4]"),
        ("Len of [1,2,3,4,5]", "print(len([1, 2, 3, 4, 5]))", "5"),
        ("Sort [3,1,2]", "items = [3, 1, 2]\nitems.sort()\nprint(items)", "[1, 2, 3]"),
        ("Pop last from [1,2,3]", "items = [1, 2, 3]\nitems.pop()\nprint(items)", "[1, 2]"),
        ("Extend list", "a = [1, 2]\na.extend([3, 4])\nprint(a)", "[1, 2, 3, 4]"),
        ("Index of 2 in [1,2,3]", "print([1, 2, 3].index(2))", "1"),
        ("Count 2 in [1,2,2,3]", "print([1, 2, 2, 3].count(2))", "2"),
        ("Slice [::2]", "print([0, 1, 2, 3, 4][::2])", "[0, 2, 4]"),
        ("Reverse slice [::-1]", "print('abc'[::-1])", "cba"),
        ("Min without min()", "nums = [3, 1, 4]\nm = nums[0]\nfor n in nums:\n    if n < m: m = n\nprint(m)", "1"),
        ("Max without max()", "nums = [3, 1, 4]\nm = nums[0]\nfor n in nums:\n    if n > m: m = n\nprint(m)", "4"),
        ("Sum list manual", "nums = [1, 2, 3]\nt = 0\nfor n in nums: t += n\nprint(t)", "6"),
        ("Copy list", "a = [1, 2, 3]\nb = a.copy()\nb.append(4)\nprint(a)", "[1, 2, 3]"),
        ("Insert at 0", "a = [2, 3]\na.insert(0, 1)\nprint(a)", "[1, 2, 3]"),
        ("Remove value", "a = [1, 2, 3]\na.remove(2)\nprint(a)", "[1, 3]"),
        ("Clear list", "a = [1, 2]\na.clear()\nprint(a)", "[]"),
        ("Nested access", "matrix = [[1, 2], [3, 4]]\nprint(matrix[1][0])", "3"),
    ]
    gen_block_drills("b1", "b1-lists", "b", b1)

    b2 = [
        ("Create and print dict", "d = {'name': 'Alice', 'age': 30}\nprint(d['name'])", "Alice"),
        ("Update dict key", "d = {'a': 1}\nd['b'] = 2\nprint(d)", "{'a': 1, 'b': 2}"),
        ("Delete key", "d = {'a': 1, 'b': 2}\ndel d['a']\nprint(d)", "{'b': 2}"),
        ("Get with default", "d = {}\nprint(d.get('x', 0))", "0"),
        ("Items loop", "d = {'a': 1, 'b': 2}\nfor k, v in d.items():\n    print(f'{k}:{v}', end=' ')", "a:1 b:2"),
        ("Keys list", "print(list({'x': 1, 'y': 2}.keys()))", "['x', 'y']"),
        ("Values sum", "print(sum({'a': 1, 'b': 2, 'c': 3}.values()))", "6"),
        ("Word frequency", "s = 'a b a'\nfreq = {}\nfor w in s.split():\n    freq[w] = freq.get(w, 0) + 1\nprint(freq['a'])", "2"),
        ("Merge dicts", "a = {'x': 1}\nb = {'y': 2}\na.update(b)\nprint(a)", "{'x': 1, 'y': 2}"),
        ("Check key exists", "d = {'a': 1}\nprint('a' in d)", "True"),
        ("Pop key", "d = {'a': 1, 'b': 2}\nprint(d.pop('a'))", "1"),
        ("Dict comprehension", "print({i: i*i for i in range(1, 4)})", "{1: 1, 2: 4, 3: 9}"),
        ("Invert dict", "d = {'a': 1, 'b': 2}\ninv = {v: k for k, v in d.items()}\nprint(inv[1])", "a"),
        ("Nested dict", "d = {'user': {'name': 'Bob'}}\nprint(d['user']['name'])", "Bob"),
        ("Setdefault", "d = {}\nd.setdefault('count', 0)\nd['count'] += 1\nprint(d['count'])", "1"),
        ("Len dict", "print(len({'a': 1, 'b': 2, 'c': 3}))", "3"),
        ("Bool dict", "print(bool({}))", "False"),
        ("Copy dict", "a = {'x': 1}\nb = a.copy()\nb['x'] = 2\nprint(a['x'])", "1"),
        ("From tuples", "print(dict([('a', 1), ('b', 2)]))", "{'a': 1, 'b': 2}"),
        ("Max value key", "d = {'a': 3, 'b': 7, 'c': 1}\nprint(max(d, key=d.get))", "b"),
    ]
    gen_block_drills("b2", "b2-dicts", "b", b2)

    b3 = [
        ("Split string", "print('a,b,c'.split(','))", "['a', 'b', 'c']"),
        ("Join list", "print(','.join(['a', 'b', 'c']))", "a,b,c"),
        ("Strip spaces", "print('  hi  '.strip())", "hi"),
        ("Replace", "print('hello'.replace('l', 'x'))", "hexxo"),
        ("Upper", "print('hi'.upper())", "HI"),
        ("Lower", "print('HI'.lower())", "hi"),
        ("Startswith", "print('hello'.startswith('he'))", "True"),
        ("Endswith", "print('hello'.endswith('lo'))", "True"),
        ("Find substring", "print('hello'.find('ll'))", "2"),
        ("Count char", "print('hello'.count('l'))", "2"),
        ("Partition", "print('a=b'.partition('='))", "('a', '=', 'b')"),
        ("Splitlines", "print('a\\nb'.splitlines())", "['a', 'b']"),
        ("Zfill", "print('42'.zfill(5))", "0042"),
        ("Title case", "print('hello world'.title())", "Hello World"),
        ("Isdigit", "print('123'.isdigit())", "True"),
        ("Isalpha", "print('abc'.isalpha())", "True"),
        ("Format", "print('{:.2f}'.format(3.14159))", "3.14"),
        ("Fstring format", "print(f'{3.14159:.2f}')", "3.14"),
        ("Normalize spaces", "print('  a   b  '.split())", "['a', 'b']"),
        ("Reverse words", "print(' '.join('hello world'.split()[::-1]))", "world hello"),
    ]
    gen_block_drills("b3", "b3-strings", "b", b3)

    b4 = [
        ("Safe divide 10/2", "try:\n    print(10 / 2)\nexcept ZeroDivisionError:\n    print('error')", "5.0"),
        ("Safe divide by zero", "try:\n    print(10 / 0)\nexcept ZeroDivisionError:\n    print('error')", "error"),
        ("Handle ValueError", "try:\n    int('abc')\nexcept ValueError:\n    print('bad')", "bad"),
        ("Finally runs", "try:\n    print(1)\nfinally:\n    print(2)", "1\n2"),
        ("Empty list check", "items = []\nprint('empty' if not items else 'ok')", "empty"),
        ("None check", "x = None\nprint('none' if x is None else 'val')", "none"),
        ("Safe index", "items = [1, 2]\ntry:\n    print(items[5])\nexcept IndexError:\n    print('bad index')", "bad index"),
        ("Safe key", "d = {}\ntry:\n    print(d['x'])\nexcept KeyError:\n    print('no key')", "no key"),
        ("Type check", "x = '5'\nprint(int(x) + 1)", "6"),
        ("Multiple except", "try:\n    int('x')\nexcept (ValueError, TypeError):\n    print('fail')", "fail"),
        ("Else clause", "try:\n    x = 1\nexcept:\n    x = 0\nelse:\n    print('ok')", "ok"),
        ("Raise error", "try:\n    raise ValueError('oops')\nexcept ValueError as e:\n    print(str(e))", "oops"),
        ("Assert", "x = 5\nassert x > 0\nprint('valid')", "valid"),
        ("Guard clause", "def f(n):\n    if n is None:\n        return 0\n    return n * 2\nprint(f(None))", "0"),
        ("Default empty list", "def f(items=None):\n    if items is None:\n        items = []\n    items.append(1)\n    return items\nprint(f())", "[1]"),
        ("Short circuit", "def bad():\n    raise Exception('no')\nprint(False and bad())", "False"),
        ("Or default", "name = None\nprint(name or 'Guest')", "Guest"),
        ("Truthy empty", "print(bool([]))", "False"),
        ("Truthy zero", "print(bool(0))", "False"),
        ("Chained compare", "x = 5\nprint(1 < x < 10)", "True"),
    ]
    gen_block_drills("b4", "b4-errors", "b", b4)


def gen_c_blocks() -> None:
    c1 = [
        ("Basic class", "class Dog:\n    def __init__(self, name):\n        self.name = name\n    def bark(self):\n        return f'{self.name} says woof!'\nd = Dog('Rex')\nprint(d.bark())", "Rex says woof!"),
        ("Cliente class", "class Cliente:\n    def __init__(self, name):\n        self.name = name\n    def saludar(self):\n        return f'Hola, {self.name}'\nc = Cliente('Ana')\nprint(c.saludar())", "Hola, Ana"),
        ("Ticket class", "class Ticket:\n    def __init__(self, title):\n        self.title = title\n        self.status = 'open'\nt = Ticket('Bug')\nprint(t.status)", "open"),
        ("Product price", "class Product:\n    def __init__(self, name, price):\n        self.name = name\n        self.price = price\np = Product('Book', 10)\nprint(p.price)", "10"),
        ("Method return", "class Calc:\n    def add(self, a, b):\n        return a + b\nc = Calc()\nprint(c.add(2, 3))", "5"),
        ("Class attribute", "class Counter:\n    count = 0\n    def __init__(self):\n        Counter.count += 1\nCounter()\nCounter()\nprint(Counter.count)", "2"),
        ("Str method", "class Point:\n    def __init__(self, x, y):\n        self.x = x\n        self.y = y\n    def __str__(self):\n        return f'({self.x},{self.y})'\nprint(Point(1, 2))", "(1,2)"),
        ("Repr method", "class Item:\n    def __init__(self, id):\n        self.id = id\n    def __repr__(self):\n        return f'Item({self.id})'\nprint(repr(Item(5)))", "Item(5)"),
        ("Property", "class Circle:\n    def __init__(self, r):\n        self.r = r\n    def area(self):\n        return 3.14 * self.r ** 2\nc = Circle(2)\nprint(int(c.area()))", "12"),
        ("Multiple methods", "class Bank:\n    def __init__(self, bal=0):\n        self.bal = bal\n    def deposit(self, n):\n        self.bal += n\n    def balance(self):\n        return self.bal\nb = Bank()\nb.deposit(100)\nprint(b.balance())", "100"),
    ] + [
        (f"Class drill {i}", f"class N:\n    def __init__(self, v):\n        self.v = v\n    def get(self):\n        return self.v\nprint(N({i}).get())", str(i))
        for i in range(11, 21)
    ]
    gen_block_drills("c1", "c1-classes", "c", c1)

    c2 = [
        ("Inheritance basic", "class Animal:\n    def speak(self):\n        return 'sound'\nclass Dog(Animal):\n    def speak(self):\n        return 'woof'\nprint(Dog().speak())", "woof"),
        ("Empleado", "class Empleado:\n    def __init__(self, name):\n        self.name = name\n    def role(self):\n        return 'employee'\nclass SupportEngineer(Empleado):\n    def role(self):\n        return 'support'\nprint(SupportEngineer('Ana').role())", "support"),
        ("Super call", "class A:\n    def greet(self):\n        return 'Hi'\nclass B(A):\n    def greet(self):\n        return super().greet() + ' there'\nprint(B().greet())", "Hi there"),
        ("Override init", "class Base:\n    def __init__(self, x):\n        self.x = x\nclass Child(Base):\n    def __init__(self, x, y):\n        super().__init__(x)\n        self.y = y\nc = Child(1, 2)\nprint(c.x, c.y)", "1 2"),
        ("Isinstance", "class A: pass\nclass B(A): pass\nprint(isinstance(B(), A))", "True"),
        ("Issubclass", "class A: pass\nclass B(A): pass\nprint(issubclass(B, A))", "True"),
    ] + [
        (f"Inherit drill {i}", f"class P:\n    def v(self): return {i}\nclass C(P):\n    pass\nprint(C().v())", str(i))
        for i in range(7, 21)
    ]
    gen_block_drills("c2", "c2-inheritance", "c", c2)

    c3 = [
        ("Filter clients", "clients = [{'name': 'A', 'active': True}, {'name': 'B', 'active': False}]\nactive = [c for c in clients if c['active']]\nprint(len(active))", "1"),
        ("Sort by field", "orders = [{'total': 30}, {'total': 10}]\norders.sort(key=lambda o: o['total'])\nprint(orders[0]['total'])", "10"),
        ("Group by client", "orders = [{'client': 'A', 'amt': 10}, {'client': 'A', 'amt': 5}, {'client': 'B', 'amt': 3}]\ntotals = {}\nfor o in orders:\n    totals[o['client']] = totals.get(o['client'], 0) + o['amt']\nprint(totals['A'])", "15"),
        ("Sum sales", "sales = [{'amt': 10}, {'amt': 20}, {'amt': 5}]\nprint(sum(s['amt'] for s in sales))", "35"),
        ("Find max order", "orders = [{'id': 1, 'total': 50}, {'id': 2, 'total': 30}]\nbest = max(orders, key=lambda o: o['total'])\nprint(best['id'])", "1"),
        ("Join simulation", "clients = [{'id': 1, 'name': 'A'}]\norders = [{'client_id': 1, 'total': 100}]\nfor o in orders:\n    c = next(c for c in clients if c['id'] == o['client_id'])\n    print(f\"{c['name']}: {o['total']}\")", "A: 100"),
    ] + [
        (f"ERP drill {i}", f"data = [{{'x': {i}}}, {{'x': {i+1}}}]\nprint(len(data))", "2")
        for i in range(7, 21)
    ]
    gen_block_drills("c3", "c3-nested", "c", c3)

    c4_commands = [
        ("git status command", "git status"),
        ("git add file", "git add ."),
        ("git commit", 'git commit -m "fix bug"'),
        ("git branch", "git branch feature-x"),
        ("git checkout", "git checkout main"),
        ("git merge", "git merge feature-x"),
        ("git pull", "git pull origin main"),
        ("git push", "git push origin main"),
        ("git log oneline", "git log --oneline"),
        ("git diff", "git diff"),
        ("ls list", "ls -la"),
        ("cd change dir", "cd /home/user"),
        ("grep search", "grep -r 'error' ."),
        ("cat file", "cat README.md"),
        ("pwd", "pwd"),
        ("mkdir", "mkdir new_folder"),
        ("rm file", "rm file.txt"),
        ("chmod", "chmod +x script.sh"),
        ("head file", "head -n 10 log.txt"),
        ("tail file", "tail -f log.txt"),
    ]
    for i, (prompt, cmd) in enumerate(c4_commands):
        order = i + 1
        drill_id = f"c4-{order:03d}"
        data = {
            "id": drill_id, "block": "c4-git", "order": order,
            "scaffolding": scaffolding(order),
            "prompt": f"Type the command: {prompt}",
            "hints": ["No spaces before command"] if order <= 3 else [],
            "starter_code": "___" if order <= 3 else (f"# {prompt}\n" if order <= 10 else ""),
            "validation": {"type": "exact_match", "expected": cmd},
        }
        write_yaml(CONTENT / "level-c" / "kumon" / f"{drill_id}.yaml", data)


def gen_leetcode() -> None:
    problems = {
        "level-a": [
            {
                "id": "palindrome", "title": "Valid Palindrome", "fn_name": "is_palindrome",
                "description": "Given integer x, return True if x reads the same forward and backward.",
                "test_cases": [{"args": [121], "expected": True}, {"args": [-121], "expected": False}, {"args": [10], "expected": False}],
                "tiers": {
                    1: {"starter_code": "def is_palindrome(x):\n    s = str(x)\n    # Compare s with its reverse\n    return ___", "explain_checklist": ["What is input type?", "How to reverse a string?", "Edge case: negative numbers"], "hints_allowed": True},
                    2: {"starter_code": "def is_palindrome(x):\n    pass", "narration_prompts": ["State your approach out loud", "What are edge cases?", "What is time complexity?"], "hints_allowed": True},
                    3: {"starter_code": "def is_palindrome(x):\n    pass", "narration_prompts": [], "hints_allowed": False},
                },
            },
            {
                "id": "fizzbuzz", "title": "FizzBuzz", "fn_name": "fizzbuzz",
                "description": "Return a list of strings from 1 to n with FizzBuzz rules.",
                "test_cases": [{"args": [5], "expected": ["1", "2", "Fizz", "4", "FizzBuzz"]}],
                "tiers": {
                    1: {"starter_code": "def fizzbuzz(n):\n    result = []\n    for i in range(1, n + 1):\n        # fill in conditions\n        pass\n    return result", "explain_checklist": ["Divisibility order matters"], "hints_allowed": True},
                    2: {"starter_code": "def fizzbuzz(n):\n    pass", "narration_prompts": ["Explain modulo checks", "Why check 15 first?"], "hints_allowed": True},
                    3: {"starter_code": "def fizzbuzz(n):\n    pass", "narration_prompts": [], "hints_allowed": False},
                },
            },
            {
                "id": "max-of-three", "title": "Maximum of Three", "fn_name": "max_of_three",
                "description": "Return the maximum of three integers.",
                "test_cases": [{"args": [1, 9, 3], "expected": 9}, {"args": [-1, -5, -2], "expected": -1}],
                "tiers": {
                    1: {"starter_code": "def max_of_three(a, b, c):\n    # use if/elif\n    return ___", "explain_checklist": ["Compare pairs step by step"], "hints_allowed": True},
                    2: {"starter_code": "def max_of_three(a, b, c):\n    pass", "narration_prompts": ["Walk through comparisons"], "hints_allowed": True},
                    3: {"starter_code": "def max_of_three(a, b, c):\n    pass", "narration_prompts": [], "hints_allowed": False},
                },
            },
            {
                "id": "count-vowels", "title": "Count Vowels", "fn_name": "count_vowels",
                "description": "Count vowels in a string.",
                "test_cases": [{"args": ["hello"], "expected": 2}, {"args": ["xyz"], "expected": 0}],
                "tiers": {
                    1: {"starter_code": "def count_vowels(s):\n    vowels = 'aeiou'\n    count = 0\n    for c in s:\n        if c in vowels:\n            count += 1\n    return ___", "explain_checklist": ["Loop each character"], "hints_allowed": True},
                    2: {"starter_code": "def count_vowels(s):\n    pass", "narration_prompts": ["Explain loop invariant"], "hints_allowed": True},
                    3: {"starter_code": "def count_vowels(s):\n    pass", "narration_prompts": [], "hints_allowed": False},
                },
            },
        ],
        "level-b": [
            {
                "id": "contains-duplicate", "title": "Contains Duplicate", "fn_name": "contains_duplicate",
                "description": "Return True if any value appears twice.",
                "test_cases": [{"args": [[1, 2, 3, 1]], "expected": True}, {"args": [[1, 2, 3]], "expected": False}],
                "tiers": {
                    1: {"starter_code": "def contains_duplicate(nums):\n  # hint: use a set\n  return ___", "explain_checklist": ["Set tracks seen items"], "hints_allowed": True},
                    2: {"starter_code": "def contains_duplicate(nums):\n    pass", "narration_prompts": ["Brute force vs set approach"], "hints_allowed": True},
                    3: {"starter_code": "def contains_duplicate(nums):\n    pass", "narration_prompts": [], "hints_allowed": False},
                },
            },
            {
                "id": "valid-anagram", "title": "Valid Anagram", "fn_name": "is_anagram",
                "description": "Return True if t is an anagram of s.",
                "test_cases": [{"args": ["anagram", "nagaram"], "expected": True}, {"args": ["rat", "car"], "expected": False}],
                "tiers": {
                    1: {"starter_code": "def is_anagram(s, t):\n    # sorted(s) == sorted(t)\n    return ___", "explain_checklist": ["Same length required"], "hints_allowed": True},
                    2: {"starter_code": "def is_anagram(s, t):\n    pass", "narration_prompts": ["Compare character counts"], "hints_allowed": True},
                    3: {"starter_code": "def is_anagram(s, t):\n    pass", "narration_prompts": [], "hints_allowed": False},
                },
            },
            {
                "id": "two-sum", "title": "Two Sum", "fn_name": "two_sum",
                "description": "Return indices of two numbers that add to target.",
                "test_cases": [{"args": [[2, 7, 11, 15], 9], "expected": [0, 1]}],
                "tiers": {
                    1: {"starter_code": "def two_sum(nums, target):\n    # brute force nested loop\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if ___:\n                return [i, j]", "explain_checklist": ["Why j starts at i+1?"], "hints_allowed": True},
                    2: {"starter_code": "def two_sum(nums, target):\n    pass", "narration_prompts": ["State brute force O(n^2)", "Can hash map help?"], "hints_allowed": True},
                    3: {"starter_code": "def two_sum(nums, target):\n    pass", "narration_prompts": [], "hints_allowed": False},
                },
            },
            {
                "id": "erp-filter", "title": "Filter Active Clients", "fn_name": "filter_active",
                "description": "Filter list of client dicts where active=True, sort by name.",
                "test_cases": [{"args": [[{"name": "B", "active": True}, {"name": "A", "active": False}, {"name": "C", "active": True}]], "expected": [{"name": "B", "active": True}, {"name": "C", "active": True}]}],
                "tiers": {
                    1: {"starter_code": "def filter_active(clients):\n    active = [c for c in clients if c['active']]\n    active.sort(key=lambda c: c['name'])\n    return ___", "explain_checklist": ["List comprehension filters", "sort key=name"], "hints_allowed": True},
                    2: {"starter_code": "def filter_active(clients):\n    pass", "narration_prompts": ["Relate to SQL WHERE and ORDER BY"], "hints_allowed": True},
                    3: {"starter_code": "def filter_active(clients):\n    pass", "narration_prompts": [], "hints_allowed": False},
                },
            },
        ],
        "level-c": [
            {
                "id": "group-anagrams", "title": "Group Anagrams", "fn_name": "group_anagrams",
                "description": "Group strings that are anagrams.",
                "test_cases": [{"args": [["eat", "tea", "tan", "ate", "nat", "bat"]], "expected": [["eat", "tea", "ate"], ["tan", "nat"], ["bat"]]}],
                "tiers": {
                    1: {"starter_code": "def group_anagrams(strs):\n    groups = {}\n    for s in strs:\n        key = tuple(sorted(s))\n        groups.setdefault(key, []).append(s)\n    return ___", "explain_checklist": ["Sorted tuple as dict key"], "hints_allowed": True},
                    2: {"starter_code": "def group_anagrams(strs):\n    pass", "narration_prompts": ["Why tuple key?"], "hints_allowed": True},
                    3: {"starter_code": "def group_anagrams(strs):\n    pass", "narration_prompts": [], "hints_allowed": False},
                },
            },
            {
                "id": "top-k-frequent", "title": "Top K Frequent", "fn_name": "top_k_frequent",
                "description": "Return k most frequent elements.",
                "test_cases": [{"args": [[1, 1, 1, 2, 2, 3], 2], "expected": [1, 2]}],
                "tiers": {
                    1: {"starter_code": "def top_k_frequent(nums, k):\n    freq = {}\n    for n in nums:\n        freq[n] = freq.get(n, 0) + 1\n    return ___", "explain_checklist": ["Count frequencies first"], "hints_allowed": True},
                    2: {"starter_code": "def top_k_frequent(nums, k):\n    pass", "narration_prompts": ["Sort by frequency"], "hints_allowed": True},
                    3: {"starter_code": "def top_k_frequent(nums, k):\n    pass", "narration_prompts": [], "hints_allowed": False},
                },
            },
            {
                "id": "merge-sorted", "title": "Merge Sorted Lists", "fn_name": "merge_sorted",
                "description": "Merge two sorted lists into one sorted list.",
                "test_cases": [{"args": [[1, 3, 5], [2, 4, 6]], "expected": [1, 2, 3, 4, 5, 6]}],
                "tiers": {
                    1: {"starter_code": "def merge_sorted(a, b):\n    result = []\n    i = j = 0\n    while i < len(a) and j < len(b):\n        if a[i] < b[j]:\n            result.append(a[i]); i += 1\n        else:\n            result.append(b[j]); j += 1\n    return result + a[i:] + b[j:]", "explain_checklist": ["Two pointer technique"], "hints_allowed": True},
                    2: {"starter_code": "def merge_sorted(a, b):\n    pass", "narration_prompts": ["Explain two pointers"], "hints_allowed": True},
                    3: {"starter_code": "def merge_sorted(a, b):\n    pass", "narration_prompts": [], "hints_allowed": False},
                },
            },
            {
                "id": "erp-join", "title": "ERP Join Query", "fn_name": "sales_per_client",
                "description": "Given clients and orders, return total sales per client name.",
                "test_cases": [{"args": [[{"id": 1, "name": "A"}], [{"client_id": 1, "amount": 10}, {"client_id": 1, "amount": 5}]], "expected": {"A": 15}}],
                "tiers": {
                    1: {"starter_code": "def sales_per_client(clients, orders):\n    totals = {}\n    for o in orders:\n        c = next(c for c in clients if c['id'] == o['client_id'])\n        totals[c['name']] = totals.get(c['name'], 0) + o['amount']\n    return ___", "explain_checklist": ["JOIN then GROUP BY in Python"], "hints_allowed": True},
                    2: {"starter_code": "def sales_per_client(clients, orders):\n    pass", "narration_prompts": ["Map to SQL JOIN + GROUP BY"], "hints_allowed": True},
                    3: {"starter_code": "def sales_per_client(clients, orders):\n    pass", "narration_prompts": [], "hints_allowed": False},
                },
            },
        ],
    }
    for level, probs in problems.items():
        for p in probs:
            write_yaml(CONTENT / level / "leetcode" / f"{p['id']}.yaml", p)


def gen_interview() -> None:
    python_qs = {
        "level-a": [
            {"id": "a-py-1", "question": "What is the difference between dynamic and static typing?", "rubric": ["Python checks types at runtime", "C#/Java check at compile time", "Variables can be rebound to different types"], "sample_answer": "Python is dynamically typed: variable types are checked at runtime and a name can refer to different types over its lifetime. C# is statically typed: the compiler enforces types before the program runs."},
            {"id": "a-py-2", "question": "Why use 'is None' instead of '== None'?", "rubric": ["Identity vs equality", "__eq__ can be overridden", "None is singleton"], "sample_answer": "is checks object identity. == checks equality which can be overridden. None is a singleton so is None is the idiomatic, safe check."},
            {"id": "a-py-3", "question": "What is the time complexity of checking if a string is a palindrome?", "rubric": ["O(n) time", "O(n) space if copied", "O(1) extra space with two pointers"], "sample_answer": "O(n) time to compare characters. O(n) extra space if we reverse/copy the string; O(1) extra with two pointers from both ends."},
        ],
        "level-b": [
            {"id": "b-py-1", "question": "What is the difference between mutable and immutable types in Python?", "rubric": ["list vs tuple", "dict vs frozenset", "str is immutable"], "sample_answer": "Mutable objects (list, dict, set) can change in place. Immutable objects (int, str, tuple, frozenset) cannot be changed after creation."},
            {"id": "b-py-2", "question": "When would you use a set vs a list?", "rubric": ["Uniqueness", "O(1) lookup", "Order preservation"], "sample_answer": "Use a set for unique items and fast membership tests. Use a list when order matters or duplicates are allowed."},
            {"id": "b-py-3", "question": "What is a defaultdict and when is it useful?", "rubric": ["Auto-default values", "Grouping/counting patterns"], "sample_answer": "defaultdict provides a default value for missing keys, useful for grouping or counting without checking key existence."},
        ],
        "level-c": [
            {"id": "c-py-1", "question": "Explain the four pillars of OOP.", "rubric": ["Encapsulation", "Abstraction", "Inheritance", "Polymorphism"], "sample_answer": "Encapsulation bundles data and methods. Abstraction hides complexity. Inheritance reuses behavior. Polymorphism allows substituting subtypes."},
            {"id": "c-git-1", "question": "Explain git branch and pull request workflow.", "rubric": ["Branch from main", "Commit changes", "PR for review", "Merge"], "sample_answer": "Create a branch from main, commit changes, push branch, open PR for review, merge after approval."},
            {"id": "c-git-2", "question": "What is the difference between merge and rebase?", "rubric": ["Merge creates merge commit", "Rebase rewrites history", "Team conventions"], "sample_answer": "Merge combines histories with a merge commit. Rebase replays commits on top of another branch for linear history."},
        ],
    }
    odoo_qs = {
        "level-a": [
            {"id": "a-odoo-1", "question": "What is Odoo and what does ERP mean?", "rubric": ["Integrated business apps", "CRM, sales, inventory, accounting", "Open source"], "sample_answer": "Odoo is an open-source ERP: integrated business applications (CRM, sales, inventory, accounting) sharing one database."},
            {"id": "a-odoo-2", "question": "Describe the support ticket lifecycle at Odoo.", "rubric": ["Report", "Triage", "Reproduce", "Resolve or escalate"], "sample_answer": "Customer reports issue → triage/prioritize → reproduce → fix or workaround → escalate to dev if needed → close with customer confirmation."},
            {"id": "a-odoo-3", "question": "What does a Technical Support Engineer do at Odoo?", "rubric": ["Debug issues", "Email communication", "Escalation", "Python/JS/SQL"], "sample_answer": "Analyze and resolve technical issues via email, reproduce bugs, escalate when needed, use Python/JS/SQL and understand Odoo modules."},
        ],
        "level-b": [
            {"id": "b-odoo-1", "question": "Explain the Odoo ORM mental model.", "rubric": ["Models map to tables", "Records are rows", "Fields are columns", "search/browse/write"], "sample_answer": "Models are Python classes mapping to PostgreSQL tables. Records are rows. Use search() for queries, browse() for IDs, write() to update."},
            {"id": "b-odoo-2", "question": "How do you read unfamiliar Python code in Odoo modules?", "rubric": ["Start with model definition", "Follow inheritance", "Check decorators", "Read tests"], "sample_answer": "Find the model class, check _name and _inherit, follow method calls, note @api decorators, look at manifest and tests for context."},
            {"id": "b-odoo-3", "question": "Why does Odoo use PostgreSQL?", "rubric": ["Relational data", "ACID", "ORM mapping", "Complex queries"], "sample_answer": "ERP data is highly relational. PostgreSQL provides ACID transactions, complex queries, and indexes that the Odoo ORM relies on."},
        ],
        "level-c": [
            {"id": "c-odoo-1", "question": "Explain model inheritance with _inherit in Odoo.", "rubric": ["Extend existing model", "Add fields/methods", "Don't create new table"], "sample_answer": "_inherit extends an existing model in-place, adding fields or overriding methods without a new database table."},
            {"id": "c-odoo-2", "question": "Describe the Sales → Delivery → Invoice flow.", "rubric": ["SO confirmation", "Delivery order", "Invoice from delivered qty", "Stock impact"], "sample_answer": "Confirm sale order → generate delivery → validate picking reduces stock → create invoice from delivered quantities."},
            {"id": "c-odoo-3", "question": "Write a professional support email responding to a bug report.", "rubric": ["Acknowledge", "Ask for reproduction steps", "Timeline", "Professional tone"], "sample_answer": "Thank the customer, acknowledge the issue, ask for steps to reproduce and screenshots, provide expected timeline, offer workaround if available.", "type": "email"},
        ],
    }
    for level, qs in python_qs.items():
        for q in qs:
            q["category"] = "python"
            write_yaml(CONTENT / level / "interview" / f"{q['id']}.yaml", q)
    for level, qs in odoo_qs.items():
        for q in qs:
            q["category"] = "odoo"
            write_yaml(CONTENT / level / "odoo" / f"{q['id']}.yaml", q)


def main() -> None:
    print("Generating Level A Kumon...")
    gen_a1_drills()
    gen_a2_drills()
    gen_a3_drills()
    gen_a4_drills()
    print("Generating Level B Kumon...")
    gen_b_blocks()
    print("Generating Level C Kumon...")
    gen_c_blocks()
    print("Generating LeetCode...")
    gen_leetcode()
    print("Generating Interview...")
    gen_interview()
    print("Done! Content written to", CONTENT)


if __name__ == "__main__":
    main()
