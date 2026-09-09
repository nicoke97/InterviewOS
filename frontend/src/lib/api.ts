const API = '/api';

function readStoredLocale(): 'en' | 'es' {
  try {
    const stored = localStorage.getItem('codenda-locale') ?? localStorage.getItem('pythonos-locale');
    if (stored === 'en' || stored === 'es') return stored;
  } catch {
    /* ignore */
  }
  return 'en';
}

let currentLocale: 'en' | 'es' = readStoredLocale();

export function setApiLocale(locale: 'en' | 'es') {
  currentLocale = locale;
}

export function getApiLocale(): 'en' | 'es' {
  return currentLocale;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      'Accept-Language': currentLocale,
    },
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
  settings: () => request<{ focus_mode: boolean; dev_mode: boolean; locale: 'en' | 'es' }>('/settings'),
  updateSettings: (body: { focus_mode?: boolean; dev_mode?: boolean; locale?: 'en' | 'es' }) =>
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
  session: (level: string, count: number, setNumber?: number) =>
    request<SessionData>(
      `/level/${level}/session?count=${count}${setNumber != null ? `&set_number=${setNumber}` : ''}`,
    ),
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

  // LeetCodes interview track
  leetcodesRoadmap: () => request<LeetcodesRoadmap>('/leetcodes/roadmap'),
  leetcodesProblem: (id: string, tier = 1, language?: string) =>
    request<ProblemDetail>(`/leetcodes/problem/${id}?tier=${tier}${language ? `&language=${language}` : ''}`),
  leetcodesPracticeSubmit: (body: {
    problem_id: string;
    tier: number;
    code: string;
    plan_id?: number;
    assignment_index?: number;
    language?: string;
  }) => request<LeetcodesPracticeResult>('/leetcodes/practice/submit', {
    method: 'POST',
    body: JSON.stringify(body),
  }),

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

  returnExamStatus: () => request<ReturnExamStatus>('/return-exam/status'),
  returnExam: () => request<ReturnExamResponse>('/return-exam'),
  returnExamSubmit: (answers: { exercise_id: string; code: string }[]) =>
    request<ReturnExamSubmitResult>('/return-exam/submit', {
      method: 'POST',
      body: JSON.stringify({ answers }),
    }),

  sdeToday: () => request<SdeToday>('/sde/today'),
  sdeReading: (weekId: string) =>
    request<{ title: string; intro: string; minutes?: number; week_id?: string }>(
      `/sde/reading/${weekId}`,
    ),
  sdeReadingComplete: (weekId: string) =>
    request<{ ok: boolean }>(`/sde/reading/${weekId}/complete`, {
      method: 'POST',
      body: JSON.stringify({}),
    }),
  sdeCardsReview: (results: { id: string; ok: boolean; section_id?: string }[]) =>
    request<{ ok: boolean; fails: number }>('/sde/cards/review', {
      method: 'POST',
      body: JSON.stringify({ results }),
    }),
  sdeSection: (id: string) => request<SdeSection>(`/sde/section/${id}`),
  sdeSectionQuiz: (id: string, answers: number[]) =>
    request<SdeTheoryResult>(`/sde/section/${id}/quiz`, {
      method: 'POST',
      body: JSON.stringify({ answers }),
    }),
  sdeSheet: (algoId: string, lang: string, sheetId: string) =>
    request<SdeSheet>(`/sde/algo/${algoId}/${lang}/${sheetId}`),
  sdeSheetSubmit: (algoId: string, lang: string, sheetId: string, code: string) =>
    request<{ passed: boolean; error?: string; results?: unknown[] }>(
      `/sde/algo/${algoId}/${lang}/${sheetId}/submit`,
      { method: 'POST', body: JSON.stringify({ code }) },
    ),
  sdeVoice: (algoId: string, lang: string, transcript: string) =>
    request<{ passed: boolean; hits: string[] }>('/sde/voice', {
      method: 'POST',
      body: JSON.stringify({ algo_id: algoId, lang, transcript }),
    }),
  sdeOffline: (body: { kinds?: string[]; section_id?: string; passed?: boolean }) =>
    request<{ ok: boolean }>('/sde/offline', { method: 'POST', body: JSON.stringify(body) }),
  sdeSql: (id: string, sql: string) =>
    request<{ passed: boolean; expected?: string }>(`/sde/sql/${id}`, {
      method: 'POST',
      body: JSON.stringify({ sql }),
    }),
  sdeDebug: (bugId: string) =>
    request<SdeDebugBug>(`/sde/debug/${bugId}`),
  sdeDebugSubmit: (bugId: string, code: string) =>
    request<{ passed: boolean; error?: string; results?: unknown[]; cause?: string }>(
      `/sde/debug/${bugId}/submit`,
      { method: 'POST', body: JSON.stringify({ code }) },
    ),
  sdePack: async () => {
    const res = await fetch('/api/sde/travel-pack', { headers: { 'Accept-Language': currentLocale } });
    return res.text();
  },

  // problem / question detail
  problem: (id: string, tier = 1, language?: string) =>
    request<ProblemDetail>(`/problem/${id}?tier=${tier}${language ? `&language=${language}` : ''}`),
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
  set_title?: string;
  display_set_number?: number;
}

