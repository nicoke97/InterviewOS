import { useEffect, useState } from 'react';
import { api } from './api';

export interface CurriculumLevel {
  id: string;
  letter: string;
  title: string;
}

export const FALLBACK_LEVELS: CurriculumLevel[] = [
  { id: 'a', letter: 'A', title: 'Level A — Fundamentos' },
  { id: 'b', letter: 'B', title: 'Level B — Bucles y funciones' },
  { id: 'c', letter: 'C', title: 'Level C — Listas, tuplas y strings' },
  { id: 'd', letter: 'D', title: 'Level D — Diccionarios, sets y errores' },
  { id: 'e', letter: 'E', title: 'Level E — Clases y OOP' },
];

export async function fetchCurriculumLevels(): Promise<CurriculumLevel[]> {
  try {
    const data = await api.curriculum();
    const levels = data.levels as CurriculumLevel[] | undefined;
    if (levels?.length) return levels;
  } catch {
    // use fallback
  }
  return FALLBACK_LEVELS;
}

export function useCurriculumLevels(): CurriculumLevel[] {
  const [levels, setLevels] = useState<CurriculumLevel[]>(FALLBACK_LEVELS);
  useEffect(() => {
    fetchCurriculumLevels().then(setLevels).catch(() => {});
  }, []);
  return levels;
}

export function useRouteLevel(levelParam: string | undefined): string | null {
  const levels = useCurriculumLevels();
  const ids = levels.map((l) => l.id);
  return levelParam && ids.includes(levelParam.toLowerCase()) ? levelParam.toLowerCase() : null;
}
