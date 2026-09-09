import type { SdeAssignment } from './api';

/** Route for an SDE block. Unknown types stay null so they are not skipped as "next". */
export function sdeAssignmentHref(a: SdeAssignment): string | null {
  if (a.type === 'reading') {
    const weekId = String(a.week_id || String(a.id || '').replace(/^reading:/, ''));
    return weekId ? `/sde/reading/${weekId}` : null;
  }
  if (a.type === 'flashcards') return '/sde/cards';
  if (a.type === 'theory') return `/sde/section/${a.section_id || a.id}`;
  if (a.type === 'algo_sheet') return `/sde/algo/${a.algo_id}/${a.lang}/${a.sheet_id}`;
  if (a.type === 'voice') return '/sde/voice';
  if (a.type === 'sql') return `/sde/sql/${a.id}`;
  if (a.type === 'story') return '/stories';
  if (a.type === 'debug') {
    const raw = String(a.bug_id || String(a.id || '').replace(/^debug:/, ''));
    const bugId = a.bug_id ? raw : raw.replace(/:(new|pool)$/, '');
    return bugId ? `/sde/debug/${bugId}` : null;
  }
  return null;
}

export function sdeNextHref(assignments: SdeAssignment[] | undefined | null): string | null {
  if (!assignments?.length) return null;
  for (const a of assignments) {
    if (a.completed) continue;
    const href = sdeAssignmentHref(a);
    if (href) return href;
  }
  return null;
}
