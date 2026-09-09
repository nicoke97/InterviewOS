import { useI18n } from './context';
import type { Locale } from './types';

export function LanguageToggle({
  compact = false,
  tone = 'light',
}: {
  compact?: boolean;
  tone?: 'light' | 'dark';
}) {
  const { locale, setLocale, t } = useI18n();
  const dark = tone === 'dark';

  const btn = (lang: Locale, label: string) => (
    <button
      key={lang}
      type="button"
      onClick={() => setLocale(lang)}
      className={`rounded-md px-2.5 py-1 text-xs font-semibold transition-colors ${
        locale === lang
          ? 'bg-brand text-on-brand'
          : dark
            ? 'text-[#95a6b8] hover:bg-white/10 hover:text-[#f2f6fa]'
            : 'text-text-muted hover:bg-surface-2 hover:text-text'
      }`}
      aria-pressed={locale === lang}
    >
      {label}
    </button>
  );

  if (compact) {
    return (
      <div
        className={`inline-flex items-center gap-0.5 rounded-lg border p-0.5 ${
          dark
            ? 'border-white/10 bg-white/5'
            : 'border-border bg-surface'
        }`}
        role="group"
        aria-label={t('settings.language.title')}
      >
        {btn('en', 'EN')}
        {btn('es', 'ES')}
      </div>
    );
  }

  return (
    <div className="card space-y-3">
      <div>
        <p className="font-medium text-text">{t('settings.language.title')}</p>
        <p className="mt-0.5 text-sm text-text-muted">{t('settings.language.desc')}</p>
      </div>
      <div
        className="inline-flex items-center gap-0.5 rounded-lg border border-border bg-surface p-0.5"
        role="group"
        aria-label={t('settings.language.title')}
      >
        {btn('en', t('settings.language.english'))}
        {btn('es', t('settings.language.spanish'))}
      </div>
    </div>
  );
}
