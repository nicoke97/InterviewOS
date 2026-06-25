const API = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

export const api = {
  health: () => request<{ status: string }>('/health'),
  curriculum: () => request<Record<string, unknown>>('/curriculum'),
  sheetToday: (slot: string) => request<Record<string, unknown>>(`/sheet/today?slot=${slot}`),
  run: (body: Record<string, unknown>) => request<Record<string, unknown>>('/run', { method: 'POST', body: JSON.stringify(body) }),
  submit: (body: Record<string, unknown>) => request<Record<string, unknown>>('/submit', { method: 'POST', body: JSON.stringify(body) }),
  stats: () => request<Record<string, unknown>>('/stats'),
  settings: () => request<{ focus_mode: boolean }>('/settings'),
  updateSettings: (body: { focus_mode?: boolean }) => request('/settings', { method: 'POST', body: JSON.stringify(body) }),
  leetcodeList: (level: string) => request<Record<string, unknown>>(`/leetcode?level=${level}`),
  leetcodeGet: (id: string, tier: number) => request<Record<string, unknown>>(`/leetcode/${id}?tier=${tier}`),
  interviewList: (level: string, category?: string) => {
    const q = category ? `&category=${category}` : '';
    return request<Record<string, unknown>>(`/interview?level=${level}${q}`);
  },
  interviewGet: (id: string) => request<Record<string, unknown>>(`/interview/${id}`),
  interviewAnswer: (id: string) => request<Record<string, unknown>>(`/interview/${id}/answer`),
  sessionStart: (slot: string) => request<{ session_id: number }>('/session/start', { method: 'POST', body: JSON.stringify({ slot }) }),
  sessionEnd: (session_id: number, duration_seconds: number) => request('/session/end', { method: 'POST', body: JSON.stringify({ session_id, duration_seconds }) }),
  exportProgress: () => request<Record<string, unknown>>('/export'),
  mockStart: (level: string) => request<Record<string, unknown>>(`/mock/start?level=${level}`, { method: 'POST' }),
  advanceDay: () => request<Record<string, unknown>>('/study/advance-day', { method: 'POST' }),
};

export interface KumonDrill {
  id: string;
  block: string;
  order: number;
  scaffolding: string;
  prompt: string;
  starter_code: string;
  hints: string[];
  csharp_note?: string;
  completed?: boolean;
}

export interface SheetData {
  sheet_id: number;
  slot: string;
  rule: string;
  current_index: number;
  drills: KumonDrill[];
  day_number: number;
  active_block: string;
}
