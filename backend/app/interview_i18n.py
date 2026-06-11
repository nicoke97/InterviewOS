"""Interview question localization for level exams."""
from __future__ import annotations

INTERVIEW_EN: dict[str, dict] = {
    "a-int-1": {
        "question": "What is the difference between an int and a str? Give an example of each.",
        "rubric": [
            "int represents numbers",
            "str represents text in quotes",
            "convert with int()/str()",
        ],
        "sample_answer": (
            "An int is a number (e.g. 42) you can do arithmetic with; a str is text in quotes "
            "(e.g. '42'). You can convert with int('42') or str(42)."
        ),
    },
    "a-int-2": {
        "question": "What does an f-string do and why is it useful? Show an example.",
        "rubric": [
            "interpolates variables inside text",
            "syntax f'...{var}...'",
            "more readable than concatenation",
        ],
        "sample_answer": (
            "An f-string inserts variable or expression values into text: "
            "f'{name} is {age} years old'. It is more readable than concatenating with +."
        ),
    },
    "b-int-1": {
        "question": "What is the difference between a for loop and a while loop? When would you use each?",
        "rubric": [
            "for iterates over a known sequence or range",
            "while repeats while a condition is true",
            "for when you know how many times; while when it depends on a condition",
        ],
        "sample_answer": (
            "Use for when traversing a sequence or when you know the number of iterations (range). "
            "Use while when repeating until a condition becomes true or false, without knowing how many times."
        ),
    },
    "b-int-2": {
        "question": "What does return do in a function and how is it different from print?",
        "rubric": [
            "return sends a value back to the caller",
            "print only displays on screen",
            "the returned value can be reused",
        ],
        "sample_answer": (
            "return gives a value to whoever called the function so it can be used later; "
            "print only shows text on the console and does not return anything useful."
        ),
    },
    "c-int-1": {
        "question": "What is the difference between a list and a tuple in Python?",
        "rubric": [
            "list is mutable",
            "tuple is immutable",
            "tuples for fixed data, lists for changing data",
        ],
        "sample_answer": (
            "A list is mutable (you can add/remove/change elements); a tuple is immutable "
            "(it cannot change after creation). Use tuples for fixed data like coordinates "
            "and lists for collections that change."
        ),
    },
    "c-int-2": {
        "question": "What is slicing and how would you get the last two elements of a list?",
        "rubric": [
            "slicing extracts a portion with [start:stop:step]",
            "negative indices count from the end",
            "list[-2:] gives the last two",
        ],
        "sample_answer": (
            "Slicing extracts a sublist with list[start:stop:step]. For the last two: list[-2:], "
            "using negative indices that count from the end."
        ),
    },
    "d-int-1": {
        "question": "When would you use a dictionary and when a set? Give an example of each.",
        "rubric": [
            "dict maps keys to values",
            "set stores unique elements without order",
            "dict for associations; set for uniqueness/membership",
        ],
        "sample_answer": (
            "A dict associates keys with values (e.g. {'price': 100}); a set stores unique elements "
            "and allows fast membership checks (e.g. removing duplicates). Use dict to map data and set for uniqueness."
        ),
    },
    "d-int-2": {
        "question": "What is try/except for and why is it better than letting the program crash?",
        "rubric": [
            "catches runtime errors",
            "allows graceful failure handling",
            "prevents the program from stopping abruptly",
        ],
        "sample_answer": (
            "try/except catches exceptions so you can handle them (show a message, use a default value) "
            "instead of the program stopping abruptly, making it more robust."
        ),
    },
    "e-int-1": {
        "question": "What is __init__ and what does self mean in a class?",
        "rubric": [
            "__init__ is the constructor",
            "self is the current instance",
            "attributes are stored on self",
        ],
        "sample_answer": (
            "__init__ runs when creating an object and initializes its attributes. "
            "self is a reference to the current instance, which is why we store data like self.name."
        ),
    },
    "e-int-2": {
        "question": "Explain inheritance and why you would override a method.",
        "rubric": [
            "a subclass inherits from a base class",
            "reuses and extends behavior",
            "overriding changes inherited behavior",
        ],
        "sample_answer": (
            "Inheritance lets a subclass reuse attributes and methods from a base class. "
            "Overriding a method redefines its behavior in the subclass, enabling polymorphism."
        ),
    },
    "sa-int-1": {
        "question": "What is the difference between int and string in C#? Give an example of each.",
        "rubric": [
            "int represents whole numbers",
            "string represents text in double quotes",
            "convert with int.Parse / .ToString()",
        ],
        "sample_answer": (
            "An int is a whole number (e.g. 42) you can do arithmetic with; a string is text in "
            'double quotes (e.g. "42"). Convert with int.Parse("42") or 42.ToString().'
        ),
    },
    "sa-int-2": {
        "question": "What does string interpolation ($\"\") do in C# and why is it useful? Show an example.",
        "rubric": [
            "inserts variables/expressions into text",
            "syntax $\"...{var}...\"",
            "more readable than concatenating with +",
        ],
        "sample_answer": (
            "Interpolation inserts variable or expression values into text: "
            "$\"{name} is {age} years old\". It is more readable than concatenating with +."
        ),
    },
    "sb-int-1": {
        "question": "What is the difference between a for loop and a while loop in C#? When would you use each?",
        "rubric": [
            "for when you know the number of iterations",
            "while when it depends on a condition",
            "for combines init/condition/increment",
        ],
        "sample_answer": (
            "for gathers initialization, condition, and increment on one line and is ideal when you "
            "know how many times to iterate. while repeats while a condition is true, useful when "
            "you don't know the number of passes ahead of time."
        ),
    },
    "sb-int-2": {
        "question": "What do break and continue do inside a loop? Give an example of each.",
        "rubric": [
            "break ends the loop",
            "continue skips to the next iteration",
            "concrete examples",
        ],
        "sample_answer": (
            "break exits the loop entirely (e.g. when you find a value). continue skips the rest of "
            "the current iteration and moves to the next (e.g. skip even numbers)."
        ),
    },
    "sc-int-1": {
        "question": "What is LINQ in C# and what is it for? Mention methods like Where, Select, and Sum.",
        "rubric": [
            "queries over collections",
            "Where filters, Select transforms, Sum aggregates",
            "declarative style",
        ],
        "sample_answer": (
            "LINQ lets you query collections declaratively: Where filters items, Select transforms "
            "them, and Sum/Count/Max aggregate. E.g. nums.Where(n => n % 2 == 0).Sum()."
        ),
    },
    "sc-int-2": {
        "question": "What is the difference between an array (int[]) and a List<int> in C#?",
        "rubric": [
            "array has a fixed size",
            "List is resizable with Add/Remove",
            "choose based on need",
        ],
        "sample_answer": (
            "An array has a fixed size at creation; a List<int> grows and shrinks with Add/Remove. "
            "Use an array if the size is fixed and List if you need to modify the collection."
        ),
    },
    "sd-int-1": {
        "question": "What is a Dictionary<TKey, TValue> in C# and when would you use it?",
        "rubric": [
            "maps keys to values",
            "fast lookup by key",
            "unique keys",
        ],
        "sample_answer": (
            "A Dictionary associates unique keys with values and allows fast lookup by key. "
            "Use it for frequency counts, caches, or any key→value mapping."
        ),
    },
    "sd-int-2": {
        "question": "How do you handle errors in C# with try/catch? Why is it useful?",
        "rubric": [
            "try wraps risky code",
            "catch captures the exception",
            "prevents the program from crashing",
        ],
        "sample_answer": (
            "Wrap risky code in try and catch the exception so you can handle it without the "
            "program stopping abruptly, for example a divide-by-zero or invalid parse."
        ),
    },
    "se-int-1": {
        "question": "What is a class in C# and how is it different from an object? Give an example.",
        "rubric": [
            "a class is the template",
            "an object is an instance",
            "example with new",
        ],
        "sample_answer": (
            "A class is a template that defines fields and methods; an object is a concrete instance "
            "created with new. E.g. class Dog {...} and var p = new Dog();"
        ),
    },
    "se-int-2": {
        "question": "What are inheritance and polymorphism in C#? Mention virtual and override.",
        "rubric": [
            "inheritance reuses a base class",
            "override redefines virtual methods",
            "polymorphism: same method, different behavior",
        ],
        "sample_answer": (
            "Inheritance lets a class derive from another and reuse its code. With virtual/override "
            "a subclass redefines a method, and polymorphism makes the same method behave "
            "differently depending on the object's actual type."
        ),
    },
}


def localize_interview(qid: str, field: str, es_value, locale: str = "en"):
    if locale == "es":
        return es_value
    entry = INTERVIEW_EN.get(qid, {})
    if field in entry:
        return entry[field]
    return es_value
