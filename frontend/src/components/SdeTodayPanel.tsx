import { Link } from 'react-router-dom';
import { type SdeAssignment } from '../lib/api';
import { sdeAssignmentHref } from '../lib/sdePaths';
import { useCodi } from '../lib/codi';
import { useI18n } from '../i18n/context';
import { InterviewStoryCard } from './StudyRitual';

function label(a: SdeAssignment, locale: string): string {
  if (a.type === 'flashcards') return locale === 'es' ? 'Mazo' : 'Cards';
  if (a.type === 'theory' || a.type === 'reading' || a.type === 'debug' || a.type === 'design' || a.type === 'project') {
    return String(a.title || a.id);
  }
  if (a.type === 'algo_sheet') {
    return `${a.title || a.algo_id} · ${a.lang} · ${a.sheet_id}`;
  }
  if (a.type === 'voice') return locale === 'es' ? 'Voz' : 'Voice';
  if (a.type === 'sql') return 'SQL';
  if (a.type === 'story') return locale === 'es' ? 'Historia' : 'Story';
  if (a.type === 'return') return locale === 'es' ? 'Retorno' : 'Return';
  return a.type;
}

function typeHint(a: SdeAssignment, locale: string): string {
  if (a.type === 'flashcards') return locale === 'es' ? 'Repaso rápido' : 'Quick recall';
  if (a.type === 'reading') return locale === 'es' ? 'Lectura' : 'Reading';
  if (a.type === 'theory') return locale === 'es' ? 'Lee + quiz' : 'Read + quiz';
  if (a.type === 'debug') return locale === 'es' ? 'Arregla el bug' : 'Fix the bug';
  if (a.type === 'design') return locale === 'es' ? 'Diseño' : 'System design';
  if (a.type === 'project') return locale === 'es' ? 'Proyecto' : 'Project story';
  if (a.type === 'algo_sheet') return locale === 'es' ? 'Escribe código' : 'Write code';
  if (a.type === 'voice') return locale === 'es' ? 'Explica en voz' : 'Explain out loud';
  if (a.type === 'sql') return locale === 'es' ? 'Consulta SQL' : 'SQL query';
  if (a.type === 'story') return locale === 'es' ? 'Historia de entrevista' : 'Interview story';
  return a.type;
}

export function SdeTodayPanel() {
  const { locale, t } = useI18n();
  const { sde: data, loading } = useCodi();

  if (!data) {
    return loading
      ? <p className="text-sm text-text-dim">{t('common.loading')}</p>
      : null;
  }

  const kindLabel = data.kind === 'flojo'
    ? (locale === 'es' ? 'Día flojo' : 'Light day')
    : data.kind === 'return'
      ? (locale === 'es' ? 'Retorno' : 'Return')
      : (locale === 'es' ? 'Día de avance' : 'Advance day');

  const doneCount = data.assignments.filter((a) => a.completed).length;
  const total = data.assignments.length;
  const pct = total ? Math.round((doneCount / total) * 100) : 0;
  const nextIndex = data.assignments.findIndex((a) => !a.completed);

  return (
    <section className="sde-panel rise-in rise-in-delay-1">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="sde-panel-kicker">{kindLabel}</p>
          <h2 className="mt-1 font-[family-name:var(--font-display)] text-xl font-bold tracking-tight text-text">
            {data.codi?.headline || (locale === 'es' ? 'Plan SDE de hoy' : "Today's SDE plan")}
          </h2>
          {data.complete ? (
            <p className="mt-1 text-sm text-brand">
              {locale === 'es' ? 'Día limpio. Buen trabajo.' : 'Day complete. Nice work.'}
            </p>
          ) : (
            <p className="mt-1 text-sm text-text-muted">
              {locale === 'es'
                ? `${doneCount} de ${total} listos — sigue el siguiente bloque.`
                : `${doneCount} of ${total} done — hit the next block.`}
            </p>
          )}
        </div>
        <Link
          to="/sde/pack"
          className="rounded-lg border border-border bg-bg px-3 py-1.5 text-xs font-semibold text-text-muted transition hover:border-brand/40 hover:text-brand"
        >
          {locale === 'es' ? 'Paquete de viaje' : 'Travel pack'}
        </Link>
      </div>

      <div className="mt-4">
        <div className="mb-2 flex items-center justify-between text-xs text-text-dim">
          <span>{locale === 'es' ? 'Progreso del día' : "Day's progress"}</span>
          <span className="font-mono tabular-nums">{pct}%</span>
        </div>
        <div className="progress-bar-lg">
          <div className={`progress-fill ${pct < 100 ? 'progress-fill-live' : ''}`} style={{ width: `${pct}%` }} />
        </div>
      </div>

      <ol className="mt-5 space-y-2">
        {data.assignments.map((a, idx) => {
          const to = sdeAssignmentHref(a);
          const done = Boolean(a.completed);
          const current = idx === nextIndex;
          const className = `sde-step ${done ? 'sde-step-done' : ''} ${current ? 'sde-step-current' : ''}`;
          const inner = (
            <>
              <span className="sde-step-index" aria-hidden>
                {done ? '✓' : idx + 1}
              </span>
              <span className="min-w-0 flex-1">
                <span className={`block text-sm font-semibold ${done ? 'text-text-dim line-through' : 'text-text'}`}>
                  {label(a, locale)}
                </span>
                <span className="mt-0.5 block text-xs text-text-dim">{typeHint(a, locale)}</span>
              </span>
              <span className={`shrink-0 text-xs font-semibold ${current ? 'text-brand' : 'text-text-dim'}`}>
                {done ? t('common.done') : current ? (locale === 'es' ? 'Ahora' : 'Now') : t('common.pending')}
              </span>
            </>
          );
          return (
            <li key={a.id}>
              {to && !done ? (
                <Link to={to} className={className}>
                  {inner}
                </Link>
              ) : (
                <div className={className}>{inner}</div>
              )}
            </li>
          );
        })}
      </ol>
      {data.assignments.some((a) => a.type === 'story' && !a.completed) && (
        <div className="mt-4">
          <InterviewStoryCard />
        </div>
      )}
    </section>
  );
}
