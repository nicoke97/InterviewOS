const API = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = err.detail;
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg || String(d)).join(', ')
          : res.statusText;
    throw new Error(message || res.statusText);
  }
  return res.json();
}

export const api = {
  health: () => request<{ status: string }>('/health'),
  curriculum: () => request<Record<string, unknown>>('/curriculum'),
  stats: () => request<Record<string, unknown>>('/stats'),
  settings: () => request<{ focus_mode: boolean; dev_mode: boolean }>('/settings'),
  updateSettings: (body: { focus_mode?: boolean; dev_mode?: boolean }) =>
    request('/settings', { method: 'POST', body: JSON.stringify(body) }),
  calendarMonth: (year: number, month: number) =>
    request<CalendarMonth>(`/calendar?year=${year}&month=${month}`),
  exportProgress: () => request<Record<string, unknown>>('/export'),

  // session timer
  sessionStart: (slot: string) =>
    request<{ session_id: number }>('/session/start', { method: 'POST', body: JSON.stringify({ slot }) }),
  sessionEnd: (session_id: number, duration_seconds: number) =>
    request('/session/end', { method: 'POST', body: JSON.stringify({ session_id, duration_seconds }) }),

  // code runner
  run: (body: Record<string, unknown>) =>
    request<Record<string, unknown>>('/run', { method: 'POST', body: JSON.stringify(body) }),

  // Kumon set model
  roadmap: (level: string) => request<Roadmap>(`/level/${level}/roadmap`),
  session: (level: string, count: number) => request<SessionData>(`/level/${level}/session?count=${count}`),
  setSubmit: (body: {
    level: string;
    set_number: number;
    time_ms: number;
    answers: { exercise_id: string; code: string }[];
    plan_id?: number;
    assignment_index?: number;
  }) => request<SetSubmitResult>('/set/submit', { method: 'POST', body: JSON.stringify(body) }),

  // orientador
  orientadorActive: (track?: string) =>
    request<OrientadorActiveResponse>(`/orientador/active${track ? `?track=${track}` : ''}`),
  orientadorInsight: (track?: string) =>
    request<Record<string, unknown>>(`/orientador/insight${track ? `?track=${track}` : ''}`),
  orientadorCalculate: (minutes: number, opts?: { track?: string; planId?: number; newSession?: boolean }) =>
    request<DailyPlanData>('/orientador/calculate', {
      method: 'POST',
      body: JSON.stringify({
        minutes,
        track: opts?.track ?? 'python',
        plan_id: opts?.planId,
        new_session: opts?.newSession ?? false,
      }),
    }),
  orientadorSession: (planId: number, index: number) =>
    request<SessionData>(`/orientador/session/${planId}/${index}`),

  // checkpoints
  checkpoint: (level: string, block: string) => request<Checkpoint>(`/level/${level}/checkpoint/${block}`),
  checkpointSubmit: (body: { level: string; problem_id: string; code: string }) =>
    request<{ passed: boolean; result: Record<string, unknown>; checkpoint_passed: boolean; block: string }>(
      '/checkpoint/submit', { method: 'POST', body: JSON.stringify(body) }),

  // exam
  exam: (level: string) => request<Exam>(`/level/${level}/exam`),
  examSubmit: (body: {
    level: string;
    exercise_id: string;
    exercise_type: string;
    code?: string;
    self_score?: number;
    answer_text?: string;
  }) => request<{ passed: boolean; result: Record<string, unknown>; exam_passed: boolean }>(
    '/exam/submit', { method: 'POST', body: JSON.stringify(body) }),

  // problem / question detail
  problem: (id: string, tier = 1) => request<ProblemDetail>(`/problem/${id}?tier=${tier}`),
  question: (id: string) => request<QuestionDetail>(`/question/${id}`),
};

export interface KumonPage {
  id: string;
  level: string;
  page: number;
  set: number;
  block: string;
  block_id: string;
  order: number;
  scaffolding: string;
  prompt: string;
  starter_code: string;
  slot_answers?: string[];
  reference_code?: string;
  hints: string[];
  time_estimate_seconds?: number;
  completed?: boolean;
}

export type SetStatus = 'mastered' | 'current' | 'repeating' | 'locked';

export interface RoadmapSet {
  set_number: number;
  block: string;
  title: string;
  page_start: number;
  page_end: number;
  standard_seconds: number;
  status: SetStatus;
  attempts: number;
  completed: number;
  total: number;
  best_time_ms: number | null;
  solid_mastery?: boolean;
  repeat_scheduled_for?: string | null;
  first_attempt_accuracy?: number | null;
}

