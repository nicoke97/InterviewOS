import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api, type Exam as ExamData, type QuestionDetail } from '../lib/api';
import { LeetcodePanel } from '../components/LeetcodePanel';
import { LockIcon } from '../components/LockIcon';

type Tab = 'leetcode' | 'interview';

export function Exam() {
  const { level: levelParam } = useParams();
  const level = (levelParam || 'a').toLowerCase();
  const [data, setData] = useState<ExamData | null>(null);
  const [tab, setTab] = useState<Tab>('leetcode');
  const [selected, setSelected] = useState<string | null>(null);

  const load = useCallback(() => {
    api.exam(level).then((d) => {
      setData(d);
      setSelected((cur) => cur ?? d.leetcode[0]?.id ?? null);
    });
  }, [level]);

  useEffect(() => { load(); }, [load]);

  if (!data) return <p className="text-text-muted">Cargando examen…</p>;

  if (!data.available) {
    return (
      <div className="locked-card mx-auto max-w-lg text-center">
        <LockIcon className="mx-auto h-10 w-10 text-warning/70" />
        <h1 className="page-title mt-4">Examen bloqueado</h1>
        <p className="mt-3 text-text-muted">
          Domina los 20 sets y aprueba los 4 checkpoints del nivel {level.toUpperCase()} para presentar el examen.
        </p>
        <Link to={`/${level}/roadmap`} className="btn-secondary mt-4 inline-block">Ver mapa</Link>
      </div>
    );
  }

  const submitLeet = async (code: string) => {
    if (!selected) return { passed: false, result: {} };
    const res = await api.examSubmit({ level, exercise_id: selected, exercise_type: 'leetcode', code });
    load();
    return { passed: res.passed, result: res.result };
  };

  const list = tab === 'leetcode' ? data.leetcode : data.interview;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="page-title">Examen de conclusion · Nivel {level.toUpperCase()}</h1>
          <p className="page-subtitle">LeetCode + Interview sobre todo el nivel</p>
        </div>
        {data.passed && <span className="badge-brand">Examen aprobado</span>}
      </div>

      {data.passed && (
        <div className="alert-success">
          Aprobaste el examen del nivel {level.toUpperCase()}. El siguiente nivel esta desbloqueado.
        </div>
      )}

      <div className="segment max-w-md">
        <button type="button" onClick={() => { setTab('leetcode'); setSelected(data.leetcode[0]?.id ?? null); }}
          className={tab === 'leetcode' ? 'segment-btn-active' : 'segment-btn'}>
          LeetCode ({data.leetcode.filter((p) => p.passed).length}/{data.leetcode.length})
        </button>
        <button type="button" onClick={() => { setTab('interview'); setSelected(data.interview[0]?.id ?? null); }}
          className={tab === 'interview' ? 'segment-btn-active' : 'segment-btn'}>
          Interview ({data.interview.filter((q) => q.completed).length}/{data.interview.length})
        </button>
      </div>

      <div className="grid gap-5 lg:grid-cols-4">
        <div className="space-y-1.5">
          <p className="px-1 text-xs font-medium uppercase tracking-wide text-text-dim">
            {tab === 'leetcode' ? 'Problemas' : 'Preguntas'}
          </p>
          {list.map((item) => {
            const id = item.id;
            const ok = 'passed' in item ? item.passed : item.completed;
            const label = 'title' in item ? item.title : item.question.slice(0, 55) + '…';
            return (
              <button key={id} type="button" onClick={() => setSelected(id)}
                className={selected === id ? 'list-item-active' : 'list-item'}>
                <p className="font-medium text-text">{label}</p>
                <p className="mt-0.5 text-xs text-text-muted">{ok ? 'Hecho' : 'Pendiente'}</p>
              </button>
            );
          })}
        </div>

        <div className="lg:col-span-3">
          {selected && tab === 'leetcode' && (
            <LeetcodePanel
              problemId={selected}
              passed={data.leetcode.find((p) => p.id === selected)?.passed || false}
              onSubmit={submitLeet}
            />
          )}
          {selected && tab === 'interview' && (
            <InterviewPanel level={level} questionId={selected} onDone={load} />
          )}
        </div>
      </div>
    </div>
  );
}

function InterviewPanel({ level, questionId, onDone }: { level: string; questionId: string; onDone: () => void }) {
  const [q, setQ] = useState<QuestionDetail | null>(null);
  const [answer, setAnswer] = useState('');
  const [revealed, setRevealed] = useState(false);
  const [score, setScore] = useState(0);

  useEffect(() => {
    api.question(questionId).then((d) => {
      setQ(d);
      setAnswer('');
      setRevealed(false);
      setScore(0);
    });
  }, [questionId]);

  if (!q) return <p className="text-text-muted">Cargando pregunta…</p>;

  const save = async () => {
    await api.examSubmit({
      level, exercise_id: questionId, exercise_type: 'interview',
      answer_text: answer, self_score: score,
    });
    onDone();
  };

  return (
    <div className="space-y-4">
      <div className="card"><p className="text-base leading-relaxed text-text">{q.question}</p></div>
      <textarea
        className="input-field h-40 resize-none"
        placeholder="Escribe tu respuesta…"
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
      />
      <button type="button" onClick={() => setRevealed(true)} className="btn-secondary">
        Ver rubrica y respuesta modelo
      </button>
      {revealed && (
        <div className="card space-y-4">
          <div>
            <p className="text-sm font-medium text-warning">Rubrica</p>
            <ul className="mt-2 space-y-1 text-sm text-text-muted">
              {q.rubric.map((r, i) => <li key={i}>· {r}</li>)}
            </ul>
          </div>
          <div className="border-t border-border pt-4">
            <p className="text-sm font-medium text-brand">Respuesta modelo</p>
            <p className="mt-2 text-sm leading-relaxed text-text-muted">{q.sample_answer}</p>
          </div>
          <div className="border-t border-border pt-4">
            <p className="mb-3 text-sm font-medium text-text">Autoevaluacion (1–4)</p>
            <div className="flex gap-2">
              {[1, 2, 3, 4].map((n) => (
                <button key={n} type="button" onClick={() => setScore(n)}
                  className={`flex h-10 w-10 items-center justify-center rounded-xl text-sm font-medium transition-colors ${
                    score === n ? 'bg-brand text-bg' : 'bg-surface-2 text-text-muted hover:bg-surface hover:text-text'
                  }`}>
                  {n}
                </button>
              ))}
            </div>
          </div>
          <button type="button" onClick={save} disabled={!score} className="btn-primary">
            Marcar como completada
          </button>
        </div>
      )}
    </div>
  );
}
