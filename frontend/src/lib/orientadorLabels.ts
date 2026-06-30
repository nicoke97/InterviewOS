import type { OrientadorAssignment } from './api';
import { formatSetLevelLabel } from './setLabels';
import { translate } from '../i18n/translate';
import { en } from '../i18n/en';
import { es } from '../i18n/es';
import type { Locale } from '../i18n/types';

function messages(locale: Locale) {
  return locale === 'es' ? es : en;
}

export function reasonLabel(reason: string, locale: Locale = 'en', type?: string): string {
  if (type === 'leetcode_practice') {
    const mapped: Record<string, string> = {
      new: 'reason.lcNew',
      repeat: 'reason.lcRepeat',
    };
    const key = mapped[reason];
    if (key) {
      const val = translate(messages(locale), key);
      if (val !== key) return val;
    }
  }
  const key = `reason.${reason}`;
  const val = translate(messages(locale), key);
  return val === key ? reason : val;
}
export function orientadorAssignmentPath(
  planId: number,
  index: number,
  assignment: Pick<OrientadorAssignment, 'type' | 'level' | 'block' | 'problem_id'>,
): string {
  if (assignment.type === 'leetcode_practice') {
    return `/leetcodes/orientador/${planId}/${index}`;
  }
  const lvl = (assignment.level || 'a').toLowerCase();
  if (assignment.type === 'checkpoint' && assignment.block) {
    return `/${lvl}/checkpoint/${assignment.block}`;
  }
  if (assignment.type === 'exam') {
    return `/${lvl}/exam`;
  }
  return `/orientador/${planId}/${index}`;
}

export function assignmentLabel(a: OrientadorAssignment, locale: Locale = 'en'): string {
  const m = messages(locale);
  if (a.type === 'leetcode_practice') {
    const ref = a.leetcode_ref ? `LC ${a.leetcode_ref} · ` : '';
    return `${ref}${a.title || a.problem_id || translate(m, 'assignment.leetcodeFallback')}`;
  }
  if (a.type === 'set') {
    return formatSetLevelLabel(a.set_number!, a.level || 'a', a.display_set_number, locale);
  }
  if (a.type === 'checkpoint') {
    return translate(m, 'assignment.checkpoint', {
      block: a.block || '',
      level: (a.level || 'a').toUpperCase(),
    });
  }
  if (a.type === 'exam') {
    return translate(m, 'assignment.exam', { level: (a.level || 'a').toUpperCase() });
  }
  return translate(m, 'assignment.fallback');
}

export function reasonBadgeClass(reason: string): string {
  switch (reason) {
    case 'repeat':
      return 'text-amber-600';
    case 'new':
      return 'text-brand';
    case 'pre_exam':
    case 'repaso':
    case 'repaso_extra':
      return 'text-sky-700';
    default:
      return 'text-text-muted';
  }
}
