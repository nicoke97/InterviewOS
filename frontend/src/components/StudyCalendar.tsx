import { useCallback, useEffect, useMemo, useState } from 'react';
import { api, type CalendarDay, type CalendarMonth } from '../lib/api';

const WEEKDAYS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];

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

function dayLabel(day: CalendarDay): string {
  if (day.level === 'complete') return 'Morning & evening complete';
  if (day.morning_done) return 'Morning sheet complete';
  if (day.evening_done) return 'Evening sheet complete';
  return 'No sheets complete';
}

function dayClass(day: CalendarDay): string {
  const parts = ['calendar-day'];
  if (!day.in_month) parts.push('calendar-day-out');
  else if (day.level === 'complete') parts.push('calendar-day-complete');
  else if (day.level === 'partial') parts.push('calendar-day-partial');
  else parts.push('calendar-day-none');
  if (day.is_today) parts.push('calendar-day-today');
  return parts.join(' ');
}

export function StudyCalendar() {
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

  const title = new Date(year, month - 1).toLocaleString('en', { month: 'long', year: 'numeric' });

  const inMonth = days.filter((d) => d.in_month);
  const stats = {
    complete: inMonth.filter((d) => d.level === 'complete').length,
    partial: inMonth.filter((d) => d.level === 'partial').length,
    none: inMonth.filter((d) => d.level === 'none').length,
  };

  return (
    <div className="calendar-widget">
      <div className="calendar-header">
        <h2 className="text-base font-semibold text-text">{title}</h2>
        <div className="flex items-center gap-0.5">
          <button type="button" onClick={() => goMonth(-1)} className="calendar-nav-btn" aria-label="Previous month">
            <ChevronUp />
          </button>
          <button type="button" onClick={() => goMonth(1)} className="calendar-nav-btn" aria-label="Next month">
            <ChevronDown />
          </button>
        </div>
      </div>

      <div className="calendar-weekdays">
        {WEEKDAYS.map((wd) => (
          <span key={wd}>{wd}</span>
        ))}
      </div>

      <div className="calendar-grid">
        {days.map((day) => (
          <div key={day.date} className="calendar-cell">
            <span className={dayClass(day)} title={`${day.date} — ${dayLabel(day)}`}>
              {day.day}
            </span>
          </div>
        ))}
      </div>

      <div className="calendar-legend">
        <LegendItem color="calendar-legend-none" label="No sheets" count={stats.none} />
        <LegendItem color="calendar-legend-partial" label="One sheet" count={stats.partial} />
        <LegendItem color="calendar-legend-complete" label="Both sheets" count={stats.complete} />
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

function ChevronUp() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
      <path d="M3.5 9L7 5.5L10.5 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ChevronDown() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
      <path d="M3.5 5L7 8.5L10.5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
