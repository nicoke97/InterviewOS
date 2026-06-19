import type { Messages } from './types';

export function translate(messages: Messages, key: string, vars?: Record<string, string | number>): string {
  const parts = key.split('.');
  let cur: unknown = messages;
  for (const part of parts) {
    if (cur == null || typeof cur !== 'object') return key;
    cur = (cur as Record<string, unknown>)[part];
  }
  if (typeof cur !== 'string') return key;
  if (!vars) return cur;
  return Object.entries(vars).reduce(
    (text, [k, v]) => text.replace(new RegExp(`\\{\\{${k}\\}\\}`, 'g'), String(v)),
    cur,
  );
}

export function dateLocale(locale: 'en' | 'es'): string {
  return locale === 'es' ? 'es-ES' : 'en-US';
}
