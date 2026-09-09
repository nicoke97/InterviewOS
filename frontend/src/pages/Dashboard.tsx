import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, CartesianGrid,
} from 'recharts';
import { useCurriculumLevels } from '../lib/levels';
import { dashboardReasonHint } from '../lib/reasonContext';
import { api, type DailyPlanData, type OrientadorActiveResponse, type OrientadorConfig, type ReturnExamStatus } from '../lib/api';
import { assignmentLabel, orientadorAssignmentPath, reasonBadgeClass, reasonLabel } from '../lib/orientadorLabels';
import { sdeNextHref as nextSdeHref } from '../lib/sdePaths';
import { CodiMascot } from '../components/CodiMascot';
import { StudyCalendar } from '../components/StudyCalendar';
import { SdeTodayPanel } from '../components/SdeTodayPanel';
import { InterviewStoryCard } from '../components/StudyRitual';
import { buildCodiMessage, useCodi, type CodiData } from '../lib/codi';
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
  background: '#f7f9fc',
  border: '1px solid #c9d3e0',
  borderRadius: '12px',
  fontSize: '12px',
  color: '#0b1420',
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

// "Code now" follows the block marked Now — do not skip reading/debug to jump to cards.
function codeTarget(codi: CodiData, ctaTo: string | null): string {
  if (codi.returnExam?.needed) return '/return-exam';
  const sde = nextSdeHref(codi.sde?.assignments);
  if (sde) return sde;
  if (ctaTo && ctaTo !== '/') return ctaTo;
  if (codi.continuePath) return codi.continuePath;
  return '/sde/cards';
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

  if (!orientadorReady) {
    return <p className="text-text-muted">{t('dashboard.loadingSession')}</p>;
  }

  const sessionDate = plan?.date ?? new Date().toISOString().slice(0, 10);

  const statValue = (value: string | number) => (statsLoading && !stats ? '…' : String(value));

  return (
    <div className="space-y-10">
      <CodeHero />

      <SdeTodayPanel />

      <section className="space-y-4 rise-in rise-in-delay-2">
        <div>
          <p className="font-mono text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-text-dim">{t('dashboard.sectionProgressKicker')}</p>
          <h2 className="dash-section-title">{t('dashboard.sectionProgress')}</h2>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatTile label={t('dashboard.metricStreak')} value={statValue(streak?.current ?? 0)} hint={t('dashboard.metricStreakHint')} accent="streak" />
          <StatTile label={t('dashboard.metricActive')} value={statValue(Number(stats?.day_number ?? 0))} hint={t('dashboard.metricActiveHint')} />
          <StatTile label={t('dashboard.passRate')} value={statValue(`${stats?.pass_rate ?? 0}%`)} hint={t('dashboard.metricPassHint')} />
          <StatTile label={t('dashboard.pagesToday')} value={statValue(todayPages)} hint={t('dashboard.metricPagesHint')} />
        </div>
      </section>

      <section className="space-y-4 rise-in rise-in-delay-3">
        <div>
          <p className="font-mono text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-text-dim">{t('dashboard.sectionMonthKicker')}</p>
          <h2 className="dash-section-title">{t('dashboard.sectionMonth')}</h2>
        </div>
        <StudyCalendar />
      </section>

      {statsError && (
        <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
          <p className="text-text-muted">{t('dashboard.statsError')}</p>
          <button type="button" onClick={() => load()} className="text-brand">{t('common.retry')}</button>
        </div>
      )}

      <details className="group overflow-hidden rounded-2xl border border-border bg-surface/50">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-5 py-4 text-sm font-medium text-text [&::-webkit-details-marker]:hidden">
          <span>{t('dashboard.moreDetails')}</span>
          <svg className="h-4 w-4 shrink-0 text-text-dim transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </summary>

        <div className="space-y-12 border-t border-border p-5">
          {examNeeded && (
            <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3">
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
          )}

          {sessions.length === 0 && !examNeeded && (
            <p className="text-sm text-text-muted">
              {t(orientadorTrack === 'leetcodes' ? 'dashboard.emptyHintLeetcodes' : 'dashboard.emptyHint').split(/(\*\*.*?\*\*)/g).map((part, i) =>
                part.startsWith('**') && part.endsWith('**')
                  ? <strong key={i} className="font-medium text-text">{part.slice(2, -2)}</strong>
                  : part,
              )}
            </p>
          )}

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

      <section className="grid gap-10 lg:grid-cols-2">
        <div>
          <h2 className="dash-section-title">{t('dashboard.chartMinutesTitle')}</h2>
          <p className="mb-4 text-sm text-text-dim">{t('dashboard.chartMinutesSubtitle')}</p>
          {statsLoading && !stats ? (
            <p className="py-16 text-sm text-text-muted">{t('dashboard.chartLoading')}</p>
          ) : (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={minutesChart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#c9d3e0" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#6b7c90' }} axisLine={false} tickLine={false} />
              <YAxis stroke="#6b7c90" axisLine={false} tickLine={false} tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={chartTooltip} />
              <Line type="monotone" dataKey="minutes" stroke="#2563eb" strokeWidth={2} dot={false} />
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
              <CartesianGrid strokeDasharray="3 3" stroke="#c9d3e0" vertical={false} />
              <XAxis dataKey="block_title" tick={{ fontSize: 9, fill: '#6b7c90' }} axisLine={false} tickLine={false} />
              <YAxis stroke="#6b7c90" domain={[0, 100]} axisLine={false} tickLine={false} tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={chartTooltip} />
              <Bar dataKey="accuracy" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          )}
        </div>
      </section>
        </div>
      </details>
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
                className={`rounded-lg px-3 py-1.5 text-sm transition ${
                  selected
                    ? 'bg-brand text-on-brand'
                    : 'border border-border bg-surface text-text-muted hover:text-text'
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
              className={`rounded-lg px-3 py-1.5 text-sm transition ${
                minutes === p ? 'bg-brand text-on-brand' : 'border border-border bg-surface text-text-muted hover:text-text'
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

function StatTile({
  label,
  value,
  hint,
  accent,
}: {
  label: string;
  value: string;
  hint: string;
  accent?: 'streak';
}) {
  return (
    <div className={`stat-tile ${accent === 'streak' ? 'stat-tile-streak' : ''}`}>
      <p className="text-xs font-medium text-text-dim">{label}</p>
      <p className="stat-tile-value tabular-nums">{value}</p>
      <p className="mt-1 text-xs text-text-dim">{hint}</p>
    </div>
  );
}

// Hero: the one action that matters — arrive, hit "Code now", start coding.
function CodeHero() {
  const { t } = useI18n();
  const codi = useCodi();
  const msg = buildCodiMessage(codi, t);
  const target = codeTarget(codi, msg.ctaTo);
  const dayDone = Boolean(codi.sde?.complete) && !codi.returnExam?.needed;

  return (
    <div className="code-hero rise-in flex flex-col gap-5 sm:flex-row sm:items-center">
      <CodiMascot mood={msg.mood} size={92} className="relative z-[1] shrink-0 self-center sm:self-auto" />
      <div className="relative z-[1] min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="code-hero-kicker">{t('codi.name')}</p>
          {codi.streakCurrent > 0 && (
            <span className="rounded-md bg-[#ff6b35]/20 px-2 py-0.5 text-xs font-semibold text-[#ffb089]">
              {t('codi.streakBadge', { n: codi.streakCurrent })}
            </span>
          )}
        </div>
        <p className="code-hero-title">{msg.headline}</p>
        <p className="code-hero-sub">
          {dayDone ? t('dashboard.codeDone') : (msg.subline || t('dashboard.codeReady'))}
        </p>
      </div>
      <Link
        to={target}
        className="code-hero-cta relative z-[1] w-full shrink-0 sm:w-auto"
      >
        {t('dashboard.codeNow')}
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.4}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14M13 6l6 6-6 6" />
        </svg>
      </Link>
    </div>
  );
}