export type SetStatus = 'mastered' | 'current' | 'repeating' | 'locked' | 'extra';

export interface RoadmapSet {
  set_number: number;
  display_set_number?: number;
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
  page_start?: number;
  page_end?: number;
  extra?: boolean;
  checkpoint: { problems: string[]; passed: boolean; available: boolean; exists: boolean };
}

export interface Target {
  type: 'set' | 'checkpoint' | 'exam' | 'complete' | 'locked';
  set_number?: number;
  display_set_number?: number;
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
  type: 'set' | 'checkpoint' | 'exam' | 'complete' | 'locked' | 'leetcode_practice';
  level: string;
  target?: Target;
  set_number?: number;
  display_set_number?: number;
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
  explain?: { title?: string; reason?: string; summary?: string };
  failure_flags?: string[];
  first_attempt_accuracy?: number | null;
  mode?: 'study' | 'review';
  checkpoint?: Checkpoint;
  exam?: Exam;
  problem_id?: string;
  title?: string;
  description?: string;
  topic?: string;
  leetcode_ref?: number;
  tier_passed?: number;
  solid_mastery?: boolean;
  steps?: { tier: number; label: string }[];
  step_index?: number;
  total_steps?: number;
  current_step?: { tier: number; label: string };
  current_tier?: number;
  hint_lock_minutes?: number;
}

export interface LeetcodesProblemSummary {
  id: string;
  title: string;
  description: string;
  topic: string;
  difficulty: string;
  global_order: number;
  leetcode_ref: number;
  tier_passed: number;
  solid_mastery: boolean;
  attempts: number;
  current_tier: number;
  last_practiced_at: string | null;
}

export interface LeetcodesRoadmap {
  track: string;
  topics: { id: string; title: string; problems: LeetcodesProblemSummary[] }[];
  total: number;
  mastered_count: number;
  started_count: number;
}

export interface LeetcodesPracticeResult {
  passed: boolean;
  tier_passed: number;
  solid_mastery: boolean;
  attempts: number;
  next_tier_suggestion: number | null;
  tier_label?: string;
  result: Record<string, unknown>;
  step_complete?: boolean;
  assignment_complete?: boolean;
  next_assignment?: { plan_id: number; index: number; assignment: OrientadorAssignment } | null;
  session_complete?: boolean;
}

