import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { orientadorAssignmentPath } from '../lib/orientadorLabels';
import { api, type KumonPage, type SessionData, type SetSubmitResult, type DrillResult } from '../lib/api';
import { KumonProblem } from '../components/KumonProblem';
import { Timer, useSessionTimer } from '../components/Timer';

const COUNT_OPTIONS = [3, 5, 10];

function fmt(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

export function KumonSession() {
  const { level: levelParam, planId, index: indexParam } = useParams<{
    level?: string;
    planId?: string;
    index?: string;
  }>();
  const navigate = useNavigate();
  const isOrientador = Boolean(planId && indexParam);
  const orientadorPlanId = planId ? Number(planId) : undefined;
  const orientadorIndex = indexParam != null ? Number(indexParam) : undefined;
  const level = (levelParam || 'a').toLowerCase();
  const [count, setCount] = useState(10);
  const [data, setData] = useState<SessionData | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [results, setResults] = useState<Record<string, DrillResult>>({});
  const [dirtyIds, setDirtyIds] = useState<Set<string>>(() => new Set());
  const [outcome, setOutcome] = useState<SetSubmitResult | null>(null);
  const [checked, setChecked] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const { running, start, stop, onTick, seconds: secondsRef } = useSessionTimer('study');
  const timerStartedRef = useRef(false);

  const load = useCallback(async () => {
    const d = isOrientador
      ? await api.orientadorSession(orientadorPlanId!, orientadorIndex!)
      : await api.session(level, count);
    if (isOrientador && d.type === 'checkpoint') {
      navigate(`/${d.level}/checkpoint/${d.checkpoint?.block ?? d.assignment?.block}`);
      return;
    }
    if (isOrientador && d.type === 'exam') {
      navigate(`/${d.level}/exam`);
      return;
    }
    setData(d);
    const init: Record<string, string> = {};
    (d.drills || []).forEach((p) => { init[p.id] = ''; });
    setAnswers(init);
    setResults({});
    setDirtyIds(new Set());
    setOutcome(null);
    setChecked(false);
    setSubmitError(null);
    timerStartedRef.current = false;
  }, [level, count, isOrientador, orientadorPlanId, orientadorIndex, navigate]);

  useEffect(() => { load(); }, [load]);

  const ensureTimer = useCallback(() => {
    if (!timerStartedRef.current) {
      timerStartedRef.current = true;
      void start();
    }
  }, [start]);

  const updateAnswer = (id: string, code: string) => {
    setAnswers((prev) => ({ ...prev, [id]: code }));
    if (checked) {
      setDirtyIds((prev) => new Set(prev).add(id));
    }
    if (code.length > 0) ensureTimer();
  };

  const check = async () => {
    if (!data || !data.drills) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      if (running) await stop();
      const time_ms = secondsRef.current * 1000;
      const res = await api.setSubmit({
        level: data.level || level,
        set_number: data.set_number!,
        time_ms,
        answers: data.drills.map((d) => ({ exercise_id: d.id, code: answers[d.id] || '' })),
        plan_id: isOrientador ? orientadorPlanId : undefined,
        assignment_index: isOrientador ? orientadorIndex : undefined,
      });
      setResults(res.results);
      setOutcome(res);
      setChecked(true);
      setDirtyIds(new Set());
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'No se pudo revisar las respuestas');
    } finally {
      setSubmitting(false);
    }
  };

  if (!data) return <p className="text-text-muted">Cargando sesion…</p>;

  if (data.type !== 'set') {
    return <NonSetState data={data} level={level} />;
  }

  const drills = data.drills || [];
  const standard = data.standard_seconds || 0;
  const passedCount = Object.values(results).filter((r) => r.passed).length;
  const failedIds = drills
    .filter((d) => checked && results[d.id] && !results[d.id].passed && !dirtyIds.has(d.id))
    .map((d) => d.id);
  const needsRecheck = checked && (failedIds.length > 0 || dirtyIds.size > 0);

  const scrollToFirstFailed = () => {
    const el = document.querySelector('[data-review-status="failed"]');
    el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  const sessionLevel = data.level || level;
  const reason = data.assignment?.reason;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="page-title">
            {isOrientador && reason === 'repeat' ? 'Repeticion · ' : ''}
            Set {data.set_number} · Nivel {sessionLevel.toUpperCase()}
          </h1>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <span className="badge">Bloque {data.block}</span>
            {reason === 'repeat' && <span className="badge-amber">Repeticion programada</span>}
            {reason === 'pre_exam' && <span className="badge-amber">Repaso pre-examen</span>}
            {data.status === 'repeating' && <span className="badge-amber">Repitiendo</span>}
            <span className="text-sm text-text-muted">
              {data.set_title} · {data.completed}/{data.total} dominadas · {data.page_range}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {!isOrientador && <CountPicker count={count} setCount={setCount} disabled={checked} />}
          <div className="timer-pill">
            <Timer running={running} onTick={onTick} />
            <span className="ml-1 text-xs text-text-dim">/ {fmt(standard)}</span>
          </div>
        </div>
      </div>

      {data.status === 'repeating' && !isOrientador && (
        <div className="alert-error">
          La ultima vez superaste el tiempo estandar. Repite el set completo, corrige tus errores y
          termina dentro de {fmt(standard)} para dominarlo.
        </div>
      )}
      {isOrientador && reason === 'repeat' && (
        <div className="alert-error">
          Repeticion del orientador: resuelve las 10 paginas dentro de {fmt(standard)} para consolidar el dominio.
        </div>
      )}

      <div className="mx-auto max-w-4xl rounded-sm border border-stone-400 bg-stone-200 p-1 shadow-2xl">
        <div className="bg-[#fffef8] px-5 py-5 text-stone-900 sm:px-8 sm:py-6">
          <div className="mb-4 border-b-2 border-stone-800 pb-3">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-stone-500">InterviewOS</p>
                <h2 className="text-xl font-bold tracking-tight text-stone-900">{data.set_title}</h2>
              </div>
              <div className="text-right text-xs font-medium text-stone-600">
                <p>Set {data.set_number}</p>
                <p>Bloque {data.block}</p>
              </div>
            </div>
          </div>

          <p className="mb-5 border-l-4 border-stone-800 pl-3 text-sm font-medium leading-relaxed text-stone-700">
            {data.instruction}
          </p>

          <div className="columns-1 gap-x-4 sm:columns-2">
            {drills.map((page: KumonPage, i: number) => {
              const reviewStatus = !checked
                ? 'pending'
                : dirtyIds.has(page.id)
                  ? 'edited'
                  : results[page.id]?.passed
                    ? 'passed'
                    : results[page.id]
                      ? 'failed'
                      : 'pending';
              return (
              <div key={page.id} className="mb-4 break-inside-avoid">
                <KumonProblem
                  number={i + 1}
                  pageLabel={page.id}
                  drill={page}
                  value={answers[page.id] || ''}
                  onChange={(code) => updateAnswer(page.id, code)}
                  result={results[page.id]}
                  reviewStatus={reviewStatus}
                />
              </div>
              );
            })}
          </div>

          <div className="mt-6 border-t border-dashed border-stone-400 pt-5">
            {!checked ? (
              <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-between">
                <div className="text-center sm:text-left">
                  <p className="text-xs text-stone-500">
                    Resuelve estas {drills.length} paginas y revisa tus respuestas. Cuenta el tiempo.
                  </p>
                  {submitError && (
                    <p className="mt-2 text-xs text-red-700">{submitError}</p>
                  )}
                </div>
                <button
                  type="button"
                  onClick={check}
                  disabled={submitting}
                  className="rounded border-2 border-stone-900 bg-stone-900 px-8 py-2.5 text-sm font-bold text-[#fffef8] transition hover:bg-stone-700 disabled:opacity-50"
                >
                  {submitting ? 'Revisando…' : 'Revisar respuestas'}
                </button>
              </div>
            ) : (
              <ResultPanel
                outcome={outcome}
                passedCount={passedCount}
                total={drills.length}
                failedCount={failedIds.length}
                editedCount={dirtyIds.size}
                needsRecheck={needsRecheck}
                onContinue={load}
                onRecheck={check}
                onScrollToFailed={scrollToFirstFailed}
                rechecking={submitting}
                level={sessionLevel}
                isOrientador={isOrientador}
                planId={orientadorPlanId}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function CountPicker({ count, setCount, disabled }: { count: number; setCount: (n: number) => void; disabled: boolean }) {
  return (
    <div className="flex items-center gap-1 rounded-lg bg-surface-2 p-1">
      {COUNT_OPTIONS.map((n) => (
        <button
          key={n}
          type="button"
          disabled={disabled}
          onClick={() => setCount(n)}
          className={`rounded px-2.5 py-1 text-xs font-medium transition ${
            count === n ? 'bg-brand text-bg' : 'text-text-muted hover:text-text'
          } disabled:opacity-40`}
        >
          {n}
        </button>
      ))}
    </div>
  );
}

function ResultPanel({ outcome, passedCount, total, failedCount, editedCount, needsRecheck, onContinue, onRecheck, onScrollToFailed, rechecking, level, isOrientador, planId }: {
  outcome: SetSubmitResult | null;
  passedCount: number;
  total: number;
  failedCount: number;
  editedCount: number;
  needsRecheck: boolean;
  onContinue: () => void;
  onRecheck: () => void;
  onScrollToFailed: () => void;
  rechecking: boolean;
  level: string;
  isOrientador?: boolean;
  planId?: number;
}) {
  if (!outcome) return null;
  const accSec = Math.round(outcome.accumulated_time_ms / 1000);
  const stdSec = Math.round(outcome.standard_ms / 1000);
  const backTo = isOrientador ? '/' : `/${level}/roadmap`;
  const backLabel = isOrientador ? 'Volver al dashboard' : 'Ver mapa';

  const next = outcome.next_assignment;
  const nextTo = next
    ? orientadorAssignmentPath(next.plan_id, next.index, next.assignment)
    : null;
  const nextLabel = outcome.session_complete
    ? 'Sesion completada'
    : 'Siguiente asignacion';
  const nextHref = nextTo ?? '/';

  if (outcome.outcome === 'mastered') {
    return (
      <div className="space-y-3 text-center">
        <p className="text-xl font-bold text-emerald-700">Set dominado!</p>
        <p className="text-sm text-stone-600">
          {passedCount}/{total} correctas · tiempo {fmt(accSec)} ≤ estandar {fmt(stdSec)}.
        </p>
        {outcome.needs_repeat && (
          <p className="text-xs text-amber-700">
            Repeticion programada manana para consolidar ({Math.round((outcome.first_attempt_accuracy ?? 0) * 100)}% en primer intento).
          </p>
        )}
        <div className="flex justify-center gap-2">
          {isOrientador ? (
            <Link
              to={nextHref}
              className="rounded border-2 border-stone-900 bg-stone-900 px-6 py-2 text-sm font-bold text-[#fffef8] hover:bg-stone-700"
            >
              {nextLabel}
            </Link>
          ) : (
            <button type="button" onClick={onContinue} className="rounded border-2 border-stone-900 bg-stone-900 px-6 py-2 text-sm font-bold text-[#fffef8] hover:bg-stone-700">
              Siguiente set
            </button>
          )}
          <Link to={backTo} className="rounded border border-stone-500 px-5 py-2 text-sm font-medium text-stone-700 hover:bg-stone-100">
            {backLabel}
          </Link>
        </div>
      </div>
    );
  }

  if (outcome.outcome === 'too_slow') {
    return (
      <div className="space-y-3 text-center">
        <p className="text-xl font-bold text-amber-700">Completo, pero lento</p>
        <p className="text-sm text-stone-600">
          Resolviste todo el set pero superaste el tiempo estandar de {fmt(stdSec)}.
          {outcome.repeat_scheduled_for
            ? ` Repeticion programada para ${outcome.repeat_scheduled_for}.`
            : ' El orientador programara una repeticion.'}
        </p>
        {isOrientador ? (
          <Link
            to={nextHref}
            className="inline-block rounded border-2 border-stone-900 bg-stone-900 px-6 py-2 text-sm font-bold text-[#fffef8] hover:bg-stone-700"
          >
            {nextTo ? 'Siguiente asignacion' : 'Volver al dashboard'}
          </Link>
        ) : (
          <button type="button" onClick={onContinue} className="rounded border-2 border-stone-900 bg-stone-900 px-6 py-2 text-sm font-bold text-[#fffef8] hover:bg-stone-700">
            Repetir set
          </button>
        )}
      </div>
    );
  }

  const missed = failedCount;
  return (
    <div className="space-y-3 text-center">
      <p className={`text-xl font-bold ${missed === 0 && editedCount === 0 ? 'text-emerald-700' : 'text-stone-800'}`}>
        {passedCount}/{total} correctas
      </p>
      <p className="text-sm text-stone-600">
        {missed > 0
          ? `${missed} ejercicio(s) en rojo por corregir. Los verdes ya estan bien.`
          : editedCount > 0
            ? 'Revisa de nuevo los ejercicios modificados.'
            : `Vas ${outcome.completed}/${outcome.set_total} del set. Continua con mas paginas.`}
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        {missed > 0 && (
          <button type="button" onClick={onScrollToFailed} className="rounded border border-stone-500 px-5 py-2 text-sm font-medium text-stone-700 hover:bg-stone-100">
            Ir al primer error
          </button>
        )}
        {needsRecheck && (
          <button
            type="button"
            onClick={onRecheck}
            disabled={rechecking}
            className="rounded border-2 border-stone-900 bg-stone-900 px-6 py-2 text-sm font-bold text-[#fffef8] hover:bg-stone-700 disabled:opacity-50"
          >
            {rechecking ? 'Revisando…' : 'Revisar de nuevo'}
          </button>
        )}
        <button type="button" onClick={onContinue} className="rounded border border-stone-500 px-5 py-2 text-sm font-medium text-stone-700 hover:bg-stone-100">
          Siguientes paginas
        </button>
      </div>
    </div>
  );
}

function NonSetState({ data, level }: { data: SessionData; level: string }) {
  const t = data.target?.type || data.type;
  if (t === 'locked') {
    return (
      <div className="locked-card mx-auto max-w-lg text-center">
        <h1 className="page-title">Nivel bloqueado</h1>
        <p className="mt-3 text-text-muted">Aprueba el examen del nivel anterior para empezar aqui.</p>
        <Link to={`/${level}/roadmap`} className="btn-secondary mt-4 inline-block">Ver mapa</Link>
      </div>
    );
  }
  if (t === 'checkpoint') {
    const block = data.target?.block;
    return (
      <div className="card mx-auto max-w-lg text-center">
        <h1 className="page-title">Checkpoint pendiente</h1>
        <p className="mt-3 text-text-muted">
          Terminaste las paginas del bloque {block}. Resuelve el checkpoint de LeetCode para continuar.
        </p>
        <Link to={`/${level}/checkpoint/${block}`} className="btn-primary mt-4 inline-block">Ir al checkpoint</Link>
      </div>
    );
  }
  if (t === 'exam') {
    return (
      <div className="card mx-auto max-w-lg text-center">
        <h1 className="page-title">Examen de nivel</h1>
        <p className="mt-3 text-text-muted">Dominaste los 20 sets. Presenta el examen de conclusion.</p>
        <Link to={`/${level}/exam`} className="btn-primary mt-4 inline-block">Ir al examen</Link>
      </div>
    );
  }
  return (
    <div className="alert-success mx-auto max-w-lg text-center">
      Nivel completado. <Link to={`/${level}/roadmap`} className="underline">Ver mapa</Link>
    </div>
  );
}
