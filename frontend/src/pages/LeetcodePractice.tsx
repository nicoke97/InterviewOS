import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../lib/api';
import { LeetcodePanel } from '../components/LeetcodePanel';
import { useI18n } from '../i18n/context';

export function LeetcodePractice() {
  const { t, locale } = useI18n();
  const { problemId } = useParams<{ problemId: string }>();
  const id = problemId || '';
  const [tier, setTier] = useState(1);
  const [tierPassed, setTierPassed] = useState(0);
  const [solid, setSolid] = useState(false);
  const [title, setTitle] = useState('');

  const tierLabels: Record<number, string> = {
    1: t('leetcodePractice.tier1'),
    2: t('leetcodePractice.tier2'),
    3: t('leetcodePractice.tier3'),
  };

  const refreshMeta = useCallback(() => {
    void locale;
    if (!id) return;
    api.leetcodesRoadmap().then((r) => {
      for (const topic of r.topics) {
        const p = topic.problems.find((x) => x.id === id);
        if (p) {
          setTierPassed(p.tier_passed);
          setSolid(p.solid_mastery);
          setTitle(p.title);
          if (!p.solid_mastery) setTier((cur) => Math.max(cur, Math.min(3, p.current_tier)));
          break;
        }
      }
    }).catch(() => {});
  }, [id, locale]);

  useEffect(() => { refreshMeta(); }, [refreshMeta]);

  if (!id) return null;

  const submit = async (code: string, submitTier: number) => {
    const res = await api.leetcodesPracticeSubmit({ problem_id: id, tier: submitTier, code });
    refreshMeta();
    if (res.passed && res.next_tier_suggestion) {
      setTier(res.next_tier_suggestion);
    }
    return { passed: res.passed, result: res.result };
  };

  return (
    <div className="lc-workspace space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link
            to="/leetcodes"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-brand transition-colors hover:text-brand-hover"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            {t('leetcodePractice.backLink')}
          </Link>
          <h1 className="page-title mt-2">{title || id}</h1>
          <p className="page-subtitle">{t('leetcodePractice.subtitle')}</p>
        </div>
        {solid && (
          <span className="badge-brand mt-6">
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {t('leetcodePractice.masteredBadge')}
          </span>
        )}
      </div>

      <div className="lc-panel px-4 py-3">
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-text-dim">{t('common.tier')}</span>
          <div className="flex flex-wrap items-center gap-2">
            {[1, 2, 3].map((tierNum) => (
              <button
                key={tierNum}
                type="button"
                onClick={() => setTier(tierNum)}
                className={`lc-tier-pill ${tier === tierNum ? 'lc-tier-pill-active' : 'lc-tier-pill-inactive'}`}
              >
                <span className="font-semibold">{tierNum}</span>
                <span className="opacity-80">{tierLabels[tierNum]}</span>
              </button>
            ))}
          </div>
          {tierPassed > 0 && (
            <span className="ml-auto text-xs text-text-dim">
              {t('leetcodePractice.bestTier', { n: tierPassed })}
            </span>
          )}
        </div>
      </div>

      <LeetcodePanel
        problemId={id}
        tier={tier}
        mode="practice"
        passed={solid}
        tierPassed={tierPassed}
        onSubmit={(code) => submit(code, tier)}
      />
    </div>
  );
}
