import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api, type CalendarDay, type CalendarMonth, type SdeToday } from '../lib/api';
import { en } from '../i18n/en';
import { es } from '../i18n/es';
import { useI18n } from '../i18n/context';

const ALGO_ORDER = [
  'two-sum', 'contains-duplicate', 'valid-anagram', 'best-time-stock',
  'group-anagrams', 'top-k-frequent', 'valid-palindrome', 'two-sum-ii',
  '3sum', 'container-water', 'longest-substring', 'min-window-substring',
  'valid-parentheses', 'min-stack', 'binary-search', 'search-rotated',
  'reverse-linked-list', 'merge-two-lists', 'linked-list-cycle',
  'max-depth-tree', 'invert-tree', 'validate-bst', 'climbing-stairs',
  'house-robber', 'coin-change', 'number-islands', 'course-schedule',
  'merge-intervals',
];

const ALGO_LABEL: Record<string, string> = {
  'two-sum': 'Two Sum', 'contains-duplicate': 'Contains Duplicate',
  'valid-anagram': 'Valid Anagram', 'best-time-stock': 'Best Time to Buy Stock',
  'group-anagrams': 'Group Anagrams', 'top-k-frequent': 'Top K Frequent',
  'valid-palindrome': 'Valid Palindrome', 'two-sum-ii': 'Two Sum II',
  '3sum': '3Sum', 'container-water': 'Container With Most Water',
  'longest-substring': 'Longest Substring Without Repeating',
  'min-window-substring': 'Minimum Window Substring',
  'valid-parentheses': 'Valid Parentheses', 'min-stack': 'Min Stack',
  'binary-search': 'Binary Search', 'search-rotated': 'Search in Rotated Sorted Array',
  'reverse-linked-list': 'Reverse Linked List', 'merge-two-lists': 'Merge Two Sorted Lists',
  'linked-list-cycle': 'Linked List Cycle', 'max-depth-tree': 'Maximum Depth of Binary Tree',
  'invert-tree': 'Invert Binary Tree', 'validate-bst': 'Validate BST',
  'climbing-stairs': 'Climbing Stairs', 'house-robber': 'House Robber',
  'coin-change': 'Coin Change', 'number-islands': 'Number of Islands',
  'course-schedule': 'Course Schedule', 'merge-intervals': 'Merge Intervals',
};

const THEORY_WEEKS = [
  'Big O', 'REST', 'SQL', 'Git / PRs', 'Azure DevOps',
  'Tests', 'C# async', 'Concurrencia', 'LINQ', 'EF Core',
  'DI + ASP.NET', 'SOLID', 'Escala + logs', 'GC + asyncio',
  'GIL + Python', 'SQLAlchemy + pytest',
];

function estimateMonths(sde: SdeToday): { algoIdx: number; sectionIdx: number; remainingMonths: number } {
  const cursor = sde.cursor as {
    active_algo_id?: string; algo_phase?: string;
    next_section_index?: number; day1_index?: number;
  };
  const algoId = cursor.active_algo_id || 'two-sum';
  const algoIdx = Math.max(0, ALGO_ORDER.indexOf(algoId));
  const phase = cursor.algo_phase || 'day1';
  const sectionIdx = Math.min(cursor.next_section_index ?? 0, 80);

  // Algo cost: each remaining algo ~5 advance days (day1+day2+voice C# + rung1+day2+voice Python)
  // Partial credit for current algo
  const phaseOffset = phase === 'day2' ? 2 : phase === 'voice' ? 3 : phase === 'rung1' ? 3.5 : 0;
  const remainingAlgoDays = (ALGO_ORDER.length - algoIdx - 1) * 5 + Math.max(0, 5 - phaseOffset);

  // Theory cost: 1 section per advance day
  const remainingTheoryDays = 80 - sectionIdx;

  // Total: they interleave, so take max + some buffer for pool reviews and off-days
  const rawDays = Math.max(remainingAlgoDays, remainingTheoryDays);
  const withBuffer = rawDays * 1.25; // 25% buffer for missed days, pool repeats, etc.
  const months = withBuffer / 26; // ~26 study days per month (6 days/week)

  return { algoIdx, sectionIdx, remainingMonths: Math.round(months) };
}

