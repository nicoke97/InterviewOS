import { useState } from 'react';
import { type KumonPage } from '../lib/api';
import { KumonCodeInput } from './KumonCodeInput';
import { useI18n } from '../i18n/context';

export type ReviewStatus = 'pending' | 'passed' | 'failed' | 'edited';

interface KumonProblemProps {
  number: number;
  pageLabel?: string;
  drill: KumonPage;
  value: string;
  onChange: (code: string) => void;
  result?: { passed: boolean; error?: string | null; expected?: string; stdout?: string };
  reviewStatus: ReviewStatus;
  focusMode?: boolean;
  highlightEmpty?: boolean;
}

const BORDER: Record<ReviewStatus, string> = {
  pending: 'border-stone-300 bg-white',
  passed: 'border-emerald-400 bg-emerald-50',
  failed: 'border-red-400 bg-red-50',
  edited: 'border-amber-400 bg-amber-50',
};

export function KumonProblem({ number, pageLabel, drill, value, onChange, result, reviewStatus, focusMode = false, highlightEmpty = false }: KumonProblemProps) {
  const { t } = useI18n();
  const template = drill.starter_code?.replace(/\r\n/g, '\n').trimEnd() ?? '';
  const useFullTyping = drill.scaffolding === 'full' && template.includes('___');
  const [showHint, setShowHint] = useState(false);
  const [showSolution, setShowSolution] = useState(false);

  const showHintButton = !focusMode || reviewStatus === 'failed';
  const showSolutionButton = reviewStatus === 'failed' && drill.reference_code;
  const emptyHighlight = highlightEmpty && reviewStatus === 'pending' && !value.trim();

  return (
    <div
      data-review-status={reviewStatus}
      className={`break-inside-avoid rounded border px-3 py-2.5 ${BORDER[reviewStatus]} ${emptyHighlight ? 'ring-2 ring-amber-500' : ''}`}
    >
      <div className="mb-1.5 flex gap-2">
        <span className="flex h-6 min-w-6 shrink-0 items-center justify-center rounded-full border-2 border-stone-800 px-1 text-[10px] font-bold text-stone-800">
          {pageLabel ?? number}
        </span>
        <p className="text-sm leading-snug text-stone-800">{drill.prompt}</p>
      </div>

      {useFullTyping ? (
        <KumonCodeInput
          template={template}
          prompt={drill.prompt}
          slotAnswers={drill.slot_answers}
          referenceCode={drill.reference_code}
          onChange={onChange}
        />
      ) : (
        <textarea
          className="w-full resize-none rounded border border-dashed border-stone-400 bg-stone-50 px-2 py-1.5 font-mono text-xs leading-relaxed text-stone-900 placeholder:text-stone-400 focus:border-stone-600 focus:bg-white focus:outline-none"
          rows={drill.scaffolding === 'minimal' ? 4 : 3}
          value={value}
          placeholder={t('kumonProblem.placeholder')}
          onChange={(e) => onChange(e.target.value)}
          spellCheck={false}
        />
      )}

      {reviewStatus === 'failed' && result && (
        <div className="mt-1 space-y-1 text-xs text-red-700">
          {result.error && <p>{result.error}</p>}
          {result.stdout != null && result.stdout !== '' && (
            <p>
              <span className="font-medium">{t('kumonProblem.yourOutput')}</span>{' '}
              <code className="rounded bg-red-100 px-1 font-mono">{result.stdout}</code>
            </p>
          )}
          {result.expected != null && result.expected !== '' && (
            <p>
              <span className="font-medium">{t('kumonProblem.expected')}</span>{' '}
              <code className="rounded bg-red-100 px-1 font-mono">{result.expected}</code>
            </p>
          )}
        </div>
      )}
      {reviewStatus === 'passed' && (
        <p className="mt-1 text-xs font-medium text-emerald-700">{t('common.correct')}</p>
      )}
      {reviewStatus === 'edited' && (
        <p className="mt-1 text-xs font-medium text-amber-700">{t('kumonProblem.edited')}</p>
      )}

      {reviewStatus === 'pending' && drill.hints?.length > 0 && showHintButton && (
        <div className="mt-1.5">
          <button
            type="button"
            onClick={() => setShowHint((s) => !s)}
            className="text-[11px] font-medium text-stone-500 underline-offset-2 hover:underline"
          >
            {showHint ? t('kumonProblem.hideHint') : t('common.hint')}
          </button>
          {showHint && <p className="mt-1 text-[11px] italic text-stone-500">{drill.hints[0]}</p>}
        </div>
      )}

      {showSolutionButton && (
        <div className="mt-1.5">
          <button
            type="button"
            onClick={() => setShowSolution((s) => !s)}
            className="text-[11px] font-medium text-stone-600 underline-offset-2 hover:underline"
          >
            {showSolution ? t('kumonProblem.hideSolution') : t('kumonProblem.showSolution')}
          </button>
          {showSolution && (
            <pre className="mt-1 overflow-x-auto rounded bg-stone-100 p-2 font-mono text-[11px] text-stone-800">
              {drill.reference_code}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
