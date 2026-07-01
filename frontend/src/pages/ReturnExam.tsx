import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, type DrillResult, type KumonPage, type ReturnExamFailedSet, type ReturnExamPayload } from '../lib/api';
import { formatSetLevelLabel, resolveDisplaySetNumber } from '../lib/setLabels';
import { clearSessionDraft, loadSessionDraft, saveSessionDraft } from '../lib/sessionDraft';
import { KumonProblem } from '../components/KumonProblem';
import { SessionTimer, useSessionTimer } from '../components/Timer';
import { useI18n } from '../i18n/context';

const DRAFT_KEY = 'return-exam';

export function ReturnExamPage() {
  const { t, locale } = useI18n();
  const [exam, setExam] = useState<ReturnExamPayload | null>(null);
  const [needed, setNeeded] = useState(true);
  const [inactivityDays, setInactivityDays] = useState(0);
  const [lastActive, setLastActive] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [results, setResults] = useState<Record<string, DrillResult>>({});
  const [failedSets, setFailedSets] = useState<ReturnExamFailedSet[]>([]);
  const [checked, setChecked] = useState(false);
  const [passedAll, setPassedAll] = useState(false);
  const [passedCount, setPassedCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [highlightEmpty, setHighlightEmpty] = useState(false);
  const [draftBanner, setDraftBanner] = useState(false);

  const { running, start, stop, onTick, seconds, setElapsed, secondsRef } = useSessionTimer('study');
  const timerStartedRef = useRef(false);

  const load = useCallback(async () => {
    void locale;
    setLoading(true);
    setLoadError(null);
    await stop();
    timerStartedRef.current = false;
    try {
      const data = await api.returnExam();
      setNeeded(data.needed);
      setInactivityDays(data.inactivity_days);
      setLastActive(data.last_active_date);
      if (!data.exam) {
        setExam(null);
        return;
      }
      const draft = loadSessionDraft(DRAFT_KEY);
      const init: Record<string, string> = {};
      (data.exam.drills || []).forEach((p) => {
        init[p.id] = draft?.answers[p.id] ?? '';
      });
      setExam(data.exam);
      setAnswers(init);
      if (draft && Object.values(init).some((v) => v.length > 0)) {
        setDraftBanner(true);
        setElapsed(draft.seconds);
        if (draft.seconds > 0 || Object.values(init).some((v) => v.length > 0)) {
          timerStartedRef.current = true;
          void start(draft.seconds);
        }
      } else {
        setElapsed(0);
        clearSessionDraft(DRAFT_KEY);
      }
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : t('returnExam.errorLoad'));
    } finally {
      setLoading(false);
    }
  }, [stop, start, setElapsed, t, locale]);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => () => { void stop(); }, [stop]);

  useEffect(() => {
    if (!exam || checked) return;
    saveSessionDraft(DRAFT_KEY, { answers, seconds: secondsRef.current, count: exam.drills.length });
  }, [answers, seconds, exam, checked, secondsRef]);

  const ensureTimer = useCallback(() => {
    if (!timerStartedRef.current) {
      timerStartedRef.current = true;
      void start(secondsRef.current);
    }
  }, [start, secondsRef]);

  const updateAnswer = (id: string, code: string) => {
    setAnswers((prev) => ({ ...prev, [id]: code }));
    if (code.length > 0) ensureTimer();
  };

  const submit = async () => {
    if (!exam) return;
    const empty = exam.drills.filter((d) => !(answers[d.id] || '').trim());
    if (empty.length > 0) {
      setHighlightEmpty(true);
      setSubmitError(t('kumon.emptyAnswers', { count: empty.length }));
      empty[0] && document.querySelector(`[data-drill-id="${empty[0].id}"]`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }
    setSubmitting(true);
    setSubmitError(null);
    setHighlightEmpty(false);
    try {
      const res = await api.returnExamSubmit(
        exam.drills.map((d) => ({ exercise_id: d.id, code: answers[d.id] || '' })),
      );
      setResults(res.results);
      setFailedSets(res.failed_sets);
      setPassedCount(res.passed_count);
      setPassedAll(res.passed);
      setChecked(true);
      setNeeded(false);
      clearSessionDraft(DRAFT_KEY);
      void stop();
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : t('returnExam.errorSubmit'));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading && !exam) {
    return <p className="text-text-muted">{t('returnExam.loading')}</p>;
  }

  if (loadError) {
    return (
      <div className="card mx-auto max-w-lg space-y-3 text-center">
        <h2 className="page-title">{t('returnExam.errorLoad')}</h2>
        <p className="text-sm text-text-muted">{loadError}</p>
        <button type="button" onClick={() => void load()} className="btn-secondary">{t('common.retry')}</button>
      </div>
    );
  }

  if (!needed && !checked) {
    return (
      <div className="card mx-auto max-w-lg space-y-3 text-center">
        <h1 className="page-title">{t('returnExam.title')}</h1>
        <p className="text-sm text-text-muted">{t('returnExam.notNeeded')}</p>
        <Link to="/" className="btn-primary inline-block">{t('returnExam.backHome')}</Link>
      </div>
    );
  }

  if (!exam) return null;

  const drills = exam.drills || [];
  const itemById = new Map((exam.items || []).map((it) => [it.exercise_id, it]));

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="page-title">{t('returnExam.title')}</h1>
          <p className="mt-1 text-sm text-text-muted">
            {t('returnExam.subtitle', { count: drills.length, days: inactivityDays || exam.inactivity_days })}
          </p>
          {lastActive && (
            <p className="mt-1 text-xs text-text-dim">{t('returnExam.inactivityNote', { date: lastActive })}</p>
          )}
        </div>
        <div className="timer-pill">
          <SessionTimer running={running} seconds={seconds} standardSeconds={0} onTick={onTick} />
        </div>
      </div>

      <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-sm text-text-muted">
        {t('returnExam.instructions', { n: drills.length })}
      </div>

      {draftBanner && !checked && (
        <div className="rounded-lg border border-sky-500/30 bg-sky-500/5 px-4 py-2 text-sm text-sky-800">
          {t('kumon.draftRestored')}
          <button
            type="button"
            className="ml-2 underline"
            onClick={() => {
              clearSessionDraft(DRAFT_KEY);
              setDraftBanner(false);
              void load();
            }}
          >
            {t('kumon.startOver')}
          </button>
        </div>
      )}

      <div className="mx-auto max-w-3xl rounded-sm border border-stone-400 bg-stone-200 p-1 shadow-2xl">
        <div className="bg-[#fffef8] px-5 py-5 text-stone-900 sm:px-8 sm:py-6">
          <div className="mb-4 border-b-2 border-stone-800 pb-3">
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-stone-500">Codenda</p>
            <h2 className="text-xl font-bold tracking-tight text-stone-900">{t('returnExam.title')}</h2>
          </div>

          <div className="space-y-5">
            {drills.map((page: KumonPage, i: number) => {
              const meta = itemById.get(page.id);
              const displaySet = resolveDisplaySetNumber(meta?.set_number ?? page.set, meta?.display_set_number ?? page.display_set_number);
              const level = (meta?.level || page.level || 'a').toLowerCase();
              const reviewStatus = !checked
                ? 'pending'
                : results[page.id]?.passed
                  ? 'passed'
                  : results[page.id]
                    ? 'failed'
                    : 'pending';
              return (
                <div key={page.id} data-drill-id={page.id}>
                  <p className="mb-1.5 text-[11px] font-medium uppercase tracking-wide text-stone-500">
                    {t('returnExam.drillMeta', {
                      set: displaySet,
                      level: level.toUpperCase(),
                      title: meta?.set_title || page.set_title || '',
                    })}
                  </p>
                  <KumonProblem
                    number={i + 1}
                    pageLabel={page.id}
                    drill={page}
                    value={answers[page.id] || ''}
                    onChange={(code) => updateAnswer(page.id, code)}
                    result={results[page.id]}
                    reviewStatus={reviewStatus}
                    focusMode={!checked}
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
                  {submitError && <p className="text-xs text-red-700">{submitError}</p>}
                </div>
                <button
                  type="button"
                  onClick={() => void submit()}
                  disabled={submitting}
                  className="rounded border-2 border-stone-900 bg-stone-900 px-8 py-2.5 text-sm font-bold text-[#fffef8] transition hover:bg-stone-700 disabled:opacity-50"
                >
                  {submitting ? t('returnExam.submitting') : t('returnExam.submit')}
                </button>
              </div>
            ) : (
              <div className="space-y-4 text-center">
                {passedAll ? (
                  <>
                    <p className="text-xl font-bold text-emerald-700">{t('returnExam.passedTitle')}</p>
                    <p className="text-sm text-stone-600">{t('returnExam.passedDesc', { passed: passedCount, total: drills.length })}</p>
                  </>
                ) : (
                  <>
                    <p className="text-xl font-bold text-amber-700">{t('returnExam.failedTitle')}</p>
                    <p className="text-sm text-stone-600">{t('returnExam.failedDesc', { passed: passedCount, total: drills.length })}</p>
                    <ul className="space-y-2 text-left">
                      {failedSets.map((s) => {
                        const displaySet = resolveDisplaySetNumber(s.set_number, s.display_set_number);
                        return (
                          <li key={`${s.level}-${s.set_number}`}>
                            <Link
                              to={`/${s.level}/roadmap`}
                              className="text-sm font-medium text-stone-800 underline-offset-2 hover:underline"
                            >
                              {t('returnExam.repeatSet', { set: displaySet, level: s.level.toUpperCase() })}
                              {s.set_title ? ` — ${s.set_title}` : ''}
                            </Link>
                            <p className="text-xs text-stone-500">{formatSetLevelLabel(s.set_number, s.level, s.display_set_number, locale)}</p>
                          </li>
                        );
                      })}
                    </ul>
                  </>
                )}
                <Link
                  to="/"
                  className="inline-block rounded border-2 border-stone-900 bg-stone-900 px-6 py-2 text-sm font-bold text-[#fffef8] hover:bg-stone-700"
                >
                  {t('returnExam.backHome')}
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
