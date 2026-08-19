import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api, type SdeSheet } from '../lib/api';
import { CodeEditor } from '../components/CodeEditor';
import { useI18n } from '../i18n/context';

export function SdeAlgoPage() {
  const { algoId, lang, sheetId } = useParams<{ algoId: string; lang: string; sheetId: string }>();
  const { locale } = useI18n();
  const navigate = useNavigate();
  const [sheet, setSheet] = useState<SdeSheet | null>(null);
  const [code, setCode] = useState('');
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!algoId || !lang || !sheetId) return;
    api.sdeSheet(algoId, lang, sheetId).then((s) => {
      setSheet(s);
      setCode(s.starter_code);
      setMsg(null);
    }).catch((e: Error) => setMsg(e.message));
  }, [algoId, lang, sheetId, locale]);

  if (!sheet) return <p className="text-sm text-text-dim">{msg || (locale === 'es' ? 'Cargando…' : 'Loading…')}</p>;

  const submit = async () => {
    if (!algoId || !lang || !sheetId) return;
    setBusy(true);
    try {
      const r = await api.sdeSheetSubmit(algoId, lang, sheetId, code);
      if (r.passed) {
        setMsg(locale === 'es' ? 'Bien. Siguiente.' : 'Passed. Next.');
        const today = await api.sdeToday();
        const next = today.assignments.find((a) => a.type === 'algo_sheet' && !a.completed);
        if (next) {
          navigate(`/sde/algo/${next.algo_id}/${next.lang}/${next.sheet_id}`);
        } else if (today.assignments.some((a) => a.type === 'voice' && !a.completed)) {
          navigate('/sde/voice');
        } else {
          navigate('/');
        }
      } else {
        setMsg(r.error || (locale === 'es' ? 'Falló. Repite esta hoja.' : 'Failed. Repeat this sheet.'));
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <p className="text-xs uppercase text-brand">{sheet.title} · {sheet.lang} · {sheet.sheet_id}</p>
      <h1 className="text-lg font-medium text-text">{sheet.prompt}</h1>
      <CodeEditor
        value={code}
        onChange={setCode}
        language={lang === 'csharp' ? 'csharp' : 'python'}
        drillId={`${algoId}-${lang}-${sheetId}`}
        height="360px"
      />
      {msg && <p className="text-sm text-text-muted">{msg}</p>}
      <div className="flex gap-3">
        <button type="button" className="btn-primary" disabled={busy} onClick={() => void submit()}>
          {locale === 'es' ? 'Enviar' : 'Submit'}
        </button>
        <Link to="/" className="btn-secondary">{locale === 'es' ? 'Hoy' : 'Today'}</Link>
      </div>
    </div>
  );
}
