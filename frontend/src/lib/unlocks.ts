export interface LevelUnlocks {
  leetcode_unlocked: boolean;
  interview_unlocked: boolean;
}

export type UnlockMap = Record<string, LevelUnlocks>;

export function levelFromBlock(block: string): string {
  if (!block) return 'a';
  const levelPart = block.includes('.') ? block.split('.')[0] : block.charAt(0);
  return levelPart.toLowerCase() || 'a';
}

export function isCategoryUnlocked(
  level: string,
  category: string,
  unlocks: UnlockMap,
): boolean {
  if (category === 'kumon') return true;
  const u = unlocks[level];
  if (!u) return false;
  if (category === 'leetcode') return u.leetcode_unlocked;
  if (category === 'interview' || category === 'odoo') return u.interview_unlocked;
  return true;
}
