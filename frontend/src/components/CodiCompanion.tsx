import { useEffect, useRef, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { CodiMascot } from './CodiMascot';
import { buildCodiMessage, useCodi } from '../lib/codi';
import { useI18n } from '../i18n/context';

const DISMISS_KEY = 'codi-bubble-dismissed';

/**
 * Floating Codi companion shown across the app. Collapsed it's a bobbing
 * mascot button; tapping opens a tutor panel with the current progress nudge.
 */
export function CodiCompanion() {
  const { t, locale } = useI18n();
  const codi = useCodi();
  const loc = useLocation();
  const [open, setOpen] = useState(false);
  const [bubbleDismissed, setBubbleDismissed] = useState(false);

  const firstPath = useRef(true);
  useEffect(() => {
    if (firstPath.current) {
      firstPath.current = false;
      return;
    }
    codi.refresh();
  }, [loc.pathname, locale]); // eslint-disable-line react-hooks/exhaustive-deps

  // Re-show the bubble once per day.
  useEffect(() => {
    try {
      const today = new Date().toISOString().slice(0, 10);
      setBubbleDismissed(localStorage.getItem(DISMISS_KEY) === today);
    } catch {
      setBubbleDismissed(false);
    }
  }, []);

  // Don't overlay Codi on its own exam page.
  if (loc.pathname === '/return-exam') return null;

  const msg = buildCodiMessage(codi, t);
  const attention = Boolean(codi.returnExam?.needed);

  const dismissBubble = () => {
    setBubbleDismissed(true);
    try {
      localStorage.setItem(DISMISS_KEY, new Date().toISOString().slice(0, 10));
    } catch {
      /* ignore */
    }
  };

  return (
    <>
      {open ? (
        <div className="codi-panel codi-pop">
          <div className="flex items-start gap-3">
            <CodiMascot mood={msg.mood} size={60} />
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-semibold text-text">{t('codi.name')}</p>
                <button
                  type="button"
                  onClick={() => setOpen(false)}
                  className="text-text-dim hover:text-text"
                  aria-label={t('codi.close')}
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <p className="mt-0.5 text-sm font-medium text-text">{msg.headline}</p>
              <p className="mt-1 text-xs leading-relaxed text-text-muted">{msg.subline}</p>
            </div>
          </div>

          <dl className="mt-3 grid grid-cols-3 gap-2 border-t border-border pt-3 text-center">
            <div>
              <dt className="text-[10px] uppercase tracking-wide text-text-dim">{t('codi.statStreak')}</dt>
              <dd className="tabular-nums text-sm font-semibold text-text">{codi.streakCurrent}</dd>
            </div>
            <div>
              <dt className="text-[10px] uppercase tracking-wide text-text-dim">{t('codi.statPages')}</dt>
              <dd className="tabular-nums text-sm font-semibold text-text">{codi.todayPages}</dd>
            </div>
            <div>
              <dt className="text-[10px] uppercase tracking-wide text-text-dim">{t('codi.statPass')}</dt>
              <dd className="tabular-nums text-sm font-semibold text-text">{codi.passRate}%</dd>
            </div>
          </dl>

          {codi.level && (
            <div className="mt-3">
              <div className="flex items-center justify-between text-xs text-text-muted">
                <span>{t('codi.levelLabel', { level: codi.level.id.toUpperCase() })}</span>
                <span className="tabular-nums">{codi.level.pct}%</span>
              </div>
              <div className="progress-bar mt-1.5">
                <div className="progress-fill" style={{ width: `${codi.level.pct}%` }} />
              </div>
            </div>
          )}

          {msg.ctaLabel && msg.ctaTo && (
            <Link
              to={msg.ctaTo}
              onClick={() => setOpen(false)}
              className="btn-primary mt-4 w-full text-center"
            >
              {msg.ctaLabel}
            </Link>
          )}
        </div>
      ) : (
        !bubbleDismissed && (
          <div className="codi-bubble codi-pop">
            <div className="flex items-start justify-between gap-2">
              <p className="pr-1 font-medium leading-snug">{msg.headline}</p>
              <button
                type="button"
                onClick={dismissBubble}
                className="shrink-0 text-text-dim hover:text-text"
                aria-label={t('codi.close')}
              >
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <button
              type="button"
              onClick={() => setOpen(true)}
              className="mt-1 text-xs font-medium text-brand hover:underline"
            >
              {t('codi.openTutor')}
            </button>
          </div>
        )
      )}

      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="codi-fab"
        aria-label={t('codi.openTutor')}
      >
        <CodiMascot mood={msg.mood} size={56} />
        {attention && !open && <span className="codi-dot" />}
      </button>
    </>
  );
}
