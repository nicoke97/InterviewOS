import { useEffect, useState } from 'react';
import { useI18n } from '../i18n/context';
import type { ProblemDetail } from '../lib/api';

const TOPIC_KEYS = [
  'arrays_hashing', 'two_pointers', 'sliding_window', 'stack', 'binary_search',
  'linked_list', 'trees', 'dp_1d', 'graphs', 'intervals',
] as const;

type TopicKey = (typeof TOPIC_KEYS)[number];

function isTopicKey(v?: string): v is TopicKey {
  return TOPIC_KEYS.includes(v as TopicKey);
}

interface WhereToStartGuideProps {
  problem: ProblemDetail;
  tier: number;
  onShowHints?: () => void;
  spoilersLocked?: boolean;
}

export function WhereToStartGuide({ problem, tier, onShowHints, spoilersLocked }: WhereToStartGuideProps) {
  const { t } = useI18n();
  const stepCount = 5;
  const [checked, setChecked] = useState<boolean[]>(() => Array(stepCount).fill(false));
  const [openStep, setOpenStep] = useState(0);

  useEffect(() => {
    setChecked(Array(stepCount).fill(false));
    setOpenStep(0);
  }, [problem.id, tier]);

  if (tier >= 3 || !problem.hints_allowed) {
    if (!problem.topic) return null;
    const topicLabel = isTopicKey(problem.topic)
      ? t(`leetcodePanel.topics.${problem.topic}`)
      : problem.topic;
    return (
      <div className="lc-start-banner">
        <p className="text-sm font-medium text-text">{t('leetcodePanel.workflowMemoryTitle')}</p>
        <p className="mt-1 text-sm text-text-muted">
          {t('leetcodePanel.workflowMemoryBody', { pattern: topicLabel })}
        </p>
      </div>
    );
  }

  const firstCase = problem.test_cases_preview?.[0];
  const inputPreview = firstCase
    ? `${problem.fn_name}(${JSON.stringify(firstCase.args).slice(1, -1)})`
    : problem.fn_name;
  const outputPreview = firstCase ? JSON.stringify(firstCase.expected) : '…';

  const topicLabel = isTopicKey(problem.topic)
    ? t(`leetcodePanel.topics.${problem.topic}`)
    : (problem.topic || t('leetcodePanel.workflowUnknownPattern'));

  const stepDetails = [
    {
      title: t('leetcodePanel.workflowStep1Title'),
      body: t('leetcodePanel.workflowStep1Body'),
      tip: t('leetcodePanel.workflowStep1Tip', { fn: problem.fn_name }),
    },
    {
      title: t('leetcodePanel.workflowStep2Title'),
      body: t('leetcodePanel.workflowStep2Body'),
      tip: t('leetcodePanel.workflowStep2Tip', { input: inputPreview, output: outputPreview }),
    },
    {
      title: t('leetcodePanel.workflowStep3Title'),
      body: t('leetcodePanel.workflowStep3Body'),
      tip: t('leetcodePanel.workflowStep3Tip'),
    },
    {
      title: t('leetcodePanel.workflowStep4Title'),
      body: t('leetcodePanel.workflowStep4Body'),
      tip: !spoilersLocked && problem.approach
        ? t('leetcodePanel.workflowStep4Tip', { pattern: topicLabel, hint: problem.approach })
        : t('leetcodePanel.workflowStep4TipNoApproach', { pattern: topicLabel }),
    },
    {
      title: t('leetcodePanel.workflowStep5Title'),
      body: t('leetcodePanel.workflowStep5Body'),
      tip: t('leetcodePanel.workflowStep5Tip'),
    },
  ];

  const doneCount = checked.filter(Boolean).length;
  const progress = (doneCount / stepCount) * 100;

  const toggle = (i: number) => {
    setChecked((prev) => {
      const next = [...prev];
      next[i] = !next[i];
      return next;
    });
    setOpenStep(i);
  };

  return (
    <div className="lc-start-guide">
      <div className="lc-start-guide-header">
        <div>
          <h4 className="text-sm font-semibold text-text">{t('leetcodePanel.workflowTitle')}</h4>
          <p className="mt-0.5 text-xs text-text-dim">{t('leetcodePanel.workflowSubtitle')}</p>
        </div>
        <span className="lc-start-progress-label">
          {t('leetcodePanel.workflowProgress', { done: doneCount, total: stepCount })}
        </span>
      </div>

      <div className="lc-hint-progress mt-3">
        <div className="lc-hint-progress-fill" style={{ width: `${progress}%` }} />
      </div>

      <ol className="mt-4 space-y-2">
        {stepDetails.map((step, i) => {
          const isOpen = openStep === i;
          const isDone = checked[i];
          return (
            <li key={i} className={`lc-start-step ${isDone ? 'lc-start-step-done' : ''} ${isOpen ? 'lc-start-step-open' : ''}`}>
              <button
                type="button"
                className="lc-start-step-head"
                onClick={() => setOpenStep(isOpen ? -1 : i)}
              >
                <span
                  role="checkbox"
                  aria-checked={isDone}
                  tabIndex={0}
                  className={`lc-start-check ${isDone ? 'lc-start-check-done' : ''}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    toggle(i);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      e.stopPropagation();
                      toggle(i);
                    }
                  }}
                >
                  {isDone ? '✓' : i + 1}
                </span>
                <span className="flex-1 text-left text-sm font-medium text-text">{step.title}</span>
                <svg
                  className={`h-4 w-4 shrink-0 text-text-dim transition-transform ${isOpen ? 'rotate-180' : ''}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {isOpen && (
                <div className="lc-start-step-body">
                  <p className="text-sm leading-relaxed text-text-muted">{step.body}</p>
                  <p className="mt-2 rounded-lg bg-brand/8 px-3 py-2 text-sm leading-relaxed text-text-muted ring-1 ring-brand/15">
                    {step.tip}
                  </p>
                </div>
              )}
            </li>
          );
        })}
      </ol>

      {doneCount < stepCount && onShowHints && (
        <button type="button" onClick={onShowHints} className="lc-start-stuck mt-4">
          {t('leetcodePanel.workflowStuck')}
        </button>
      )}
    </div>
  );
}
