import type { AnalyzedMover } from '../../../shared/types/movers';
import { formatCurrency, formatPercent } from '../../../shared/utils/format';

interface MoverDetailProps {
  mover: AnalyzedMover;
}

export function MoverDetail({ mover }: MoverDetailProps) {
  return (
    <div className="border-t border-border bg-surface px-6 py-4 text-sm">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <h4 className="mb-1 font-medium text-text-bright">AI Summary</h4>
          <p className="text-muted">{mover.summary || 'No summary available'}</p>
        </div>
        <div>
          <h4 className="mb-1 font-medium text-text-bright">Price Details</h4>
          <div className="space-y-0.5 text-muted">
            <p>Current: {formatCurrency(mover.current_price)}</p>
            <p>5 days ago: {formatCurrency(mover.price_5d_ago)}</p>
            <p>Move: {formatPercent(mover.move_pct)}</p>
            <p>Category: {mover.category}</p>
            <p>Micro theme: {mover.micro_theme}</p>
          </div>
        </div>
      </div>
      {mover.headlines.length > 0 && (
        <div className="mt-3">
          <h4 className="mb-1 font-medium text-text-bright">Headlines</h4>
          <ul className="list-inside list-disc space-y-0.5 text-muted">
            {mover.headlines.map((h, i) => (
              <li key={i}>{h}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
