import { useEffect, useRef, useState } from 'react';
import { api, type ProblemDetail } from '../lib/api';
import { CodeEditor } from './CodeEditor';
import { ResizableSplit } from './ResizableSplit';
import { WhereToStartGuide } from './WhereToStartGuide';
import { useI18n } from '../i18n/context';
import {
  STUDY_LANG_LABEL,
  ensureHintLockStart,
  formatCountdown,
  hintUnlockAt,
  languageOfDay,
} from '../lib/studySession';

type ExecLang = 'python' | 'csharp';

const LC_LANG_KEY = 'codenda-lc-lang';

function readLcLang(): ExecLang {
  try {
    const stored = localStorage.getItem(LC_LANG_KEY);
    if (stored === 'csharp' || stored === 'python') return stored;
  } catch {
    /* ignore */
  }
  return 'python';
}

function writeLcLang(lang: ExecLang) {
  try {
    localStorage.setItem(LC_LANG_KEY, lang);
  } catch {
    /* ignore */
  }
}

function canSwitchLanguage(problemId: string, mode: string) {
  return mode === 'practice' || mode === 'guided' || problemId.startsWith('lc-');
}

interface LeetcodePanelProps {
  problemId: string;
  passed: boolean;
  tier?: number;
  tierPassed?: number;
  mode?: 'official' | 'practice' | 'guided';
  hintLockMinutes?: number;
  onSubmit: (code: string, language?: string) => Promise<{ passed: boolean; result: Record<string, unknown> }>;
}

/* ── Inline icons (no external lib) ── */

function Icon({ d, className = 'h-4 w-4' }: { d: string; className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
      <path strokeLinecap="round" strokeLinejoin="round" d={d} />
    </svg>
  );
}

const icons = {
  doc: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
  checklist: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
  code: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4',
  lightbulb: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
  book: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253',
  chat: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
  mic: 'M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z',
  play: 'M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  check: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
  copy: 'M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z',
  arrow: 'M13 7l5 5m0 0l-5 5m5-5H6',
};

function ProblemText({ text }: { text: string }) {
  const paragraphs = text.split(/\n\n+/).filter(Boolean);
  return (
    <div className="space-y-3">
      {paragraphs.map((para, i) => (
        <p key={i} className="text-sm leading-relaxed text-text-muted">{para}</p>
      ))}
    </div>
  );
}

function difficultyClass(d?: string) {
  if (d === 'easy') return 'lc-difficulty lc-difficulty-easy';
  if (d === 'medium') return 'lc-difficulty lc-difficulty-medium';
  if (d === 'hard') return 'lc-difficulty lc-difficulty-hard';
  return 'badge-muted capitalize';
}

function PanelHeader({ icon, title, subtitle, actions }: {
  icon: keyof typeof icons;
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="lc-panel-header">
      <div className="lc-section-icon">
        <Icon d={icons[icon]} className="h-3.5 w-3.5" />
      </div>
      <div className="min-w-0 flex-1">
        <h3 className="text-sm font-semibold text-text">{title}</h3>
        {subtitle && <p className="text-xs text-text-dim">{subtitle}</p>}
      </div>
      {actions}
    </div>
  );
}

function SectionBlock({ icon, title, children }: { icon: keyof typeof icons; title: string; children: React.ReactNode }) {
  return (
    <div className="lc-section">
      <div className="lc-section-title">
        <Icon d={icons[icon]} className="h-3.5 w-3.5 text-text-dim" />
        {title}
      </div>
      <div className="mt-3">{children}</div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="lc-workspace grid gap-5 xl:grid-cols-12">
      <div className="xl:col-span-5 space-y-3">
        <div className="lc-panel p-5 space-y-4">
          <div className="lc-skeleton h-6 w-2/3" />
          <div className="flex gap-2">
            <div className="lc-skeleton h-5 w-16 rounded-full" />
            <div className="lc-skeleton h-5 w-12 rounded-full" />
          </div>
          <div className="lc-skeleton h-20 w-full" />
          <div className="lc-skeleton h-16 w-full" />
        </div>
      </div>
      <div className="xl:col-span-7 space-y-3">
        <div className="lc-panel">
          <div className="lc-skeleton h-10 w-full rounded-none" />
          <div className="lc-skeleton m-2 h-[420px] w-[calc(100%-1rem)]" />
        </div>
      </div>
    </div>
  );
}