export interface RoadmapBlock {
  letter: string;
  title: string;
  instruction: string;
  set_start: number;
  set_end: number;
  checkpoint: { problems: string[]; passed: boolean; available: boolean; exists: boolean };
}

export interface Target {
  type: 'set' | 'checkpoint' | 'exam' | 'complete' | 'locked';
  set_number?: number;
  repeating?: boolean;
  block?: string;
}

export interface Roadmap {
  level: string;
  unlocked: boolean;
  target: Target;
  sets: RoadmapSet[];
  blocks: RoadmapBlock[];
  exam: { leetcode: string[]; interview: string[]; passed: boolean; available: boolean; exists: boolean };
  mastered_sets: number;
  total_sets: number;
}

export interface SessionData {
  type: 'set' | 'checkpoint' | 'exam' | 'complete' | 'locked';
  level: string;
  target?: Target;
  set_number?: number;
  set_title?: string;
  block?: string;
  block_title?: string;
  instruction?: string;
  standard_seconds?: number;
  status?: string;
  attempts?: number;
  completed?: number;
  total?: number;
  accumulated_time_ms?: number;
  page_range?: string;
  drills?: KumonPage[];
  plan_id?: number;
  assignment_index?: number;
  assignment?: OrientadorAssignment;
  checkpoint?: Checkpoint;
  exam?: Exam;
}

export interface OrientadorAssignment {
  type: 'set' | 'checkpoint' | 'exam';
  level: string;
  set_number?: number;
  block?: string;
  reason: 'repeat' | 'new' | 'pre_exam' | 'checkpoint' | 'exam';
  estimated_minutes?: number;
  index?: number;
  completed?: boolean;
}

export interface DailyPlanData {
  id: number;
  date: string;
  track: string;
  session_number: number;
  status: 'active' | 'completed';
  minutes_budget: number;
  assignments: OrientadorAssignment[];
  completed_count: number;
  total_count: number;
  estimated_minutes: number;
  calculated_at: string | null;
  config: OrientadorConfig;
}

export interface OrientadorConfig {
  minute_presets: number[];
  min_minutes: number;
  max_minutes: number;
  first_attempt_threshold: number;
  pre_exam_enabled: boolean;
  pre_exam_max_sets: number;
}

export interface OrientadorActiveResponse {
  active: boolean;
  sessions?: DailyPlanData[];
  active_plan_id?: number | null;
  config?: OrientadorConfig;
  id?: number;
  date?: string;
  track?: string;
  session_number?: number;
  status?: 'active' | 'completed';
  minutes_budget?: number;
  assignments?: OrientadorAssignment[];
  completed_count?: number;
  total_count?: number;
  estimated_minutes?: number;
  calculated_at?: string | null;
}

export interface DrillResult {
  passed: boolean;
  error?: string | null;
  expected?: string;
  stdout?: string;
}

export interface SetSubmitResult {
  results: Record<string, DrillResult>;
  passed_count: number;
  total: number;
  outcome: 'mastered' | 'too_slow' | 'in_progress';
  set_status: string;
  completed: number;
  set_total: number;
  accumulated_time_ms: number;
  standard_ms: number;
  mastered: boolean;
  needs_repeat?: boolean;
  first_attempt_accuracy?: number | null;
  solid_mastery?: boolean;
  repeat_scheduled_for?: string | null;
  next_assignment?: {
    plan_id: number;
    index: number;
    assignment: OrientadorAssignment;
  } | null;
  session_complete?: boolean;
}

export interface Checkpoint {
  level: string;
  block: string;
  block_title: string;
  available: boolean;
  passed: boolean;
  problems: { id: string; title: string; description: string; passed: boolean }[];
}

export interface Exam {
  level: string;
  available: boolean;
  passed: boolean;
  leetcode: { id: string; title: string; description: string; passed: boolean }[];
  interview: { id: string; question: string; completed: boolean }[];
}

export interface ProblemDetail {
  id: string;
  title: string;
  description: string;
  tier: number;
  fn_name: string;
  starter_code: string;
  explain_checklist: string[];
  narration_prompts: string[];
  hints_allowed: boolean;
  test_cases_preview: { args: unknown[]; expected: unknown }[];
}

export interface QuestionDetail {
  id: string;
  category: string;
  question: string;
  type: string;
  rubric: string[];
  sample_answer: string;
}

export interface CalendarDay {
  date: string;
  day: number;
  in_month: boolean;
  is_today: boolean;
  level: 'none' | 'partial' | 'complete';
  morning_done: boolean;
  evening_done: boolean;
}

export interface CalendarMonth {
  year: number;
  month: number;
  month_name: string;
  days: CalendarDay[];
  stats: { complete: number; partial: number; none: number };
}
