"""C# starters and solutions for the interview LeetCodes catalog.

Test cases stay shared with the Python YAML. This module supplies the
PascalCase entry point, tier stubs, and a reference solution used by the
editor and the C# runner.
"""
from __future__ import annotations


TREE_NODE_PRELUDE = """
class TNode
{
    public int V;
    public TNode L;
    public TNode R;
}
"""


def normalize_exec_language(language: str | None) -> str:
    lang = (language or "").strip().lower()
    if lang in {"csharp", "cs", "c#"}:
        return "csharp"
    return "python"


def csharp_spec(problem_id: str, tier: int = 1) -> dict[str, str] | None:
    item = PROBLEMS.get(problem_id)
    if not item:
        return None
    starters = item["starters"]
    starter = starters.get(tier) or starters.get(2) or starters[1]
    solution = item["solution"]
    if problem_id in {"lc-invert-tree", "lc-validate-bst"}:
        solution = TREE_NODE_PRELUDE.strip() + "\n\n" + solution
    return {
        "fn_name": item["fn_name"],
        "starter_code": starter,
        "solution_code": solution,
    }


def _method(ret: str, name: str, params: str, body: str) -> str:
    return f"{ret} {name}({params})\n{{\n{body.rstrip()}\n}}"


def _stub(ret: str, name: str, params: str, default: str, comment: str = "") -> str:
    inner = f"    // {comment}\n    return {default};" if comment else f"    return {default};"
    return _method(ret, name, params, inner)


def _entry(name: str, ret: str, params: str, default: str, solution: str, comment: str = "") -> dict:
    return {
        "fn_name": name,
        "starters": {
            1: _stub(ret, name, params, default, comment),
            2: _stub(ret, name, params, default),
            3: _stub(ret, name, params, default),
        },
        "solution": _method(ret, name, params, solution),
    }


