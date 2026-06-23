export function resolveDisplaySetNumber(globalSetNumber: number, displaySetNumberFromApi?: number): number {
  const SETS_PER_BLOCK = 5;
  return displaySetNumberFromApi ?? ((globalSetNumber - 1) % SETS_PER_BLOCK) + 1;
}

export function formatSetLevelLabel(
  globalSetNumber: number,
  level: string,
  displaySetNumberFromApi?: number,
  locale: 'en' | 'es' = 'en',
): string {
  const SETS_PER_BLOCK = 5;
  const displaySetNumber = displaySetNumberFromApi ?? ((globalSetNumber - 1) % SETS_PER_BLOCK) + 1;
  if (locale === 'es') {
    return `Set ${displaySetNumber} · Nivel ${level.toUpperCase()}`;
  }
  return `Set ${displaySetNumber} · Level ${level.toUpperCase()}`;
}
