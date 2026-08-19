import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../lib/api';
import { useI18n } from '../i18n/context';

export function SdeSqlPage() {
  const { id } = useParams<{ id: string }>();
  const { locale } = useI18n();
  const [prompt, setPrompt] = useState('');
  const [sql, setSql] = useState('');
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    api.sdeToday().then((d) => {
      const a = d.assignments.find((x) => x.type === 'sql' && x.id === id) || d.assignments.find((x) => x.type === 'sql');
      setPrompt(String(a?.prompt || ''));
    }).catch(() => {});
  }, [id, locale]);

  const submit = async () => {
    if (!id) return;
    const r = await api.sdeSql(id, sql);
    setMsg(r.passed ? (locale === 'es' ? 'OK' : 'OK') : `${locale === 'es' ? 'Esperado' : 'Expected'}: ${r.expected || ''}`);
  };

  return (
    <div className="mx-auto max-w-xl space-y-4">
      <h1 className="page-title">SQL</h1>
      <p className="text-sm text-text-muted">{prompt}</p>
      <textarea className="w-full rounded-lg border border-border bg-surface p-3 font-mono text-sm" rows={6} value={sql} onChange={(e) => setSql(e.target.value)} />
      <button type="button" className="btn-primary" onClick={() => void submit()}>{locale === 'es' ? 'Enviar' : 'Submit'}</button>
      {msg && <p className="text-sm text-text-muted">{msg}</p>}
      <Link to="/" className="text-sm text-brand">{locale === 'es' ? 'Hoy' : 'Today'}</Link>
    </div>
  );
}

export function SdePackPage() {
  const { locale } = useI18n();
  const [text, setText] = useState('');
  useEffect(() => {
    api.sdePack().then(setText).catch(() => setText(''));
  }, [locale]);
  return (
    <div className="space-y-4">
      <h1 className="page-title">{locale === 'es' ? 'Paquete de viaje' : 'Travel pack'}</h1>
      <pre className="whitespace-pre-wrap rounded-lg border border-border p-4 text-sm text-text-muted">{text}</pre>
      <Link to="/" className="btn-primary">{locale === 'es' ? 'Hoy' : 'Today'}</Link>
    </div>
  );
}
