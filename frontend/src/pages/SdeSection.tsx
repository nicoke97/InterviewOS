import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api, type SdeSection } from '../lib/api';
import { useI18n } from '../i18n/context';

export function SdeSectionPage() {
  const { id } = useParams<{ id: string }>();
  const { locale } = useI18n();
  const [sec, setSec] = useState<SdeSection | null>(null);
  const [answers, setAnswers] = useState<number[]>([]);
  const [result, setResult] = useState<{ passed: boolean; correct: number; total: number; cards: { front: string; back: string }[] } | null>(null);

  useEffect(() => {
    if (id) api.sdeSection(id).then(setSec).catch(() => {});
  }, [id, locale]);

  if (!sec) return <p className="text-sm text-text-dim">{locale === 'es' ? 'Cargando…' : 'Loading…'}</p>;

  const submit = async () => {
    if (!id) return;
    const r = await api.sdeSectionQuiz(id, answers);
    setResult(r);
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <p className="text-xs uppercase text-brand">
        {sec.anchor ? `${sec.week_title} · ${sec.anchor}` : sec.week_title}
      </p>
      <h1 className="page-title">{sec.title}</h1>
      <p className="text-sm leading-relaxed text-text-muted">{sec.reading}</p>
      {!result && (
        <div className="space-y-5">
          {sec.questions.map((q, qi) => (
            <fieldset key={q.id} className="space-y-2">
              <legend className="text-sm font-medium text-text">{q.q}</legend>
              {q.choices.map((c, ci) => (
                <label key={ci} className="flex gap-2 text-sm text-text-muted">
                  <input
                    type="radio"
                    name={q.id}
                    checked={answers[qi] === ci}
                    onChange={() => {
                      const next = [...answers];
                      next[qi] = ci;
                      setAnswers(next);
                    }}
                  />
                  {c}
                </label>
              ))}
            </fieldset>
          ))}
          <button type="button" className="btn-primary" onClick={() => void submit()}>
            {locale === 'es' ? 'Enviar quiz' : 'Submit quiz'}
          </button>
        </div>
      )}
      {result && (
        <div className="space-y-4">
          <p className="text-text">{result.passed ? (locale === 'es' ? 'Sección cerrada.' : 'Section closed.') : (locale === 'es' ? 'Fallaste. Mañana la misma.' : 'Missed. Same section tomorrow.')} ({result.correct}/{result.total})</p>
          <div className="space-y-2">
            <p className="text-sm font-medium">{locale === 'es' ? 'Cartas nuevas (repásalas)' : 'New cards'}</p>
            {result.cards.map((c) => (
              <div key={c.front} className="rounded-lg border border-border px-3 py-2 text-sm">
                <p className="text-text">{c.front}</p>
                <p className="text-text-muted">{c.back}</p>
              </div>
            ))}
          </div>
          <Link to="/" className="btn-primary">{locale === 'es' ? 'Hoy' : 'Today'}</Link>
        </div>
      )}
    </div>
  );
}
