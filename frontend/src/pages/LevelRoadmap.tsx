import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api, type Roadmap, type RoadmapSet, type SetStatus } from '../lib/api';
import { LockIcon } from '../components/LockIcon';

function fmtTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

function fmtMs(ms: number | null): string {
  if (ms == null) return '—';
  return fmtTime(Math.round(ms / 1000));
}

const STATUS_STYLE: Record<SetStatus, string> = {
  mastered: 'border-emerald-500/40 bg-emerald-500/10',
  current: 'border-brand bg-brand/10 ring-1 ring-brand',
  repeating: 'border-amber-500/50 bg-amber-500/10 ring-1 ring-amber-500/60',
  locked: 'border-border bg-surface-2 opacity-60',
};

const STATUS_BADGE: Record<SetStatus, { label: string; cls: string }> = {
  mastered: { label: 'Dominado', cls: 'text-emerald-400' },
  current: { label: 'Actual', cls: 'text-brand' },
  repeating: { label: 'Repetir', cls: 'text-amber-400' },
  locked: { label: 'Bloqueado', cls: 'text-text-dim' },
};

export function LevelRoadmap() {
  const { level: levelParam } = useParams();
  const level = (levelParam || 'a').toLowerCase();
  const [data, setData] = useState<Roadmap | null>(null);
  const [error, setError] = useState(false);

  const load = useCallback(() => {
    api.roadmap(level).then(setData).catch(() => setError(true));
  }, [level]);

  useEffect(() => { load(); }, [load]);

  if (error) {
    return (
      <div className="card space-y-3 text-center">
        <h2 className="page-title">No se pudo cargar el nivel</h2>
        <p className="text-text-muted">
          El servidor no respondió. Reinicia <code className="text-brand">npm run dev</code> (API en puerto 8001).
        </p>
        <button type="button" onClick={() => { setError(false); load(); }} className="btn-secondary">
          Reintentar
        </button>
      </div>
    );
  }
  if (!data) return <p className="text-text-muted">Cargando ejercicios…</p>;

  const pct = data.total_sets ? Math.round((data.mastered_sets / data.total_sets) * 100) : 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="page-title">Nivel {level.toUpperCase()}</h1>
          <p className="page-subtitle">200 paginas · 20 sets · 4 bloques · avance por dominio</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="badge-brand">{data.mastered_sets}/{data.total_sets} sets</span>
          <span className="badge-muted">{pct}% completado</span>
        </div>
      </div>

      {!data.unlocked ? (
        <div className="locked-card mx-auto max-w-lg text-center">
          <LockIcon className="mx-auto h-10 w-10 text-warning/70" />
          <h2 className="page-title mt-4">Nivel bloqueado</h2>
          <p className="mt-3 text-text-muted">
            Aprueba el examen de conclusion del nivel anterior para desbloquear este nivel.
          </p>
        </div>
      ) : (
        <>
          <TargetBanner data={data} />

          <p className="text-xs text-text-dim">
            Vista de progreso. Usa el dashboard para calcular tu sesion del dia.
          </p>
          {data.blocks.map((block) => {
            const sets = data.sets.filter((s) => s.block === block.letter);
            return (
              <div key={block.letter} className="card space-y-4">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <div>
                    <h2 className="text-lg font-semibold text-text">
                      Bloque {block.letter} · {block.title}
                    </h2>
                    <p className="text-xs text-text-dim">
                      Sets {block.set_start}–{block.set_end} · paginas {(block.set_start - 1) * 10 + 1}–{block.set_end * 10}
                    </p>
                  </div>
                </div>
                <p className="border-l-2 border-border pl-3 text-sm text-text-muted">{block.instruction}</p>

                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {sets.map((s) => <SetCard key={s.set_number} set={s} />)}
                </div>

                {block.checkpoint.exists && (
                  <CheckpointCard
                    level={level}
                    block={block.letter}
                    checkpoint={block.checkpoint}
                  />
                )}
              </div>
            );
          })}

          {data.exam.exists && <ExamCard data={data} level={level} />}
        </>
      )}
    </div>
  );
}

