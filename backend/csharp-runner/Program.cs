using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.CodeAnalysis.CSharp.Scripting;
using Microsoft.CodeAnalysis.Scripting;

namespace CsharpRunner
{
    // Persistent C# execution server for the Codenda C# track.
    //
    // Protocol: one JSON request per line on stdin, one JSON response per line
    // on stdout. Keeping the process alive lets us pay the Roslyn warm-up /
    // compilation cost once instead of on every drill.
    //
    // Request  : {"type":"run","code":"...","expected":"...","timeoutMs":5000}
    //            {"type":"leetcode","code":"...","fnName":"F","testCases":[{"args":[...],"expected":...}],"timeoutMs":5000}
    //            {"type":"ping"}
    public static class Program
    {
        private static readonly string[] DefaultImports =
        {
            "System",
            "System.Collections.Generic",
            "System.Linq",
            "System.Text",
        };

        // Substrings that indicate an attempt to touch the filesystem, network,
        // processes, reflection, etc. Beginner drills never need these.
        private static readonly string[] Forbidden =
        {
            "System.IO", "System.Net", "System.Diagnostics", "System.Reflection",
            "System.Runtime", "System.Threading", "Process", "File.", "File(",
            "Directory", "Environment", "AppDomain", "Assembly", "DllImport",
            "unsafe", "stackalloc", "GC.", "Marshal",
        };

        private static ScriptOptions _options;
        private static readonly TextWriter RealStdout = Console.Out;

        public static async Task<int> Main(string[] args)
        {
            CultureInfo.DefaultThreadCurrentCulture = CultureInfo.InvariantCulture;
            CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;

            _options = ScriptOptions.Default
                .WithImports(DefaultImports)
                .WithReferences(
                    typeof(object).Assembly,
                    typeof(Console).Assembly,
                    typeof(Enumerable).Assembly,
                    typeof(JsonSerializer).Assembly,
                    typeof(System.Collections.Generic.List<>).Assembly);

            // Warm up the Roslyn pipeline so the first real request is fast.
            try { await CSharpScript.EvaluateAsync("1 + 1", _options); } catch { /* ignore */ }

            RealStdout.WriteLine("{\"type\":\"ready\"}");
            RealStdout.Flush();

            using var stdin = Console.In;
            string line;
            while ((line = await stdin.ReadLineAsync()) != null)
            {
                if (line.Length == 0) continue;
                string response;
                try
                {
                    using var doc = JsonDocument.Parse(line);
                    response = await Handle(doc.RootElement);
                }
                catch (Exception ex)
                {
                    response = Json(new Dictionary<string, object>
                    {
                        ["error"] = "runner error: " + ex.Message,
                    });
                }
                RealStdout.WriteLine(response);
                RealStdout.Flush();
            }
            return 0;
        }

        private static async Task<string> Handle(JsonElement req)
        {
            var type = req.TryGetProperty("type", out var t) ? t.GetString() : "run";
            var timeoutMs = req.TryGetProperty("timeoutMs", out var tm) ? tm.GetInt32() : 5000;

            if (type == "ping")
            {
                return Json(new Dictionary<string, object> { ["ok"] = true });
            }

            if (type == "leetcode")
            {
                return await HandleLeetcode(req, timeoutMs);
            }

            if (type == "capture")
            {
                // Run and return stdout without comparison (used by the generator).
                var src = req.GetProperty("code").GetString() ?? "";
                var bad = FindForbidden(src);
                if (bad != null)
                    return Json(new Dictionary<string, object> { ["stdout"] = "", ["error"] = $"El uso de '{bad}' no está permitido" });
                var r = await Execute(src, timeoutMs);
                return Json(new Dictionary<string, object>
                {
                    ["stdout"] = NormalizeStdout(r.Stdout),
                    ["error"] = r.Error,
                });
            }

            // default: run + match stdout
            var code = req.GetProperty("code").GetString() ?? "";
            var expected = req.TryGetProperty("expected", out var e) ? (e.ValueKind == JsonValueKind.String ? e.GetString() : e.ToString()) : "";

            var forbidden = FindForbidden(code);
            if (forbidden != null)
            {
                return Json(new Dictionary<string, object>
                {
                    ["passed"] = false,
                    ["stdout"] = "",
                    ["expected"] = expected ?? "",
                    ["error"] = $"El uso de '{forbidden}' no está permitido",
                });
            }

            var exec = await Execute(code, timeoutMs);
            if (exec.Error != null)
            {
                return Json(new Dictionary<string, object>
                {
                    ["passed"] = false,
                    ["stdout"] = exec.Stdout ?? "",
                    ["expected"] = expected ?? "",
                    ["error"] = exec.Error,
                });
            }

            var actual = NormalizeStdout(exec.Stdout);
            var exp = NormalizeStdout(expected);
            var passed = actual == exp;
            return Json(new Dictionary<string, object>
            {
                ["passed"] = passed,
                ["stdout"] = actual,
                ["expected"] = exp,
                ["error"] = passed ? null : $"Se esperaba: {exp}, se obtuvo: {actual}",
            });
        }

