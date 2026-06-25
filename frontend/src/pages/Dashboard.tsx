import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, CartesianGrid,
} from 'recharts';
import { api } from '../lib/api';

export function Dashboard() {
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);
  const [morning, setMorning] = useState<Record<string, unknown> | null>(null);
  const [evening, setEvening] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    Promise.all([
      api.stats(),
      api.sheetToday('morning'),
      api.sheetToday('evening'),
    ]).then(([s, m, e]) => {
      setStats(s);
      setMorning(m);
      setEvening(e);
    }).catch(console.error);
  }, []);

  const streak = stats?.streak as { current: number; best: number } | undefined;
  const minutesChart = (stats?.minutes_chart as { date: string; minutes: number }[]) || [];
  const blockAccuracy = (stats?.block_accuracy as { block: string; accuracy: number }[]) || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="flex gap-4 text-sm">
          <span className="rounded-full bg-emerald-600/20 px-3 py-1 text-emerald-400">
            Streak: {streak?.current ?? 0} days
          </span>
          <span className="text-slate-400">Best: {streak?.best ?? 0}</span>
          <span className="text-slate-400">Day #{String(stats?.day_number ?? 1)}</span>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <SheetCard title="Morning Sheet" data={morning} slot="morning" />
        <SheetCard title="Evening Sheet" data={evening} slot="evening" />
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="card">
          <p className="text-sm text-slate-400">Pass Rate</p>
          <p className="text-3xl font-bold text-emerald-400">{String(stats?.pass_rate ?? 0)}%</p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-400">Total Attempts</p>
          <p className="text-3xl font-bold">{String(stats?.total_attempts ?? 0)}</p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-400">Active Block</p>
          <p className="text-lg font-semibold">{String(morning?.active_block ?? 'a1-variables')}</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="card">
          <h2 className="mb-4 font-semibold">Study Minutes (30 days)</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={minutesChart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #475569' }} />
              <Line type="monotone" dataKey="minutes" stroke="#22c55e" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h2 className="mb-4 font-semibold">Block Accuracy</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={blockAccuracy}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="block" tick={{ fontSize: 9 }} stroke="#64748b" />
              <YAxis stroke="#64748b" domain={[0, 100]} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #475569' }} />
              <Bar dataKey="accuracy" fill="#22c55e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <UnlockStatus unlocks={stats?.unlocks as Record<string, unknown>} />
    </div>
  );
}

function SheetCard({ title, data, slot }: { title: string; data: Record<string, unknown> | null; slot: string }) {
  const drills = (data?.drills as { id: string; completed?: boolean }[]) || [];
  const done = drills.filter((d) => d.completed).length;
  return (
    <div className="card">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="font-semibold">{title}</h2>
        <span className="rounded bg-slate-700 px-2 py-0.5 text-xs text-amber-400">
          {String(data?.rule ?? 'intro')}
        </span>
      </div>
      <p className="mb-3 text-sm text-slate-400">
        {done}/{drills.length} drills · {drills.length} assigned
      </p>
      <Link to={`/kumon?slot=${slot}`} className="btn-primary inline-block text-sm">
        Start {slot} session
      </Link>
    </div>
  );
}

function UnlockStatus({ unlocks }: { unlocks?: Record<string, unknown> }) {
  if (!unlocks) return null;
  return (
    <div className="card">
      <h2 className="mb-3 font-semibold">Level Progress</h2>
      <div className="grid gap-3 md:grid-cols-3">
        {['a', 'b', 'c'].map((level) => {
          const u = unlocks[level] as Record<string, unknown>;
          return (
            <div key={level} className="rounded-lg border border-slate-600 p-3">
              <p className="mb-2 font-medium uppercase text-emerald-400">Level {level.toUpperCase()}</p>
              <p className="text-xs text-slate-400">
                LeetCode: {u?.leetcode_unlocked ? 'Unlocked' : 'Locked'}
              </p>
              <p className="text-xs text-slate-400">
                Interview: {u?.interview_unlocked ? 'Unlocked' : 'Locked'}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
