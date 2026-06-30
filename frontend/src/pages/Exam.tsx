import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api, type Exam as ExamData, type QuestionDetail } from '../lib/api';
import { LeetcodePanel } from '../components/LeetcodePanel';
import { LockIcon } from '../components/LockIcon';
import { useI18n } from '../i18n/context';

type Tab = 'leetcode' | 'interview';

export function Exam() {
  const { t, locale } = useI18n();
  const { level: levelParam } = useParams();
  const level = (levelParam || 'a').toLowerCase();
  const [data, setData] = useState<ExamData | null>(null);
  const [tab, setTab] = useState<Tab>('leetcode');
  const [selected, setSelected] = useState<string | null>(null);

  const load = useCallback(() => {
    void locale;
    api.exam(level).then((d) => {
      setData(d);
      setSelected((cur) => cur ?? d.leetcode[0]?.id ?? null);
    });
  }, [level, locale]);

  useEffect(() => { load(); }, [load]);

  if (!data) return <p className="text-text-muted">{t('exam.loading')}</p>;

  if (!data.available) {
    return (
      <div className="locked-card mx-auto max-w-lg text-center">
        <LockIcon className="mx-auto h-10 w-10 text-warning/70" />
        <h1 className="page-title mt-4">{t('exam.lockedTitle')}</h1>
        <p className="mt-3 text-text-muted">
          {t('exam.lockedDesc', { level: level.toUpperCase() })}
        </p>
        <Link to={`/${level}/roadmap`} className="btn-secondary mt-4 inline-block">{t('common.viewMap')}</Link>
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
          <h1 className="page-title">{t('exam.title', { level: level.toUpperCase() })}</h1>
          <p className="page-subtitle">{t('exam.subtitle')}</p>
        </div>
        {data.passed && <span className="badge-brand">{t('exam.passed')}</span>}
      </div>

      {data.passed && (
        <div className="alert-success">
          {t('exam.success', { level: level.toUpperCase() })}
        </div>
      )}

      <div className="segment max-w-md">
        <button type="button" onClick={() => { setTab('leetcode'); setSelected(data.leetcode[0]?.id ?? null); }}
          className={tab === 'leetcode' ? 'segment-btn-active' : 'segment-btn'}>
          {t('exam.tabLeetcode', { passed: data.leetcode.filter((p) => p.passed).length, total: data.leetcode.length })}
        </button>
        <button type="button" onClick={() => { setTab('interview'); setSelected(data.interview[0]?.id ?? null); }}
          className={tab === 'interview' ? 'segment-btn-active' : 'segment-btn'}>
          {t('exam.tabInterview', { done: data.interview.filter((q) => q.completed).length, total: data.interview.length })}
        </button>
      </div>

      <div className="grid gap-5 xl:grid-cols-5">
        <div className="space-y-1.5 xl:col-span-1">
          <p className="px-1 text-xs font-medium uppercase tracking-wide text-text-dim">
            {tab === 'leetcode' ? t('common.problems') : t('common.questions')}
          </p>
          {list.map((item) => {
            const id = item.id;
            const ok = 'passed' in item ? item.passed : item.completed;
            const label = 'title' in item ? item.title : item.question.slice(0, 55) + '…';
            return (
              <button key={id} type="button" onClick={() => setSelected(id)}
                className={selected === id ? 'list-item-active' : 'list-item'}>
                <p className="font-medium text-text">{label}</p>
                <p className="mt-0.5 text-xs text-text-muted">{ok ? t('common.done') : t('common.pending')}</p>
              </button>
            );
          })}
        </div>

        <div className="xl:col-span-4">
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
  const { t, locale } = useI18n();
  const [q, setQ] = useState<QuestionDetail | null>(null);
  const [answer, setAnswer] = useState('');
  const [revealed, setRevealed] = useState(false);
  const [score, setScore] = useState(0);

  useEffect(() => {
    void locale;
    api.question(questionId).then((d) => {
      setQ(d);
      setAnswer('');
      setRevealed(false);
      setScore(0);
    });
  }, [questionId, locale]);

  if (!q) return <p className="text-text-muted">{t('exam.interviewLoading')}</p>;

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
        placeholder={t('exam.interviewPlaceholder')}
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
      />
      <button type="button" onClick={() => setRevealed(true)} className="btn-secondary">
        {t('exam.showRubric')}
      </button>
      {revealed && (
        <div className="card space-y-4">
          <div>
            <p className="text-sm font-medium text-warning">{t('exam.rubric')}</p>
            <ul className="mt-2 space-y-1 text-sm text-text-muted">
              {q.rubric.map((r, i) => <li key={i}>· {r}</li>)}
            </ul>
          </div>
          <div className="border-t border-border pt-4">
            <p className="text-sm font-medium text-brand">{t('exam.modelAnswer')}</p>
            <p className="mt-2 text-sm leading-relaxed text-text-muted">{q.sample_answer}</p>
          </div>
          <div className="border-t border-border pt-4">
            <p className="mb-3 text-sm font-medium text-text">{t('exam.selfScore')}</p>
            <div className="flex gap-2">
              {[1, 2, 3, 4].map((n) => (
                <button key={n} type="button" onClick={() => setScore(n)}
                  className={`flex h-10 w-10 items-center justify-center rounded-xl text-sm font-medium transition-colors ${
                    score === n ? 'bg-brand text-on-brand' : 'bg-surface-2 text-text-muted hover:bg-surface hover:text-text'
                  }`}>
                  {n}
                </button>
              ))}
            </div>
          </div>
          <button type="button" onClick={save} disabled={!score} className="btn-primary">
            {t('exam.markComplete')}
          </button>
        </div>
      )}
    </div>
  );
}
