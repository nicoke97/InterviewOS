import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { api, setApiLocale } from '../lib/api';
import { en } from './en';
import { es } from './es';
import { dateLocale, translate } from './translate';
import type { Locale } from './types';

const STORAGE_KEY = 'codenda-locale';

interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
  dateLocale: string;
}

const I18nContext = createContext<I18nContextValue | null>(null);

function readStoredLocale(): Locale {
  try {
    const stored = localStorage.getItem(STORAGE_KEY) ?? localStorage.getItem('pythonos-locale');
    if (stored === 'en' || stored === 'es') return stored;
  } catch {
    /* ignore */
  }
  return 'en';
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => {
    const initial = readStoredLocale();
    setApiLocale(initial);
    return initial;
  });

  const messages = locale === 'es' ? es : en;

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next);
    setApiLocale(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* ignore */
    }
    document.documentElement.lang = next;
    void api.updateSettings({ locale: next }).catch(() => {});
  }, []);

  useEffect(() => {
    setApiLocale(locale);
    document.documentElement.lang = locale;
    api.settings()
      .then((s) => {
        if (s.locale && s.locale !== locale) {
          setLocaleState(s.locale);
          setApiLocale(s.locale);
          try {
            localStorage.setItem(STORAGE_KEY, s.locale);
          } catch {
            /* ignore */
          }
          document.documentElement.lang = s.locale;
        } else if (!s.locale) {
          void api.updateSettings({ locale }).catch(() => {});
        }
      })
      .catch(() => {});
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) => translate(messages, key, vars),
    [messages],
  );

  const value = useMemo(
    () => ({ locale, setLocale, t, dateLocale: dateLocale(locale) }),
    [locale, setLocale, t],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useI18n must be used within I18nProvider');
  return ctx;
}
