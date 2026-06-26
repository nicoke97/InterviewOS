import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, CartesianGrid,
} from 'recharts';
import { useCurriculumLevels } from '../lib/levels';
import { api, type DailyPlanData, type OrientadorActiveResponse, type OrientadorConfig } from '../lib/api';
import { assignmentLabel, REASON_LABEL, reasonBadgeClass } from '../lib/orientadorLabels';
import { StudyCalendar } from '../components/StudyCalendar';

const chartTooltip = {
  background: '#1f2937',
  border: '1px solid #374151',
  borderRadius: '8px',
  fontSize: '12px',
  color: '#f3f4f6',
};

interface LevelProgress {
  leetcode_unlocked: boolean;
  interview_unlocked: boolean;
  sets_mastered: number;
  total_sets: number;
  pages_completed: number;
  total_pages: number;
  progress_pct: number;
}

function formatDate(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString('es-ES', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });
}

function applyOrientadorResponse(
  o: OrientadorActiveResponse,
  setConfig: (c: OrientadorConfig | null) => void,
  setSessions: (s: DailyPlanData[]) => void,
  setPlan: (p: DailyPlanData | null) => void,
  setPlanActive: (v: boolean) => void,
  setMinutes: (n: number) => void,
  setSelectedPlanId: (id: number | null) => void,
  preferPlanId?: number | null,
) {
  setConfig(o.config ?? null);
  const list = o.sessions ?? [];
  setSessions(list);

  const pickId = preferPlanId ?? o.active_plan_id ?? (list.length ? list[list.length - 1].id : null);
  const picked = list.find((s) => s.id === pickId)
    ?? (o.id ? {
      id: o.id,
      date: o.date!,
      track: o.track ?? 'python',
      session_number: o.session_number ?? 1,
      status: o.status ?? 'active',
      minutes_budget: o.minutes_budget!,
      assignments: o.assignments ?? [],
      completed_count: o.completed_count ?? 0,
      total_count: o.total_count ?? 0,
      estimated_minutes: o.estimated_minutes ?? 0,
      calculated_at: o.calculated_at ?? null,
      config: o.config!,
    } as DailyPlanData : null);

  if (picked) {
    setPlan(picked);
    setPlanActive(true);
    setSelectedPlanId(picked.id);
    setMinutes(picked.minutes_budget);
  } else {
    setPlan(null);
    setPlanActive(false);
    setSelectedPlanId(null);
  }
}

