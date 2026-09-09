import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api, type SdeDebugBug } from '../lib/api';
import { sdeNextHref } from '../lib/sdePaths';
import { CodeEditor } from '../components/CodeEditor';
import { useI18n } from '../i18n/context';

export function SdeDebugPage() {
  const { bugId } = useParams<{ bugId: string }>();
  const { locale } = useI18n();
  const navigate = useNavigate();
  const [bug, setBug] = useState<SdeDebugBug | null>(null);
  const [code, setCode] = useState('');
  const [msg, setMsg] = useState<string | null>(null);
  const [cause, setCause] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!bugId) return;
    api.sdeDebug(bugId).then((b) => {
      setBug(b);
      setCode(b.broken_code);
      setMsg(null);
      setCause(null);
    }).catch((e: Error) => setMsg(e.message));
  }, [bugId, locale]);

  if (!bug) return <p className="text-sm text-text-dim">{msg || (locale === 'es' ? 'Cargando…' : 'Loading…')}</p>;

  const submit = async () => {
    if (!bugId) return;
    setBusy(true);
    try {
      const r = await api.sdeDebugSubmit(bugId, code);
      if (r.passed) {
        setCause(r.cause || null);
        setMsg(locale === 'es' ? 'Bien. Siguiente.' : 'Passed. Next.');
        const today = await api.sdeToday();
        const next = sdeNextHref(today.assignments);
        navigate(next || '/');
      } else {
        setMsg(r.error || (locale === 'es' ? 'Sigue fallando. Cambia una cosa y reintenta.' : 'Still failing. Change one thing and retry.'));
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <p className="text-xs uppercase text-brand">
        Debug · {bug.lang} · {bug.difficulty} · {bug.family}
      </p>
      <h1 className="text-lg font-medium text-text">{bug.title}</h1>
      <p className="text-sm text-text-muted">{bug.error_hint}</p>
      <CodeEditor
        value={code}
        onChange={setCode}
        language={bug.lang === 'csharp' ? 'csharp' : 'python'}
        drillId={`debug-${bug.id}`}
        height="360px"
      />
      {msg && <p className="text-sm text-text-muted">{msg}</p>}
      {cause && <p className="text-sm text-brand">{cause}</p>}
      <div className="flex gap-3">
        <button type="button" className="btn-primary" disabled={busy} onClick={() => void submit()}>
          {locale === 'es' ? 'Enviar' : 'Submit'}
        </button>
        <Link to="/" className="btn-secondary">{locale === 'es' ? 'Hoy' : 'Today'}</Link>
      </div>
    </div>
  );
}
