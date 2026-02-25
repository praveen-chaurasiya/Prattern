import type { AnalyzedMover } from '../../../shared/types/movers';
import { formatCurrency, formatPercent } from '../../../shared/utils/format';

interface MoverRowProps {
  mover: AnalyzedMover;
  index: number;
  expanded: boolean;
  onToggle: () => void;
}

export function MoverRow({ mover, index, expanded, onToggle }: MoverRowProps) {
  return (
    <tr
      className={`cursor-pointer border-b border-border transition-colors hover:bg-surface-hover ${expanded ? 'bg-surface-hover' : ''}`}
      onClick={onToggle}
    >
      <td className="px-3 py-2.5 text-muted">{index + 1}</td>
      <td className="px-3 py-2.5 font-mono font-bold text-text-bright">{mover.ticker}</td>
      <td className="px-3 py-2.5 font-mono text-accent">{formatPercent(mover.move_pct)}</td>
      <td className="px-3 py-2.5 font-mono text-muted">{formatCurrency(mover.current_price)}</td>
      <td className="px-3 py-2.5">{mover.category}</td>
      <td className="px-3 py-2.5">{mover.primary_theme}</td>
      <td className="hidden px-3 py-2.5 md:table-cell">{mover.sub_niche}</td>
      <td className="hidden px-3 py-2.5 lg:table-cell">{mover.ecosystem_role}</td>
    </tr>
  );
}