        private static async Task<string> HandleLeetcode(JsonElement req, int timeoutMs)
        {
            var code = req.GetProperty("code").GetString() ?? "";
            var fnName = req.TryGetProperty("fnName", out var fn) ? fn.GetString() : "Solution";

            var forbidden = FindForbidden(code);
            if (forbidden != null)
            {
                return Json(new Dictionary<string, object>
                {
                    ["passed"] = false,
                    ["results"] = new List<object>(),
                    ["error"] = $"El uso de '{forbidden}' no está permitido",
                });
            }

            var results = new List<object>();
            var allPassed = true;
            var cases = req.GetProperty("testCases");
            var index = 0;
            foreach (var tc in cases.EnumerateArray())
            {
                index++;
                var argsExpr = BuildArgsExpr(tc.GetProperty("args"));
                var expectedEl = tc.GetProperty("expected");
                var harness =
                    code + "\n" +
                    $"return System.Text.Json.JsonSerializer.Serialize((object)({fnName}({argsExpr})));";

                var exec = await Execute(harness, timeoutMs, returnValue: true);
                if (exec.Error != null)
                {
                    allPassed = false;
                    results.Add(new Dictionary<string, object>
                    {
                        ["case"] = index,
                        ["passed"] = false,
                        ["error"] = exec.Error,
                    });
                    continue;
                }

                bool passed;
                object actualObj;
                try
                {
                    using var actualDoc = JsonDocument.Parse(exec.ReturnJson ?? "null");
                    passed = DeepEqual(actualDoc.RootElement, expectedEl);
                    actualObj = JsonToObject(actualDoc.RootElement);
                }
                catch
                {
                    passed = false;
                    actualObj = exec.ReturnJson;
                }

                if (!passed) allPassed = false;
                results.Add(new Dictionary<string, object>
                {
                    ["case"] = index,
                    ["passed"] = passed,
                    ["expected"] = JsonToObject(expectedEl),
                    ["actual"] = actualObj,
                });
            }

            return Json(new Dictionary<string, object>
            {
                ["passed"] = allPassed,
                ["results"] = results,
                ["error"] = allPassed ? null : "Algunos casos de prueba fallaron",
            });
        }

        private sealed class ExecResult
        {
            public string Stdout;
            public string Error;
            public string ReturnJson;
        }

        private static async Task<ExecResult> Execute(string code, int timeoutMs, bool returnValue = false)
        {
            var sw = new StringWriter();
            var res = new ExecResult();
            using var cts = new CancellationTokenSource();
            try
            {
                Console.SetOut(sw);
                var evalTask = CSharpScript.EvaluateAsync(code, _options, cancellationToken: cts.Token);
                var completed = await Task.WhenAny(evalTask, Task.Delay(timeoutMs, cts.Token));
                if (completed != evalTask)
                {
                    cts.Cancel();
                    res.Error = $"Tiempo excedido ({timeoutMs / 1000.0:0.#}s)";
                    return res;
                }

                var value = await evalTask; // may throw compilation/runtime error
                res.Stdout = sw.ToString();
                if (returnValue)
                {
                    res.ReturnJson = value as string ?? (value?.ToString() ?? "null");
                }
            }
            catch (CompilationErrorException cex)
            {
                res.Error = "Error de compilación: " + string.Join("; ", cex.Diagnostics.Select(d => d.GetMessage()));
                res.Stdout = sw.ToString();
            }
            catch (OperationCanceledException)
            {
                res.Error = $"Tiempo excedido ({timeoutMs / 1000.0:0.#}s)";
            }
            catch (Exception ex)
            {
                res.Error = "Error de ejecución: " + ex.GetType().Name + ": " + ex.Message;
                res.Stdout = sw.ToString();
            }
            finally
            {
                Console.SetOut(RealStdout);
            }
            return res;
        }

        // ---- helpers ----------------------------------------------------------

        private static string FindForbidden(string code)
        {
            foreach (var f in Forbidden)
            {
                if (code.Contains(f, StringComparison.Ordinal)) return f;
            }
            return null;
        }

        private static string NormalizeStdout(string s)
        {
            if (s == null) return "";
            return s.Replace("\r\n", "\n").Replace("\r", "\n").Trim('\n', ' ', '\t');
        }

        private static string BuildArgsExpr(JsonElement args)
        {
            return string.Join(", ", args.EnumerateArray().Select(LiteralOf));
        }

        private static string LiteralOf(JsonElement el)
        {
            switch (el.ValueKind)
            {
                case JsonValueKind.String:
                    return "\"" + el.GetString()
                        .Replace("\\", "\\\\").Replace("\"", "\\\"")
                        .Replace("\n", "\\n").Replace("\r", "\\r").Replace("\t", "\\t") + "\"";
                case JsonValueKind.True: return "true";
                case JsonValueKind.False: return "false";
                case JsonValueKind.Null: return "null";
                case JsonValueKind.Number:
                    var raw = el.GetRawText();
                    return raw.Contains('.') || raw.Contains('e') || raw.Contains('E') ? raw + "d" : raw;
                case JsonValueKind.Array:
                    return ArrayLiteral(el);
                default:
                    return "null";
            }
        }

