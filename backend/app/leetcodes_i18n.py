"""English localization for LeetCodes catalog content (mirrors generate-leetcodes.py)."""
from __future__ import annotations

TOPIC_GUIDES_EN: dict[str, dict] = {
    "arrays_hashing": {
        "approach": (
            "Many array problems are solved with a single pass and a hash map or set for O(1) lookup. "
            "Ask yourself: what do I need to remember from what I've already seen?"
        ),
        "learning": [
            "Hash maps and sets for O(1) lookups and counts",
            "Extra space vs runtime trade-off",
            "When to sort first vs use an auxiliary structure",
        ],
        "interview_questions": [
            "What is the time and space complexity?",
            "What if the array is sorted — would your approach change?",
            "How would you handle duplicates or memory constraints?",
        ],
    },
    "two_pointers": {
        "approach": (
            "With two pointers (or one at each end) you can reduce O(n²) searches to O(n). "
            "Works well on sorted arrays or when finding pairs/triplets with monotonic conditions."
        ),
        "learning": [
            "Left/right pointers on sorted arrays",
            "When to move each pointer based on sum or comparison",
            "Avoiding duplicate triplets with sort + skip",
        ],
        "interview_questions": [
            "Why two pointers and not a hash map here?",
            "What edge cases exist (empty array, no solution)?",
            "What is the complexity and can it be improved?",
        ],
    },
    "sliding_window": {
        "approach": (
            "Keep a window [left, right] that satisfies a condition and expand/shrink as it grows or breaks the rule. "
            "Ideal for contiguous substrings/subarrays."
        ),
        "learning": [
            "Fixed vs variable window",
            "Updating counters when entering/leaving the window",
            "When to move left vs right",
        ],
        "interview_questions": [
            "How do you guarantee you don't revisit positions unnecessarily?",
            "What auxiliary structure do you need (set, frequency dict)?",
            "Time and space complexity of your solution",
        ],
    },
    "stack": {
        "approach": (
            "A stack (LIFO) solves matching, nesting, or 'most recent relevant' problems. "
            "Think about what you need to undo when you find a closing bracket or smaller value."
        ),
        "learning": [
            "Stack for parentheses and expressions",
            "Monotonic stack for min/max in a window",
            "Simulating operations with two stacks if needed",
        ],
        "interview_questions": [
            "Why a stack and not another approach?",
            "What happens with empty input or a single element?",
            "Can it be done in O(1) per operation?",
        ],
    },
    "binary_search": {
        "approach": (
            "If the search space is monotonic (sorted array or yes/no answer), use binary search. "
            "Define clearly what you're searching for: index, value, or minimum valid condition."
        ),
        "learning": [
            "Invariant: the answer lies in [lo, hi]",
            "Exact value search vs first valid position",
            "Binary search on the answer space (not just arrays)",
        ],
        "interview_questions": [
            "Why O(log n) and when does it not apply?",
            "How do you avoid off-by-one errors at the bounds?",
            "What if the array is rotated?",
        ],
    },
    "linked_list": {
        "approach": (
            "On linked lists use slow/fast pointers (Floyd), prev for reversal, or a dummy head to simplify edges. "
            "Draw the pointers before coding."
        ),
        "learning": [
            "Dummy node to avoid special cases at the head",
            "Fast/slow pointers for cycles and midpoint",
            "Inverting and merging by reconnecting next",
        ],
        "interview_questions": [
            "Time and space complexity?",
            "How would you detect a cycle without extra set space?",
            "Iterative vs recursive — trade-offs?",
        ],
    },
    "trees": {
        "approach": (
            "DFS traversals (pre/in/post) or BFS by level. "
            "Define the base case (None), what each node returns, and how left/right children combine."
        ),
        "learning": [
            "Recursive vs iterative DFS with stack",
            "BFS with queue for levels",
            "Propagating min/max in BST validation",
        ],
        "interview_questions": [
            "Recursive or iterative — when each?",
            "Complexity on balanced vs degenerate trees?",
            "How would you serialize/deserialize the tree?",
        ],
    },
    "dp_1d": {
        "approach": (
            "Define dp[i] = best answer up to position i (or for amount i). "
            "The transition usually looks at 1–2 previous states. Optimize space if you only need recent values."
        ),
        "learning": [
            "Formulate state and transition before coding",
            "Bottom-up vs top-down with memo",
            "Rolling array for O(1) extra space",
        ],
        "interview_questions": [
            "What is your state and why?",
            "Can space be reduced to O(1)?",
            "How would you detect overlapping subproblems?",
        ],
    },
    "graphs": {
        "approach": (
            "Model nodes and edges; choose BFS (min steps/layers), DFS (components, cycles), or topological sort (dependencies). "
            "Mark visited to avoid repeats."
        ),
        "learning": [
            "BFS vs DFS — when each",
            "Cycle detection and topological sort",
            "Grid as implicit graph (4/8 directions)",
        ],
        "interview_questions": [
            "Representation: adjacency list vs matrix?",
            "How do you detect a cycle?",
            "Complexity with V vertices and E edges",
        ],
    },
    "intervals": {
        "approach": (
            "Sort by start (or end). Merge or insert by comparing overlaps: intervals overlap if start <= prev_end."
        ),
        "learning": [
            "Sort as almost always the first step",
            "Linear merge after sorting",
            "Insert with binary search in advanced cases",
        ],
        "interview_questions": [
            "Why sort first?",
            "How do you handle open/closed intervals?",
            "Total complexity of your algorithm",
        ],
    },
}

