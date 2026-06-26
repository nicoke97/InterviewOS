import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api';
import { assignmentLabel, REASON_LABEL, reasonBadgeClass } from '../lib/orientadorLabels';

interface SetHistoryRow {
  level: string;
  set_number: number;
  title: string;
  status: string;
  attempts: number;
  solid_mastery: boolean;
  first_attempt_accuracy: number | null;
  failure_flags: string[];
  repeat_scheduled_for: string | null;
  repeat_completed_at: string | null;
}

interface PriorityRule {
  order: number;
  id: string;
  label: string;
  description: string;
}

interface ExplainedAssignment {
  type: string;
  level: string;
  set_number?: number;
  reason: string;
  estimated_minutes?: number;
  index?: number;
  completed?: boolean;
  lap?: number;
  explain: {
    title: string;
    reason: string;
    summary: string;
    set_progress: SetHistoryRow | null;
  };
}

interface InsightData {
  date: string;
  active_level: string;
  priority_rules: PriorityRule[];
  set_history: SetHistoryRow[];
  plan: {
    id: number;
    minutes_budget: number;
    estimated_minutes: number;
    assignments: ExplainedAssignment[];
    completed_count: number;
    total_count: number;
  } | null;
}

export function OrientadorPage() {
  const [data, setData] = useState<InsightData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    api.orientadorInsight()
      .then((d) => setData(d as unknown as InsightData))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading && !data) {
    return <p className="text-text-muted">Cargando orientador…</p>;
  }

  if (error || !data) {
    return (
      <div className="card space-y-3 text-center">
        <h2 className="page-title">No se pudo cargar el orientador</h2>
        <button type="button" onClick={load} className="btn-secondary">Reintentar</button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="page-title">Orientador</h1>
        <p className="page-subtitle">
          Entiende por que tu sesion incluye sets nuevos, repeticiones o repasos de sets anteriores.
        </p>
      </div>

      <section className="card space-y-4">
        <h2 className="text-lg font-semibold text-text">Como se arma tu sesion</h2>
        <p className="text-sm text-text-muted">
          Al pulsar <strong className="text-text">Calcular sesion</strong> en el dashboard, el orientador
          ordena las actividades por prioridad y mete tantas como quepan en los minutos que indicaste.
        </p>
        <ol className="space-y-3">
          {data.priority_rules.map((rule) => (
            <li key={rule.id} className="flex gap-3 text-sm">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand/15 text-xs font-bold text-brand">
                {rule.order}
              </span>
              <div>
                <p className="font-medium text-text">{rule.label}</p>
                <p className="text-text-muted">{rule.description}</p>
              </div>
            </li>
          ))}
        </ol>
        <Link to="/" className="btn-secondary inline-block text-sm">
          Ir al dashboard para calcular sesion
        </Link>
      </section>

      {data.set_history.length > 0 && (
        <section className="card space-y-4">
          <h2 className="text-lg font-semibold text-text">
            Historial de sets · Nivel {data.active_level.toUpperCase()}
          </h2>
          <p className="text-sm text-text-muted">
            Aqui ves si fallaste en tiempo, en precision, o si hay una repeticion programada.
          </p>
          <div className="space-y-2">
            {data.set_history.map((row) => (
              <SetHistoryCard key={row.set_number} row={row} today={data.date} />
            ))}
          </div>
        </section>
      )}

      {data.plan ? (
        <section className="card space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-lg font-semibold text-text">Plan de hoy explicado</h2>
            <span className="badge-brand">
              {data.plan.completed_count}/{data.plan.total_count} hechas · {data.plan.minutes_budget} min
            </span>
          </div>
          <p className="text-sm text-text-muted">
            ~{data.plan.estimated_minutes} min en actividades de {data.plan.minutes_budget} min pedidos.
          </p>
          <div className="space-y-3">
            {data.plan.assignments.map((a, i) => (
              <ExplainedAssignmentCard key={i} assignment={a} planId={data.plan!.id} />
            ))}
          </div>
        </section>
      ) : (
        <section className="card text-sm text-text-muted">
          Aun no calculaste la sesion de hoy. Ve al{' '}
          <Link to="/" className="text-brand hover:underline">dashboard</Link>, elige tus minutos y pulsa
          Calcular sesion. Luego vuelve aqui para ver el desglose.
        </section>
      )}
    </div>
  );
}

function SetHistoryCard({ row, today }: { row: SetHistoryRow; today: string }) {
  const acc = row.first_attempt_accuracy != null
    ? `${Math.round(row.first_attempt_accuracy * 100)}%`
    : null;

  return (
    <div className="rounded-lg border border-border bg-surface-2 px-4 py-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-sm font-medium text-text">
            Set {row.set_number} · {row.title}
          </p>
          <p className="text-xs text-text-dim">
            Estado: {row.status}
            {row.attempts > 0 ? ` · ${row.attempts} intento(s)` : ''}
            {acc ? ` · 1.er intento ${acc}` : ''}
          </p>
        </div>
        {row.solid_mastery ? (
          <span className="badge-brand text-xs">Dominio solido</span>
        ) : row.status === 'mastered' ? (
          <span className="badge-muted text-xs">Dominado · repaso recomendado</span>
        ) : null}
      </div>
      {(row.failure_flags.length > 0 || row.repeat_scheduled_for) && (
        <ul className="mt-2 space-y-1 text-xs text-amber-400">
          {row.failure_flags.includes('too_slow') && (
            <li>Superaste el tiempo estandar en el primer intento completo.</li>
          )}
          {row.failure_flags.includes('low_accuracy') && (
            <li>Precision del primer intento por debajo del umbral ({acc ?? '?'}).</li>
          )}
          {row.repeat_scheduled_for && (
            <li>
              Repeticion programada: {row.repeat_scheduled_for}
              {row.repeat_completed_at === today ? ' (completada hoy)' : ''}
            </li>
          )}
        </ul>
      )}
    </div>
  );
}

function ExplainedAssignmentCard({ assignment, planId }: { assignment: ExplainedAssignment; planId: number }) {
  const ex = assignment.explain;
  const reason = assignment.reason;
  const idx = assignment.index ?? 0;

  return (
    <div className={`rounded-xl border px-4 py-4 ${
      assignment.completed ? 'border-emerald-500/30 bg-emerald-500/5 opacity-80' : 'border-border bg-surface-2'
    }`}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className={`text-xs font-semibold uppercase tracking-wide ${reasonBadgeClass(reason)}`}>
            {REASON_LABEL[reason] ?? reason}
            {assignment.lap ? ` · vuelta ${assignment.lap}` : ''}
          </p>
          <p className="mt-1 text-base font-semibold text-text">{ex.title || assignmentLabel(assignment)}</p>
        </div>
        <span className="text-xs text-text-dim">
          {assignment.completed ? 'Hecho' : `~${Math.round(assignment.estimated_minutes ?? 0)} min`}
        </span>
      </div>
      <p className="mt-2 text-sm text-text-muted">{ex.summary}</p>
      {!assignment.completed && assignment.type === 'set' && (
        <Link
          to={`/orientador/${planId}/${idx}`}
          className="btn-primary mt-3 inline-block text-sm"
        >
          Empezar esta actividad
        </Link>
      )}
    </div>
  );
}
