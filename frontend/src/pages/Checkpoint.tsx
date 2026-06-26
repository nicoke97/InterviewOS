import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api, type Checkpoint as CheckpointData } from '../lib/api';
import { LeetcodePanel } from '../components/LeetcodePanel';
import { LockIcon } from '../components/LockIcon';

export function Checkpoint() {
  const { level: levelParam, block: blockParam } = useParams();
  const level = (levelParam || 'a').toLowerCase();
  const block = (blockParam || 'A').toUpperCase();
  const [data, setData] = useState<CheckpointData | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  const load = useCallback(() => {
    api.checkpoint(level, block).then((d) => {
      setData(d);
      setSelected((cur) => cur ?? d.problems[0]?.id ?? null);
    });
  }, [level, block]);

  useEffect(() => { load(); }, [load]);

  if (!data) return <p className="text-text-muted">Cargando checkpoint…</p>;

  if (!data.available) {
    return (
      <div className="locked-card mx-auto max-w-lg text-center">
        <LockIcon className="mx-auto h-10 w-10 text-warning/70" />
        <h1 className="page-title mt-4">Checkpoint bloqueado</h1>
        <p className="mt-3 text-text-muted">Domina los 5 sets del bloque {block} para desbloquear el checkpoint.</p>
        <Link to={`/${level}/roadmap`} className="btn-secondary mt-4 inline-block">Ver mapa</Link>
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
          <h1 className="page-title">Checkpoint · Bloque {block}</h1>
          <p className="page-subtitle">Nivel {level.toUpperCase()} · {data.block_title}</p>
        </div>
        {data.passed ? (
          <span className="badge-brand">Checkpoint aprobado</span>
        ) : (
          <Link to={`/${level}/roadmap`} className="btn-secondary text-sm">Volver al mapa</Link>
        )}
      </div>

      {data.passed && (
        <div className="alert-success">
          Aprobaste el checkpoint del bloque {block}. El siguiente bloque esta desbloqueado.
        </div>
      )}

      <div className="grid gap-5 lg:grid-cols-4">
        <div className="space-y-1.5">
          <p className="px-1 text-xs font-medium uppercase tracking-wide text-text-dim">Problemas</p>
          {data.problems.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => setSelected(p.id)}
              className={selected === p.id ? 'list-item-active' : 'list-item'}
            >
              <p className="font-medium text-text">{p.title}</p>
              <p className="mt-0.5 text-xs text-text-muted">{p.passed ? 'Resuelto' : 'Pendiente'}</p>
            </button>
          ))}
        </div>

        <div className="lg:col-span-3">
          {selected ? (
            <LeetcodePanel
              problemId={selected}
              passed={data.problems.find((p) => p.id === selected)?.passed || false}
              onSubmit={submit}
            />
          ) : (
            <div className="empty-state"><p className="text-text-muted">Selecciona un problema.</p></div>
          )}
        </div>
      </div>
    </div>
  );
}