PROBLEM_HINTS_EN: dict[str, list[str]] = {
    "lc-two-sum": [
        "For each number nums[i], the complement is target - nums[i].",
        "Store {value: index} in a dict as you scan; before saving, check if the complement is already there.",
        "Single pass: O(n) time, O(n) space.",
    ],
    "lc-contains-duplicate": [
        "Do you need to count or just detect a duplicate?",
        "A set of seen values: if nums[i] is already in the set, return True.",
        "Alternative: sort and compare neighbors — O(n log n) without extra space.",
    ],
    "lc-valid-anagram": [
        "Same length and same character frequencies.",
        "Count chars of s in a dict and subtract with t; or use Counter(s) == Counter(t).",
        "If len(s) != len(t), return False immediately.",
    ],
    "lc-best-time-stock": [
        "You want max(prices[j] - prices[i]) with j > i.",
        "Scan prices tracking min_price seen; update max_profit with price - min_price.",
        "One pass O(n), O(1) space.",
    ],
    "lc-group-anagrams": [
        "Anagrams share the same 'signature': sorted letters or count tuple.",
        "dict[signature] -> list of strings; group strs by signature.",
        "Signature with tuple(sorted(s)) is simple and sufficient here.",
    ],
    "lc-top-k-frequent": [
        "First count frequencies with Counter or dict.",
        "Then extract the k most frequent: bucket sort by freq or size-k heap.",
        "Bucket: list indexed by frequency — O(n) average.",
    ],
    "lc-valid-palindrome": [
        "Normalize: alphanumeric only in lowercase (two pointers or filter).",
        "Compare chars at left and right moving toward the center.",
        "Skip non-alphanumeric chars before comparing.",
    ],
    "lc-two-sum-ii": [
        "Sorted array: pointers left=0, right=len-1.",
        "If sum < target, left++; if sum > target, right--.",
        "Return 1-based indices: [left+1, right+1].",
    ],
    "lc-3sum": [
        "Sort nums; fix i and two-sum the pair in i+1..n-1.",
        "If nums[i] == nums[i-1], skip duplicates at i.",
        "Same when moving left/right after finding triplets.",
    ],
    "lc-container-water": [
        "Two pointers at the ends of the height array.",
        "Area = min(h[left], h[right]) * (right - left).",
        "Move the pointer on the shorter side — the other can't improve area.",
    ],
    "lc-longest-substring": [
        "Window [left, right] with set or dict of last char position.",
        "Expand right; if char repeats, move left past last occurrence.",
        "Track max(right - left + 1) each step.",
    ],
    "lc-min-window-substring": [
        "Variable window with char counters of t in s.",
        "Expand right until t is covered; then shrink left minimizing window.",
        "Track formed/required to know when window is valid.",
    ],
    "lc-valid-parentheses": [
        "Stack of opening brackets; on closing, must match top.",
        "Map {')':'(', '}':'{', ']':'['}.",
        "Stack must be empty at the end.",
    ],
    "lc-min-stack": [
        "Two stacks: values and current mins in parallel.",
        "On push: push value and min(val, top_mins or val).",
        "getMin in O(1) reading top of mins.",
    ],
    "lc-binary-search": [
        "Classic: lo, hi, mid = (lo+hi)//2.",
        "If nums[mid] < target, lo = mid+1; if >, hi = mid-1.",
        "Return -1 if lo > hi.",
    ],
    "lc-search-rotated": [
        "Binary search: one half is always sorted.",
        "Check if target is in the sorted half; if not, search the other.",
        "Identify sorted half comparing nums[mid] with nums[lo].",
    ],
    "lc-reverse-linked-list": [
        "Three pointers: prev, curr, next while traversing.",
        "curr.next = prev; advance all three.",
        "Return prev at the end (new head).",
    ],
    "lc-merge-two-lists": [
        "Dummy head + tail pointer; compare heads of a and b.",
        "Link the smaller and advance that pointer.",
        "When done, link the non-empty remainder.",
    ],
    "lc-linked-list-cycle": [
        "Floyd: slow moves 1, fast moves 2; cycle if they meet.",
        "In this MVP, pos >= 0 indicates a cycle in the given representation.",
        "In a real interview: detect cycle without modifying the list.",
    ],
    "lc-max-depth-tree": [
        "DFS: 1 + max(left depth, right depth); None -> 0.",
        "BFS: count levels with queue.",
        "Base case: None node returns 0.",
    ],
    "lc-invert-tree": [
        "Swap left and right children at each node (DFS or BFS).",
        "Recursive: invert(left), invert(right), swap.",
        "Return the root (same reference).",
    ],
    "lc-validate-bst": [
        "Pass valid (min, max) range per node.",
        "Node must be in (min, max); validate subtrees with updated ranges.",
        "None is always valid.",
    ],
    "lc-climbing-stairs": [
        "dp[i] = ways to reach step i.",
        "dp[i] = dp[i-1] + dp[i-2] — same as Fibonacci.",
        "Optimize to two variables: prev1, prev2.",
    ],
    "lc-house-robber": [
        "dp[i] = max money robbing up to house i.",
        "dp[i] = max(dp[i-1], dp[i-2] + nums[i]) — no adjacent houses.",
        "You only need the two previous values.",
    ],
    "lc-coin-change": [
        "dp[a] = minimum coins for amount a; init inf except dp[0]=0.",
        "For each coin and amount, dp[a] = min(dp[a], dp[a-coin]+1).",
        "Return dp[amount] if not inf, else -1.",
    ],
    "lc-number-islands": [
        "For each unvisited '1', DFS/BFS marks entire island visited.",
        "Increment counter for each new component.",
        "Mark visited in-place or with set of (r,c).",
    ],
    "lc-course-schedule": [
        "Prerequisite graph; cycle => cannot finish.",
        "Topological sort (Kahn BFS or DFS with visiting/visited states).",
        "n nodes, edge prerequisites[i]=[a,b] means b -> a.",
    ],
    "lc-merge-intervals": [
        "Sort by start; merge if intervals[i].start <= merged[-1].end.",
        "If overlapping, extend end of last interval.",
        "If not, append new interval.",
    ],
}