function TargetBanner({ data }: { data: Roadmap }) {
  const t = data.target;
  if (t.type === 'complete') {
    return (
      <div className="alert-success">
        Nivel completado. Felicidades — desbloqueaste el siguiente nivel.
      </div>
    );
  }
  let desc = '';
  if (t.type === 'set') {
    desc = t.repeating
      ? `Set ${t.set_number} pendiente de repeticion. Calcula tu sesion en el dashboard.`
      : `Siguiente set: ${t.set_number}. Calcula tu sesion en el dashboard.`;
  } else if (t.type === 'checkpoint') {
    desc = `Checkpoint del bloque ${t.block} pendiente.`;
  } else if (t.type === 'exam') {
    desc = 'Examen de conclusion del nivel pendiente.';
  }
  return (
    <div className="card border-brand/40 bg-brand/5">
      <p className="text-sm font-semibold text-text">Siguiente paso</p>
      <p className="text-sm text-text-muted">{desc}</p>
      <Link to="/" className="btn-primary mt-3 inline-block">Ir al dashboard</Link>
    </div>
  );
}

function SetCard({ set }: { set: RoadmapSet }) {
  const badge = STATUS_BADGE[set.status];
  const inner = (
    <div className={`flex h-full flex-col gap-2 rounded-xl border p-3 ${STATUS_STYLE[set.status]}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wide text-text-dim">Set {set.set_number}</span>
        <span className={`text-[11px] font-semibold ${badge.cls}`}>{badge.label}</span>
      </div>
      <p className="text-sm font-medium leading-snug text-text">{set.title}</p>
      <div className="mt-auto space-y-1 text-[11px] text-text-dim">
        <p>Paginas {set.page_start}–{set.page_end}</p>
        <p>Tiempo estandar: {fmtTime(set.standard_seconds)}</p>
        {set.status === 'mastered' ? (
          <p className="text-emerald-400">
            Mejor: {fmtMs(set.best_time_ms)} · {set.attempts} intento(s)
            {set.solid_mastery === false && ' · repaso pendiente'}
          </p>
        ) : set.status === 'current' || set.status === 'repeating' ? (
          <p>{set.completed}/{set.total} paginas · {set.attempts} intento(s)</p>
        ) : (
          <p>Se desbloquea en orden</p>
        )}
        {set.repeat_scheduled_for && (
          <p className="text-amber-400">Repeticion: {set.repeat_scheduled_for}</p>
        )}
      </div>
    </div>
  );
  return inner;
}

function CheckpointCard({ level, block, checkpoint }: {
  level: string;
  block: string;
  checkpoint: { problems: string[]; passed: boolean; available: boolean; exists: boolean };
}) {
  const state = checkpoint.passed ? 'passed' : checkpoint.available ? 'available' : 'locked';
  const styles = {
    passed: 'border-emerald-500/40 bg-emerald-500/10',
    available: 'border-brand/50 bg-brand/5',
    locked: 'border-border bg-surface-2 opacity-70',
  }[state];
  return (
    <div className={`flex flex-wrap items-center justify-between gap-3 rounded-xl border p-3 ${styles}`}>
      <div>
        <p className="text-sm font-semibold text-text">
          Checkpoint LeetCode · Bloque {block}
        </p>
        <p className="text-xs text-text-dim">
          {checkpoint.problems.length} problema(s) sobre lo aprendido en este bloque.
        </p>
      </div>
      {checkpoint.passed ? (
        <span className="badge-brand">Aprobado</span>
      ) : checkpoint.available ? (
        <Link to={`/${level}/checkpoint/${block}`} className="btn-secondary text-sm">Resolver</Link>
      ) : (
        <span className="inline-flex items-center gap-1 text-xs text-text-dim">
          <LockIcon className="h-3.5 w-3.5" /> Domina los 5 sets
        </span>
      )}
    </div>
  );
}

function ExamCard({ data, level }: { data: Roadmap; level: string }) {
  const exam = data.exam;
  return (
    <div className={`card flex flex-wrap items-center justify-between gap-3 ${exam.passed ? 'border-emerald-500/40 bg-emerald-500/10' : 'border-amber-500/30'}`}>
      <div>
        <h2 className="text-lg font-semibold text-text">Examen de conclusion · Pagina 200</h2>
        <p className="text-sm text-text-muted">
          {exam.leetcode.length} LeetCode + {exam.interview.length} preguntas de entrevista sobre todo el nivel.
        </p>
      </div>
      {exam.passed ? (
        <span className="badge-brand">Aprobado</span>
      ) : exam.available ? (
        <Link to={`/${level}/exam`} className="btn-primary">Presentar examen</Link>
      ) : (
        <span className="inline-flex items-center gap-1 text-xs text-text-dim">
          <LockIcon className="h-3.5 w-3.5" /> Domina los 20 sets y 4 checkpoints
        </span>
      )}
    </div>
  );
}
