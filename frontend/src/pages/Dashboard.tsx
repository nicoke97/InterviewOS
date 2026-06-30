import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, CartesianGrid,
} from 'recharts';
import { continueStudyPath } from '../lib/continueStudy';
import { useCurriculumLevels } from '../lib/levels';
import { dashboardReasonHint } from '../lib/reasonContext';
import { api, type DailyPlanData, type OrientadorActiveResponse, type OrientadorConfig, type ReturnExamStatus } from '../lib/api';
import { assignmentLabel, orientadorAssignmentPath, reasonBadgeClass, reasonLabel } from '../lib/orientadorLabels';
import { StudyCalendar } from '../components/StudyCalendar';
import { CodiMascot } from '../components/CodiMascot';
import { InterviewStoryCard } from '../components/StudyRitual';
import { buildCodiMessage, useCodi } from '../lib/codi';
import { useI18n } from '../i18n/context';
import {
  STUDY_LANG_LABEL,
  defaultMinutesForTrack,
  languageOfDay,
  readOrientadorTrack,
  writeOrientadorTrack,
  type OrientadorTrack,
} from '../lib/studySession';

const chartTooltip = {
  background: '#ffffff',
  border: '1px solid #ddd6f3',
  borderRadius: '12px',
  fontSize: '12px',
  color: '#242746',
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

function formatDate(iso: string, dateLocale: string): string {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString(dateLocale, {
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
    setMinutes(o.config?.default_minutes ?? 15);
  }
}

export function Dashboard() {
  const { t, locale } = useI18n();
  const location = useLocation();
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);
  const [plan, setPlan] = useState<DailyPlanData | null>(null);
  const [sessions, setSessions] = useState<DailyPlanData[]>([]);
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
  const [planActive, setPlanActive] = useState(false);
  const [config, setConfig] = useState<OrientadorConfig | null>(null);
  const [orientadorTrack, setOrientadorTrack] = useState<OrientadorTrack>(readOrientadorTrack);
  const [minutes, setMinutes] = useState(() => defaultMinutesForTrack(readOrientadorTrack()));
  const [calculating, setCalculating] = useState(false);
  const [orientadorReady, setOrientadorReady] = useState(false);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState(false);
  const [calcError, setCalcError] = useState('');
  const [returnExam, setReturnExam] = useState<ReturnExamStatus | null>(null);
  const levels = useCurriculumLevels();

  const load = useCallback((track: OrientadorTrack = orientadorTrack) => {
    void locale;
    setOrientadorReady(false);
    setStatsLoading(true);
    setStatsError(false);

    api.orientadorActive(track)
      .then((o) => {
        applyOrientadorResponse(
          o, setConfig, setSessions, setPlan, setPlanActive, setMinutes, setSelectedPlanId,
        );
        if (o.return_exam) setReturnExam(o.return_exam);
        setOrientadorReady(true);
      })
      .catch(() => setOrientadorReady(true));

    api.returnExamStatus()
      .then(setReturnExam)
      .catch(() => {});

    api.stats()
      .then((s) => {
        setStats(s);
        const re = s.return_exam as ReturnExamStatus | undefined;
        if (re) setReturnExam(re);
      })
      .catch(() => setStatsError(true))
      .finally(() => setStatsLoading(false));
  }, [orientadorTrack, locale]);

  useEffect(() => {
    if (location.pathname === '/') load(orientadorTrack);
  }, [load, location.pathname, orientadorTrack]);

  useEffect(() => {
    const refresh = () => {
      if (document.visibilityState === 'visible' && location.pathname === '/') load(orientadorTrack);
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
        track: orientadorTrack,
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
      const msg = err instanceof Error ? err.message : t('dashboard.calcErrorDefault');
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
  const presets = config?.minute_presets ?? (orientadorTrack === 'leetcodes' ? [45, 60, 90] : [15, 20, 30, 40, 60]);
  const examNeeded = Boolean(returnExam?.needed);
  const continuePath = examNeeded ? '/return-exam' : continueStudyPath(planActive ? plan : null);
  const nextPending = plan?.assignments.find((a) => !a.completed);

  if (!orientadorReady) {
    return <p className="text-text-muted">{t('dashboard.loadingSession')}</p>;
  }

  const sessionDate = plan?.date ?? new Date().toISOString().slice(0, 10);

  const statValue = (value: string | number) => (statsLoading && !stats ? '…' : String(value));

  return (
    <div className="space-y-12">
      <CodiGreeting />

      <div className="flex flex-wrap items-end justify-between gap-6">
        <div>
          <h1 className="page-title">{t('dashboard.title')}</h1>
          <p className="page-subtitle">{t('dashboard.subtitle')}</p>
        </div>
        <dl className="flex flex-wrap gap-x-8 gap-y-3 text-sm">
          <div>
            <dt className="text-text-dim">{t('dashboard.metricStreak')}</dt>
            <dd className="mt-0.5 tabular-nums text-text">{statValue(streak?.current ?? 0)}</dd>
          </div>
          <div>
            <dt className="text-text-dim">{t('dashboard.passRate')}</dt>
            <dd className="mt-0.5 tabular-nums text-text">{statValue(`${stats?.pass_rate ?? 0}%`)}</dd>
          </div>
          <div>
            <dt className="text-text-dim">{t('dashboard.metricActive')}</dt>
            <dd className="mt-0.5 tabular-nums text-text">{statValue(Number(stats?.day_number ?? 0))}</dd>
          </div>
          <div>
            <dt className="text-text-dim">{t('dashboard.pagesToday')}</dt>
            <dd className="mt-0.5 tabular-nums text-text">{statValue(todayPages)}</dd>
          </div>
        </dl>
      </div>

      {examNeeded ? (
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-amber-500/30 pb-8">
          <div>
            <p className="text-base font-medium text-text">{t('dashboard.returnExamTitle')}</p>
            <p className="mt-1 text-sm text-text-muted">
              {t('dashboard.returnExamDesc', { days: returnExam?.inactivity_days ?? returnExam?.threshold_days ?? 3 })}
            </p>
          </div>
          <Link to="/return-exam" className="btn-primary shrink-0">
            {t('dashboard.returnExamStart')}
          </Link>
        </div>
      ) : continuePath && nextPending && plan?.status === 'active' ? (
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-8">
          <div>
            <p className="text-base font-medium text-text">{assignmentLabel(nextPending, locale)}</p>
            <p className="mt-1 text-sm text-text-muted">
              {dashboardReasonHint(nextPending, locale) ?? reasonLabel(nextPending.reason, locale, nextPending.type)}
            </p>
          </div>
          <Link to={continuePath} className="btn-primary shrink-0">
            {t('dashboard.startNow')}
          </Link>
        </div>
      ) : sessions.length === 0 ? (
        <p className="text-sm text-text-muted">
          {t(orientadorTrack === 'leetcodes' ? 'dashboard.emptyHintLeetcodes' : 'dashboard.emptyHint').split(/(\*\*.*?\*\*)/g).map((part, i) =>
            part.startsWith('**') && part.endsWith('**')
              ? <strong key={i} className="font-medium text-text">{part.slice(2, -2)}</strong>
              : part,
          )}
        </p>
      ) : null}

      <div className="space-y-6">
        <div className="flex gap-6 border-b border-border text-sm">
          {(['leetcodes', 'python'] as const).map((trackKey) => (
            <button
              key={trackKey}
              type="button"
              onClick={() => {
                writeOrientadorTrack(trackKey);
                setOrientadorTrack(trackKey);
                setMinutes(defaultMinutesForTrack(trackKey));
              }}
              className={`-mb-px border-b-2 pb-2 transition ${
                orientadorTrack === trackKey
                  ? 'border-brand text-text'
                  : 'border-transparent text-text-muted hover:text-text'
              }`}
            >
              {trackKey === 'python' ? t('dashboard.trackPython') : t('common.leetcodes')}
            </button>
          ))}
        </div>

        <OrientadorCard
          date={sessionDate}
          track={orientadorTrack}
          minutes={minutes}
          setMinutes={setMinutes}
          presets={presets}
          minMinutes={config?.min_minutes ?? (orientadorTrack === 'leetcodes' ? 30 : 15)}
          maxMinutes={config?.max_minutes ?? 90}
          sessions={sessions}
          selectedPlanId={selectedPlanId}
          onSelectSession={selectSession}
          plan={planActive ? plan : null}
          calculating={calculating}
          calcError={calcError}
          onCalculate={calculate}
          examNeeded={examNeeded}
        />
      </div>

      {statsError && (
        <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
          <p className="text-text-muted">{t('dashboard.statsError')}</p>
          <button type="button" onClick={() => load()} className="text-brand">{t('common.retry')}</button>
        </div>
      )}

      <div className="grid items-start gap-12 lg:grid-cols-2">
        <section>
          <StudyCalendar />
        </section>

        <section>
          <h2 className="dash-section-title mb-4">{t('common.levels')}</h2>
          <div className="divide-y divide-border">
            {levels.map((lvl) => {
              const u = unlocks[lvl.id];
              const mastered = u?.sets_mastered ?? 0;
              const totalSets = u?.total_sets ?? 20;
              const pagesDone = u?.pages_completed ?? 0;
              const totalPages = u?.total_pages ?? 200;
              const pct = u?.progress_pct ?? (totalPages ? Math.round((pagesDone / totalPages) * 100) : 0);
              const subtitle = lvl.title.replace(/^Level \w+ — /, '').replace(/^Nivel \w+ — /, '');
              return (
                <Link
                  key={lvl.id}
                  to={`/${lvl.id}/roadmap`}
                  className="flex items-center gap-4 py-3.5 first:pt-0 last:pb-0"
                >
                  <span className="w-5 shrink-0 text-sm text-text-dim">{lvl.letter}</span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-baseline justify-between gap-3">
                      <p className="truncate text-sm text-text">{subtitle}</p>
                      <span className="shrink-0 text-sm tabular-nums text-text-muted">{pct}%</span>
                    </div>
                    <p className="mt-0.5 text-xs text-text-dim">
                      {t('dashboard.levelsPages', { pagesDone, totalPages })}
                      {' · '}
                      {t('dashboard.levelsSets', { mastered, totalSets })}
                    </p>
                    <div className="progress-bar mt-2">
                      <div className="progress-fill" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </section>
      </div>

      <section className="grid gap-10 lg:grid-cols-2">
        <div>
          <h2 className="dash-section-title">{t('dashboard.chartMinutesTitle')}</h2>
          <p className="mb-4 text-sm text-text-dim">{t('dashboard.chartMinutesSubtitle')}</p>
          {statsLoading && !stats ? (
            <p className="py-16 text-sm text-text-muted">{t('dashboard.chartLoading')}</p>
          ) : (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={minutesChart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eceaf3" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#8b8eaa' }} axisLine={false} tickLine={false} />
              <YAxis stroke="#8b8eaa" axisLine={false} tickLine={false} tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={chartTooltip} />
              <Line type="monotone" dataKey="minutes" stroke="#7e4bde" strokeWidth={1.75} dot={false} />
            </LineChart>
          </ResponsiveContainer>
          )}
        </div>
        <div>
          <h2 className="dash-section-title">{t('dashboard.chartBlocksTitle')}</h2>
          <p className="mb-4 text-sm text-text-dim">{t('dashboard.chartBlocksSubtitle')}</p>
          {statsLoading && !stats ? (
            <p className="py-16 text-sm text-text-muted">{t('dashboard.chartLoading')}</p>
          ) : (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={blockAccuracy}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eceaf3" vertical={false} />
              <XAxis dataKey="block_title" tick={{ fontSize: 9, fill: '#8b8eaa' }} axisLine={false} tickLine={false} />
              <YAxis stroke="#8b8eaa" domain={[0, 100]} axisLine={false} tickLine={false} tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={chartTooltip} />
              <Bar dataKey="accuracy" fill="#7e4bde" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          )}
        </div>
      </section>
    </div>
  );
}

function OrientadorCard({
  date,
  track,
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
  examNeeded,
}: {
  date: string;
  track: 'python' | 'leetcodes';
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
  examNeeded?: boolean;
}) {
  const { t, locale, dateLocale } = useI18n();
  const nextPending = plan?.assignments.find((a) => !a.completed);
  const allDone = plan && plan.total_count > 0 && plan.completed_count >= plan.total_count;
  const overProblemCap = Boolean(
    plan
    && track === 'leetcodes'
    && plan.status === 'active'
    && plan.assignments.length > (plan.config?.max_problems_per_session ?? 1),
  );
  const planStale = Boolean(
    plan
    && plan.status === 'active'
    && (Number(minutes) !== Number(plan.minutes_budget) || overProblemCap),
  );
  const hasActiveSession = sessions.some((s) => s.status === 'active');
  const allSessionsDone = sessions.length > 0 && sessions.every((s) => s.status === 'completed');
  const isViewingActive = plan?.status === 'active';
  const overBudget = plan != null && plan.estimated_minutes > plan.minutes_budget;
  const showFirstCalc = sessions.length === 0;
  const showRecalc = isViewingActive && planStale;
  const showAdd = allSessionsDone && !hasActiveSession;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-text">
            {t('dashboard.sessionTitle', {
              track: track === 'leetcodes' ? t('common.leetcodes') : 'Python',
              date: formatDate(date, dateLocale),
            })}
          </h2>
          <p className="text-sm text-text-muted">
            {track === 'leetcodes' ? t('dashboard.descLeetcodes') : t('dashboard.descPython')}
          </p>
          {track === 'leetcodes' && (
            <p className="mt-2 text-xs text-text-dim">
              {t('studySession.langToday', { lang: STUDY_LANG_LABEL[languageOfDay()] })}
            </p>
          )}
        </div>
        {plan && plan.total_count > 0 && (
          <span className="badge-brand">
            {plan.completed_count}/{plan.total_count}
          </span>
        )}
      </div>

      {track === 'leetcodes' && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-text">{t('studySession.storiesTitle')}</h3>
          <InterviewStoryCard />
        </div>
      )}

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
                className={`rounded-full px-3 py-1 text-sm transition ${
                  selected
                    ? 'bg-brand text-on-brand'
                    : 'text-text-muted hover:text-text'
                }`}
              >
                {t('dashboard.sessionTab', { n: s.session_number })}
                {done ? t('dashboard.sessionCompleted') : t('dashboard.sessionProgress', { done: s.completed_count, total: s.total_count })}
                {' · '}
                {t('dashboard.minutesN', { n: s.minutes_budget })}
              </button>
            );
          })}
        </div>
      )}

      {examNeeded && (
        <p className="text-sm text-amber-700">{t('dashboard.returnExamBlockCalc')}</p>
      )}

      {(isViewingActive || allSessionsDone || sessions.length === 0) && !examNeeded && (
      <div className="space-y-3">
        <p className="text-sm font-medium text-text">{t('dashboard.timeAvailable')}</p>
        <div className="flex flex-wrap items-center gap-2">
          {presets.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setMinutes(p)}
              className={`rounded-full px-3 py-1 text-sm transition ${
                minutes === p ? 'bg-brand text-on-brand' : 'text-text-muted hover:text-text'
              }`}
            >
              {t('dashboard.minutesN', { n: p })}
            </button>
          ))}
          <label className="flex items-center gap-2 text-sm text-text-muted">
            <span>{t('dashboard.other')}</span>
            <input
              type="number"
              min={minMinutes}
              max={maxMinutes}
              value={minutes}
              onChange={(e) => setMinutes(Number(e.target.value))}
              className="w-16 border-b border-border bg-transparent px-1 py-1 text-text outline-none"
            />
            <span>{t('common.min')}</span>
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
              {calculating ? t('dashboard.calculating') : showFirstCalc ? t('dashboard.calcFirst') : t('dashboard.calcRecalc')}
            </button>
          )}
          {showAdd && (
            <button
              type="button"
              onClick={() => onCalculate({ newSession: true })}
              disabled={calculating}
              className="btn-primary"
            >
              {calculating ? t('dashboard.calculating') : t('dashboard.calcAdd')}
            </button>
          )}
        </div>
        {calcError && (
          <p className="text-sm text-red-600">
            {t('dashboard.calcErrorHint', { msg: calcError })}
          </p>
        )}
        {planStale && isViewingActive && (
          <p className="text-xs text-amber-600">
            {overProblemCap
              ? t('dashboard.staleTooManyProblems')
              : minutes > (plan?.minutes_budget ?? 0)
                ? t('dashboard.staleMoreTime')
                : overBudget
                  ? t('dashboard.staleOverBudget')
                  : t('dashboard.staleLessTime')}
          </p>
        )}
      </div>
      )}

      {plan && plan.assignments.length === 0 && (
        <p className="text-sm text-text-muted">
          {t('dashboard.noActivities', { min: plan.minutes_budget })}
        </p>
      )}

      {plan && plan.assignments.length > 0 && (
        <div className="space-y-3 border-t border-border pt-4">
          <p className="text-sm text-text-muted">
            {t('dashboard.sessionTab', { n: plan.session_number })}
            {' · '}
            {t('dashboard.planSummary', { n: plan.session_number, budget: plan.minutes_budget, estimated: plan.estimated_minutes }).split('**').map((part, i) =>
              i % 2 === 1 ? <span key={i} className="font-medium text-text">{part}</span> : part,
            )}
            {plan.status === 'completed' && (
              <span className="ml-2 text-emerald-700">{t('dashboard.planCompleted')}</span>
            )}
          </p>

          {planStale && isViewingActive && (
            <p className="text-xs text-amber-600">
              {t('dashboard.staleBanner', { min: plan.minutes_budget })}
            </p>
          )}

          {allDone ? (
            <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700">
              {t('dashboard.allDone')}
              {!hasActiveSession && sessions.length > 0 && (
                <span> {t('dashboard.allDoneAddHint')}</span>
              )}
            </div>
          ) : nextPending && isViewingActive ? (
            <div className="py-1">
              <p className="text-sm text-text-dim">{t('common.next')}</p>
              <p className="mt-1 text-base font-medium text-text">{assignmentLabel(nextPending, locale)}</p>
              <p className="mt-1 text-sm text-text-muted">
                {dashboardReasonHint(nextPending, locale) ?? reasonLabel(nextPending.reason, locale, nextPending.type) ?? nextPending.reason}
                {nextPending.estimated_minutes ? ` · ${t('dashboard.estimatedMin', { n: Math.round(nextPending.estimated_minutes) })}` : ''}
              </p>
              <Link
                to={orientadorAssignmentPath(
                  plan.id,
                  nextPending.index ?? plan.assignments.indexOf(nextPending),
                  nextPending,
                )}
                className="btn-primary mt-4 inline-block w-full text-center sm:w-auto"
              >
                {t('common.start')}
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
                      {reasonLabel(a.reason, locale, a.type)}
                    </span>
                    {' · '}
                    {assignmentLabel(a, locale)}
                    {!a.completed && dashboardReasonHint(a, locale) && (
                      <span className="block text-xs text-text-dim">{dashboardReasonHint(a, locale)}</span>
                    )}
                  </span>
                  <span className="shrink-0 text-xs">
                    {a.completed ? t('common.done') : t('dashboard.estimatedMin', { n: Math.round(a.estimated_minutes ?? 0) })}
                  </span>
                </li>
              ))}
            </ul>
          )}
          <Link to="/orientador" className="text-sm text-brand hover:underline">
            {t('dashboard.whyLink')}
          </Link>
        </div>
      )}
    </div>
  );
}

function CodiGreeting() {
  const { t } = useI18n();
  const codi = useCodi();
  const msg = buildCodiMessage(codi, t);

  return (
    <div className="flex items-center gap-4 rounded-2xl border border-brand/20 bg-brand/5 p-4 sm:p-5">
      <CodiMascot mood={msg.mood} size={76} className="shrink-0" />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="text-sm font-semibold text-brand">{t('codi.name')}</p>
          {codi.streakCurrent > 0 && (
            <span className="badge-brand">{t('codi.streakBadge', { n: codi.streakCurrent })}</span>
          )}
        </div>
        <p className="mt-0.5 text-base font-medium text-text">{msg.headline}</p>
        <p className="mt-0.5 text-sm text-text-muted">{msg.subline}</p>
      </div>
      {msg.ctaLabel && msg.ctaTo && (
        <Link to={msg.ctaTo} className="btn-primary shrink-0 max-sm:hidden">
          {msg.ctaLabel}
        </Link>
      )}
    </div>
  );
}

