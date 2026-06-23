export interface SessionDraft {
  answers: Record<string, string>;
  seconds: number;
  count?: number;
}

export function draftKey(key: string): string {
  return `kumon-draft:${key}`;
}

export function loadSessionDraft(key: string): SessionDraft | null {
  try {
    const raw = localStorage.getItem(draftKey(key));
    if (!raw) return null;
    const parsed = JSON.parse(raw) as SessionDraft;
    if (!parsed || typeof parsed.answers !== 'object') return null;
    return {
      answers: parsed.answers,
      seconds: typeof parsed.seconds === 'number' ? parsed.seconds : 0,
      count: parsed.count,
    };
  } catch {
    return null;
  }
}

export function saveSessionDraft(key: string, draft: SessionDraft): void {
  try {
    localStorage.setItem(draftKey(key), JSON.stringify(draft));
  } catch {
    /* quota exceeded — ignore */
  }
}

export function clearSessionDraft(key: string): void {
  try {
    localStorage.removeItem(draftKey(key));
  } catch {
    /* ignore */
  }
}
