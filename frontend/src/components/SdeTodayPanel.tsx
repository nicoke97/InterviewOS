import { Link } from 'react-router-dom';
import { type SdeAssignment } from '../lib/api';
import { useCodi } from '../lib/codi';
import { useI18n } from '../i18n/context';
import { InterviewStoryCard } from './StudyRitual';

function hrefFor(a: SdeAssignment): string | null {
  if (a.type === 'flashcards') return '/sde/cards';
  if (a.type === 'theory') return `/sde/section/${a.section_id || a.id}`;
  if (a.type === 'algo_sheet') {
    return `/sde/algo/${a.algo_id}/${a.lang}/${a.sheet_id}`;
  }
  if (a.type === 'voice') return '/sde/voice';
  if (a.type === 'sql') return `/sde/sql/${a.id}`;
  if (a.type === 'story') return '/stories';
  return null;
}

function label(a: SdeAssignment, locale: string): string {
  if (a.type === 'flashcards') return locale === 'es' ? 'Mazo' : 'Cards';
  if (a.type === 'theory') return String(a.title || a.id);
  if (a.type === 'algo_sheet') {
    return `${a.title || a.algo_id} · ${a.lang} · ${a.sheet_id}`;
  }
  if (a.type === 'voice') return locale === 'es' ? 'Voz' : 'Voice';
  if (a.type === 'sql') return 'SQL';
  if (a.type === 'story') return locale === 'es' ? 'Historia' : 'Story';
  if (a.type === 'return') return locale === 'es' ? 'Retorno' : 'Return';
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

  return (
    <section className="space-y-4 rounded-xl border border-brand/30 bg-brand/5 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">{kindLabel}</p>
          <h2 className="mt-1 text-lg font-medium text-text">
            {data.codi?.headline || (locale === 'es' ? 'Plan SDE de hoy' : "Today's SDE plan")}
          </h2>
          {data.complete && (
            <p className="mt-1 text-sm text-text-muted">{locale === 'es' ? 'Día limpio.' : 'Day complete.'}</p>
          )}
        </div>
        <Link to="/sde/pack" className="text-xs text-brand hover:underline">
          {locale === 'es' ? 'Paquete de viaje' : 'Travel pack'}
        </Link>
      </div>
      <ol className="space-y-2">
        {data.assignments.map((a) => {
          const to = hrefFor(a);
          const done = Boolean(a.completed);
          const inner = (
            <span className="flex items-center justify-between gap-3 text-sm">
              <span className={done ? 'text-text-dim line-through' : 'text-text'}>{label(a, locale)}</span>
              <span className="text-xs text-text-dim">{done ? t('common.done') : t('common.pending')}</span>
            </span>
          );
          return (
            <li key={a.id} className="rounded-lg border border-border bg-surface px-3 py-2">
              {to && !done ? <Link to={to} className="block hover:text-brand">{inner}</Link> : inner}
            </li>
          );
        })}
      </ol>
      {data.assignments.some((a) => a.type === 'story' && !a.completed) && (
        <InterviewStoryCard />
      )}
    </section>
  );
}