export interface OrientadorAssignment {
  type: 'set' | 'checkpoint' | 'exam' | 'leetcode_practice';
  level?: string;
  problem_id?: string;
  title?: string;
  topic?: string;
  leetcode_ref?: number;
  set_number?: number;
  display_set_number?: number;
  block?: string;
  reason: 'repeat' | 'new' | 'pre_exam' | 'repaso' | 'repaso_extra' | 'checkpoint' | 'exam';
  from_return_exam?: boolean;
  estimated_minutes?: number;
  steps?: { tier: number; label: string }[];
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
  default_minutes?: number;
  hint_lock_minutes?: number;
  focus_topics?: string[];
  max_problems_per_session?: number;
  first_attempt_threshold?: number;
  pre_exam_enabled?: boolean;
  pre_exam_max_sets?: number;
}

export interface OrientadorActiveResponse {
  active: boolean;
  sessions?: DailyPlanData[];
  active_plan_id?: number | null;
  return_exam?: ReturnExamStatus;
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
  tier_label?: string;
  fn_name: string;
  language?: string;
  topic?: string;
  difficulty?: string;
  leetcode_ref?: number;
  starter_code: string;
  explain_checklist: string[];
  narration_prompts: string[];
  hints_allowed: boolean;
  hints: string[];
  approach: string;
  learning: string[];
  interview_questions: string[];
  solution_code?: string;
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

export interface ReturnExamStatus {
  needed: boolean;
  status: 'pending' | 'eligible' | 'none' | 'completed';
  exam_id: number | null;
  inactivity_days: number;
  threshold_days: number;
  last_active_date: string | null;
  exercise_count: number;
}

export interface ReturnExamItem {
  exercise_id: string;
  level: string;
  set_number: number;
  display_set_number?: number;
  set_title?: string;
}

export interface ReturnExamFailedSet {
  level: string;
  set_number: number;
  display_set_number?: number;
  set_title?: string;
}

export interface ReturnExamPayload {
  id: number;
  status: string;
  inactivity_days: number;
  last_active_date: string | null;
  drills: KumonPage[];
  items: ReturnExamItem[];
  results: Record<string, DrillResult> | null;
  failed_sets: ReturnExamFailedSet[];
  completed_at: string | null;
}

export interface ReturnExamResponse extends ReturnExamStatus {
  exam: ReturnExamPayload | null;
}

export interface ReturnExamSubmitResult extends ReturnExamResponse {
  results: Record<string, DrillResult>;
  passed_count: number;
  total: number;
  passed: boolean;
  failed_sets: ReturnExamFailedSet[];
}

export interface CalendarDay {
  date: string;
  day: number;
  in_month: boolean;
  is_today: boolean;
  level: 'none' | 'partial' | 'complete';
  morning_done: boolean;
  evening_done: boolean;
  repeat_scheduled?: number;
}

export interface CalendarMonth {
  year: number;
  month: number;
  month_name: string;
  days: CalendarDay[];
  stats: { complete: number; partial: number; none: number };
}

export interface SdeAssignment {
  type: string;
  id: string;
  completed?: boolean;
  [key: string]: unknown;
}

export interface SdeToday {
  date: string;
  kind: string;
  complete: boolean;
  assignments: SdeAssignment[];
  cursor: Record<string, unknown>;
  analysis: { cause: string; line: string; cta: string } | null;
  codi: { mood: string; headline: string; cta: string; to: string };
}

export interface SdeSection {
  id: string;
  title: string;
  reading: string;
  week_title?: string;
  anchor?: string;
  questions: { id: string; q: string; choices: string[]; answer: number }[];
  cards: { id: string; front: string; back: string }[];
}

export interface SdeTheoryResult {
  passed: boolean;
  correct: number;
  total: number;
  cards: { id: string; front: string; back: string; section_id: string }[];
}

export interface SdeSheet {
  type: string;
  algo_id: string;
  lang: string;
  sheet_id: string;
  title: string;
  prompt: string;
  starter_code: string;
  fn_name: string;
  language: string;
  description?: string;
}

export interface SdeDebugBug {
  id: string;
  title: string;
  difficulty?: string;
  family?: string;
  lang: string;
  error_hint: string;
  fn_name: string;
  broken_code: string;
  test_cases?: { args: unknown[]; expected: unknown }[];
  cause_locked?: boolean;
}
