import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { api, type DailyPlanData, type OrientadorAssignment, type ReturnExamStatus, type SdeToday } from './api';
import { continueStudyPath } from './continueStudy';
import { readOrientadorTrack } from './studySession';
import type { CodiMood } from '../components/CodiMascot';
import { useI18n } from '../i18n/context';

interface LevelSummary {
  id: string;
  mastered: number;
  totalSets: number;
  pagesDone: number;
  totalPages: number;
  pct: number;
}

export interface CodiData {
  loading: boolean;
  returnExam: ReturnExamStatus | null;
  streakCurrent: number;
  streakBest: number;
  passRate: number;
  activeDays: number;
  todayPages: number;
  plan: DailyPlanData | null;
  nextAssignment: OrientadorAssignment | null;
  planAllDone: boolean;
  continuePath: string | null;
  level: LevelSummary | null;
  totalPagesDone: number;
  sde: SdeToday | null;
  refresh: () => void;
}

interface RawLevelProgress {
  sets_mastered?: number;
  total_sets?: number;
  pages_completed?: number;
  total_pages?: number;
  progress_pct?: number;
}

const CodiContext = createContext<CodiData | null>(null);

function pickActiveLevel(unlocks: Record<string, RawLevelProgress>): LevelSummary | null {
  const ids = Object.keys(unlocks).sort();
  if (ids.length === 0) return null;
  const toSummary = (id: string): LevelSummary => {
    const u = unlocks[id] ?? {};
    const totalPages = u.total_pages ?? 200;
    const pagesDone = u.pages_completed ?? 0;
    return {
      id,
      mastered: u.sets_mastered ?? 0,
      totalSets: u.total_sets ?? 20,
      pagesDone,
      totalPages,
      pct: u.progress_pct ?? (totalPages ? Math.round((pagesDone / totalPages) * 100) : 0),
    };
  };
  // First in-progress level (has some progress but not finished).
  const started = ids.map(toSummary).filter((l) => l.pct > 0 && l.pct < 100);
  if (started.length) return started[started.length - 1];
  // Otherwise the first not-yet-complete level.
  const unfinished = ids.map(toSummary).find((l) => l.pct < 100);
  return unfinished ?? toSummary(ids[ids.length - 1]);
}

export function CodiProvider({ children }: { children: ReactNode }) {
  const { locale } = useI18n();
  const [loading, setLoading] = useState(true);
  const [returnExam, setReturnExam] = useState<ReturnExamStatus | null>(null);
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);
  const [plan, setPlan] = useState<DailyPlanData | null>(null);
  const [sde, setSde] = useState<SdeToday | null>(null);

  const refresh = useCallback(() => {
    void locale;
    setLoading(true);
    Promise.allSettled([api.stats(), api.orientadorActive(readOrientadorTrack()), api.sdeToday()])
      .then(([statsRes, orientadorRes, sdeRes]) => {
        if (statsRes.status === 'fulfilled') {
          setStats(statsRes.value);
          const re = statsRes.value.return_exam as ReturnExamStatus | undefined;
          if (re) setReturnExam(re);
        }
        if (orientadorRes.status === 'fulfilled') {
          const o = orientadorRes.value;
          if (o.return_exam) setReturnExam(o.return_exam);
          const list = o.sessions ?? [];
          const active = list.find((s) => s.status === 'active') ?? null;
          setPlan(active);
        }
        if (sdeRes.status === 'fulfilled') setSde(sdeRes.value);
      })
      .finally(() => setLoading(false));
  }, [locale]);

  useEffect(() => { refresh(); }, [refresh]);

  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === 'visible') refresh();
    };
    document.addEventListener('visibilitychange', onVisible);
    return () => document.removeEventListener('visibilitychange', onVisible);
  }, [refresh]);

  const value = useMemo<CodiData>(() => {
    const streak = (stats?.streak as { current?: number; best?: number } | undefined) ?? {};
    const unlocks = (stats?.unlocks as Record<string, RawLevelProgress>) ?? {};
    const todayPages = (stats?.today_activity as { pages_passed_today?: number } | undefined)?.pages_passed_today ?? 0;
    const nextAssignment = plan?.status === 'active'
      ? plan.assignments.find((a) => !a.completed) ?? null
      : null;
    const planAllDone = Boolean(plan && plan.total_count > 0 && plan.completed_count >= plan.total_count);
    const levelSummaries = Object.values(unlocks);
    const totalPagesDone = levelSummaries.reduce((sum, l) => sum + (l.pages_completed ?? 0), 0);

    return {
      loading,
      returnExam,
      streakCurrent: streak.current ?? 0,
      streakBest: streak.best ?? 0,
      passRate: Number(stats?.pass_rate ?? 0),
      activeDays: Number(stats?.day_number ?? 0),
      todayPages,
      plan,
      nextAssignment,
      planAllDone,
      continuePath: returnExam?.needed ? '/return-exam' : continueStudyPath(plan),
      level: pickActiveLevel(unlocks),
      totalPagesDone,
      sde,
      refresh,
    };
  }, [stats, plan, returnExam, loading, refresh, sde]);

  return <CodiContext.Provider value={value}>{children}</CodiContext.Provider>;
}

