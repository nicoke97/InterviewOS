import { useCallback, useEffect, useMemo, useState } from 'react';
import { api, type CalendarDay, type CalendarMonth } from '../lib/api';
import { en } from '../i18n/en';
import { es } from '../i18n/es';
import { useI18n } from '../i18n/context';

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

  return (
    <div className={`calendar-widget ${className}`.trim()}>
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
