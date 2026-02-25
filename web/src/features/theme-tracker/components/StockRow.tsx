import type { ThemeStock } from '../../../shared/types/themes';
import { formatCurrency, formatPercent } from '../../../shared/utils/format';

interface StockRowProps {
  stock: ThemeStock;
}

export function StockRow({ stock }: StockRowProps) {
  const isPositive = stock.change_pct >= 0;

  return (
    <div className="flex items-center justify-between border-t border-border px-4 py-2 text-sm">
      <span className="font-mono font-bold text-text-bright">{stock.ticker}</span>
      <div className="flex items-center gap-4">
        <span className="font-mono text-muted">{formatCurrency(stock.current_price)}</span>
        <span className={`font-mono font-medium ${isPositive ? 'text-accent' : 'text-danger'}`}>
          {formatPercent(stock.change_pct)}
        </span>
      </div>
    </div>
  );
}