const TRACKING_START_MONTH = 6;
const TRACKING_START_DAY = 25;

function formatIso(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function buildMonthGrid(year: number, month: number): CalendarDay[] {
  const first = new Date(year, month - 1, 1);
  const last = new Date(year, month, 0);

  const gridStart = new Date(first);
  gridStart.setDate(first.getDate() - first.getDay());

  const gridEnd = new Date(last);
  gridEnd.setDate(last.getDate() + (6 - last.getDay()));

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const days: CalendarDay[] = [];
  const cursor = new Date(gridStart);

  while (cursor <= gridEnd) {
    const current = new Date(cursor);
    current.setHours(0, 0, 0, 0);
    days.push({
      date: formatIso(current),
      day: current.getDate(),
      in_month: current.getMonth() === month - 1,
      is_today: current.getTime() === today.getTime(),
      level: 'none',
      morning_done: false,
      evening_done: false,
    });
    cursor.setDate(cursor.getDate() + 1);
  }

  return days;
}

function trackingStartIso(year: number): string {
  const m = String(TRACKING_START_MONTH).padStart(2, '0');
  const d = String(TRACKING_START_DAY).padStart(2, '0');
  return `${year}-${m}-${d}`;
}

function isMissedDay(day: CalendarDay, todayIso: string): boolean {
  if (!day.in_month || day.level !== 'none' || day.date >= todayIso) return false;
  const year = Number(day.date.slice(0, 4));
  return day.date >= trackingStartIso(year);
}

function dayLabel(day: CalendarDay, todayIso: string, t: (key: string, vars?: Record<string, string | number>) => string): string {
  const repeatNote = day.repeat_scheduled
    ? ` · ${t('calendar.repeatScheduled', { count: day.repeat_scheduled })}`
    : '';
  if (isMissedDay(day, todayIso)) return `${t('calendar.missed')}${repeatNote}`;
  if (day.level === 'complete') return `${t('calendar.complete')}${repeatNote}`;
  if (day.morning_done) return `${t('calendar.morningOnly')}${repeatNote}`;
  if (day.evening_done) return `${t('calendar.eveningOnly')}${repeatNote}`;
  if (day.repeat_scheduled) return t('calendar.repeatOnly', { count: day.repeat_scheduled });
  return t('calendar.none');
}

function dayClass(day: CalendarDay, todayIso: string): string {
  const parts = ['calendar-day'];
  if (!day.in_month) parts.push('calendar-day-out');
  else if (isMissedDay(day, todayIso)) parts.push('calendar-day-missed');
  else if (day.level === 'complete') parts.push('calendar-day-complete');
  else if (day.level === 'partial') parts.push('calendar-day-partial');
  else if (day.repeat_scheduled) parts.push('calendar-day-repeat');
  else parts.push('calendar-day-none');
  if (day.is_today) parts.push('calendar-day-today');
  return parts.join(' ');
}

export function StudyCalendar({ className = '' }: { className?: string }) {
  const { t, locale, dateLocale } = useI18n();
  const cal = (locale === 'es' ? es : en) as { calendar: { weekdaysEn: string[]; weekdaysEs: string[] } };
  const weekdays = locale === 'es' ? cal.calendar.weekdaysEs : cal.calendar.weekdaysEn;
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [completion, setCompletion] = useState<CalendarMonth | null>(null);
  const [sde, setSde] = useState<SdeToday | null>(null);
  const [guideVisible, setGuideVisible] = useState(false);
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    api.sdeToday().then(setSde).catch(() => {});
  }, []);

  const days = useMemo(() => {
    const grid = buildMonthGrid(year, month);
    if (!completion) return grid;
    const byDate = new Map(completion.days.map((d) => [d.date, d]));
    return grid.map((cell) => {
      const remote = byDate.get(cell.date);
      if (!remote) return cell;
      return {
        ...cell,
        level: remote.level,
        morning_done: remote.morning_done,
        evening_done: remote.evening_done,
        repeat_scheduled: remote.repeat_scheduled,
      };
    });
  }, [year, month, completion]);

  const load = useCallback(async () => {
    try {
      const result = await api.calendarMonth(year, month);
      setCompletion(result);
    } catch {
      setCompletion(null);
    }
  }, [year, month]);

  useEffect(() => {
    load();
  }, [load]);

  const goMonth = (delta: number) => {
    const d = new Date(year, month - 1 + delta, 1);
    setYear(d.getFullYear());
    setMonth(d.getMonth() + 1);
    setCompletion(null);
  };

  const title = new Date(year, month - 1).toLocaleString(dateLocale, { month: 'long', year: 'numeric' });
  const todayIso = formatIso(new Date());

  const inMonth = days.filter((d) => d.in_month);
  const stats = {
    complete: inMonth.filter((d) => d.level === 'complete').length,
    partial: inMonth.filter((d) => d.level === 'partial').length,
    none: inMonth.filter((d) => d.level === 'none' && !isMissedDay(d, todayIso) && !d.repeat_scheduled).length,
    missed: inMonth.filter((d) => isMissedDay(d, todayIso)).length,
    repeats: inMonth.filter((d) => (d.repeat_scheduled ?? 0) > 0).length,
  };

  const handleMouseEnter = () => {
    if (hideTimer.current) clearTimeout(hideTimer.current);
    setGuideVisible(true);
  };
  const handleMouseLeave = () => {
    hideTimer.current = setTimeout(() => setGuideVisible(false), 200);
  };

  return (
    <div
      className={`calendar-widget-wrap relative ${className}`.trim()}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
    <div className="calendar-widget">
      <div className="calendar-header">
        <h2 className="text-base font-semibold capitalize text-text">{title}</h2>
        <div className="flex items-center gap-0.5">
          <button type="button" onClick={() => goMonth(-1)} className="calendar-nav-btn" aria-label={t('calendar.prevMonth')}>
            <ChevronLeft />
          </button>
          <button type="button" onClick={() => goMonth(1)} className="calendar-nav-btn" aria-label={t('calendar.nextMonth')}>
            <ChevronRight />
          </button>
        </div>
      </div>

      <div className="calendar-weekdays">
        {weekdays.map((wd) => (
          <span key={wd}>{wd}</span>
        ))}
      </div>

      <div className="calendar-grid">
        {days.map((day) => (
          <div key={day.date} className="calendar-cell">
            <span className={dayClass(day, todayIso)} title={t('calendar.dayTitle', { date: day.date, label: dayLabel(day, todayIso, t) })}>
              {day.day}
            </span>
          </div>
        ))}
      </div>

      <div className="calendar-legend">
        <LegendItem color="calendar-legend-missed" label={t('calendar.legendMissed')} count={stats.missed} />
        <LegendItem color="calendar-legend-repeat" label={t('calendar.legendRepeat')} count={stats.repeats} />
        <LegendItem color="calendar-legend-none" label={t('calendar.legendNone')} count={stats.none} />
        <LegendItem color="calendar-legend-partial" label={t('calendar.legendPartial')} count={stats.partial} />
        <LegendItem color="calendar-legend-complete" label={t('calendar.legendComplete')} count={stats.complete} />
      </div>
    </div>

    {guideVisible && sde && (
      <StudyGuidePanel sde={sde} locale={locale} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
    )}
    </div>
  );
}

