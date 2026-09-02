import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api, type SessionData } from '../lib/api';
import { orientadorAssignmentPath } from '../lib/orientadorLabels';
import { LeetcodePanel } from '../components/LeetcodePanel';
import {
  ComplexityLog,
  SecondLanguagePad,
  SessionRitual,
  StudyOutcome,
} from '../components/StudyRitual';
import { useI18n } from '../i18n/context';

export function LeetcodeSession() {
  const { t, locale } = useI18n();
  const { planId, index: indexParam } = useParams<{ planId: string; index: string }>();
  const navigate = useNavigate();
  const planIdNum = Number(planId);
  const index = Number(indexParam);
  const [data, setData] = useState<SessionData | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!planIdNum || Number.isNaN(index)) return;
    api.orientadorSession(planIdNum, index)
      .then(setData)
      .catch((err) => setLoadError(err instanceof Error ? err.message : t('leetcodeSession.errorDefault')));
  }, [planIdNum, index, t, locale]);

  useEffect(() => { load(); }, [load]);

  if (loadError) {
    return (
      <div className="card text-center">
        <p className="text-text-muted">{loadError}</p>
        <Link to="/" className="btn-secondary mt-3 inline-block">{t('common.dashboard')}</Link>
      </div>
    );
  }

  if (!data) return <p className="text-text-muted">{t('leetcodeSession.loading')}</p>;

  const problemId = data.problem_id || '';
  const tier = data.current_tier ?? data.current_step?.tier ?? 1;
  const stepNum = (data.step_index ?? 0) + 1;
  const totalSteps = data.total_steps ?? 1;
  const lockMinutes = data.hint_lock_minutes ?? 25;

  const submit = async (code: string, language?: string) => {
    const res = await api.leetcodesPracticeSubmit({
      problem_id: problemId,
      tier,
      code,
      plan_id: planIdNum,
      assignment_index: index,
      language,
    });
    if (res.assignment_complete) {
      if (res.next_assignment) {
        const path = orientadorAssignmentPath(
          res.next_assignment.plan_id,
          res.next_assignment.index,
          res.next_assignment.assignment,
        );
        navigate(path);
      } else {
        load();
      }
    } else if (res.step_complete) {
      load();
    }
    return { passed: res.passed, result: res.result };
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <span className="badge-brand">{t('leetcodeSession.badge')}</span>
          <h1 className="page-title mt-2">{data.title}</h1>
          <p className="page-subtitle">
            {t('leetcodeSession.step', {
              step: stepNum,
              total: totalSteps,
              tier,
              label: data.current_step?.label ?? '',
            })}
          </p>
        </div>
        <Link to="/" className="btn-secondary text-sm">{t('common.dashboard')}</Link>
      </div>

      <SessionRitual lockMinutes={lockMinutes} />

      {data.explain?.summary && (
        <div className="rounded-lg border border-border px-4 py-3 text-sm text-text-muted">
          {data.explain.summary}
        </div>
      )}

      <LeetcodePanel
        problemId={problemId}
        tier={tier}
        mode="guided"
        passed={false}
        tierPassed={data.tier_passed ?? 0}
        hintLockMinutes={lockMinutes}
        onSubmit={submit}
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <ComplexityLog problemId={problemId} />
        <StudyOutcome problemId={problemId} />
      </div>
      <SecondLanguagePad problemId={problemId} />
    </div>
  );
}