DESCRIPTIONS_EN: dict[str, str] = {
    "lc-two-sum": (
        "Given an array of integers nums and an integer target, return the indices "
        "of the two numbers such that they add up to target.\n\n"
        "You may assume that each input has exactly one solution, and you may not "
        "use the same element twice. You can return the answer in any order."
    ),
    "lc-contains-duplicate": (
        "Given an integer array nums, return true if any value appears at least "
        "twice in the array, and false if every element is distinct."
    ),
    "lc-valid-anagram": (
        "Given two strings s and t, return true if t is an anagram of s, and false "
        "otherwise.\n\n"
        "An anagram is a word formed by rearranging the letters of another, using "
        "all the original letters exactly once."
    ),
    "lc-best-time-stock": (
        "You are given an array prices where prices[i] is the price of a stock on "
        "day i.\n\n"
        "You want to maximize profit by choosing one day to buy and a different "
        "day in the future to sell. Return the maximum profit you can achieve. If "
        "you cannot make a profit, return 0."
    ),
    "lc-group-anagrams": (
        "Given an array of strings strs, group the anagrams together. You can "
        "return the answer in any order, and the order within each group does not "
        "matter."
    ),
    "lc-top-k-frequent": (
        "Given an integer array nums and an integer k, return the k most frequent "
        "elements. You may return the answer in any order."
    ),
    "lc-valid-palindrome": (
        "Given a string s, return true if it is a palindrome considering only "
        "alphanumeric characters and ignoring cases.\n\n"
        "A palindrome reads the same forward and backward."
    ),
    "lc-two-sum-ii": (
        "Given a 1-indexed array of integers numbers that is sorted in non-decreasing "
        "order, find two numbers such that they add up to a specific target number.\n\n"
        "Return the indices (1-indexed) of the two numbers. You may assume each "
        "input has exactly one solution, and you may not use the same element twice. "
        "Your solution must use only constant extra memory and run in O(n) time."
    ),
    "lc-3sum": (
        "Given an integer array nums, return all unique triplets [nums[i], nums[j], "
        "nums[k]] such that i != j, i != k, j != k, and nums[i] + nums[j] + "
        "nums[k] == 0.\n\n"
        "The output must not contain duplicate triplets."
    ),
    "lc-container-water": (
        "You are given n non-negative integers height where the ith line goes from "
        "(i, 0) to (i, height[i]).\n\n"
        "Find two lines that together with the x-axis form a container that holds "
        "as much water as possible. Return the maximum amount of water the "
        "container can store."
    ),
    "lc-longest-substring": (
        "Given a string s, find the length of the longest substring without "
        "repeating characters."
    ),
    "lc-min-window-substring": (
        "Given two strings s and t, return the minimum window substring of s such "
        "that every character in t (including duplicates) is included in the "
        "window. If there is no such substring, return an empty string."
    ),
    "lc-valid-parentheses": (
        "Given a string s containing just the characters '(', ')', '{', '}', '[' "
        "and ']', determine if the input string is valid.\n\n"
        "A string is valid if open brackets are closed by the same type of "
        "brackets, in the correct order, and each close bracket has a matching "
        "open bracket of the same type."
    ),
    "lc-min-stack": (
        "Design a stack that supports push, pop, top, and retrieving the minimum "
        "element in constant time.\n\n"
        "In this exercise you receive a list ops of operations in order: "
        "['push', val], ['pop'], ['top'], or ['getMin']. Return a list with the "
        "result of each top and getMin (None for other operations)."
    ),
    "lc-binary-search": (
        "Given an array of integers nums which is sorted in ascending order, and an "
        "integer target, return the index of target if it is in nums, or -1 if it "
        "is not.\n\n"
        "You must write an algorithm with O(log n) runtime complexity."
    ),
    "lc-search-rotated": (
        "Given an integer array nums sorted in ascending order that has been "
        "rotated between 1 and n times, and an integer target, return the index of "
        "target if it is in nums, or -1 if it is not.\n\n"
        "You must write an algorithm with O(log n) runtime complexity."
    ),
    "lc-reverse-linked-list": (
        "Given a linked list represented as an array of values in order, reverse it "
        "and return the values in the new order.\n\n"
        "For example, [1, 2, 3, 4, 5] becomes [5, 4, 3, 2, 1]."
    ),
    "lc-merge-two-lists": (
        "Given two sorted linked lists represented as arrays a and b, merge them "
        "into one sorted list and return its values.\n\n"
        "The result should be formed by splicing together the nodes of a and b in "
        "ascending order."
    ),
    "lc-linked-list-cycle": (
        "You are given a linked list represented by values (node values in order) "
        "and pos (the index the tail connects to for a cycle, or -1 if there is "
        "no cycle).\n\n"
        "Return true if there is a cycle in the linked list, and false otherwise."
    ),
    "lc-max-depth-tree": (
        "Given a binary tree in level-order representation (an array where None "
        "means an empty node), return its maximum depth.\n\n"
        "The maximum depth is the number of nodes along the longest path from the "
        "root down to the farthest leaf node."
    ),
    "lc-invert-tree": (
        "Given a binary tree in level-order representation (array with None for "
        "empty nodes), invert the tree (swap left and right children at every "
        "node) and return the new level-order representation."
    ),
    "lc-validate-bst": (
        "Given a binary tree in level-order representation, determine if it is a "
        "valid binary search tree (BST).\n\n"
        "A valid BST has every node's left subtree containing only values less than "
        "the node, and every right subtree containing only values greater than the "
        "node."
    ),
    "lc-climbing-stairs": (
        "You are climbing a staircase. It takes n steps to reach the top.\n\n"
        "Each time you can climb either 1 or 2 steps. Given n, return how many "
        "distinct ways you can climb to the top."
    ),
    "lc-house-robber": (
        "You are a robber planning to rob houses along a street. Each house has a "
        "certain amount of money. Adjacent houses have security systems that will "
        "alert the police if both are robbed on the same night.\n\n"
        "Given nums where nums[i] is the money in the ith house, return the maximum "
        "amount you can rob without alerting the police."
    ),
    "lc-coin-change": (
        "Given an array coins of distinct coin denominations and an integer amount, "
        "return the fewest number of coins needed to make up that amount. If the "
        "amount cannot be made up, return -1.\n\n"
        "You may use each denomination as many times as you want."
    ),
    "lc-number-islands": (
        "Given an m x n 2D grid map of '1's (land) and '0's (water), return the "
        "number of islands.\n\n"
        "An island is surrounded by water and is formed by connecting adjacent "
        "lands horizontally or vertically."
    ),
    "lc-course-schedule": (
        "There are numCourses courses labeled from 0 to numCourses - 1. You are "
        "given prerequisites where [a, b] indicates you must take course b before "
        "course a.\n\n"
        "Return true if you can finish all courses, or false if there is a "
        "prerequisite cycle that makes completion impossible."
    ),
    "lc-merge-intervals": (
        "Given an array of intervals where intervals[i] = [start, end], merge all "
        "overlapping intervals and return an array of the non-overlapping intervals "
        "that cover all the intervals in the input.\n\n"
        "Two intervals overlap if the start of one is less than or equal to the "
        "end of the other."
    ),
}

