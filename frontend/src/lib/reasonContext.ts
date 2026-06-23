import type { OrientadorAssignment, SessionData } from './api';
import { translate } from '../i18n/translate';
import { en } from '../i18n/en';
import { es } from '../i18n/es';
import type { Locale } from '../i18n/types';
import { reasonLabel } from './orientadorLabels';

function messages(locale: Locale) {
  return locale === 'es' ? es : en;
}

export function assignmentReasonContext(
  data: SessionData,
  locale: Locale = 'en',
  explain?: { summary?: string; reason?: string; title?: string } | null,
): string | null {
  if (explain?.summary) return explain.summary;

  const reason = data.assignment?.reason;
  if (!reason) return null;

  const m = messages(locale);
  const flags = data.failure_flags ?? [];
  const acc = data.first_attempt_accuracy;
  const accPct = acc != null ? Math.round(acc * 100) : null;

  switch (reason) {
    case 'repeat':
      if (flags.includes('return_exam')) {
        return translate(m, 'reason.repeatReturnExam');
      }
      if (flags.includes('too_slow')) {
        return translate(m, 'reason.repeatTooSlow');
      }
      if (flags.includes('low_accuracy') && accPct != null) {
        return translate(m, 'reason.repeatLowAccuracy', { pct: accPct });
      }
      return translate(m, 'reason.repeatDefault');
    case 'pre_exam':
      return translate(m, 'reason.preExamContext');
    case 'repaso':
    case 'repaso_extra':
      return translate(m, 'reason.repasoContext');
    case 'new':
      if (data.type === 'leetcode_practice' || data.assignment?.type === 'leetcode_practice') {
        return translate(m, 'reason.newContextLeetcode');
      }
      return translate(m, 'reason.newContext');
    default:
      return reasonLabel(reason, locale)
        ? translate(m, 'reason.fallback', { label: reasonLabel(reason, locale) })
        : null;
  }
}

export function dashboardReasonHint(assignment: OrientadorAssignment, locale: Locale = 'en'): string | null {
  const m = messages(locale);
  switch (assignment.reason) {
    case 'repeat':
      if (assignment.from_return_exam) {
        return translate(m, 'reason.hintReturnExam');
      }
      if (assignment.type === 'leetcode_practice') {
        return translate(m, 'reason.hintRepeatLeetcode');
      }
      return translate(m, 'reason.hintRepeat');
    case 'new':
      if (assignment.type === 'leetcode_practice') {
        return translate(m, 'reason.hintNewLeetcode');
      }
      return translate(m, 'reason.hintNew');
    case 'pre_exam':
      return translate(m, 'reason.hintPreExam');
    case 'repaso':
    case 'repaso_extra':
      return translate(m, 'reason.hintRepaso');
    default:
      return null;
  }
}
