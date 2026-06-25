import { useEffect, useState } from 'react';
import { api } from '../lib/api';

export function Settings() {
  const [focusMode, setFocusMode] = useState(false);
  const [exportData, setExportData] = useState<string>('');

  useEffect(() => {
    api.settings().then((s) => setFocusMode(s.focus_mode));
  }, []);

  const toggleFocus = async () => {
    const next = !focusMode;
    await api.updateSettings({ focus_mode: next });
    setFocusMode(next);
  };

  const doExport = async () => {
    const data = await api.exportProgress();
    setExportData(JSON.stringify(data, null, 2));
  };

  const startMock = async (level: string) => {
    try {
      const m = await api.mockStart(level);
      alert(`Mock started: ${m.title} — ${m.time_limit_minutes} min, Tier 3, no hints`);
    } catch (e) {
      alert(String(e));
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      <div className="card flex items-center justify-between">
        <div>
          <p className="font-medium">Focus Mode</p>
          <p className="text-sm text-slate-400">Hide hints until first failed submit (Kumon drills 4-10)</p>
        </div>
        <button
          type="button"
          onClick={toggleFocus}
          className={`rounded-full px-4 py-2 text-sm ${focusMode ? 'bg-emerald-600' : 'bg-slate-600'}`}
        >
          {focusMode ? 'On' : 'Off'}
        </button>
      </div>

      <div className="card space-y-3">
        <p className="font-medium">Mock Interview Mode</p>
        <p className="text-sm text-slate-400">Timed Tier 3 problem, no hints (unlocked per level)</p>
        <div className="flex gap-2">
          {['a', 'b', 'c'].map((l) => (
            <button key={l} type="button" onClick={() => startMock(l)} className="btn-secondary text-sm">
              Level {l.toUpperCase()} Mock
            </button>
          ))}
        </div>
      </div>

      <div className="card space-y-3">
        <p className="font-medium">Export Progress</p>
        <button type="button" onClick={doExport} className="btn-secondary">Download JSON</button>
        {exportData && (
          <pre className="max-h-60 overflow-auto rounded bg-slate-900 p-3 text-xs">{exportData}</pre>
        )}
      </div>

      <div className="card space-y-3">
        <p className="font-medium">Study Day</p>
        <button
          type="button"
          onClick={() => api.advanceDay().then((r) => alert(`Advanced to day ${r.day_number}, block ${r.active_block}`))}
          className="btn-secondary text-sm"
        >
          Advance study day (dev)
        </button>
      </div>
    </div>
  );
}
