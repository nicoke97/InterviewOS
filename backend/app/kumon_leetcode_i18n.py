"""Kumon-track LeetCode checkpoint/exam problem localization."""
from __future__ import annotations

TITLES_EN: dict[str, str] = {
    "a-cp-sum-pair": "Sum of two numbers",
    "a-cp-reverse-string": "Reverse a string",
    "a-cp-fizzbuzz": "FizzBuzz of a number",
    "a-cp-grade": "Score to letter grade",
    "a-exam-temperature": "Celsius to Fahrenheit",
    "a-exam-leap-year": "Leap year",
    "b-cp-sum-range": "Sum from 1 to n",
    "b-cp-count-positive": "Count positives",
    "b-cp-pair-sums": "Pairwise sums",
    "b-cp-apply-twice": "Apply twice",
    "b-exam-factorial": "Factorial",
    "b-exam-collatz": "Collatz steps",
    "c-cp-list-sum": "List sum",
    "c-cp-reverse-list": "Reverse a list",
    "c-cp-evens": "Filter evens",
    "c-cp-word-count": "Word count",
    "c-exam-second-largest": "Second largest",
    "c-exam-anagram": "Anagram",
    "d-cp-merge-dicts": "Merge dicts",
    "d-cp-word-freq": "Word frequency",
    "d-cp-unique": "Unique elements",
    "d-cp-safe-div": "Safe division",
    "d-exam-group-by": "Group and count",
    "d-exam-two-sum": "Two Sum",
    "e-cp-counter": "Counter class",
    "e-cp-bank": "Final balance",
    "e-cp-point-str": "Point as text",
    "e-cp-shape-area": "Area via inheritance",
    "e-exam-stack": "Stack",
    "e-exam-shapes": "Sum of areas (polymorphism)",
    "oa-cp-total-orders": "Total invoiced",
    "ob-cp-search-write": "Search + write",
    "oc-cp-group-tickets": "Group tickets",
}

DESCRIPTIONS_EN: dict[str, str] = {
    "a-cp-fizzbuzz": "Return 'Fizz', 'Buzz', 'FizzBuzz', or the number as a string.",
    "a-cp-grade": "Return 'A', 'B', 'C', or 'F' based on the score.",
    "a-cp-reverse-string": "Return the text reversed.",
    "a-cp-sum-pair": "Return a + b.",
    "a-exam-leap-year": "Return True if the year is a leap year.",
    "a-exam-temperature": "Convert Celsius to Fahrenheit (c*9/5+32).",
    "b-cp-apply-twice": "Apply f(f(x)).",
    "b-cp-count-positive": "Count how many numbers are > 0.",
    "b-cp-pair-sums": "With zip, sum element-by-element of two lists.",
    "b-cp-sum-range": "Return the sum of 1..n with a loop.",
    "b-exam-collatz": "Count steps until reaching 1 (even->/2, odd->*3+1).",
    "b-exam-factorial": "Return n! with a loop.",
    "c-cp-evens": "Return only the even numbers.",
    "c-cp-list-sum": "Sum all elements.",
    "c-cp-reverse-list": "Return the reversed list.",
    "c-cp-word-count": "Count how many words the text has.",
    "c-exam-anagram": "True if t is an anagram of s.",
    "c-exam-second-largest": "Return the second largest distinct number.",
    "d-cp-merge-dicts": "Combine two dicts (b overwrites a).",
    "d-cp-safe-div": "Return a/b or 0 if b is 0.",
    "d-cp-unique": "Return the count of unique elements.",
    "d-cp-word-freq": "Count each word and return a dict.",
    "d-exam-group-by": "Count the frequency of each element.",
    "d-exam-two-sum": "Return the indices of the two numbers that sum to target.",
    "e-cp-bank": "Create a Cuenta class with deposit and return the balance.",
    "e-cp-counter": "Create a Counter class, increment n times, and return the count.",
    "e-cp-point-str": "Create Punto with __str__ '(x, y)' and return str(Punto).",
    "e-cp-shape-area": "Define base Shape and Square(Shape) that overrides area.",
    "e-exam-shapes": "Given a list of square side lengths, sum their areas.",
    "e-exam-stack": "Create a Stack with push/pop; apply the operations.",
    "oa-cp-total-orders": "Sum the 'amount' of orders whose state is 'done'.",
    "ob-cp-search-write": "Set state='done' on records with amount>100 and return how many changed.",
    "oc-cp-group-tickets": "Return a dict {state: count} counting tickets by state.",
}

DEFAULT_APPROACH_EN = (
    "Read the statement, identify inputs/output, and solve step by step "
    "with the logic you already know."
)

DEFAULT_LEARNING_EN = [
    "Translate the statement into Python code",
    "Test with the given examples",
    "Handle edge cases before submitting",
]

DEFAULT_INTERVIEW_EN = [
    "What is the complexity of your solution?",
    "What edge cases did you consider?",
    "Is there a more efficient approach?",
]

DEFAULT_HINTS_EN = [
    "Read the statement carefully and identify the pattern.",
    "Start with the simplest correct solution.",
    "Test with the provided examples before submitting.",
]


def _lookup_id(problem_id: str) -> str:
    """C# checkpoints mirror Python ids with an 's' prefix (sa-cp-* → a-cp-*)."""
    if len(problem_id) > 1 and problem_id[0] == "s" and problem_id[1] in "abcde":
        return problem_id[1:]
    return problem_id


def localize_field(problem_id: str, field: str, es_value, locale: str = "en"):
    if locale == "es":
        return es_value
    key = problem_id if problem_id in TITLES_EN or problem_id in DESCRIPTIONS_EN else _lookup_id(problem_id)
    if field == "title":
        return TITLES_EN.get(problem_id, TITLES_EN.get(key, es_value))
    if field == "description":
        return DESCRIPTIONS_EN.get(problem_id, DESCRIPTIONS_EN.get(key, es_value))
    if field == "approach":
        return DEFAULT_APPROACH_EN if es_value else es_value
    if field == "learning":
        return DEFAULT_LEARNING_EN if es_value else es_value
    if field == "interview_questions":
        return DEFAULT_INTERVIEW_EN if es_value else es_value
    if field == "hints":
        if isinstance(es_value, list) and es_value:
            return [DEFAULT_HINTS_EN[i] if i < len(DEFAULT_HINTS_EN) else h for i, h in enumerate(es_value)]
        return es_value
    return es_value
