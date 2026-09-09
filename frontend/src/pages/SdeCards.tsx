import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, type SdeAssignment } from '../lib/api';
import { useI18n } from '../i18n/context';

export function SdeCardsPage() {
  const { locale } = useI18n();
  const navigate = useNavigate();
  const [cards, setCards] = useState<{ id: string; front: string; back: string; section_id?: string }[]>([]);
  const [i, setI] = useState(0);
  const [show, setShow] = useState(false);
  const [results, setResults] = useState<{ id: string; ok: boolean; section_id?: string }[]>([]);
  const [done, setDone] = useState(false);
  const [justGraded, setJustGraded] = useState<'ok' | 'miss' | null>(null);

  useEffect(() => {
    api.sdeToday().then((d) => {
      const block = d.assignments.find((a: SdeAssignment) => a.type === 'flashcards');
      const list = (block?.cards as typeof cards) || [];
      setCards(list);
      if (!list.length) setDone(true);
    }).catch(() => {});
  }, [locale]);

  const card = cards[i];
  const finish = async (all: typeof results) => {
    if (all.length) await api.sdeCardsReview(all);
    setDone(true);
  };

  const grade = (ok: boolean) => {
    if (!card) return;
    setJustGraded(ok ? 'ok' : 'miss');
    const next = [...results, { id: card.id, ok, section_id: card.section_id }];
    setResults(next);
    window.setTimeout(() => {
      setShow(false);
      setJustGraded(null);
      if (i + 1 >= cards.length) void finish(next);
      else setI(i + 1);
    }, 220);
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (done || !card) return;
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        if (!show) setShow(true);
      } else if (show && (e.key === '1' || e.key.toLowerCase() === 'g')) {
        e.preventDefault();
        grade(true);
      } else if (show && (e.key === '2' || e.key.toLowerCase() === 'm')) {
        e.preventDefault();
        grade(false);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
    // grade closes over latest card/results; rebind when flip or index changes
  }, [show, done, card, i, results]); // eslint-disable-line react-hooks/exhaustive-deps

  if (done) {
    const okCount = results.filter((r) => r.ok).length;
    return (
      <div className="mx-auto max-w-lg space-y-6 rise-in">
        <div className="sde-panel text-center">
          <p className="sde-panel-kicker">{locale === 'es' ? 'Mazo' : 'Deck'}</p>
          <h1 className="mt-2 font-[family-name:var(--font-display)] text-2xl font-bold text-text">
            {locale === 'es' ? 'Mazo listo.' : 'Deck done.'}
          </h1>
          {results.length > 0 && (
            <p className="mt-2 text-sm text-text-muted">
              {locale === 'es'
                ? `${okCount} de ${results.length} bien`
                : `${okCount} of ${results.length} correct`}
            </p>
          )}
          <Link to="/" className="btn-primary mt-6 inline-flex">
            {locale === 'es' ? 'Volver a hoy' : 'Back to today'}
          </Link>
        </div>
      </div>
    );
  }
  if (!card) {
    return <p className="text-sm text-text-dim">{locale === 'es' ? 'Cargando…' : 'Loading…'}</p>;
  }

  const pct = Math.round(((i + (show ? 0.5 : 0)) / cards.length) * 100);

  return (
    <div className="mx-auto max-w-lg space-y-5 rise-in">
      <div className="flex items-end justify-between gap-3">
        <div>
          <p className="sde-panel-kicker">{locale === 'es' ? 'Flashcards' : 'Flashcards'}</p>
          <h1 className="mt-1 font-[family-name:var(--font-display)] text-xl font-bold text-text">
            {locale === 'es' ? 'Repaso del día' : "Today's recall"}
          </h1>
        </div>
        <p className="font-mono text-sm tabular-nums text-text-dim">
          {i + 1} / {cards.length}
        </p>
      </div>

      <div className="flash-progress" aria-hidden>
        <span style={{ width: `${pct}%` }} />
      </div>

      <div className="flash-stage">
        <button
          type="button"
          className={`flash-card w-full text-left ${show ? 'is-flipped' : ''} ${
            justGraded === 'ok' ? 'ring-2 ring-brand' : justGraded === 'miss' ? 'ring-2 ring-error' : ''
          }`}
          onClick={() => setShow((s) => !s)}
          aria-label={show
            ? (locale === 'es' ? 'Voltear a pregunta' : 'Flip to question')
            : (locale === 'es' ? 'Mostrar respuesta' : 'Show answer')}
        >
          <div className="flash-face">
            <p className="flash-face-label">{locale === 'es' ? 'Pregunta' : 'Prompt'}</p>
            <p className="font-[family-name:var(--font-display)] text-xl font-semibold leading-snug text-text sm:text-2xl">
              {card.front}
            </p>
            <p className="flash-hint">{locale === 'es' ? 'Tap · Espacio' : 'Tap · Space'}</p>
          </div>
          <div className="flash-face flash-face-back">
            <p className="flash-face-label">{locale === 'es' ? 'Respuesta' : 'Answer'}</p>
            <p className="text-base leading-relaxed text-text sm:text-lg">{card.back}</p>
            <p className="flash-hint">{locale === 'es' ? '1 = bien · 2 = mal' : '1 = got it · 2 = miss'}</p>
          </div>
        </button>
      </div>

      {!show ? (
        <button type="button" className="btn-primary w-full" onClick={() => setShow(true)}>
          {locale === 'es' ? 'Mostrar respuesta' : 'Reveal answer'}
        </button>
      ) : (
        <div className="flash-actions">
          <button type="button" className="btn-danger" onClick={() => grade(false)}>
            {locale === 'es' ? 'Mal' : 'Miss'}
          </button>
          <button type="button" className="btn-primary" onClick={() => grade(true)}>
            {locale === 'es' ? 'Bien' : 'Got it'}
          </button>
        </div>
      )}

      <button
        type="button"
        className="text-xs font-medium text-text-dim transition hover:text-text"
        onClick={() => navigate('/')}
      >
        ← {locale === 'es' ? 'Hoy' : 'Today'}
      </button>
    </div>
  );
}