PROBLEMS: dict[str, dict] = {
    "lc-two-sum": _entry(
        "TwoSum", "int[]", "int[] nums, int target", "new int[] {}",
        """    var seen = new Dictionary<int, int>();
    for (int i = 0; i < nums.Length; i++)
    {
        int need = target - nums[i];
        if (seen.ContainsKey(need))
            return new[] { seen[need], i };
        seen[nums[i]] = i;
    }
    return new int[] {};""",
        "use a hash map",
    ),
    "lc-contains-duplicate": _entry(
        "ContainsDuplicate", "bool", "int[] nums", "false",
        """    return nums.Length != nums.Distinct().Count();""",
    ),
    "lc-valid-anagram": _entry(
        "IsAnagram", "bool", "string s, string t", "false",
        """    if (s.Length != t.Length) return false;
    var count = new Dictionary<char, int>();
    foreach (var c in s)
        count[c] = count.GetValueOrDefault(c) + 1;
    foreach (var c in t)
    {
        if (count.GetValueOrDefault(c) == 0) return false;
        count[c] -= 1;
    }
    return true;""",
    ),
    "lc-best-time-stock": _entry(
        "MaxProfit", "int", "int[] prices", "0",
        """    int best = 0, low = int.MaxValue;
    foreach (var p in prices)
    {
        low = Math.Min(low, p);
        best = Math.Max(best, p - low);
    }
    return best;""",
    ),
    "lc-group-anagrams": _entry(
        "GroupAnagrams", "string[][]", "string[] strs", "new string[][] {}",
        """    var groups = new Dictionary<string, List<string>>();
    foreach (var s in strs)
    {
        var chars = s.ToCharArray();
        Array.Sort(chars);
        var key = new string(chars);
        if (!groups.ContainsKey(key)) groups[key] = new List<string>();
        groups[key].Add(s);
    }
    return groups.Values.Select(v => v.ToArray()).ToArray();""",
    ),
    "lc-top-k-frequent": _entry(
        "TopKFrequent", "int[]", "int[] nums, int k", "new int[] {}",
        """    var count = new Dictionary<int, int>();
    foreach (var n in nums)
        count[n] = count.GetValueOrDefault(n) + 1;
    return count.OrderByDescending(kv => kv.Value).Take(k).Select(kv => kv.Key).ToArray();""",
    ),
    "lc-valid-palindrome": _entry(
        "IsPalindrome", "bool", "string s", "false",
        """    var cleaned = s.Where(char.IsLetterOrDigit).Select(char.ToLower).ToArray();
    return cleaned.SequenceEqual(cleaned.Reverse());""",
    ),
    "lc-two-sum-ii": _entry(
        "TwoSumIi", "int[]", "int[] numbers, int target", "new int[] {}",
        """    int left = 0, right = numbers.Length - 1;
    while (left < right)
    {
        int sum = numbers[left] + numbers[right];
        if (sum == target) return new[] { left + 1, right + 1 };
        if (sum < target) left++;
        else right--;
    }
    return new int[] {};""",
    ),
    "lc-3sum": _entry(
        "ThreeSum", "int[][]", "int[] nums", "new int[][] {}",
        """    Array.Sort(nums);
    var output = new List<int[]>();
    for (int i = 0; i < nums.Length; i++)
    {
        if (i > 0 && nums[i] == nums[i - 1]) continue;
        int left = i + 1, right = nums.Length - 1;
        while (left < right)
        {
            int sum = nums[i] + nums[left] + nums[right];
            if (sum == 0)
            {
                output.Add(new[] { nums[i], nums[left], nums[right] });
                left++;
                right--;
                while (left < right && nums[left] == nums[left - 1]) left++;
            }
            else if (sum < 0) left++;
            else right--;
        }
    }
    return output.ToArray();""",
    ),
    "lc-container-water": _entry(
        "MaxArea", "int", "int[] height", "0",
        """    int left = 0, right = height.Length - 1, best = 0;
    while (left < right)
    {
        best = Math.Max(best, Math.Min(height[left], height[right]) * (right - left));
        if (height[left] < height[right]) left++;
        else right--;
    }
    return best;""",
    ),
    "lc-longest-substring": _entry(
        "LengthOfLongest", "int", "string s", "0",
        """    var last = new Dictionary<char, int>();
    int left = 0, best = 0;
    for (int right = 0; right < s.Length; right++)
    {
        char ch = s[right];
        if (last.ContainsKey(ch) && last[ch] >= left)
            left = last[ch] + 1;
        last[ch] = right;
        best = Math.Max(best, right - left + 1);
    }
    return best;""",
    ),
    "lc-min-window-substring": _entry(
        "MinWindow", "string", "string s, string t", "\"\"",
        """    if (string.IsNullOrEmpty(t)) return "";
    var need = new Dictionary<char, int>();
    foreach (var c in t)
        need[c] = need.GetValueOrDefault(c) + 1;
    int missing = t.Length, left = 0, bestLen = 0;
    string best = "";
    for (int right = 0; right < s.Length; right++)
    {
        char c = s[right];
        if (need.ContainsKey(c))
        {
            if (need[c] > 0) missing--;
            need[c]--;
        }
        while (missing == 0)
        {
            if (bestLen == 0 || right - left + 1 < bestLen)
            {
                bestLen = right - left + 1;
                best = s.Substring(left, bestLen);
            }
            char leftC = s[left];
            if (need.ContainsKey(leftC))
            {
                need[leftC]++;
                if (need[leftC] > 0) missing++;
            }
            left++;
        }
    }
    return best;""",
    ),
    "lc-valid-parentheses": _entry(
        "IsValidParen", "bool", "string s", "false",
        """    var stack = new Stack<char>();
    var pairs = new Dictionary<char, char> { [')'] = '(', ['}'] = '{', [']'] = '[' };
    foreach (var c in s)
    {
        if (pairs.ContainsKey(c))
        {
            if (stack.Count == 0 || stack.Pop() != pairs[c]) return false;
        }
        else stack.Push(c);
    }
    return stack.Count == 0;""",
    ),
    "lc-min-stack": _entry(
        "MinStackOps", "object[]", "object[][] ops", "new object[] {}",
        """    var stack = new List<int>();
    var mins = new List<int>();
    var output = new List<object>();
    foreach (var op in ops)
    {
        var name = Convert.ToString(op[0]);
        if (name == "push")
        {
            int v = Convert.ToInt32(op[1]);
            stack.Add(v);
            mins.Add(mins.Count == 0 ? v : Math.Min(v, mins[mins.Count - 1]));
            output.Add(null);
        }
        else if (name == "pop")
        {
            stack.RemoveAt(stack.Count - 1);
            mins.RemoveAt(mins.Count - 1);
            output.Add(null);
        }
        else if (name == "top")
            output.Add(stack[stack.Count - 1]);
        else if (name == "getMin")
            output.Add(mins[mins.Count - 1]);
    }
    return output.ToArray();""",
    ),
    "lc-binary-search": _entry(
        "BinarySearch", "int", "int[] nums, int target", "-1",
        """    int lo = 0, hi = nums.Length - 1;
    while (lo <= hi)
    {
        int mid = lo + (hi - lo) / 2;
        if (nums[mid] == target) return mid;
        if (nums[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1;""",
    ),
    "lc-search-rotated": _entry(
        "SearchRotated", "int", "int[] nums, int target", "-1",
        """    int lo = 0, hi = nums.Length - 1;
    while (lo <= hi)
    {
        int mid = lo + (hi - lo) / 2;
        if (nums[mid] == target) return mid;
        if (nums[lo] <= nums[mid])
        {
            if (nums[lo] <= target && target < nums[mid]) hi = mid - 1;
            else lo = mid + 1;
        }
        else
        {
            if (nums[mid] < target && target <= nums[hi]) lo = mid + 1;
            else hi = mid - 1;
        }
    }
    return -1;""",
    ),
    "lc-reverse-linked-list": _entry(
        "ReverseList", "int[]", "int[] nums", "nums",
        """    return Enumerable.Reverse(nums).ToArray();""",
    ),
    "lc-merge-two-lists": _entry(
        "MergeLists", "int[]", "int[] a, int[] b", "new int[] {}",
        """    int i = 0, j = 0;
    var output = new List<int>();
    while (i < a.Length && j < b.Length)
    {
        if (a[i] <= b[j]) output.Add(a[i++]);
        else output.Add(b[j++]);
    }
    while (i < a.Length) output.Add(a[i++]);
    while (j < b.Length) output.Add(b[j++]);
    return output.ToArray();""",
    ),
    "lc-linked-list-cycle": _entry(
        "HasCycle", "bool", "int[] values, int pos", "false",
        """    return pos >= 0;""",
    ),
    "lc-max-depth-tree": _entry(
        "MaxDepth", "int", "int?[] nodes", "0",
        """    if (nodes == null || nodes.Length == 0) return 0;
    int Dfs(int i)
    {
        if (i >= nodes.Length || nodes[i] == null) return 0;
        return 1 + Math.Max(Dfs(2 * i + 1), Dfs(2 * i + 2));
    }
    return Dfs(0);""",
    ),
    "lc-invert-tree": _entry(
        "InvertTree", "int[]", "int[] nodes", "nodes",
        """    if (nodes == null || nodes.Length == 0) return nodes;
    TNode Build(int i)
    {
        if (i >= nodes.Length) return null;
        return new TNode { V = nodes[i], L = Build(2 * i + 1), R = Build(2 * i + 2) };
    }
    TNode Invert(TNode n)
    {
        if (n == null) return null;
        var left = Invert(n.R);
        var right = Invert(n.L);
        n.L = left;
        n.R = right;
        return n;
    }
    int[] Serialize(TNode root)
    {
        if (root == null) return new int[] {};
        var output = new List<int>();
        var q = new Queue<TNode>();
        q.Enqueue(root);
        while (q.Count > 0)
        {
            var cur = q.Dequeue();
            output.Add(cur.V);
            if (cur.L != null) q.Enqueue(cur.L);
            if (cur.R != null) q.Enqueue(cur.R);
        }
        return output.ToArray();
    }
    return Serialize(Invert(Build(0)));""",
    ),
    "lc-validate-bst": _entry(
        "IsValidBst", "bool", "object nodesRaw", "false",
        """    var nodes = new List<int?>();
    foreach (var x in (System.Collections.IEnumerable)nodesRaw)
        nodes.Add(x == null ? null : Convert.ToInt32(x));
    if (nodes.Count == 0) return true;
    TNode Build(int i)
    {
        if (i >= nodes.Count || nodes[i] == null) return null;
        return new TNode { V = nodes[i].Value, L = Build(2 * i + 1), R = Build(2 * i + 2) };
    }
    bool Valid(TNode node, long lo, long hi)
    {
        if (node == null) return true;
        if (node.V <= lo || node.V >= hi) return false;
        return Valid(node.L, lo, node.V) && Valid(node.R, node.V, hi);
    }
    return Valid(Build(0), long.MinValue, long.MaxValue);""",
    ),
    "lc-climbing-stairs": _entry(
        "ClimbStairs", "int", "int n", "0",
        """    if (n <= 2) return n;
    int a = 1, b = 2;
    for (int i = 3; i <= n; i++)
    {
        int next = a + b;
        a = b;
        b = next;
    }
    return b;""",
    ),
    "lc-house-robber": _entry(
        "Rob", "int", "int[] nums", "0",
        """    int prev2 = 0, prev1 = 0;
    foreach (var n in nums)
    {
        int cur = Math.Max(prev1, prev2 + n);
        prev2 = prev1;
        prev1 = cur;
    }
    return prev1;""",
    ),
    "lc-coin-change": _entry(
        "CoinChange", "int", "int[] coins, int amount", "-1",
        """    var dp = Enumerable.Repeat(1_000_000_000, amount + 1).ToArray();
    dp[0] = 0;
    for (int a = 1; a <= amount; a++)
        foreach (var c in coins)
            if (c <= a)
                dp[a] = Math.Min(dp[a], dp[a - c] + 1);
    return dp[amount] == 1_000_000_000 ? -1 : dp[amount];""",
    ),
    "lc-number-islands": _entry(
        "NumIslands", "int", "string[][] grid", "0",
        """    if (grid == null || grid.Length == 0) return 0;
    int rows = grid.Length, cols = grid[0].Length, count = 0;
    void Dfs(int r, int c)
    {
        if (r < 0 || c < 0 || r >= rows || c >= cols || grid[r][c] != "1") return;
        grid[r][c] = "0";
        Dfs(r + 1, c); Dfs(r - 1, c); Dfs(r, c + 1); Dfs(r, c - 1);
    }
    for (int r = 0; r < rows; r++)
        for (int c = 0; c < cols; c++)
            if (grid[r][c] == "1")
            {
                count++;
                Dfs(r, c);
            }
    return count;""",
    ),
    "lc-course-schedule": _entry(
        "CanFinish", "bool", "int numCourses, int[][] prerequisites", "false",
        """    var adj = Enumerable.Range(0, numCourses).Select(_ => new List<int>()).ToList();
    foreach (var p in prerequisites)
        adj[p[1]].Add(p[0]);
    var state = new int[numCourses];
    bool Dfs(int u)
    {
        if (state[u] == 1) return false;
        if (state[u] == 2) return true;
        state[u] = 1;
        foreach (var v in adj[u])
            if (!Dfs(v)) return false;
        state[u] = 2;
        return true;
    }
    return Enumerable.Range(0, numCourses).All(Dfs);""",
    ),
    "lc-merge-intervals": _entry(
        "MergeIntervals", "int[][]", "int[][] intervals", "new int[][] {}",
        """    if (intervals == null || intervals.Length == 0) return new int[][] {};
    var ordered = intervals.OrderBy(iv => iv[0]).ToArray();
    var merged = new List<int[]> { (int[])ordered[0].Clone() };
    foreach (var iv in ordered.Skip(1))
    {
        if (iv[0] <= merged[merged.Count - 1][1])
            merged[merged.Count - 1][1] = Math.Max(merged[merged.Count - 1][1], iv[1]);
        else
            merged.Add((int[])iv.Clone());
    }
    return merged.ToArray();""",
    ),
}

def csharp_solution(problem_id: str) -> str | None:
    spec = csharp_spec(problem_id, 1)
    if not spec:
        return None
    code = spec["solution_code"]
    if problem_id in {"lc-invert-tree", "lc-validate-bst"}:
        return TREE_NODE_PRELUDE.strip() + "\n\n" + code
    return code


def csharp_starter(problem_id: str, tier: int = 1) -> str | None:
    spec = csharp_spec(problem_id, tier)
    return spec["starter_code"] if spec else None