export function Dashboard() {
  const location = useLocation();
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);
  const [plan, setPlan] = useState<DailyPlanData | null>(null);
  const [sessions, setSessions] = useState<DailyPlanData[]>([]);
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
  const [planActive, setPlanActive] = useState(false);
  const [config, setConfig] = useState<OrientadorConfig | null>(null);
  const [minutes, setMinutes] = useState(30);
  const [calculating, setCalculating] = useState(false);
  const [orientadorReady, setOrientadorReady] = useState(false);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState(false);
  const [calcError, setCalcError] = useState('');
  const levels = useCurriculumLevels();

  const load = useCallback(() => {
    setOrientadorReady(false);
    setStatsLoading(true);
    setStatsError(false);

    api.orientadorActive()
      .then((o) => {
        applyOrientadorResponse(
          o, setConfig, setSessions, setPlan, setPlanActive, setMinutes, setSelectedPlanId,
        );
        setOrientadorReady(true);
      })
      .catch(() => setOrientadorReady(true));

    api.stats()
      .then(setStats)
      .catch(() => setStatsError(true))
      .finally(() => setStatsLoading(false));
  }, []);

  useEffect(() => {
    if (location.pathname === '/') load();
  }, [load, location.pathname]);

  useEffect(() => {
    const refresh = () => {
      if (document.visibilityState === 'visible' && location.pathname === '/') load();
    };
    document.addEventListener('visibilitychange', refresh);
    return () => document.removeEventListener('visibilitychange', refresh);
  }, [load, location.pathname]);

  const selectSession = (session: DailyPlanData) => {
    setSelectedPlanId(session.id);
    setPlan(session);
    setMinutes(session.minutes_budget);
  };

  const calculate = async (opts?: { newSession?: boolean }) => {
    setCalculating(true);
    setCalcError('');
    const viewing = sessions.find((s) => s.id === selectedPlanId) ?? plan;
    const isActive = viewing?.status === 'active';
    const allDone = sessions.length > 0 && sessions.every((s) => s.status === 'completed');
    try {
      const p = await api.orientadorCalculate(Number(minutes), {
        planId: isActive && !opts?.newSession ? viewing?.id : undefined,
        newSession: opts?.newSession ?? allDone,
      });
      setSessions((prev) => {
        const idx = prev.findIndex((s) => s.id === p.id);
        if (idx >= 0) {
          const next = [...prev];
          next[idx] = p;
          return next;
        }
        return [...prev, p].sort((a, b) => a.session_number - b.session_number);
      });
      setPlan(p);
      setPlanActive(true);
      setSelectedPlanId(p.id);
      setMinutes(p.minutes_budget);
      setConfig(p.config);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'No se pudo calcular la sesion';
      setCalcError(msg);
    } finally {
      setCalculating(false);
    }
  };

  const streak = stats?.streak as { current: number; best: number } | undefined;
  const minutesChart = (stats?.minutes_chart as { date: string; minutes: number }[]) || [];
  const blockAccuracyRaw = (stats?.block_accuracy as { block: string; block_title?: string; accuracy: number; mastered?: number; total?: number }[]) || [];
  const blockAccuracy = useMemo(() => {
    const active = blockAccuracyRaw.filter((b) => (b.mastered ?? 0) > 0);
    return active.length ? active : blockAccuracyRaw.slice(0, 8);
  }, [blockAccuracyRaw]);
  const todayPages = (stats?.today_activity as { pages_passed_today?: number } | undefined)?.pages_passed_today ?? 0;
  const unlocks = (stats?.unlocks as Record<string, LevelProgress>) || {};
  const presets = config?.minute_presets ?? [20, 30, 40, 60];

  if (!orientadorReady) {
    return <p className="text-text-muted">Cargando sesion…</p>;
  }

  const sessionDate = plan?.date ?? new Date().toISOString().slice(0, 10);

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Tu progreso de entrenamiento</p>
        </div>
      <div className="flex flex-wrap items-center gap-2">
          <span className="badge-brand">{streak?.current ?? 0} dias seguidos</span>
          <span className="badge-muted">Mejor: {streak?.best ?? 0}</span>
          <span className="badge-muted">{String(stats?.day_number ?? 0)} dias activos</span>
          {statsLoading && <span className="badge-muted">Actualizando stats…</span>}
        </div>
      </div>

      <OrientadorCard
        date={sessionDate}
        minutes={minutes}
        setMinutes={setMinutes}
        presets={presets}
        minMinutes={config?.min_minutes ?? 15}
        maxMinutes={config?.max_minutes ?? 90}
        sessions={sessions}
        selectedPlanId={selectedPlanId}
        onSelectSession={selectSession}
        plan={planActive ? plan : null}
        calculating={calculating}
        calcError={calcError}
        onCalculate={calculate}
      />

      {statsError && (
        <div className="card flex flex-wrap items-center justify-between gap-3 border-amber-500/30">
          <p className="text-sm text-text-muted">No se pudieron cargar las estadisticas.</p>
          <button type="button" onClick={load} className="btn-secondary text-sm">Reintentar</button>
        </div>
      )}

      <StudyCalendar />

      <div>
        <h2 className="mb-3 font-medium text-text">Niveles</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {levels.map((lvl) => {
            const u = unlocks[lvl.id];
            const mastered = u?.sets_mastered ?? 0;
            const totalSets = u?.total_sets ?? 20;
            const pagesDone = u?.pages_completed ?? 0;
            const totalPages = u?.total_pages ?? 200;
            const pct = u?.progress_pct ?? (totalPages ? Math.round((pagesDone / totalPages) * 100) : 0);
            return (
              <Link key={lvl.id} to={`/${lvl.id}/roadmap`} className="card transition hover:border-brand/40">
                <p className="text-sm font-semibold text-text">{lvl.title}</p>
                <div className="mt-3 mb-1.5 flex justify-between text-xs text-text-muted">
                  <span>{pagesDone}/{totalPages} paginas · {mastered}/{totalSets} sets</span>
                  <span className="font-medium text-text">{pct}%</span>
                </div>
                <div className="progress-bar"><div className="progress-fill" style={{ width: `${pct}%` }} /></div>
              </Link>
            );
          })}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Tasa de aciertos" value={statsLoading && !stats ? '…' : `${String(stats?.pass_rate ?? 0)}%`} highlight />
        <StatCard label="Intentos totales" value={statsLoading && !stats ? '…' : String(stats?.total_attempts ?? 0)} />
        <StatCard label="Paginas hoy" value={statsLoading && !stats ? '…' : String(todayPages)} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h2 className="font-medium text-text">Minutos de estudio</h2>
          <p className="mb-4 text-xs text-text-dim">Ultimos 30 dias</p>
          {statsLoading && !stats ? (
            <p className="py-16 text-center text-sm text-text-muted">Cargando grafico…</p>
          ) : (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={minutesChart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#6b7280' }} axisLine={false} tickLine={false} />
              <YAxis stroke="#6b7280" axisLine={false} tickLine={false} tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={chartTooltip} />
              <Line type="monotone" dataKey="minutes" stroke="#26d0a4" strokeWidth={2} dot={false}
                activeDot={{ r: 4, fill: '#26d0a4', stroke: '#111827', strokeWidth: 2 }} />
            </LineChart>
          </ResponsiveContainer>
          )}
        </div>
        <div className="card">
          <h2 className="font-medium text-text">Dominio por bloque</h2>
          <p className="mb-4 text-xs text-text-dim">Paginas completadas por bloque (sets en curso incluidos)</p>
          {statsLoading && !stats ? (
            <p className="py-16 text-center text-sm text-text-muted">Cargando grafico…</p>
          ) : (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={blockAccuracy}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
              <XAxis dataKey="block_title" tick={{ fontSize: 9, fill: '#6b7280' }} axisLine={false} tickLine={false} />
              <YAxis stroke="#6b7280" domain={[0, 100]} axisLine={false} tickLine={false} tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={chartTooltip} />
              <Bar dataKey="accuracy" fill="#26d0a4" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}

function OrientadorCard({
  date,
  minutes,
  setMinutes,
  presets,
  minMinutes,
  maxMinutes,
  sessions,
  selectedPlanId,
  onSelectSession,
  plan,
  calculating,
  calcError,
  onCalculate,
}: {
  date: string;
  minutes: number;
  setMinutes: (n: number) => void;
  presets: number[];
  minMinutes: number;
  maxMinutes: number;
  sessions: DailyPlanData[];
  selectedPlanId: number | null;
  onSelectSession: (s: DailyPlanData) => void;
  plan: DailyPlanData | null;
  calculating: boolean;
  calcError: string;
  onCalculate: (opts?: { newSession?: boolean }) => void;
}) {
  const nextPending = plan?.assignments.find((a) => !a.completed);
  const allDone = plan && plan.total_count > 0 && plan.completed_count >= plan.total_count;
  const planStale = plan != null && plan.status === 'active' && Number(minutes) !== Number(plan.minutes_budget);
  const hasActiveSession = sessions.some((s) => s.status === 'active');
  const allSessionsDone = sessions.length > 0 && sessions.every((s) => s.status === 'completed');
  const isViewingActive = plan?.status === 'active';
  const overBudget = plan != null && plan.estimated_minutes > plan.minutes_budget;
  const showFirstCalc = sessions.length === 0;
  const showRecalc = isViewingActive && planStale;
  const showAdd = allSessionsDone && !hasActiveSession;

  return (
    <div className="card space-y-4 border-brand/30">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-text">Sesion de {formatDate(date)}</h2>
          <p className="text-sm text-text-muted">
            Elige cuantos minutos tienes. Calculamos repeticiones, repaso y nuevos sets que quepan en ese tiempo.
          </p>
        </div>
        {plan && plan.total_count > 0 && (
          <span className="badge-brand">
            {plan.completed_count}/{plan.total_count}
          </span>
        )}
      </div>

      {sessions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {sessions.map((s) => {
            const selected = s.id === selectedPlanId;
            const done = s.status === 'completed';
            return (
              <button
                key={s.id}
                type="button"
                onClick={() => onSelectSession(s)}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                  selected
                    ? 'bg-brand text-bg'
                    : 'bg-surface-2 text-text-muted hover:text-text'
                }`}
              >
                Sesion {s.session_number}
                {done ? ' · completada' : ` · ${s.completed_count}/${s.total_count}`}
                {' · '}
                {s.minutes_budget} min
              </button>
            );
          })}
        </div>
      )}

      {(isViewingActive || allSessionsDone || sessions.length === 0) && (
      <div className="space-y-3">
        <p className="text-sm font-medium text-text">Tiempo disponible</p>
        <div className="flex flex-wrap items-center gap-2">
          {presets.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setMinutes(p)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                minutes === p ? 'bg-brand text-bg' : 'bg-surface-2 text-text-muted hover:text-text'
              }`}
            >
              {p} min
            </button>
          ))}
          <label className="flex items-center gap-2 text-sm text-text-muted">
            <span>Otro:</span>
            <input
              type="number"
              min={minMinutes}
              max={maxMinutes}
              value={minutes}
              onChange={(e) => setMinutes(Number(e.target.value))}
              className="w-20 rounded-lg border border-border bg-surface-2 px-2 py-1 text-text"
            />
            <span>min</span>
          </label>
        </div>
        <div className="flex flex-wrap gap-2">
          {(showFirstCalc || showRecalc) && (
            <button
              type="button"
              onClick={() => onCalculate()}
              disabled={calculating}
              className="btn-primary"
            >
              {calculating ? 'Calculando…' : showFirstCalc ? 'Calcular sesion' : 'Recalcular sesion'}
            </button>
          )}
          {showAdd && (
            <button
              type="button"
              onClick={() => onCalculate({ newSession: true })}
              disabled={calculating}
              className="btn-primary"
            >
              {calculating ? 'Calculando…' : 'Anadir sesion'}
            </button>
          )}
        </div>
        {calcError && (
          <p className="text-sm text-red-400">
            {calcError}. ¿Está corriendo <code className="text-brand">npm run dev</code>?
          </p>
        )}
        {planStale && isViewingActive && (
          <p className="text-xs text-amber-400">
            {minutes > (plan?.minutes_budget ?? 0)
              ? 'Mas tiempo: se anadiran actividades que quepan en la diferencia.'
              : overBudget
                ? 'Menos tiempo, pero el plan ya supera ese presupuesto — se mantiene igual.'
                : 'Menos tiempo: se recalcula el plan conservando lo ya hecho.'}
          </p>
        )}
      </div>
      )}

      {plan && plan.assignments.length === 0 && (
        <p className="text-sm text-text-muted">
          Con {plan.minutes_budget} min no entra ninguna actividad. Prueba con mas tiempo.
        </p>
      )}

      {plan && plan.assignments.length > 0 && (
        <div className="space-y-3 border-t border-border pt-4">
          <p className="text-sm text-text-muted">
            Sesion {plan.session_number}
            {' · '}
            Plan para <span className="font-medium text-text">{plan.minutes_budget} min</span>
            {' · '}
            <span className="font-medium text-text">~{plan.estimated_minutes} min</span> en actividades
            {plan.status === 'completed' && (
              <span className="ml-2 text-emerald-400">· Completada</span>
            )}
          </p>

          {planStale && isViewingActive && (
            <p className="text-xs text-amber-400">
              Plan calculado para {plan.minutes_budget} min — recalcula si quieres otro presupuesto.
            </p>
          )}

          {allDone ? (
            <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300">
              Sesion completada.
              {!hasActiveSession && sessions.length > 0 && (
                <span> Puedes anadir otra sesion con el boton de arriba.</span>
              )}
            </div>
          ) : nextPending && isViewingActive ? (
            <div className="rounded-xl border border-brand/40 bg-brand/5 px-4 py-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-brand">Siguiente</p>
              <p className="mt-1 text-lg font-semibold text-text">{assignmentLabel(nextPending)}</p>
              <p className="mt-1 text-sm text-text-muted">
                {REASON_LABEL[nextPending.reason] ?? nextPending.reason}
                {nextPending.estimated_minutes ? ` · ~${Math.round(nextPending.estimated_minutes)} min` : ''}
              </p>
              <Link
                to={`/orientador/${plan.id}/${nextPending.index ?? plan.assignments.indexOf(nextPending)}`}
                className="btn-primary mt-4 inline-block w-full text-center sm:w-auto"
              >
                Empezar
              </Link>
            </div>
          ) : null}

          {plan.assignments.length > 1 && (
            <ul className="space-y-2">
              {plan.assignments.map((a, i) => (
                <li
                  key={i}
                  className={`flex items-center justify-between gap-2 text-sm ${
                    a.completed ? 'text-text-dim line-through' : 'text-text-muted'
                  }`}
                >
                  <span>
                    <span className={`text-xs font-medium ${reasonBadgeClass(a.reason)}`}>
                      {REASON_LABEL[a.reason] ?? a.reason}
                    </span>
                    {' · '}
                    {assignmentLabel(a)}
                  </span>
                  <span className="shrink-0 text-xs">
                    {a.completed ? 'Hecho' : `~${Math.round(a.estimated_minutes ?? 0)} min`}
                  </span>
                </li>
              ))}
            </ul>
          )}
          <Link to="/orientador" className="text-sm text-brand hover:underline">
            Ver por que se eligio cada actividad
          </Link>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="card">
      <p className="stat-label">{label}</p>
      <p className={`stat-value ${highlight ? 'text-brand' : ''}`}>{value}</p>
    </div>
  );
}