EXPLAIN_CHECKLIST_EN = [
    "Read the statement and examples",
    "Identify inputs, output, and edge cases",
    "Think about the pattern before writing code",
]

NARRATION_PROMPTS_EN = [
    "Explain your approach out loud step by step",
    "What is the time and space complexity?",
    "What edge cases did you test?",
]

DEFAULT_BLOCK_INSTRUCTION_EN = "Solve each problem. Review all answers when done."


def pick(problem_id: str, topic: str, field: str, es_value, locale: str):
    if locale == "es":
        return es_value
    if field == "description":
        return DESCRIPTIONS_EN.get(problem_id, es_value)
    if field == "hints":
        return PROBLEM_HINTS_EN.get(problem_id, es_value)
    guide = TOPIC_GUIDES_EN.get(topic, {})
    if field == "approach":
        return guide.get("approach", es_value)
    if field == "learning":
        return guide.get("learning", es_value)
    if field == "interview_questions":
        return guide.get("interview_questions", es_value)
    return es_value


def localized_tier_lists(tier_data: dict, locale: str) -> tuple[list[str], list[str]]:
    if locale == "es":
        return (
            list(tier_data.get("explain_checklist", []) or []),
            list(tier_data.get("narration_prompts", []) or []),
        )
    explain = tier_data.get("explain_checklist_en") or EXPLAIN_CHECKLIST_EN
    narrate = tier_data.get("narration_prompts_en") or NARRATION_PROMPTS_EN
    return list(explain), list(narrate)
