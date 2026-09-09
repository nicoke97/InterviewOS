import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api } from '../lib/api';
import { useCodi } from '../lib/codi';
import { useI18n } from '../i18n/context';

export function SdeReadingPage() {
  const { weekId } = useParams<{ weekId: string }>();
  const { locale, t } = useI18n();
  const navigate = useNavigate();
  const { refresh } = useCodi();
  const [data, setData] = useState<{
    title: string;
    intro: string;
    minutes?: number;
    week_id?: string;
  } | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!weekId) return;
    api.sdeReading(weekId).then(setData).catch(() => setData(null));
  }, [weekId, locale]);

  const finish = async () => {
    if (!weekId || saving) return;
    setSaving(true);
    try {
      await api.sdeReadingComplete(weekId);
      refresh();
      navigate('/');
    } finally {
      setSaving(false);
    }
  };

  if (!data) {
    return <p className="text-sm text-text-dim">{t('common.loading')}</p>;
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 rise-in">
      <div>
        <p className="sde-panel-kicker">{locale === 'es' ? 'Lectura' : 'Reading'}</p>
        <h1 className="mt-1 font-[family-name:var(--font-display)] text-2xl font-bold text-text">
          {data.title}
        </h1>
        {data.minutes ? (
          <p className="mt-1 text-sm text-text-dim">{data.minutes} min</p>
        ) : null}
      </div>
      <div className="sde-panel">
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-text-muted">{data.intro}</p>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <button type="button" className="btn-primary" onClick={() => void finish()} disabled={saving}>
          {locale === 'es' ? 'Listo, a las cartas' : 'Done — on to cards'}
        </button>
        <Link to="/" className="text-sm text-brand">
          {t('common.dashboard')}
        </Link>
      </div>
    </div>
  );
}
