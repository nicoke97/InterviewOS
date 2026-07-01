import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, type LeetcodesRoadmap } from '../lib/api';
import { useI18n } from '../i18n/context';

const DIFFICULTY_STYLE: Record<string, string> = {
  easy: 'text-emerald-700',
  medium: 'text-amber-600',
  hard: 'text-red-600',
};

export function LeetcodeRoadmap() {
  const { t, locale } = useI18n();
  const [data, setData] = useState<LeetcodesRoadmap | null>(null);
  const [error, setError] = useState(false);

  const statusBadge = (p: { tier_passed: number; solid_mastery: boolean }) => {
    if (p.solid_mastery) return { label: t('common.mastered'), cls: 'badge-brand' };
    if (p.tier_passed >= 2) return { label: t('leetcodes.tierN', { n: p.tier_passed }), cls: 'badge-muted' };
    if (p.tier_passed >= 1) return { label: t('leetcodes.tier1'), cls: 'badge-muted' };
    return { label: t('common.notStarted'), cls: 'text-text-dim text-xs' };
  };

  const load = useCallback(() => {
    void locale;
    api.leetcodesRoadmap().then(setData).catch(() => setError(true));
  }, [locale]);

  useEffect(() => { load(); }, [load]);

  if (error) {
    return (
      <div className="card space-y-3 text-center">
        <h2 className="page-title">{t('leetcodes.errorTitle')}</h2>
        <button type="button" onClick={() => { setError(false); load(); }} className="btn-secondary">
          {t('common.retry')}
        </button>
      </div>
    );
  }

  if (!data) return <p className="text-text-muted">{t('leetcodes.loading')}</p>;

  const pct = data.total ? Math.round((data.mastered_count / data.total) * 100) : 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="page-title">{t('common.leetcodes')}</h1>
          <p className="page-subtitle">{t('leetcodes.subtitle')}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="badge-brand">{t('leetcodes.masteredBadge', { count: data.mastered_count, total: data.total })}</span>
          <span className="badge-muted">{t('leetcodes.pctMastered', { pct })}</span>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-surface-2 px-4 py-3 text-sm text-text-muted">
        {t('leetcodes.freePracticeBanner').split(/(\*\*.*?\*\*)/g).map((part, i) => {
          if (part.startsWith('**') && part.endsWith('**')) {
            const text = part.slice(2, -2);
            if (text.toLowerCase().includes('orientador') || text.toLowerCase().includes('study guide')) {
              return <Link key={i} to="/" className="text-brand hover:underline">{text}</Link>;
            }
            return <strong key={i} className="text-text">{text}</strong>;
          }
          return part;
        })}
      </div>

      {data.topics.map((topic) => (
        <div key={topic.id} className="card space-y-4">
          <h2 className="text-lg font-semibold text-text">{topic.title}</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {topic.problems.map((p) => {
              const badge = statusBadge(p);
              const diffCls = DIFFICULTY_STYLE[p.difficulty] ?? 'text-text-dim';
              return (
                <div
                  key={p.id}
                  className="flex flex-col gap-2 rounded-xl border border-border bg-surface p-3 transition hover:border-brand/40"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wide text-text-dim">
                        LC {p.leetcode_ref} · <span className={diffCls}>{p.difficulty}</span>
                      </p>
                      <p className="font-medium text-text">{p.title}</p>
                    </div>
                    <span className={badge.cls}>{badge.label}</span>
                  </div>
                  <p className="text-xs text-text-muted line-clamp-2">{p.description}</p>
                  <div className="mt-auto flex items-center justify-between gap-2 pt-1">
                    <span className="text-[11px] text-text-dim">
                      {p.attempts > 0 ? t('common.attempts', { n: p.attempts }) : '—'}
                    </span>
                    <Link
                      to={`/leetcodes/${p.id}`}
                      className="rounded-lg border border-border bg-surface-2 px-2.5 py-1 text-xs font-medium text-text hover:border-brand/40"
                    >
                      {t('common.practice')}
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
