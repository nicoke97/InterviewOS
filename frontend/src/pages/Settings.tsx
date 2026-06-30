import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { LanguageToggle } from '../i18n/LanguageToggle';
import { useI18n } from '../i18n/context';

export function Settings() {
  const { t } = useI18n();
  const [focusMode, setFocusMode] = useState(false);
  const [devMode, setDevMode] = useState(false);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    api.settings().then((s) => {
      setFocusMode(s.focus_mode);
      setDevMode(s.dev_mode);
    });
  }, []);

  const toggleFocus = async () => {
    const next = !focusMode;
    await api.updateSettings({ focus_mode: next });
    setFocusMode(next);
  };

  const toggleDevMode = async () => {
    const next = !devMode;
    await api.updateSettings({ dev_mode: next });
    setDevMode(next);
  };

  const doExport = async () => {
    setExporting(true);
    try {
      const data = await api.exportProgress();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      const stamp = new Date().toISOString().slice(0, 10);
      a.href = url;
      a.download = t('settings.export.filename', { date: stamp });
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="page-title">{t('settings.title')}</h1>
        <p className="page-subtitle">{t('settings.subtitle')}</p>
      </div>

      <LanguageToggle />

      <div className="card flex items-center justify-between gap-4">
        <div>
          <p className="font-medium text-text">{t('settings.focus.title')}</p>
          <p className="mt-0.5 text-sm text-text-muted">{t('settings.focus.desc')}</p>
        </div>
        <button type="button" onClick={toggleFocus} className={focusMode ? 'toggle-on' : 'toggle-off'} aria-pressed={focusMode}>
          <span className={focusMode ? 'toggle-knob-on' : 'toggle-knob-off'} />
        </button>
      </div>

      <div className="card flex items-center justify-between gap-4">
        <div>
          <p className="font-medium text-text">{t('settings.dev.title')}</p>
          <p className="mt-0.5 text-sm text-text-muted">{t('settings.dev.desc')}</p>
        </div>
        <button type="button" onClick={toggleDevMode} className={devMode ? 'toggle-on' : 'toggle-off'} aria-pressed={devMode}>
          <span className={devMode ? 'toggle-knob-on' : 'toggle-knob-off'} />
        </button>
      </div>

      <div className="card space-y-4">
        <div>
          <p className="font-medium text-text">{t('settings.export.title')}</p>
          <p className="mt-0.5 text-sm text-text-muted">{t('settings.export.desc')}</p>
        </div>
        <button type="button" onClick={() => void doExport()} disabled={exporting} className="btn-secondary">
          {exporting ? t('settings.export.preparing') : t('settings.export.download')}
        </button>
      </div>
    </div>
  );
}
