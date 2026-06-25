import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { CodeEditor } from '../components/CodeEditor';
import { Timer } from '../components/Timer';

const LEVELS = ['a', 'b', 'c'];

export function LeetCode() {
  const [level, setLevel] = useState('a');
  const [problems, setProblems] = useState<{ id: string; title: string; tier_passed: number }[]>([]);
  const [unlocked, setUnlocked] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [tier, setTier] = useState(1);
  const [problem, setProblem] = useState<Record<string, unknown> | null>(null);
  const [code, setCode] = useState('');
  const [narrationIdx, setNarrationIdx] = useState(0);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    api.leetcodeList(level).then((res) => {
      setUnlocked(!!res.unlocked);
      setProblems((res.problems as typeof problems) || []);
    });
  }, [level]);

  useEffect(() => {
    if (!selected) return;
    api.leetcodeGet(selected, tier).then((p) => {
      setProblem(p);
      setCode(String(p.starter_code || ''));
      setNarrationIdx(0);
      setResult(null);
      setRunning(true);
    });
  }, [selected, tier]);

  const narrations = (problem?.narration_prompts as string[]) || [];

  const run = async () => {
    if (!selected) return;
    const res = await api.run({ code, exercise_id: selected, exercise_type: 'leetcode', tier });
    setResult(res);
  };

  const submit = async () => {
    if (!selected) return;
    const res = await api.submit({
      code,
      exercise_id: selected,
      exercise_type: 'leetcode',
      tier,
      hints_used: narrationIdx,
      time_ms: 0,
    }) as { passed: boolean; result: Record<string, unknown> };
    setResult(res.result);
  };

  if (!unlocked) {
    return (
      <div className="card text-center">
        <h1 className="text-xl font-bold">LeetCode Locked</h1>
        <p className="mt-2 text-slate-400">
          Complete all Kumon blocks in Level {level.toUpperCase()} with stable mastery to unlock.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">LeetCode</h1>
        <div className="flex gap-2">
          {LEVELS.map((l) => (
            <button
              key={l}
              type="button"
              onClick={() => { setLevel(l); setSelected(null); }}
              className={`rounded px-3 py-1 text-sm ${level === l ? 'bg-emerald-600' : 'bg-slate-700'}`}
            >
              Level {l.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <div className="space-y-2">
          {problems.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => setSelected(p.id)}
              className={`block w-full rounded-lg border p-3 text-left text-sm ${
                selected === p.id ? 'border-emerald-500 bg-emerald-900/20' : 'border-slate-600'
              }`}
            >
              <p className="font-medium">{p.title}</p>
              <p className="text-xs text-slate-400">Tier {p.tier_passed}/3 passed</p>
            </button>
          ))}
        </div>

        <div className="md:col-span-3 space-y-4">
          {selected && problem ? (
            <>
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold">{String(problem.title)}</h2>
                <Timer running={running} />
              </div>

              <div className="flex gap-2">
                {[1, 2, 3].map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setTier(t)}
                    className={`rounded px-3 py-1 text-sm ${
                      tier === t ? 'bg-emerald-600' : 'bg-slate-700'
                    }`}
                  >
                    Tier {t}: {t === 1 ? 'Understand' : t === 2 ? 'Explain' : 'Solo'}
                  </button>
                ))}
              </div>

              <div className="card">
                <p>{String(problem.description)}</p>
                {tier === 1 && (problem.explain_checklist as string[])?.map((item, i) => (
                  <p key={i} className="mt-1 text-sm text-slate-400">- {item}</p>
                ))}
              </div>

              {tier === 2 && narrations.length > 0 && (
                <div className="card border-amber-700">
                  <p className="text-sm text-amber-400">Explain out loud:</p>
                  <p className="mt-1">{narrations[narrationIdx]}</p>
                  {narrationIdx < narrations.length - 1 && (
                    <button
                      type="button"
                      className="btn-secondary mt-2 text-sm"
                      onClick={() => setNarrationIdx((i) => i + 1)}
                    >
                      Next prompt
                    </button>
                  )}
                </div>
              )}

              <CodeEditor value={code} onChange={setCode} height="320px" />

              {result && (
                <div className={`rounded-lg p-3 text-sm ${result.passed ? 'bg-emerald-900/40' : 'bg-red-900/40'}`}>
                  {result.passed ? 'All tests passed!' : String(result.error || 'Failed')}
                  {(result.results as { case: number; passed: boolean }[])?.map((r) => (
                    <p key={r.case} className="text-xs">Case {r.case}: {r.passed ? 'OK' : 'FAIL'}</p>
                  ))}
                </div>
              )}

              <div className="flex gap-2">
                <button type="button" onClick={run} className="btn-secondary">Run Tests</button>
                <button type="button" onClick={submit} className="btn-primary">Submit</button>
              </div>
            </>
          ) : (
            <p className="text-slate-400">Select a problem</p>
          )}
        </div>
      </div>
    </div>
  );
}
