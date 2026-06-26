import { useEffect, useState } from 'react';
import { api, type ProblemDetail } from '../lib/api';
import { CodeEditor } from './CodeEditor';

interface LeetcodePanelProps {
  problemId: string;
  passed: boolean;
  onSubmit: (code: string) => Promise<{ passed: boolean; result: Record<string, unknown> }>;
}

export function LeetcodePanel({ problemId, passed, onSubmit }: LeetcodePanelProps) {
  const [problem, setProblem] = useState<ProblemDetail | null>(null);
  const [code, setCode] = useState('');
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(passed);

  useEffect(() => {
    setDone(passed);
    api.problem(problemId, 1).then((p) => {
      setProblem(p);
      setCode(p.starter_code || '');
      setResult(null);
    });
  }, [problemId, passed]);

  if (!problem) return <p className="text-text-muted">Cargando problema…</p>;

  const run = async () => {
    setBusy(true);
    try {
      const res = await api.run({ code, exercise_id: problemId, exercise_type: 'leetcode', tier: 1 });
      setResult(res);
    } finally {
      setBusy(false);
    }
  };

  const submit = async () => {
    setBusy(true);
    try {
      const res = await onSubmit(code);
      setResult(res.result);
      if (res.passed) setDone(true);
    } finally {
      setBusy(false);
    }
  };

  const cases = (result?.results as { case: number; passed: boolean }[]) || [];

  return (
    <div className="space-y-4">
      <div className="card">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-text">{problem.title}</h3>
          {done && <span className="badge-brand">Resuelto</span>}
        </div>
        <p className="mt-2 leading-relaxed text-text-muted">{problem.description}</p>
        {problem.explain_checklist?.length > 0 && (
          <ul className="mt-2 space-y-1 text-sm text-text-dim">
            {problem.explain_checklist.map((c, i) => <li key={i}>· {c}</li>)}
          </ul>
        )}
        {problem.test_cases_preview?.length > 0 && (
          <div className="mt-3 rounded-lg bg-surface-2 p-3 font-mono text-xs text-text-muted">
            {problem.test_cases_preview.map((tc, i) => (
              <p key={i}>{problem.fn_name}({JSON.stringify(tc.args).slice(1, -1)}) → {JSON.stringify(tc.expected)}</p>
            ))}
          </div>
        )}
      </div>

      <CodeEditor value={code} onChange={setCode} height="280px" drillId={problemId} />

      {result && (
        <div className={result.passed ? 'alert-success' : 'alert-error'}>
          {result.passed ? 'Todos los casos pasaron.' : String(result.error || 'Fallo')}
          {cases.map((r) => (
            <p key={r.case} className="mt-1 text-xs opacity-80">Caso {r.case}: {r.passed ? 'OK' : 'FALLO'}</p>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <button type="button" onClick={run} disabled={busy} className="btn-secondary">Probar</button>
        <button type="button" onClick={submit} disabled={busy} className="btn-primary">Enviar</button>
      </div>
    </div>
  );
}
