import type { DailyPlanData, OrientadorActiveResponse } from './api';
import { orientadorAssignmentPath } from './orientadorLabels';

export function nextAssignmentFromPlan(plan: DailyPlanData | null | undefined) {
  if (!plan || plan.status !== 'active') return null;
  const idx = plan.assignments.findIndex((a) => !a.completed);
  if (idx < 0) return null;
  const assignment = plan.assignments[idx];
  return { plan, assignment, index: assignment.index ?? idx };
}

export function continueStudyPath(plan: DailyPlanData | null | undefined): string | null {
  const next = nextAssignmentFromPlan(plan);
  if (!next) return null;
  return orientadorAssignmentPath(next.plan.id, next.index, next.assignment);
}

export function pickActivePlan(o: OrientadorActiveResponse): DailyPlanData | null {
  const list = o.sessions ?? [];
  const pickId = o.active_plan_id ?? (list.length ? list[list.length - 1].id : null);
  if (!pickId) return null;
  const fromList = list.find((s) => s.id === pickId);
  if (fromList) return fromList;
  if (o.id && o.minutes_budget != null) {
    return {
      id: o.id,
      date: o.date!,
      track: o.track ?? 'python',
      session_number: o.session_number ?? 1,
      status: o.status ?? 'active',
      minutes_budget: o.minutes_budget,
      assignments: o.assignments ?? [],
      completed_count: o.completed_count ?? 0,
      total_count: o.total_count ?? 0,
      estimated_minutes: o.estimated_minutes ?? 0,
      calculated_at: o.calculated_at ?? null,
      config: o.config!,
    };
  }
  return null;
}
