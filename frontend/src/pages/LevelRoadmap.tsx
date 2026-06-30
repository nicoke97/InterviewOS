import { useCallback, useEffect, useState, type ReactNode } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api, type Roadmap, type RoadmapSet, type SetStatus } from '../lib/api';
import { resolveDisplaySetNumber } from '../lib/setLabels';
import { LockIcon } from '../components/LockIcon';
import { useI18n } from '../i18n/context';

function fmtTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

function fmtMs(ms: number | null): string {
  if (ms == null) return '—';
  return fmtTime(Math.round(ms / 1000));
}

const STATUS_STYLE: Record<SetStatus, string> = {
  mastered: 'border-emerald-500/40 bg-emerald-500/10',
  current: 'border-brand bg-brand/10 ring-1 ring-brand',
  repeating: 'border-amber-500/50 bg-amber-500/10 ring-1 ring-amber-500/60',
  locked: 'border-border bg-surface-2 opacity-60',
  extra: 'border-violet-500/40 bg-violet-500/10',
};

function statusBadge(status: SetStatus, t: (key: string) => string): { label: string; cls: string } {
  switch (status) {
    case 'mastered': return { label: t('common.mastered'), cls: 'text-emerald-700' };
    case 'current': return { label: t('common.current'), cls: 'text-brand' };
    case 'repeating': return { label: t('common.repeat'), cls: 'text-amber-600' };
    case 'extra': return { label: t('common.extraPractice'), cls: 'text-violet-700' };
    default: return { label: t('common.locked'), cls: 'text-text-dim' };
  }
}

export function LevelRoadmap() {
  const { t, locale } = useI18n();
  const { level: levelParam } = useParams();
  const level = (levelParam || 'a').toLowerCase();
  const [data, setData] = useState<Roadmap | null>(null);
  const [error, setError] = useState(false);

  const load = useCallback(() => {
    void locale;
    api.roadmap(level).then(setData).catch(() => setError(true));
  }, [level, locale]);

  useEffect(() => { load(); }, [load]);

  if (error) {
    return (
      <div className="card space-y-3 text-center">
        <h2 className="page-title">{t('roadmap.errorTitle')}</h2>
        <p className="text-text-muted">
          {t('roadmap.errorHint')}
        </p>
        <button type="button" onClick={() => { setError(false); load(); }} className="btn-secondary">
          {t('common.retry')}
        </button>
      </div>
    );
  }
  if (!data) return <p className="text-text-muted">{t('roadmap.loading')}</p>;

  const pct = data.total_sets ? Math.round((data.mastered_sets / data.total_sets) * 100) : 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="page-title">{t('roadmap.title', { level: level.toUpperCase() })}</h1>
          <p className="page-subtitle">{t('roadmap.subtitle')}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="badge-brand">{t('roadmap.setsBadge', { mastered: data.mastered_sets, total: data.total_sets })}</span>
          <span className="badge-muted">{t('roadmap.pctComplete', { pct })}</span>
        </div>
      </div>

      {!data.unlocked ? (
        <div className="locked-card mx-auto max-w-lg text-center">
          <LockIcon className="mx-auto h-10 w-10 text-warning/70" />
          <h2 className="page-title mt-4">{t('roadmap.lockedTitle')}</h2>
          <p className="mt-3 text-text-muted">
            {t('roadmap.lockedDesc')}
          </p>
        </div>
      ) : (
        <>
          <TargetBanner data={data} level={level} />

          <p className="text-xs text-text-dim">
            {t('roadmap.hint')}
          </p>
          {data.blocks.map((block) => {
            const sets = data.sets.filter((s) => s.block === block.letter);
            return (
              <div key={block.letter} className="card space-y-4">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="text-lg font-semibold text-text">
                        {block.extra
                          ? t('roadmap.extraBlockTitle', { title: block.title })
                          : t('roadmap.blockTitle', { letter: block.letter, title: block.title })}
                      </h2>
                      {block.extra && <span className="badge-muted">{t('roadmap.alwaysAvailable')}</span>}
                    </div>
                    <p className="text-xs text-text-dim">
                      {t('roadmap.blockSetsRange', {
                        start: block.set_start,
                        end: block.set_end,
                        pageStart: block.page_start ?? (block.set_start - 1) * 10 + 1,
                        pageEnd: block.page_end ?? block.set_end * 10,
                      })}
                    </p>
                  </div>
                </div>
                <p className="border-l-2 border-border pl-3 text-sm text-text-muted">{block.instruction}</p>

                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {sets.map((s) => <SetCard key={s.set_number} set={s} level={level} />)}
                </div>

                {block.checkpoint.exists && (
                  <CheckpointCard
                    level={level}
                    block={block.letter}
                    checkpoint={block.checkpoint}
                  />
                )}
              </div>
            );
          })}

          {data.exam.exists && <ExamCard data={data} level={level} />}
        </>
      )}
    </div>
  );
}

function TargetBanner({ data, level }: { data: Roadmap; level: string }) {
  const { t } = useI18n();
  const target = data.target;
  if (target.type === 'complete') {
    return (
      <div className="alert-success">
        {t('roadmap.targetComplete')}
      </div>
    );
  }
  let desc = '';
  let action: ReactNode = null;
  if (target.type === 'set') {
    const n = resolveDisplaySetNumber(target.set_number!, target.display_set_number);
    desc = target.repeating
      ? t('roadmap.targetSetRepeat', { n })
      : t('roadmap.targetSetNext', { n });
    action = (
      <div className="mt-3 flex flex-wrap gap-2">
        <Link to="/" className="btn-primary">{t('common.guidedSession')}</Link>
        <Link to={`/${level}/kumon`} className="btn-secondary">{t('common.freePractice')}</Link>
      </div>
    );
  } else if (target.type === 'checkpoint') {
    desc = t('roadmap.targetCheckpoint', { block: target.block ?? '' });
    action = (
      <Link to={`/${level}/checkpoint/${target.block}`} className="btn-primary mt-3 inline-block">
        {t('common.goCheckpoint')}
      </Link>
    );
  } else if (target.type === 'exam') {
    desc = t('roadmap.targetExam');
    action = (
      <Link to={`/${level}/exam`} className="btn-primary mt-3 inline-block">
        {t('common.goExam')}
      </Link>
    );
  }
  return (
    <div className="card border-brand/40 bg-brand/5">
      <p className="text-sm font-semibold text-text">{t('roadmap.targetNextStep')}</p>
      <p className="text-sm text-text-muted">{desc}</p>
      {action}
    </div>
  );
}

