import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api, type Checkpoint as CheckpointData } from '../lib/api';
import { LeetcodePanel } from '../components/LeetcodePanel';
import { LockIcon } from '../components/LockIcon';
import { useI18n } from '../i18n/context';

export function Checkpoint() {
  const { t, locale } = useI18n();
  const { level: levelParam, block: blockParam } = useParams();
  const level = (levelParam || 'a').toLowerCase();
  const block = (blockParam || 'A').toUpperCase();
  const [data, setData] = useState<CheckpointData | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  const load = useCallback(() => {
    void locale;
    api.checkpoint(level, block).then((d) => {
      setData(d);
      setSelected((cur) => cur ?? d.problems[0]?.id ?? null);
    });
  }, [level, block, locale]);

  useEffect(() => { load(); }, [load]);

  if (!data) return <p className="text-text-muted">{t('checkpoint.loading')}</p>;

  if (!data.available) {
    return (
      <div className="locked-card mx-auto max-w-lg text-center">
        <LockIcon className="mx-auto h-10 w-10 text-warning/70" />
        <h1 className="page-title mt-4">{t('checkpoint.lockedTitle')}</h1>
        <p className="mt-3 text-text-muted">{t('checkpoint.lockedDesc', { block })}</p>
        <Link to={`/${level}/roadmap`} className="btn-secondary mt-4 inline-block">{t('common.viewMap')}</Link>
      </div>
    );
  }

  const submit = async (code: string) => {
    if (!selected) return { passed: false, result: {} };
    const res = await api.checkpointSubmit({ level, problem_id: selected, code });
    load();
    return { passed: res.passed, result: res.result };
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="page-title">{t('checkpoint.title', { block })}</h1>
          <p className="page-subtitle">{t('checkpoint.subtitle', { level: level.toUpperCase(), blockTitle: data.block_title })}</p>
        </div>
        {data.passed ? (
          <span className="badge-brand">{t('checkpoint.passed')}</span>
        ) : (
          <Link to={`/${level}/roadmap`} className="btn-secondary text-sm">{t('common.backToMap')}</Link>
        )}
      </div>

      {data.passed && (
        <div className="alert-success">
          {t('checkpoint.success', { block })}
        </div>
      )}

      <div className="grid gap-5 xl:grid-cols-5">
        <div className="space-y-1.5 xl:col-span-1">
          <p className="px-1 text-xs font-medium uppercase tracking-wide text-text-dim">{t('common.problems')}</p>
          {data.problems.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => setSelected(p.id)}
              className={selected === p.id ? 'list-item-active' : 'list-item'}
            >
              <p className="font-medium text-text">{p.title}</p>
              <p className="mt-0.5 text-xs text-text-muted">{p.passed ? t('common.solved') : t('common.pending')}</p>
            </button>
          ))}
        </div>

        <div className="xl:col-span-4">
          {selected ? (
            <LeetcodePanel
              problemId={selected}
              passed={data.problems.find((p) => p.id === selected)?.passed || false}
              onSubmit={submit}
            />
          ) : (
            <div className="empty-state"><p className="text-text-muted">{t('checkpoint.selectProblem')}</p></div>
          )}
        </div>
      </div>
    </div>
  );
}