        private static string ArrayLiteral(JsonElement el)
        {
            var items = el.EnumerateArray().ToList();
            if (items.Count == 0) return "new int[]{}";

            var kinds = items.Select(i => i.ValueKind).Distinct().ToList();
            var hasNull = kinds.Contains(JsonValueKind.Null);
            var hasNumber = kinds.Contains(JsonValueKind.Number);
            var hasString = kinds.Contains(JsonValueKind.String);
            var hasArray = kinds.Contains(JsonValueKind.Array);
            var hasBool = kinds.Contains(JsonValueKind.True) || kinds.Contains(JsonValueKind.False);
            var inner = string.Join(", ", items.Select(LiteralOf));

            if (hasString && (hasNumber || hasBool || hasNull))
                return "new object[]{" + inner + "}";
            if (hasNull && hasNumber && !hasString && !hasArray)
                return "new int?[]{" + inner + "}";
            if (hasNull && !hasNumber && !hasString && !hasArray)
                return "new object[]{" + inner + "}";
            return "new[]{" + inner + "}";
        }

        private static bool DeepEqual(JsonElement a, JsonElement b)
        {
            if (a.ValueKind != b.ValueKind)
            {
                // treat integer/float equivalence
                if ((a.ValueKind == JsonValueKind.Number) && (b.ValueKind == JsonValueKind.Number)) { }
                else return false;
            }
            switch (a.ValueKind)
            {
                case JsonValueKind.Number:
                    return a.GetDouble() == b.GetDouble();
                case JsonValueKind.String:
                    return a.GetString() == b.GetString();
                case JsonValueKind.True:
                case JsonValueKind.False:
                case JsonValueKind.Null:
                    return true;
                case JsonValueKind.Array:
                    var ae = a.EnumerateArray().ToList();
                    var be = b.EnumerateArray().ToList();
                    if (ae.Count != be.Count) return false;
                    var ordered = true;
                    for (int i = 0; i < ae.Count; i++)
                    {
                        if (!DeepEqual(ae[i], be[i]))
                        {
                            ordered = false;
                            break;
                        }
                    }
                    return ordered || UnorderedArrayEqual(ae, be);
                case JsonValueKind.Object:
                    var ao = a.EnumerateObject().OrderBy(p => p.Name).ToList();
                    var bo = b.EnumerateObject().OrderBy(p => p.Name).ToList();
                    if (ao.Count != bo.Count) return false;
                    for (int i = 0; i < ao.Count; i++)
                    {
                        if (ao[i].Name != bo[i].Name) return false;
                        if (!DeepEqual(ao[i].Value, bo[i].Value)) return false;
                    }
                    return true;
                default:
                    return a.GetRawText() == b.GetRawText();
            }
        }

        private static bool UnorderedArrayEqual(List<JsonElement> a, List<JsonElement> b)
        {
            if (a.Count == 0) return b.Count == 0;
            if (a[0].ValueKind == JsonValueKind.Array || (b.Count > 0 && b[0].ValueKind == JsonValueKind.Array))
            {
                var na = a.Select(NormalizeNested).OrderBy(x => x, StringComparer.Ordinal).ToList();
                var nb = b.Select(NormalizeNested).OrderBy(x => x, StringComparer.Ordinal).ToList();
                return na.SequenceEqual(nb, StringComparer.Ordinal);
            }
            var sa = a.Select(e => e.GetRawText()).OrderBy(x => x, StringComparer.Ordinal).ToList();
            var sb = b.Select(e => e.GetRawText()).OrderBy(x => x, StringComparer.Ordinal).ToList();
            return sa.SequenceEqual(sb, StringComparer.Ordinal);
        }

        private static string NormalizeNested(JsonElement e)
        {
            if (e.ValueKind != JsonValueKind.Array)
                return e.GetRawText();
            var inner = e.EnumerateArray().Select(x => x.GetRawText()).OrderBy(x => x, StringComparer.Ordinal);
            return "[" + string.Join(",", inner) + "]";
        }

        private static object JsonToObject(JsonElement el)
        {
            switch (el.ValueKind)
            {
                case JsonValueKind.String: return el.GetString();
                case JsonValueKind.Number:
                    if (el.TryGetInt64(out var l)) return l;
                    return el.GetDouble();
                case JsonValueKind.True: return true;
                case JsonValueKind.False: return false;
                case JsonValueKind.Null: return null;
                case JsonValueKind.Array:
                    return el.EnumerateArray().Select(JsonToObject).ToList();
                case JsonValueKind.Object:
                    var d = new Dictionary<string, object>();
                    foreach (var p in el.EnumerateObject()) d[p.Name] = JsonToObject(p.Value);
                    return d;
                default: return null;
            }
        }

        private static string Json(object o) => JsonSerializer.Serialize(o);
    }
}
