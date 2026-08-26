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
    const next = [...results, { id: card.id, ok, section_id: card.section_id }];
    setResults(next);
    setShow(false);
    if (i + 1 >= cards.length) void finish(next);
    else setI(i + 1);
  };

  if (done) {
    return (
      <div className="space-y-4">
        <p className="text-text">{locale === 'es' ? 'Mazo listo.' : 'Deck done.'}</p>
        <Link to="/" className="btn-primary">{locale === 'es' ? 'Hoy' : 'Today'}</Link>
      </div>
    );
  }
  if (!card) return <p className="text-sm text-text-dim">{locale === 'es' ? 'Cargando…' : 'Loading…'}</p>;

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <p className="text-xs text-text-dim">{i + 1} / {cards.length}</p>
      <div className="rounded-xl border border-border p-6">
        <p className="text-lg text-text">{card.front}</p>
        {show && <p className="mt-4 text-sm text-text-muted">{card.back}</p>}
      </div>
      {!show ? (
        <button type="button" className="btn-primary" onClick={() => setShow(true)}>
          {locale === 'es' ? 'Mostrar' : 'Show'}
        </button>
      ) : (
        <div className="flex gap-3">
          <button type="button" className="btn-primary" onClick={() => grade(true)}>{locale === 'es' ? 'Bien' : 'Got it'}</button>
          <button type="button" className="btn-secondary" onClick={() => grade(false)}>{locale === 'es' ? 'Mal' : 'Miss'}</button>
        </div>
      )}
      <button type="button" className="text-xs text-text-dim" onClick={() => navigate('/')}>←</button>
    </div>
  );
}
