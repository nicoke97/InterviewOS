import { useEffect, useState } from 'react';
import { api } from './api';
import { useI18n } from '../i18n/context';

export interface CurriculumLevel {
  id: string;
  letter: string;
  title: string;
}

const FALLBACK_KEYS = ['a', 'b', 'c', 'd', 'e'] as const;

export function useCurriculumLevels(): CurriculumLevel[] {
  const { t, locale } = useI18n();
  const [levels, setLevels] = useState<CurriculumLevel[]>(() =>
    FALLBACK_KEYS.map((id) => ({
      id,
      letter: id.toUpperCase(),
      title: t(`levels.${id}`),
    })),
  );

  useEffect(() => {
    api.curriculum()
      .then((data) => {
        const apiLevels = data.levels as CurriculumLevel[] | undefined;
        if (apiLevels?.length) setLevels(apiLevels);
      })
      .catch(() => {});
  }, [locale]);

  return levels;
}

export function useRouteLevel(levelParam: string | undefined): string | null {
  const levels = useCurriculumLevels();
  const ids = levels.map((l) => l.id);
  return levelParam && ids.includes(levelParam.toLowerCase()) ? levelParam.toLowerCase() : null;
}

export async function fetchCurriculumLevels(): Promise<CurriculumLevel[]> {
  try {
    const data = await api.curriculum();
    const levels = data.levels as CurriculumLevel[] | undefined;
    if (levels?.length) return levels;
  } catch {
    /* use fallback */
  }
  return FALLBACK_KEYS.map((id) => ({ id, letter: id.toUpperCase(), title: `Level ${id.toUpperCase()}` }));
}
