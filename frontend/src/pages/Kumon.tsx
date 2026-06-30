import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { orientadorAssignmentPath } from '../lib/orientadorLabels';
import { assignmentReasonContext } from '../lib/reasonContext';
import { clearSessionDraft, loadSessionDraft, saveSessionDraft } from '../lib/sessionDraft';
import { api, type KumonPage, type SessionData, type SetSubmitResult, type DrillResult } from '../lib/api';
import { resolveDisplaySetNumber } from '../lib/setLabels';
import { KumonProblem } from '../components/KumonProblem';
import { SessionTimer, useSessionTimer } from '../components/Timer';
import { useI18n } from '../i18n/context';

const COUNT_OPTIONS = [3, 5, 10];

function fmt(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

function sessionStorageKey(data: SessionData, isOrientador: boolean, orientadorPlanId?: number, orientadorIndex?: number, level?: string): string {
  if (isOrientador) return `plan-${orientadorPlanId}-${orientadorIndex}`;
  if (data.mode === 'review') return `${data.level || level}-review-${data.set_number}`;
  return `${data.level || level}-set-${data.set_number}`;
}

export function KumonSession() {
  const { t, locale } = useI18n();
  const { level: levelParam, planId, index: indexParam } = useParams<{
    level?: string;
    planId?: string;
    index?: string;
  }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const isOrientador = Boolean(planId && indexParam);
  const orientadorPlanId = planId ? Number(planId) : undefined;
  const orientadorIndex = indexParam != null ? Number(indexParam) : undefined;
  const level = (levelParam || 'a').toLowerCase();
  const rawSet = searchParams.get('set');
  const reviewSetNumber = rawSet && Number.isFinite(Number(rawSet)) ? Number(rawSet) : undefined;

  const [count, setCount] = useState(10);
  const [data, setData] = useState<SessionData | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [results, setResults] = useState<Record<string, DrillResult>>({});
  const [dirtyIds, setDirtyIds] = useState<Set<string>>(() => new Set());
  const [outcome, setOutcome] = useState<SetSubmitResult | null>(null);
  const [checked, setChecked] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [focusMode, setFocusMode] = useState(false);
  const [highlightEmpty, setHighlightEmpty] = useState(false);
  const [draftBanner, setDraftBanner] = useState(false);

  const { running, start, stop, onTick, seconds, setElapsed, secondsRef } = useSessionTimer('study');
  const timerStartedRef = useRef(false);
  const storageKeyRef = useRef<string | null>(null);

  useEffect(() => {
    api.settings().then((s) => setFocusMode(s.focus_mode)).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    void locale;
    setLoading(true);
    setLoadError(null);
    await stop();
    timerStartedRef.current = false;
    setData(null);
    setChecked(false);
    setOutcome(null);
    setResults({});
    setAnswers({});
    setHighlightEmpty(false);
    setDraftBanner(false);

    try {
      const d = isOrientador
        ? await api.orientadorSession(orientadorPlanId!, orientadorIndex!)
        : await api.session(level, reviewSetNumber ? 10 : count, reviewSetNumber);

      if (isOrientador && d.type === 'checkpoint') {
        navigate(`/${d.level}/checkpoint/${d.checkpoint?.block ?? d.assignment?.block}`);
        return;
      }
      if (isOrientador && d.type === 'exam') {
        navigate(`/${d.level}/exam`);
        return;
      }

      const key = sessionStorageKey(d, isOrientador, orientadorPlanId, orientadorIndex, level);
      storageKeyRef.current = key;
      const draft = loadSessionDraft(key);

      const init: Record<string, string> = {};
      (d.drills || []).forEach((p) => {
        init[p.id] = draft?.answers[p.id] ?? '';
      });

      setData(d);
      setAnswers(init);
      setDirtyIds(new Set());
      setSubmitError(null);

      if (draft && Object.values(init).some((v) => v.length > 0)) {
        setDraftBanner(true);
        setElapsed(draft.seconds);
        if (draft.seconds > 0 || Object.values(init).some((v) => v.length > 0)) {
          timerStartedRef.current = true;
          void start(draft.seconds);
        }
      } else {
        setElapsed(0);
        clearSessionDraft(key);
      }
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : t('kumon.errorTitle'));
    } finally {
      setLoading(false);
    }
  }, [level, count, isOrientador, orientadorPlanId, orientadorIndex, navigate, stop, start, setElapsed, reviewSetNumber, locale]);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => () => { void stop(); }, [stop]);

  useEffect(() => {
    const key = storageKeyRef.current;
    if (!key || !data || checked) return;
    saveSessionDraft(key, { answers, seconds: secondsRef.current, count });
  }, [answers, seconds, data, checked, count, secondsRef]);

  const ensureTimer = useCallback(() => {
    if (!timerStartedRef.current) {
      timerStartedRef.current = true;
      void start(secondsRef.current);
    }
  }, [start, secondsRef]);

  const updateAnswer = (id: string, code: string) => {
    setAnswers((prev) => ({ ...prev, [id]: code }));
    if (checked) {
      setDirtyIds((prev) => new Set(prev).add(id));
    }
    if (code.length > 0) ensureTimer();
  };

  const check = useCallback(async () => {
    if (!data || !data.drills) return;

    const empty = data.drills.filter((d) => !(answers[d.id] || '').trim());
    if (empty.length > 0 && !checked) {
      setHighlightEmpty(true);
      setSubmitError(t('kumon.emptyAnswers', { count: empty.length }));
      empty[0] && document.querySelector(`[data-drill-id="${empty[0].id}"]`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }

    setSubmitting(true);
    setSubmitError(null);
    setHighlightEmpty(false);

    try {
      const time_ms = secondsRef.current * 1000;
      const isReview = data.mode === 'review';

      if (isReview) {
        const reviewResults: Record<string, DrillResult> = {};
        for (const d of data.drills) {
          const res = await api.run({
            code: answers[d.id] || '',
            exercise_id: d.id,
            exercise_type: 'kumon',
          });
          reviewResults[d.id] = {
            passed: Boolean(res.passed),
            error: res.error as string | null | undefined,
            expected: res.expected as string | undefined,
            stdout: res.stdout as string | undefined,
          };
        }
        const passedCount = Object.values(reviewResults).filter((r) => r.passed).length;
        setResults(reviewResults);
        setOutcome({
          results: reviewResults,
          passed_count: passedCount,
          total: data.drills.length,
          outcome: passedCount === data.drills.length ? 'mastered' : 'in_progress',
          set_status: 'mastered',
          completed: data.total ?? data.drills.length,
          set_total: data.total ?? data.drills.length,
          accumulated_time_ms: time_ms,
          standard_ms: (data.standard_seconds || 0) * 1000,
          mastered: passedCount === data.drills.length,
        });
        setChecked(true);
        setDirtyIds(new Set());
        if (storageKeyRef.current) clearSessionDraft(storageKeyRef.current);
        return;
      }

      const res = await api.setSubmit({
        level: data.level || level,
        set_number: data.set_number!,
        time_ms,
        answers: data.drills.map((d) => ({ exercise_id: d.id, code: answers[d.id] || '' })),
        plan_id: isOrientador ? orientadorPlanId : undefined,
        assignment_index: isOrientador ? orientadorIndex : undefined,
      });
      setResults(res.results);
      setOutcome(res);
      setChecked(true);
      setDirtyIds(new Set());
      if (storageKeyRef.current) clearSessionDraft(storageKeyRef.current);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : t('kumon.errorReview'));
    } finally {
      setSubmitting(false);
    }
  }, [data, answers, checked, isOrientador, orientadorPlanId, orientadorIndex, level, secondsRef]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && !checked && !submitting) {
        e.preventDefault();
        void check();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [check, checked, submitting]);

  if (loading && !data) {
    return <p className="text-text-muted">{t('kumon.loading')}</p>;
  }

  if (loadError) {
    return (
      <div className="card mx-auto max-w-lg space-y-3 text-center">
        <h2 className="page-title">{t('kumon.errorTitle')}</h2>
        <p className="text-sm text-text-muted">{loadError}</p>
        <button type="button" onClick={() => void load()} className="btn-secondary">{t('common.retry')}</button>
      </div>
    );
  }

  if (!data) return null;

  if (data.type !== 'set') {
    return <NonSetState data={data} level={level} />;
  }

  const drills = data.drills || [];
  const standard = data.standard_seconds || 0;
  const isReview = data.mode === 'review';
  const passedCount = Object.values(results).filter((r) => r.passed).length;
  const answeredCount = drills.filter((d) => (answers[d.id] || '').trim().length > 0).length;
  const failedIds = drills
    .filter((d) => checked && results[d.id] && !results[d.id].passed && !dirtyIds.has(d.id))
    .map((d) => d.id);
  const needsRecheck = checked && !isReview && (failedIds.length > 0 || dirtyIds.size > 0);

  const scrollToFirstFailed = () => {
    document.querySelector('[data-review-status="failed"]')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  const sessionLevel = data.level || level;
  const reason = data.assignment?.reason;
  const displaySet = resolveDisplaySetNumber(data.set_number!, data.display_set_number);
  const reasonContext = assignmentReasonContext(data, locale, data.explain);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="page-title">
            {isReview ? t('kumon.titleReview') + ' ' : ''}
            {isOrientador && reason === 'repeat' ? t('kumon.titleRepeat') + ' ' : ''}
            {t('kumon.titleSetLevel', { set: displaySet, level: sessionLevel.toUpperCase() })}
          </h1>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <span className="badge">{t('common.blockN', { block: data.block ?? '' })}</span>
            {isOrientador && <span className="badge-brand">{t('common.guidedSession')}</span>}
            {!isOrientador && !isReview && <span className="badge-muted">{t('common.freePractice')}</span>}
            {isReview && <span className="badge-muted">{t('kumon.reviewNoProgress')}</span>}
            {reason === 'repeat' && <span className="badge-amber">{t('kumon.scheduledRepeat')}</span>}
            {reason === 'pre_exam' && <span className="badge-amber">{t('kumon.preExam')}</span>}
            {data.status === 'repeating' && <span className="badge-amber">{t('kumon.repeating')}</span>}
            <span className="text-sm text-text-muted">
              {t('kumon.setMeta', { title: data.set_title ?? '', completed: data.completed ?? 0, total: data.total ?? 0, range: data.page_range ?? '' })}
            </span>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <div className="flex items-center gap-2">
            {!isOrientador && !isReview && <CountPicker count={count} setCount={setCount} disabled={checked} />}
            <div className="timer-pill">
              <SessionTimer running={running} seconds={seconds} standardSeconds={standard} onTick={onTick} />
              <span className="ml-1 text-xs text-text-dim">/ {fmt(standard)}</span>
            </div>
          </div>
          {!checked && (
            <p className="text-xs text-text-dim">
              {t('kumon.answered', { answered: answeredCount, total: drills.length })}
            </p>
          )}
        </div>
      </div>

      {!isOrientador && !isReview && (
        <div className="rounded-lg border border-border bg-surface-2 px-4 py-3 text-sm text-text-muted">
          {t('kumon.freePracticeBanner').split(/(\*\*.*?\*\*)/g).map((part, i) => {
            if (part.startsWith('**') && part.endsWith('**')) {
              const text = part.slice(2, -2);
              if (text.toLowerCase() === 'dashboard') {
                return <Link key={i} to="/" className="text-brand hover:underline">{text}</Link>;
              }
              return <strong key={i} className="text-text">{text}</strong>;
            }
            return part;
          })}
        </div>
      )}
      {isOrientador && (
        <div className="rounded-lg border border-brand/30 bg-brand/5 px-4 py-3 text-sm text-text-muted">
          {t('kumon.guidedBanner').split(/(\*\*.*?\*\*)/g).map((part, i) =>
            part.startsWith('**') && part.endsWith('**')
              ? <strong key={i} className="text-text">{part.slice(2, -2)}</strong>
              : part,
          )}
        </div>
      )}
      {reasonContext && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-sm text-text-muted">
          <span className="font-medium text-amber-700">{t('kumon.whySet')} </span>
          {reasonContext}
        </div>
      )}
      {draftBanner && !checked && (
        <div className="rounded-lg border border-sky-500/30 bg-sky-500/5 px-4 py-2 text-sm text-sky-800">
          {t('kumon.draftRestored')}
          <button
            type="button"
            className="ml-2 underline"
            onClick={() => {
              if (storageKeyRef.current) clearSessionDraft(storageKeyRef.current);
              setDraftBanner(false);
              void load();
            }}
          >
            {t('kumon.startOver')}
          </button>
        </div>
      )}

      {data.status === 'repeating' && !isOrientador && !isReview && (
        <div className="alert-error">
          {t('kumon.repeatSlowWarning', { time: fmt(standard) })}
        </div>
      )}
      {isOrientador && reason === 'repeat' && (
        <div className="alert-error">
          {t('kumon.repeatOrientador', { time: fmt(standard) })}
        </div>
      )}

      <div className="mx-auto max-w-4xl rounded-sm border border-stone-400 bg-stone-200 p-1 shadow-2xl">
        <div className="bg-[#fffef8] px-5 py-5 text-stone-900 sm:px-8 sm:py-6">
          <div className="mb-4 border-b-2 border-stone-800 pb-3">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-stone-500">Codenda</p>
                <h2 className="text-xl font-bold tracking-tight text-stone-900">{data.set_title}</h2>
              </div>
              <div className="text-right text-xs font-medium text-stone-600">
                <p>Set {displaySet}</p>
                <p>{t('common.blockN', { block: data.block ?? '' })}</p>
              </div>
            </div>
          </div>

          <p className="mb-5 border-l-4 border-stone-800 pl-3 text-sm font-medium leading-relaxed text-stone-700">
            {data.instruction}
          </p>

          <div className="columns-1 gap-x-4 sm:columns-2">
            {drills.map((page: KumonPage, i: number) => {
              const reviewStatus = !checked
                ? 'pending'
                : dirtyIds.has(page.id)
                  ? 'edited'
                  : results[page.id]?.passed
                    ? 'passed'
                    : results[page.id]
                      ? 'failed'
                      : 'pending';
              return (
                <div key={page.id} data-drill-id={page.id} className="mb-4 break-inside-avoid">
                  <KumonProblem
                    number={i + 1}
                    pageLabel={page.id}
                    drill={page}
                    value={answers[page.id] || ''}
                    onChange={(code) => updateAnswer(page.id, code)}
                    result={results[page.id]}
                    reviewStatus={reviewStatus}
                    focusMode={focusMode}
                    highlightEmpty={highlightEmpty}
                  />
                </div>
              );
            })}
          </div>

          <div className="mt-6 border-t border-dashed border-stone-400 pt-5">
            {!checked ? (
              <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-between">
                <div className="text-center sm:text-left">
                  <p className="text-xs text-stone-500">
                    {t('kumon.sheetInstructions', { n: drills.length })}
                  </p>
                  {submitError && (
                    <p className="mt-2 text-xs text-red-700">{submitError}</p>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => void check()}
                  disabled={submitting}
                  className="rounded border-2 border-stone-900 bg-stone-900 px-8 py-2.5 text-sm font-bold text-[#fffef8] transition hover:bg-stone-700 disabled:opacity-50"
                >
                  {submitting ? t('kumon.reviewing') : t('kumon.reviewAnswers')}
                </button>
              </div>
            ) : (
              <ResultPanel
                outcome={outcome}
                passedCount={passedCount}
                total={drills.length}
                failedCount={failedIds.length}
                editedCount={dirtyIds.size}
                needsRecheck={needsRecheck}
                onContinue={load}
                onRecheck={check}
                onScrollToFailed={scrollToFirstFailed}
                rechecking={submitting}
                level={sessionLevel}
                isOrientador={isOrientador}
                isReview={isReview}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function CountPicker({ count, setCount, disabled }: { count: number; setCount: (n: number) => void; disabled: boolean }) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col items-end gap-0.5">
      <span className="text-[10px] font-medium uppercase tracking-wide text-text-dim">{t('common.exercises')}</span>
      <div className="flex items-center gap-1 rounded-lg bg-surface-2 p-1">
        {COUNT_OPTIONS.map((n) => (
          <button
            key={n}
            type="button"
            disabled={disabled}
            onClick={() => setCount(n)}
            className={`rounded px-2.5 py-1 text-xs font-medium transition ${
              count === n ? 'bg-brand text-on-brand' : 'text-text-muted hover:text-text'
            } disabled:opacity-40`}
          >
            {n}
          </button>
        ))}
      </div>
    </div>
  );
}

function ResultPanel({ outcome, passedCount, total, failedCount, editedCount, needsRecheck, onContinue, onRecheck, onScrollToFailed, rechecking, level, isOrientador, isReview }: {
  outcome: SetSubmitResult | null;
  passedCount: number;
  total: number;
  failedCount: number;
  editedCount: number;
  needsRecheck: boolean;
  onContinue: () => void;
  onRecheck: () => void;
  onScrollToFailed: () => void;
  rechecking: boolean;
  level: string;
  isOrientador?: boolean;
  isReview?: boolean;
}) {
  const { t } = useI18n();
  if (!outcome) return null;
  const accSec = Math.round(outcome.accumulated_time_ms / 1000);
  const stdSec = Math.round(outcome.standard_ms / 1000);
  const backTo = isOrientador ? '/' : `/${level}/roadmap`;
  const backLabel = isOrientador ? t('kumon.backDashboard') : t('common.viewMap');

  const next = outcome.next_assignment;
  const nextTo = next
    ? orientadorAssignmentPath(next.plan_id, next.index, next.assignment)
    : null;
  const nextLabel = outcome.session_complete ? t('kumon.sessionComplete') : t('kumon.nextAssignment');
  const nextHref = nextTo ?? '/';

  if (isReview) {
    return (
      <div className="space-y-3 text-center">
        <p className={`text-xl font-bold ${passedCount === total ? 'text-emerald-700' : 'text-stone-800'}`}>
          {t('kumon.reviewSummary', { passed: passedCount, total })}
        </p>
        <p className="text-sm text-stone-600">{t('kumon.reviewNote')}</p>
        <Link to={`/${level}/roadmap`} className="inline-block rounded border-2 border-stone-900 bg-stone-900 px-6 py-2 text-sm font-bold text-[#fffef8] hover:bg-stone-700">
          {t('common.viewMap')}
        </Link>
      </div>
    );
  }

  if (outcome.outcome === 'mastered') {
    return (
      <div className="space-y-3 text-center">
        <p className="text-xl font-bold text-emerald-700">{t('kumon.setMastered')}</p>
        <p className="text-sm text-stone-600">
          {t('kumon.masteredDetail', { passed: passedCount, total, actual: fmt(accSec), standard: fmt(stdSec) })}
        </p>
        {outcome.needs_repeat && (
          <p className="text-xs text-amber-700">
            {t('kumon.repeatTomorrow', { pct: Math.round((outcome.first_attempt_accuracy ?? 0) * 100) })}
          </p>
        )}
        <div className="flex justify-center gap-2">
          {isOrientador ? (
            <Link
              to={nextHref}
              className="rounded border-2 border-stone-900 bg-stone-900 px-6 py-2 text-sm font-bold text-[#fffef8] hover:bg-stone-700"
            >
              {nextLabel}
            </Link>
          ) : (
            <button type="button" onClick={onContinue} className="rounded border-2 border-stone-900 bg-stone-900 px-6 py-2 text-sm font-bold text-[#fffef8] hover:bg-stone-700">
              {t('kumon.nextSet')}
            </button>
          )}
          <Link to={backTo} className="rounded border border-stone-500 px-5 py-2 text-sm font-medium text-stone-700 hover:bg-stone-100">
            {backLabel}
          </Link>
        </div>
      </div>
    );
  }

  if (outcome.outcome === 'too_slow') {
    return (
      <div className="space-y-3 text-center">
        <p className="text-xl font-bold text-amber-700">{t('kumon.tooSlow')}</p>
        <p className="text-sm text-stone-600">
          {t('kumon.tooSlowDetail', { actual: fmt(accSec), standard: fmt(stdSec) })}
          {outcome.repeat_scheduled_for
            ? ` ${t('kumon.repeatOnDate', { date: outcome.repeat_scheduled_for })}`
            : ` ${t('kumon.repeatOrientadorSchedule')}`}
        </p>
        {isOrientador ? (
          <Link
            to={nextHref}
            className="inline-block rounded border-2 border-stone-900 bg-stone-900 px-6 py-2 text-sm font-bold text-[#fffef8] hover:bg-stone-700"
          >
            {nextTo ? t('kumon.nextAssignment') : t('kumon.backDashboard')}
          </Link>
        ) : (
          <button type="button" onClick={onContinue} className="rounded border-2 border-stone-900 bg-stone-900 px-6 py-2 text-sm font-bold text-[#fffef8] hover:bg-stone-700">
            {t('kumon.repeatSet')}
          </button>
        )}
      </div>
    );
  }

  const missed = failedCount;
  return (
    <div className="space-y-3 text-center">
      <p className={`text-xl font-bold ${missed === 0 && editedCount === 0 ? 'text-emerald-700' : 'text-stone-800'}`}>
        {t('kumon.score', { passed: passedCount, total })}
      </p>
      <p className="text-sm text-stone-600">
        {missed > 0
          ? t('kumon.fixRed', { count: missed })
          : editedCount > 0
            ? t('kumon.recheckEdited')
            : t('kumon.partialProgress', { completed: outcome.completed, total: outcome.set_total })}
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        {missed > 0 && (
          <button type="button" onClick={onScrollToFailed} className="rounded border border-stone-500 px-5 py-2 text-sm font-medium text-stone-700 hover:bg-stone-100">
            {t('kumon.goFirstError')}
          </button>
        )}
        {needsRecheck && (
          <button
            type="button"
            onClick={() => void onRecheck()}
            disabled={rechecking}
            className="rounded border-2 border-stone-900 bg-stone-900 px-6 py-2 text-sm font-bold text-[#fffef8] hover:bg-stone-700 disabled:opacity-50"
          >
            {rechecking ? t('kumon.reviewing') : t('kumon.reviewAgain')}
          </button>
        )}
        <button type="button" onClick={onContinue} className="rounded border border-stone-500 px-5 py-2 text-sm font-medium text-stone-700 hover:bg-stone-100">
          {t('kumon.nextPages')}
        </button>
      </div>
    </div>
  );
}

function NonSetState({ data, level }: { data: SessionData; level: string }) {
  const { t } = useI18n();
  const stateType = data.target?.type || data.type;
  if (stateType === 'locked') {
    return (
      <div className="locked-card mx-auto max-w-lg text-center">
        <h1 className="page-title">{t('roadmap.lockedTitle')}</h1>
        <p className="mt-3 text-text-muted">{t('kumon.lockedDesc')}</p>
        <Link to={`/${level}/roadmap`} className="btn-secondary mt-4 inline-block">{t('common.viewMap')}</Link>
      </div>
    );
  }
  if (stateType === 'checkpoint') {
    const block = data.target?.block;
    return (
      <div className="card mx-auto max-w-lg text-center">
        <h1 className="page-title">{t('kumon.checkpointPending')}</h1>
        <p className="mt-3 text-text-muted">
          {t('kumon.checkpointDesc', { block: block ?? '' })}
        </p>
        <Link to={`/${level}/checkpoint/${block}`} className="btn-primary mt-4 inline-block">{t('common.goCheckpoint')}</Link>
      </div>
    );
  }
  if (stateType === 'exam') {
    return (
      <div className="card mx-auto max-w-lg text-center">
        <h1 className="page-title">{t('kumon.examTitle')}</h1>
        <p className="mt-3 text-text-muted">{t('kumon.examDesc')}</p>
        <Link to={`/${level}/exam`} className="btn-primary mt-4 inline-block">{t('common.goExam')}</Link>
      </div>
    );
  }
  return (
    <div className="alert-success mx-auto max-w-lg text-center">
      {t('kumon.levelComplete')} <Link to={`/${level}/roadmap`} className="underline">{t('common.viewMap')}</Link>
    </div>
  );
}