function HintsBlock({
  hints,
  lockUntil,
  lockMinutes,
}: {
  hints: string[];
  lockUntil?: number | null;
  lockMinutes?: number;
}) {
  const { t } = useI18n();
  const [revealed, setRevealed] = useState(0);
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    setRevealed(0);
  }, [hints]);

  useEffect(() => {
    if (!lockUntil || lockUntil <= Date.now()) return;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [lockUntil]);

  if (hints.length === 0) return null;

  const firstLocked = revealed === 0 && lockUntil != null && now < lockUntil;
  const remainingMs = firstLocked && lockUntil ? lockUntil - now : 0;
  const progress = (revealed / hints.length) * 100;

  return (
    <SectionBlock icon="lightbulb" title={t('common.hints')}>
      {revealed > 0 && (
        <>
          <div className="mb-3 flex items-center justify-between text-xs text-text-dim">
            <span>{revealed} / {hints.length}</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="lc-hint-progress mb-3">
            <div className="lc-hint-progress-fill" style={{ width: `${progress}%` }} />
          </div>
        </>
      )}
      <ul className="space-y-2">
        {hints.slice(0, revealed).map((hint, i) => (
          <li key={i} className="lc-hint-card pl-5">
            <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-brand">
              {t('common.hint')} {i + 1}
            </span>
            {hint}
          </li>
        ))}
      </ul>
      {revealed < hints.length && (
        <button
          type="button"
          onClick={() => { if (!firstLocked) setRevealed((n) => n + 1); }}
          disabled={firstLocked}
          className="lc-hint-btn mt-3 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Icon d={icons.lightbulb} className="h-4 w-4" />
          {firstLocked
            ? t('studySession.hintLockedBtn', { remain: formatCountdown(remainingMs) })
            : revealed === 0
              ? t('leetcodePanel.showFirstHint')
              : t('leetcodePanel.showNextHint')}
        </button>
      )}
      {firstLocked && lockMinutes ? (
        <p className="mt-2 text-xs text-amber-700">
          {t('studySession.hintLocked', { remain: formatCountdown(remainingMs), min: lockMinutes })}
        </p>
      ) : null}
    </SectionBlock>
  );
}