function SetCard({ set, level }: { set: RoadmapSet; level: string }) {
  const { t } = useI18n();
  const badge = statusBadge(set.status, t);
  const displaySet = resolveDisplaySetNumber(set.set_number, set.display_set_number);
  const studyLink = set.status === 'current' || set.status === 'repeating'
    ? `/${level}/kumon`
    : set.status === 'mastered' || set.status === 'extra'
      ? `/${level}/kumon?set=${set.set_number}`
      : null;

  const inner = (
    <div className={`flex h-full flex-col gap-2 rounded-xl border p-3 ${STATUS_STYLE[set.status]}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wide text-text-dim">{t('common.setN', { n: displaySet })}</span>
        <span className={`text-[11px] font-semibold ${badge.cls}`}>{badge.label}</span>
      </div>
      <p className="text-sm font-medium leading-snug text-text">{set.title}</p>
      <div className="mt-auto space-y-1 text-[11px] text-text-dim">
        <p>{t('roadmap.setPages', { start: set.page_start, end: set.page_end })}</p>
        <p>{t('roadmap.standardTime', { time: fmtTime(set.standard_seconds) })}</p>
        {set.status === 'mastered' ? (
          <p className="text-emerald-700">
            {t('roadmap.bestAttempt', { time: fmtMs(set.best_time_ms), attempts: set.attempts })}
            {set.solid_mastery === false && t('roadmap.reviewPending')}
          </p>
        ) : set.status === 'current' || set.status === 'repeating' ? (
          <p>{t('roadmap.setProgress', { completed: set.completed, total: set.total, attempts: set.attempts })}</p>
        ) : set.status === 'extra' ? (
          <p>{t('roadmap.extraSetHint')}</p>
        ) : (
          <p>{t('roadmap.unlockOrder')}</p>
        )}
        {set.repeat_scheduled_for && (
          <p className="text-amber-600">{t('roadmap.repeatScheduled', { date: set.repeat_scheduled_for })}</p>
        )}
      </div>
      {studyLink && (
        <Link
          to={studyLink}
          className="mt-2 inline-block rounded-lg border border-border bg-surface px-2.5 py-1.5 text-center text-xs font-medium text-text transition hover:border-brand/40"
          onClick={(e) => e.stopPropagation()}
        >
          {set.status === 'mastered' ? t('common.review') : set.status === 'extra' ? t('common.practice') : t('common.study')}
        </Link>
      )}
    </div>
  );
  return inner;
}

function CheckpointCard({ level, block, checkpoint }: {
  level: string;
  block: string;
  checkpoint: { problems: string[]; passed: boolean; available: boolean; exists: boolean };
}) {
  const { t } = useI18n();
  const state = checkpoint.passed ? 'passed' : checkpoint.available ? 'available' : 'locked';
  const styles = {
    passed: 'border-emerald-500/40 bg-emerald-500/10',
    available: 'border-brand/50 bg-brand/5',
    locked: 'border-border bg-surface-2 opacity-70',
  }[state];
  return (
    <div className={`flex flex-wrap items-center justify-between gap-3 rounded-xl border p-3 ${styles}`}>
      <div>
        <p className="text-sm font-semibold text-text">
          {t('roadmap.checkpointTitle', { block })}
        </p>
        <p className="text-xs text-text-dim">
          {t('roadmap.checkpointDesc', { count: checkpoint.problems.length })}
        </p>
      </div>
      {checkpoint.passed ? (
        <span className="badge-brand">{t('common.passed')}</span>
      ) : checkpoint.available ? (
        <Link to={`/${level}/checkpoint/${block}`} className="btn-secondary text-sm">{t('common.start')}</Link>
      ) : (
        <span className="inline-flex items-center gap-1 text-xs text-text-dim">
          <LockIcon className="h-3.5 w-3.5" /> {t('roadmap.checkpointLocked')}
        </span>
      )}
    </div>
  );
}

function ExamCard({ data, level }: { data: Roadmap; level: string }) {
  const { t } = useI18n();
  const exam = data.exam;
  return (
    <div className={`card flex flex-wrap items-center justify-between gap-3 ${exam.passed ? 'border-emerald-500/40 bg-emerald-500/10' : 'border-amber-500/30'}`}>
      <div>
        <h2 className="text-lg font-semibold text-text">{t('roadmap.examTitle')}</h2>
        <p className="text-sm text-text-muted">
          {t('roadmap.examDesc', { leetcode: exam.leetcode.length, interview: exam.interview.length })}
        </p>
      </div>
      {exam.passed ? (
        <span className="badge-brand">{t('common.passed')}</span>
      ) : exam.available ? (
        <Link to={`/${level}/exam`} className="btn-primary">{t('roadmap.takeExam')}</Link>
      ) : (
        <span className="inline-flex items-center gap-1 text-xs text-text-dim">
          <LockIcon className="h-3.5 w-3.5" /> {t('roadmap.examLocked')}
        </span>
      )}
    </div>
  );
}