export function useCodi(): CodiData {
  const ctx = useContext(CodiContext);
  if (!ctx) throw new Error('useCodi must be used within CodiProvider');
  return ctx;
}

export interface CodiMessage {
  mood: CodiMood;
  headline: string;
  subline: string;
  ctaLabel: string | null;
  ctaTo: string | null;
}

type Translate = (key: string, vars?: Record<string, string | number>) => string;

/**
 * Turn the current progress snapshot into Codi's mood + tutor message.
 * Ordered by urgency so Codi always surfaces the most useful nudge.
 */
export function buildCodiMessage(data: CodiData, t: Translate): CodiMessage {
  const levelUpper = data.level ? data.level.id.toUpperCase() : 'A';

  if (data.sde?.codi) {
    const mood = (data.sde.codi.mood as CodiMood) || 'happy';
    const celebrate = data.sde.complete && !data.sde.analysis;
    return {
      mood: celebrate ? 'celebrate' : mood,
      headline: data.sde.codi.headline,
      subline: data.sde.analysis?.line || t('codi.nextSub'),
      ctaLabel: data.sde.codi.cta,
      ctaTo: data.sde.codi.to || '/',
    };
  }

  if (data.returnExam?.needed) {
    return {
      mood: 'think',
      headline: t('codi.returnExamHead'),
      subline: t('codi.returnExamSub', { days: data.returnExam.inactivity_days || data.returnExam.threshold_days || 3 }),
      ctaLabel: t('codi.returnExamCta'),
      ctaTo: '/return-exam',
    };
  }

  if (data.planAllDone) {
    return {
      mood: 'celebrate',
      headline: t('codi.doneHead'),
      subline: t('codi.doneSub', { pages: data.todayPages }),
      ctaLabel: t('codi.progressCta'),
      ctaTo: `/${data.level?.id ?? 'a'}/roadmap`,
    };
  }

  if (data.nextAssignment && data.continuePath) {
    const isRepeat = data.nextAssignment.reason === 'repeat';
    return {
      mood: isRepeat ? 'worried' : 'happy',
      headline: data.streakCurrent > 0
        ? t('codi.streakHead', { n: data.streakCurrent })
        : t('codi.nextHead'),
      subline: t('codi.nextSub'),
      ctaLabel: t('codi.nextCta'),
      ctaTo: data.continuePath,
    };
  }

  if (data.streakCurrent >= 3) {
    return {
      mood: 'celebrate',
      headline: t('codi.streakHead', { n: data.streakCurrent }),
      subline: t('codi.streakSub'),
      ctaLabel: t('codi.planCta'),
      ctaTo: '/',
    };
  }

  if (data.level && data.level.pct > 0) {
    return {
      mood: 'idle',
      headline: t('codi.progressHead', { level: levelUpper, pct: data.level.pct }),
      subline: t('codi.progressSub', { mastered: data.level.mastered, total: data.level.totalSets }),
      ctaLabel: t('codi.planCta'),
      ctaTo: '/',
    };
  }

  return {
    mood: 'happy',
    headline: t('codi.welcomeHead'),
    subline: t('codi.welcomeSub'),
    ctaLabel: t('codi.planCta'),
    ctaTo: '/',
  };
}
