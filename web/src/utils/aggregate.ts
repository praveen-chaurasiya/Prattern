import type { AnalyzedMover } from '../types/movers';

export function countByField(
  movers: AnalyzedMover[],
  field: keyof AnalyzedMover,
): { label: string; count: number }[] {
  const counts = new Map<string, number>();
  for (const m of movers) {
    const val = String(m[field] || 'Unknown');
    counts.set(val, (counts.get(val) || 0) + 1);
  }
  return [...counts.entries()]
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count);
}
