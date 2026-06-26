import { useEffect, useState } from 'react';
import { api } from '../lib/api';

export function Settings() {
  const [focusMode, setFocusMode] = useState(false);
  const [devMode, setDevMode] = useState(false);
  const [exportData, setExportData] = useState<string>('');

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
    const data = await api.exportProgress();
    setExportData(JSON.stringify(data, null, 2));
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">Configura tu experiencia de estudio</p>
      </div>

      <div className="card flex items-center justify-between gap-4">
        <div>
          <p className="font-medium text-text">Modo enfoque</p>
          <p className="mt-0.5 text-sm text-text-muted">
            Oculta las pistas hasta tu primer error en cada pagina.
          </p>
        </div>
        <button type="button" onClick={toggleFocus} className={focusMode ? 'toggle-on' : 'toggle-off'} aria-pressed={focusMode}>
          <span className={focusMode ? 'toggle-knob-on' : 'toggle-knob-off'} />
        </button>
      </div>

      <div className="card flex items-center justify-between gap-4">
        <div>
          <p className="font-medium text-text">Modo desarrollador</p>
          <p className="mt-0.5 text-sm text-text-muted">
            Desbloquea todos los sets, checkpoints, examenes y niveles sin importar el progreso.
          </p>
        </div>
        <button type="button" onClick={toggleDevMode} className={devMode ? 'toggle-on' : 'toggle-off'} aria-pressed={devMode}>
          <span className={devMode ? 'toggle-knob-on' : 'toggle-knob-off'} />
        </button>
      </div>

      <div className="card space-y-4">
        <div>
          <p className="font-medium text-text">Exportar progreso</p>
          <p className="mt-0.5 text-sm text-text-muted">Descarga tu historial completo como JSON.</p>
        </div>
        <button type="button" onClick={doExport} className="btn-secondary">Descargar JSON</button>
        {exportData && (
          <pre className="max-h-60 overflow-auto rounded-xl bg-surface-2 p-4 font-mono text-xs text-text-muted">
            {exportData}
          </pre>
        )}
      </div>
    </div>
  );
}
