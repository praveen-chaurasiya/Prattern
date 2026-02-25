import type { AnalyzedMover } from '../../../shared/types/movers';
import { countByField } from '../../../shared/utils/aggregate';
import { BreakdownCard } from './BreakdownCard';

interface ThemeBreakdownProps {
  movers: AnalyzedMover[];
}

export function ThemeBreakdown({ movers }: ThemeBreakdownProps) {
  if (movers.length === 0) return null;

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      <BreakdownCard title="Primary Theme" items={countByField(movers, 'primary_theme')} />
      <BreakdownCard title="Ecosystem Role" items={countByField(movers, 'ecosystem_role')} />
      <BreakdownCard title="Sub-Niche" items={countByField(movers, 'sub_niche')} />
    </div>
  );
}
