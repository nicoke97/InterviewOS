import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, type OrientadorAssignment } from '../lib/api';
import { assignmentLabel, orientadorAssignmentPath, reasonBadgeClass, reasonLabel } from '../lib/orientadorLabels';
import { resolveDisplaySetNumber } from '../lib/setLabels';
import { useI18n } from '../i18n/context';
import { readOrientadorTrack, writeOrientadorTrack, type OrientadorTrack } from '../lib/studySession';

interface SetHistoryRow {
  level: string;
  set_number: number;
  display_set_number?: number;
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
  type: 'set' | 'checkpoint' | 'exam' | 'leetcode_practice';
  level: string;
  set_number?: number;
  display_set_number?: number;
  block?: string;
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
  const { t, locale } = useI18n();
  const [track, setTrack] = useState<OrientadorTrack>(readOrientadorTrack);
  const [data, setData] = useState<InsightData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(() => {
    void locale;
    setLoading(true);
    setError(false);
    api.orientadorInsight(track)
      .then((d) => setData(d as unknown as InsightData))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [track, locale]);

  useEffect(() => { load(); }, [load]);

  if (loading && !data) {
    return <p className="text-text-muted">{t('orientador.loading')}</p>;
  }

  if (error || !data) {
    return (
      <div className="card space-y-3 text-center">
        <h2 className="page-title">{t('orientador.errorTitle')}</h2>
        <button type="button" onClick={load} className="btn-secondary">{t('common.retry')}</button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="page-title">{t('common.orientador')}</h1>
          <p className="page-subtitle">
            {track === 'leetcodes' ? t('orientador.subtitleLeetcodes') : t('orientador.subtitlePython')}
          </p>
        </div>
        <div className="flex gap-1 rounded-xl bg-surface-2 p-1">
          {(['leetcodes', 'python'] as const).map((trackKey) => (
            <button
              key={trackKey}
              type="button"
              onClick={() => {
                writeOrientadorTrack(trackKey);
                setTrack(trackKey);
              }}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
                track === trackKey ? 'bg-brand text-on-brand' : 'text-text-muted hover:text-text'
              }`}
            >
              {trackKey === 'python' ? t('common.python') : t('common.leetcodes')}
            </button>
          ))}
        </div>
      </div>

      <section className="card space-y-4">
        <h2 className="text-lg font-semibold text-text">{t('orientador.howTitle')}</h2>
        <p className="text-sm text-text-muted">
          {t(track === 'leetcodes' ? 'orientador.howIntroLeetcodes' : 'orientador.howIntro').split(/(\*\*.*?\*\*)/g).map((part, i) =>
            part.startsWith('**') && part.endsWith('**')
              ? <strong key={i} className="text-text">{part.slice(2, -2)}</strong>
              : part,
          )}
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
          {t('orientador.howDashboardLink')}
        </Link>
      </section>

      {data.set_history.length > 0 && (
        <section className="card space-y-4">
          <h2 className="text-lg font-semibold text-text">
            {t('orientador.historyTitle', { level: data.active_level.toUpperCase() })}
          </h2>
          <p className="text-sm text-text-muted">
            {t('orientador.historyDesc')}
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
            <h2 className="text-lg font-semibold text-text">{t('orientador.planTitle')}</h2>
            <span className="badge-brand">
              {t('orientador.planBadge', { done: data.plan.completed_count, total: data.plan.total_count, min: data.plan.minutes_budget })}
            </span>
          </div>
          <p className="text-sm text-text-muted">
            {t('orientador.planSummary', { estimated: data.plan.estimated_minutes, budget: data.plan.minutes_budget })}
          </p>
          <div className="space-y-3">
            {data.plan.assignments.map((a, i) => (
              <ExplainedAssignmentCard key={i} assignment={a} planId={data.plan!.id} />
            ))}
          </div>
        </section>
      ) : (
        <section className="card text-sm text-text-muted">
          {t('orientador.planEmpty').split(/(\*\*.*?\*\*)/g).map((part, i) => {
            if (part.startsWith('**') && part.endsWith('**')) {
              const text = part.slice(2, -2);
              if (text.toLowerCase() === 'dashboard') {
                return <Link key={i} to="/" className="text-brand hover:underline">{text}</Link>;
              }
              return <strong key={i} className="text-text">{text}</strong>;
            }
            return part;
          })}
        </section>
      )}
    </div>
  );
}

function SetHistoryCard({ row, today }: { row: SetHistoryRow; today: string }) {
  const { t } = useI18n();
  const acc = row.first_attempt_accuracy != null
    ? `${Math.round(row.first_attempt_accuracy * 100)}%`
    : null;
  const displaySet = resolveDisplaySetNumber(row.set_number, row.display_set_number);

  return (
    <div className="rounded-lg border border-border bg-surface-2 px-4 py-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-sm font-medium text-text">
            Set {displaySet} · {row.title}
          </p>
          <p className="text-xs text-text-dim">
            {t('orientador.setStatus', { status: row.status })}
            {row.attempts > 0 ? ` · ${t('orientador.setAttempts', { n: row.attempts })}` : ''}
            {acc ? ` · ${t('orientador.firstAttempt', { pct: acc })}` : ''}
          </p>
        </div>
        {row.solid_mastery ? (
          <span className="badge-brand text-xs">{t('orientador.solidMastery')}</span>
        ) : row.status === 'mastered' ? (
          <span className="badge-muted text-xs">{t('orientador.masteredReview')}</span>
        ) : null}
      </div>
      {(row.failure_flags.length > 0 || row.repeat_scheduled_for) && (
        <ul className="mt-2 space-y-1 text-xs text-amber-600">
          {row.failure_flags.includes('too_slow') && (
            <li>{t('orientador.failTooSlow')}</li>
          )}
          {row.failure_flags.includes('low_accuracy') && (
            <li>{t('orientador.failLowAccuracy', { pct: acc ?? '?' })}</li>
          )}
          {row.repeat_scheduled_for && (
            <li>
              {t('orientador.repeatScheduled', { date: row.repeat_scheduled_for })}
              {row.repeat_completed_at === today ? ` ${t('orientador.repeatDoneToday')}` : ''}
            </li>
          )}
        </ul>
      )}
    </div>
  );
}

function ExplainedAssignmentCard({ assignment, planId }: { assignment: ExplainedAssignment; planId: number }) {
  const { t, locale } = useI18n();
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
            {reasonLabel(reason, locale, assignment.type)}
            {assignment.lap ? ` ${t('orientador.assignmentLap', { n: assignment.lap })}` : ''}
          </p>
          <p className="mt-1 text-base font-semibold text-text">{ex.title || assignmentLabel(assignment as OrientadorAssignment, locale)}</p>
        </div>
        <span className="text-xs text-text-dim">
          {assignment.completed ? t('common.done') : t('dashboard.estimatedMin', { n: Math.round(assignment.estimated_minutes ?? 0) })}
        </span>
      </div>
      <p className="mt-2 text-sm text-text-muted">{ex.summary}</p>
      {!assignment.completed && (assignment.type === 'set' || assignment.type === 'leetcode_practice') && (
        <Link
          to={orientadorAssignmentPath(planId, idx, assignment as OrientadorAssignment)}
          className="btn-primary mt-3 inline-block text-sm"
        >
          {t('orientador.startActivity')}
        </Link>
      )}
    </div>
  );
}
