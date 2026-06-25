import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api, type SheetData } from '../lib/api';
import { CodeEditor } from '../components/CodeEditor';
import { Timer, useSessionTimer } from '../components/Timer';

export function Kumon() {
  const [params] = useSearchParams();
  const slot = params.get('slot') || 'morning';
  const [sheet, setSheet] = useState<SheetData | null>(null);
  const [index, setIndex] = useState(0);
  const [code, setCode] = useState('');
  const [hintsShown, setHintsShown] = useState(0);
  const [failedOnce, setFailedOnce] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [focusMode, setFocusMode] = useState(false);
  const [startTime] = useState(Date.now());
  const { running, start, stop, onTick } = useSessionTimer(slot);

  const drill = sheet?.drills[index];

  const loadSheet = useCallback(async () => {
    const data = await api.sheetToday(slot) as unknown as SheetData;
    setSheet(data);
    const firstIncomplete = data.drills.findIndex((d) => !d.completed);
    const idx = firstIncomplete >= 0 ? firstIncomplete : 0;
    setIndex(idx);
    setCode(data.drills[idx]?.starter_code || '');
    setHintsShown(0);
    setFailedOnce(false);
    setResult(null);
    start();
  }, [slot, start]);

  useEffect(() => {
    api.settings().then((s) => setFocusMode(s.focus_mode));
    loadSheet();
    return () => { stop(); };
  }, [loadSheet, stop]);

  const maxHints = drill?.scaffolding === 'full' ? 3 : drill?.scaffolding === 'minimal' && failedOnce ? 1 : 0;

  const showHint = () => {
    if (hintsShown < maxHints && drill?.hints?.[hintsShown]) {
      setHintsShown((h) => h + 1);
    }
  };

  const runCode = async () => {
    if (!drill) return;
    const res = await api.run({
      code,
      exercise_id: drill.id,
      exercise_type: 'kumon',
    });
    setResult(res);
  };

  const submit = async () => {
    if (!drill) return;
    const time_ms = Date.now() - startTime;
    const res = await api.submit({
      code,
      exercise_id: drill.id,
      exercise_type: 'kumon',
      hints_used: hintsShown,
      time_ms,
    }) as { passed: boolean; result: Record<string, unknown> };
    setResult(res.result);

    if (res.passed) {
      if (sheet && index < sheet.drills.length - 1) {
        const next = index + 1;
        setIndex(next);
        setCode(sheet.drills[next].starter_code || '');
        setHintsShown(0);
        setFailedOnce(false);
        setResult(null);
      } else {
        stop();
        await loadSheet();
      }
    } else {
      setFailedOnce(true);
    }
  };

  if (!sheet || !drill) {
    return <p className="text-slate-400">Loading sheet...</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Kumon Sheet</h1>
          <p className="text-sm text-slate-400">
            {slot} · {sheet.rule} · Drill {index + 1}/{sheet.drills.length} · {drill.block} #{drill.order}
          </p>
        </div>
        <Timer running={running} onTick={onTick} />
      </div>

      <div className="card">
        <p className="mb-2 text-xs uppercase tracking-wide text-emerald-400">
          Scaffolding: {drill.scaffolding}
        </p>
        <p className="text-lg">{drill.prompt}</p>
        {drill.csharp_note && (
          <details className="mt-2 text-sm text-slate-400">
            <summary className="cursor-pointer text-amber-400">From C#</summary>
            <p className="mt-1 font-mono">{drill.csharp_note}</p>
          </details>
        )}
      </div>

      <CodeEditor value={code} onChange={setCode} />

      {!focusMode && maxHints > 0 && hintsShown < maxHints && (
        <div className="space-y-2">
          {drill.hints.slice(0, hintsShown).map((h, i) => (
            <p key={i} className="rounded bg-amber-900/30 px-3 py-2 text-sm text-amber-200">
              Hint {i + 1}: {h}
            </p>
          ))}
          <button type="button" onClick={showHint} className="btn-secondary text-sm">
            Show hint ({hintsShown}/{maxHints})
          </button>
        </div>
      )}

      {result && (
        <div className={`rounded-lg p-3 text-sm ${result.passed ? 'bg-emerald-900/40 text-emerald-200' : 'bg-red-900/40 text-red-200'}`}>
          {result.passed ? 'Correct!' : String(result.error || 'Incorrect')}
          {result.stdout != null && (
            <pre className="mt-1 font-mono text-xs">stdout: {String(result.stdout)}</pre>
          )}
        </div>
      )}

      <div className="flex gap-2">
        <button type="button" onClick={runCode} className="btn-secondary">Run</button>
        <button type="button" onClick={submit} className="btn-primary">Submit</button>
      </div>

      <div className="flex flex-wrap gap-1">
        {sheet.drills.map((d, i) => (
          <button
            key={d.id}
            type="button"
            onClick={() => { setIndex(i); setCode(d.starter_code || ''); setResult(null); }}
            className={`h-8 w-8 rounded text-xs ${
              d.completed ? 'bg-emerald-600' : i === index ? 'bg-slate-500' : 'bg-slate-700'
            }`}
          >
            {i + 1}
          </button>
        ))}
      </div>
    </div>
  );
}
