import { useEffect, useState } from 'react';
import { api } from '../lib/api';

const LEVELS = ['a', 'b', 'c'];

export function Interview({ category }: { category?: string }) {
  const title = category === 'odoo' ? 'Odoo Corner' : 'Interview Questions';
  const [level, setLevel] = useState('a');
  const [questions, setQuestions] = useState<{ id: string; question: string; completed: boolean }[]>([]);
  const [unlocked, setUnlocked] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [answer, setAnswer] = useState('');
  const [revealed, setRevealed] = useState(false);
  const [rubric, setRubric] = useState<string[]>([]);
  const [sample, setSample] = useState('');
  const [selfScore, setSelfScore] = useState(0);

  useEffect(() => {
    api.interviewList(level, category).then((res) => {
      setUnlocked(!!res.unlocked);
      setQuestions((res.questions as typeof questions) || []);
    });
  }, [level, category]);

  const selectQuestion = async (id: string) => {
    setSelected(id);
    setAnswer('');
    setRevealed(false);
    setSelfScore(0);
  };

  const reveal = async () => {
    if (!selected) return;
    const a = await api.interviewAnswer(selected);
    setRubric((a.rubric as string[]) || []);
    setSample(String(a.sample_answer || ''));
    setRevealed(true);
  };

  const submitScore = async () => {
    if (!selected) return;
    await api.submit({
      code: answer,
      exercise_id: selected,
      exercise_type: 'interview',
      self_score: selfScore,
      time_ms: 0,
    });
    setQuestions((qs) => qs.map((q) => q.id === selected ? { ...q, completed: true } : q));
  };

  const current = questions.find((q) => q.id === selected);

  if (!unlocked) {
    return (
      <div className="card text-center">
        <h1 className="text-xl font-bold">{title} Locked</h1>
        <p className="mt-2 text-slate-400">
          Pass all LeetCode Tier 3 problems in Level {level.toUpperCase()} to unlock.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{title}</h1>
        <div className="flex gap-2">
          {LEVELS.map((l) => (
            <button
              key={l}
              type="button"
              onClick={() => { setLevel(l); setSelected(null); }}
              className={`rounded px-3 py-1 text-sm ${level === l ? 'bg-emerald-600' : 'bg-slate-700'}`}
            >
              Level {l.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-2">
          {questions.map((q) => (
            <button
              key={q.id}
              type="button"
              onClick={() => selectQuestion(q.id)}
              className={`block w-full rounded-lg border p-3 text-left text-sm ${
                selected === q.id ? 'border-emerald-500' : 'border-slate-600'
              } ${q.completed ? 'opacity-70' : ''}`}
            >
              {q.completed && <span className="text-emerald-400">✓ </span>}
              {q.question.slice(0, 60)}...
            </button>
          ))}
        </div>

        <div className="md:col-span-2 space-y-4">
          {current ? (
            <>
              <div className="card">
                <p className="text-lg">{current.question}</p>
              </div>
              <textarea
                className="h-40 w-full rounded-lg border border-slate-600 bg-slate-900 p-3 text-sm"
                placeholder="Write your answer here..."
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
              />
              <button type="button" onClick={reveal} className="btn-secondary">
                Reveal rubric & sample answer
              </button>
              {revealed && (
                <div className="card space-y-3">
                  <div>
                    <p className="text-sm font-medium text-amber-400">Rubric</p>
                    <ul className="mt-1 list-inside list-disc text-sm text-slate-300">
                      {rubric.map((r, i) => <li key={i}>{r}</li>)}
                    </ul>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-emerald-400">Sample Answer</p>
                    <p className="mt-1 text-sm text-slate-300">{sample}</p>
                  </div>
                  <div>
                    <p className="mb-2 text-sm">Self-score (1-4)</p>
                    <div className="flex gap-2">
                      {[1, 2, 3, 4].map((n) => (
                        <button
                          key={n}
                          type="button"
                          onClick={() => setSelfScore(n)}
                          className={`h-10 w-10 rounded ${selfScore === n ? 'bg-emerald-600' : 'bg-slate-700'}`}
                        >
                          {n}
                        </button>
                      ))}
                    </div>
                  </div>
                  <button type="button" onClick={submitScore} className="btn-primary" disabled={!selfScore}>
                    Save score
                  </button>
                </div>
              )}
            </>
          ) : (
            <p className="text-slate-400">Select a question</p>
          )}
        </div>
      </div>
    </div>
  );
}