function LegendItem({ color, label, count }: { color: string; label: string; count: number }) {
  return (
    <span className="calendar-legend-item">
      <span className={`calendar-legend-dot ${color}`} />
      <span>{label}</span>
      <span className="text-text-dim">({count})</span>
    </span>
  );
}

function StudyGuidePanel({
  sde, locale, onMouseEnter, onMouseLeave,
}: {
  sde: SdeToday;
  locale: string;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
}) {
  const cursor = sde.cursor as {
    active_algo_id?: string; algo_phase?: string;
    next_section_index?: number;
  };
  const algoId = cursor.active_algo_id || 'two-sum';
  const phase = cursor.algo_phase || 'day1';
  const { algoIdx, sectionIdx, remainingMonths } = estimateMonths(sde);
  const currentWeekIdx = Math.min(Math.floor(sectionIdx / 5), THEORY_WEEKS.length - 1);
  const isEs = locale === 'es';

  const phaseLabel: Record<string, string> = {
    day1: isEs ? 'Día 1' : 'Day 1',
    day2: isEs ? 'Día 2' : 'Day 2',
    voice: isEs ? 'Voz' : 'Voice',
    rung1: isEs ? 'Py — Rung 1' : 'Py — Rung 1',
  };

  return (
    <div
      className="study-guide-panel"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      {/* Header */}
      <div className="study-guide-header">
        <span className="study-guide-icon">📚</span>
        <span className="study-guide-title">
          {isEs ? 'Plan de estudio — SDE II' : 'Study plan — SDE II'}
        </span>
      </div>

      {/* Current position */}
      <div className="study-guide-section">
        <p className="study-guide-label">{isEs ? 'Posición actual' : 'Current position'}</p>
        <p className="study-guide-value">
          {isEs ? 'Algoritmo' : 'Algo'} {algoIdx + 1}/{ALGO_ORDER.length} —{' '}
          <span className="font-medium text-text">{ALGO_LABEL[algoId] ?? algoId}</span>
          {' '}
          <span className="study-guide-badge">{phaseLabel[phase] ?? phase}</span>
        </p>
        <p className="study-guide-value mt-0.5">
          {isEs ? 'Semana' : 'Week'} {currentWeekIdx + 1}/{THEORY_WEEKS.length} —{' '}
          <span className="font-medium text-text">{THEORY_WEEKS[currentWeekIdx]}</span>
        </p>
      </div>

      {/* Algo progress bar */}
      <div className="study-guide-section">
        <p className="study-guide-label">{isEs ? 'Algoritmos' : 'Algorithms'}</p>
        <div className="study-guide-bar-track">
          <div
            className="study-guide-bar-fill"
            style={{ width: `${Math.round((algoIdx / ALGO_ORDER.length) * 100)}%` }}
          />
        </div>
        <p className="study-guide-sub">{algoIdx}/{ALGO_ORDER.length} {isEs ? 'algoritmos completados' : 'completed'}</p>
      </div>

      {/* Theory progress */}
      <div className="study-guide-section">
        <p className="study-guide-label">{isEs ? 'Temario' : 'Theory'}</p>
        <div className="study-guide-weeks">
          {THEORY_WEEKS.map((w, i) => (
            <span
              key={w}
              className={`study-guide-week-chip ${
                i < currentWeekIdx
                  ? 'study-guide-week-done'
                  : i === currentWeekIdx
                  ? 'study-guide-week-current'
                  : 'study-guide-week-pending'
              }`}
              title={w}
            >
              {i < currentWeekIdx ? '✓' : i + 1}
            </span>
          ))}
        </div>
        <p className="study-guide-sub">
          {currentWeekIdx}/{THEORY_WEEKS.length}{' '}
          {isEs ? 'semanas · siguiente:' : 'weeks · next:'}{' '}
          <span className="text-brand">{THEORY_WEEKS[Math.min(currentWeekIdx, THEORY_WEEKS.length - 1)]}</span>
        </p>
      </div>

      {/* Time estimate */}
      <div className="study-guide-estimate">
        <span className="study-guide-clock">⏱</span>
        <span>
          {isEs
            ? `~${remainingMonths} ${remainingMonths === 1 ? 'mes' : 'meses'} para estar listo para SDE 2/3`
            : `~${remainingMonths} ${remainingMonths === 1 ? 'month' : 'months'} to be SDE 2/3 ready`}
        </span>
      </div>
    </div>
  );
}

function ChevronLeft() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
      <path d="M8.5 3.5L5 7L8.5 10.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ChevronRight() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
      <path d="M5.5 3.5L9 7L5.5 10.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
