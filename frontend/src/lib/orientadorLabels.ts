import type { OrientadorAssignment } from './api';

export const REASON_LABEL: Record<string, string> = {
  repeat: 'Repeticion',
  new: 'Nuevo set',
  pre_exam: 'Repaso pre-examen',
  repaso: 'Repaso',
  repaso_extra: 'Repaso adicional',
  checkpoint: 'Checkpoint',
  exam: 'Examen',
};

export function orientadorAssignmentPath(
  planId: number,
  index: number,
  assignment: Pick<OrientadorAssignment, 'type' | 'level' | 'block'>,
): string {
  const lvl = (assignment.level || 'a').toLowerCase();
  if (assignment.type === 'checkpoint' && assignment.block) {
    return `/${lvl}/checkpoint/${assignment.block}`;
  }
  if (assignment.type === 'exam') {
    return `/${lvl}/exam`;
  }
  return `/orientador/${planId}/${index}`;
}

export function assignmentLabel(a: OrientadorAssignment): string {
  if (a.type === 'set') {
    return `Set ${a.set_number} · Nivel ${(a.level || 'a').toUpperCase()}`;
  }
  if (a.type === 'checkpoint') {
    return `Checkpoint Bloque ${a.block} · Nivel ${(a.level || 'a').toUpperCase()}`;
  }
  if (a.type === 'exam') {
    return `Examen · Nivel ${(a.level || 'a').toUpperCase()}`;
  }
  return 'Asignacion';
}

export function reasonBadgeClass(reason: string): string {
  switch (reason) {
    case 'repeat':
      return 'text-amber-400';
    case 'new':
      return 'text-brand';
    case 'pre_exam':
    case 'repaso':
    case 'repaso_extra':
      return 'text-sky-400';
    default:
      return 'text-text-muted';
  }
}