export function LeetcodePanel({
  problemId,
  passed,
  tier = 1,
  tierPassed = 0,
  mode = 'official',
  hintLockMinutes = 0,
  onSubmit,
}: LeetcodePanelProps) {
  const { t, locale } = useI18n();
  const switchable = canSwitchLanguage(problemId, mode);
  const [execLang, setExecLang] = useState<ExecLang>(() => (canSwitchLanguage(problemId, mode) ? readLcLang() : 'python'));
  const [problem, setProblem] = useState<ProblemDetail | null>(null);
  const [code, setCode] = useState('');
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(passed);
  const [copied, setCopied] = useState(false);
  const [lockUntil, setLockUntil] = useState<number | null>(null);
  const [now, setNow] = useState(Date.now());
  const guideRef = useRef<HTMLElement>(null);

  const scrollToGuide = () => {
    guideRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  useEffect(() => {
    setDone(passed);
    setResult(null);
    api.problem(problemId, tier, switchable ? execLang : undefined).then((p) => {
      setProblem(p);
      setCode(p.starter_code || '');
    });
  }, [problemId, tier, passed, locale, execLang, switchable]);

  useEffect(() => {
    if (mode !== 'guided' || !hintLockMinutes || !problemId) {
      setLockUntil(null);
      return;
    }
    const started = ensureHintLockStart(problemId);
    setLockUntil(hintUnlockAt(started, hintLockMinutes));
  }, [problemId, mode, hintLockMinutes]);

  useEffect(() => {
    if (!lockUntil || lockUntil <= Date.now()) return;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [lockUntil]);

  if (!problem) return <LoadingSkeleton />;

  const run = async () => {
    setBusy(true);
    try {
      const res = await api.run({
        code,
        exercise_id: problemId,
        exercise_type: 'leetcode',
        tier,
        language: switchable ? execLang : undefined,
      });
      setResult(res);
    } finally {
      setBusy(false);
    }
  };

  const submit = async () => {
    setBusy(true);
    try {
      const res = await onSubmit(code, switchable ? execLang : (problem.language || 'python'));
      setResult(res.result);
      if (res.passed && mode === 'official') setDone(true);
    } finally {
      setBusy(false);
    }
  };

  const copySolution = () => {
    setCode(problem.solution_code || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const cases = (result?.results as { case: number; passed: boolean }[]) || [];
  const isPractice = mode === 'practice' || mode === 'guided';
  const isGuided = mode === 'guided';
  const spoilersLocked = isGuided && lockUntil != null && now < lockUntil;
  const hints = problem.hints ?? [];
  const learning = problem.learning ?? [];
  const interviewQuestions = problem.interview_questions ?? [];
  const showGuide = problem.hints_allowed && (
    hints.length > 0
    || !!problem.approach
    || learning.length > 0
    || interviewQuestions.length > 0
    || (problem.narration_prompts?.length ?? 0) > 0
  );
  const studyLang = languageOfDay();

  const editorBlock = (
    <main className="flex min-h-[420px] flex-col">
      <div className="lc-panel flex flex-col">
        <div className="lc-editor-toolbar">
          <div className="flex items-center gap-3">
            <div className="lc-editor-dots">
              <span className="lc-editor-dot bg-rose-500/80" />
              <span className="lc-editor-dot bg-amber-500/80" />
              <span className="lc-editor-dot bg-emerald-500/80" />
            </div>
            <span className="text-xs font-medium text-text-muted">{t('leetcodePanel.yourSolution')}</span>
            {switchable ? (
              <div className="lc-lang-toggle" role="group" aria-label={t('common.languages')}>
                <button
                  type="button"
                  className={execLang === 'python' ? 'lc-lang-toggle-active' : ''}
                  onClick={() => { setExecLang('python'); writeLcLang('python'); }}
                >
                  {t('common.python')}
                </button>
                <button
                  type="button"
                  className={execLang === 'csharp' ? 'lc-lang-toggle-active' : ''}
                  onClick={() => { setExecLang('csharp'); writeLcLang('csharp'); }}
                >
                  {t('common.csharp')}
                </button>
              </div>
            ) : (
              <span className="lc-lang-badge">
                <Icon d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" className="h-3 w-3" />
                {problem.language === 'csharp' ? t('common.csharp') : t('common.python')}
              </span>
            )}
            {isGuided ? (
              <span className="text-xs text-text-dim">
                {t('studySession.langToday', { lang: STUDY_LANG_LABEL[studyLang] })}
              </span>
            ) : null}
          </div>
          <div className="flex items-center gap-2">
            <button type="button" onClick={run} disabled={busy} className="btn-secondary !py-1.5 !px-3 !text-xs">
              <Icon d={icons.play} className="h-3.5 w-3.5" />
              {t('common.run')}
            </button>
            <button type="button" onClick={submit} disabled={busy} className="btn-primary !py-1.5 !px-3 !text-xs">
              {busy ? t('leetcodePanel.submitting') : (
                <>
                  <Icon d={icons.check} className="h-3.5 w-3.5" />
                  {isPractice ? t('leetcodePanel.submitTier') : t('common.submit')}
                </>
              )}
            </button>
          </div>
        </div>
        <div className="p-1">
          <CodeEditor
            value={code}
            onChange={setCode}
            height="480px"
            drillId={`${problemId}:${switchable ? execLang : (problem.language ?? 'python')}`}
            language={problem.language ?? execLang}
            chrome={false}
          />
        </div>
      </div>

      {result && (
        <div className={`mt-3 ${result.passed ? 'alert-success' : 'alert-error'}`}>
          <div className="flex items-center gap-2 font-medium">
            <Icon d={result.passed ? icons.check : 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z'} className="h-5 w-5" />
            {result.passed ? t('leetcodePanel.allPassed') : String(result.error || t('common.failed'))}
          </div>
          {cases.length > 0 && (
            <div className="lc-result-cases">
              {cases.map((r) => (
                <span key={r.case} className={`lc-result-case ${r.passed ? 'lc-result-case-pass' : 'lc-result-case-fail'}`}>
                  {r.passed ? '✓' : '✗'} {t('leetcodePanel.case', { n: r.case, status: r.passed ? t('common.ok') : t('common.fail') }).replace(/ — .*/, '')}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </main>
  );

  const guideBlock = (
    <aside ref={guideRef} className="h-full min-h-[420px] scroll-mt-24">
      <div className="lc-panel lc-panel-scroll h-full max-h-[calc(100vh-7rem)] xl:sticky xl:top-24">
        <PanelHeader
          icon="book"
          title={t('leetcodePanel.guideTitle')}
          subtitle={tier === 1 ? t('leetcodePanel.tier1Hint') : t('leetcodePanel.tierOtherHint')}
        />
        <div className="lc-panel-body space-y-3">
          <HintsBlock
            hints={hints}
            lockUntil={isGuided ? lockUntil : null}
            lockMinutes={isGuided ? hintLockMinutes : 0}
          />

          {problem.approach && !spoilersLocked && problem.hints_allowed && (
            <SectionBlock icon="lightbulb" title={t('leetcodePanel.howItWorks')}>
              <p className="text-sm leading-relaxed text-text-muted">{problem.approach}</p>
            </SectionBlock>
          )}

          {learning.length > 0 && (
            <SectionBlock icon="book" title={t('leetcodePanel.whatToLearn')}>
              <ul className="space-y-2">
                {learning.map((item, i) => (
                  <li key={i} className="lc-learning-item">
                    <span className="mt-0.5 text-brand">✓</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </SectionBlock>
          )}

          {interviewQuestions.length > 0 && (
            <SectionBlock icon="chat" title={t('leetcodePanel.interviewQuestions')}>
              <ul className="space-y-2">
                {interviewQuestions.map((q, i) => (
                  <li key={i} className="lc-interview-item">
                    <span className="mt-0.5 shrink-0 text-text-dim">?</span>
                    <span>{q}</span>
                  </li>
                ))}
              </ul>
            </SectionBlock>
          )}

          {problem.narration_prompts.length > 0 && (
            <SectionBlock icon="mic" title={t('leetcodePanel.explainAloud')}>
              <ul className="space-y-2">
                {problem.narration_prompts.map((c, i) => (
                  <li key={i} className="lc-narration-card">{c}</li>
                ))}
              </ul>
            </SectionBlock>
          )}
        </div>
      </div>
    </aside>
  );

  return (
    <div className="lc-workspace grid gap-4 xl:grid-cols-12">
      {/* Left: problem statement */}
      <aside className="space-y-4 xl:col-span-5">
        <div className="lc-panel">
          <div className="lc-panel-header">
            <div className="min-w-0 flex-1">
              <h3 className="text-lg font-semibold tracking-tight text-text">{problem.title}</h3>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {problem.leetcode_ref ? (
                  <span className="lc-ref-badge">LC {problem.leetcode_ref}</span>
                ) : null}
                {problem.difficulty ? (
                  <span className={difficultyClass(problem.difficulty)}>{problem.difficulty}</span>
                ) : null}
                {isPractice ? (
                  <span className="badge-muted">
                    {t('leetcodePanel.tierBadge', { tier, label: problem.tier_label ? ` · ${problem.tier_label}` : '' })}
                  </span>
                ) : null}
                {done && mode === 'official' && <span className="badge-brand">{t('leetcodePanel.resolved')}</span>}
                {tierPassed >= 3 && isPractice && <span className="badge-brand">{t('common.mastered')}</span>}
              </div>
            </div>
          </div>

          <div className="lc-panel-body space-y-3">
            <WhereToStartGuide
              problem={problem}
              tier={tier}
              onShowHints={scrollToGuide}
              spoilersLocked={spoilersLocked}
            />

            <SectionBlock icon="doc" title={t('leetcodePanel.statement')}>
              <ProblemText text={problem.description} />
            </SectionBlock>

            {problem.explain_checklist?.length > 0 && tier >= 2 && (
              <SectionBlock icon="checklist" title={t('leetcodePanel.beforeCoding')}>
                <ul className="space-y-1">
                  {problem.explain_checklist.map((c, i) => (
                    <li key={i} className="lc-checklist-item">
                      <span className="lc-checklist-box">○</span>
                      <span>{c}</span>
                    </li>
                  ))}
                </ul>
              </SectionBlock>
            )}

            {problem.test_cases_preview?.length > 0 && (
              <SectionBlock icon="code" title={t('common.examples')}>
                <div className="space-y-2">
                  {problem.test_cases_preview.map((tc, i) => (
                    <div key={i} className="lc-test-case">
                      <div>
                        <div className="lc-test-case-label">Input</div>
                        <div className="lc-test-case-value">
                          {problem.fn_name}({JSON.stringify(tc.args).slice(1, -1)})
                        </div>
                      </div>
                      <div className="border-t border-border">
                        <div className="lc-test-case-label">Output</div>
                        <div className="lc-test-case-value lc-test-case-output">
                          {JSON.stringify(tc.expected)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </SectionBlock>
            )}

            {tier === 1 && problem.solution_code && !isGuided && (
              <SectionBlock icon="code" title={t('common.solution')}>
                <div className="mb-3 flex items-center justify-between gap-2">
                  <p className="text-xs text-text-dim">{t('leetcodePanel.studyHint')}</p>
                  <button type="button" onClick={copySolution} className="lc-copy-btn">
                    <Icon d={copied ? icons.check : icons.copy} className="h-3.5 w-3.5" />
                    {copied ? t('common.done') : t('leetcodePanel.copyToEditor')}
                  </button>
                </div>
                <pre className="overflow-x-auto rounded-xl border border-border bg-bg/80 p-3 font-mono text-xs leading-relaxed text-text-muted">
                  {problem.solution_code}
                </pre>
              </SectionBlock>
            )}
          </div>
        </div>
      </aside>

      {/* Center + right: resizable editor / guide split */}
      <div className="xl:col-span-7">
        {showGuide ? (
          <>
            <div className="hidden xl:block">
              <ResizableSplit
                left={editorBlock}
                right={guideBlock}
                defaultLeftPct={62}
                storageKey="codenda-lc-editor-guide-split"
              />
            </div>
            <div className="space-y-4 xl:hidden">
              {editorBlock}
              {guideBlock}
            </div>
          </>
        ) : (
          editorBlock
        )}
      </div>
    </div>
  );
}
