import { useState } from 'react';
import type { ThemeStats } from '../../../shared/types/themes';
import { formatPercent, formatCurrency } from '../../../shared/utils/format';
import { removeTickerFromTheme, deleteTheme } from '../api';

interface ThemeCardProps {
  theme: ThemeStats;
  onUpdate?: () => void;
}

export function ThemeCard({ theme, onUpdate }: ThemeCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const isPositive = theme.avg_change_pct >= 0;

  const handleRemoveTicker = async (ticker: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await removeTickerFromTheme(theme.theme, ticker);
      onUpdate?.();
    } catch {
      // ignore
    }
  };

  const handleDeleteTheme = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setDeleting(true);
    try {
      await deleteTheme(theme.theme);
      onUpdate?.();
    } catch {
      // ignore
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div
      className="cursor-pointer overflow-hidden rounded-lg border border-border bg-surface-alt transition-colors hover:border-accent/30"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-center justify-between p-4">
        <div className="min-w-0 flex-1">
          <h3 className="font-medium text-text-bright">{theme.theme}</h3>
          <p className="mt-0.5 text-xs text-muted">{theme.description}</p>
        </div>
        <div className="ml-4 text-right">
          <p className={`text-lg font-bold font-mono ${isPositive ? 'text-accent' : 'text-danger'}`}>
            {formatPercent(theme.avg_change_pct)}
          </p>
          <p className="text-xs text-muted">{theme.stock_count} stocks</p>
        </div>
      </div>

      {expanded && theme.stocks.length > 0 && (
        <div className="border-t border-border bg-surface">
          {theme.stocks.map((stock) => (
            <div key={stock.ticker} className="flex items-center border-t border-border px-4 py-2 text-sm">
              <span className="font-mono font-bold text-text-bright">{stock.ticker}</span>
              <div className="ml-auto flex items-center gap-4">
                <span className="font-mono text-muted">{formatCurrency(stock.current_price)}</span>
                <span className={`font-mono font-medium ${stock.change_pct >= 0 ? 'text-accent' : 'text-danger'}`}>
                  {formatPercent(stock.change_pct)}
                </span>
                <button
                  className="rounded px-2 py-0.5 text-xs text-danger hover:bg-danger/10"
                  onClick={(e) => handleRemoveTicker(stock.ticker, e)}
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {expanded && theme.stock_count === 0 && (
        <div className="border-t border-border p-3 text-center">
          <button
            className="rounded bg-danger px-3 py-1 text-xs font-medium text-white disabled:opacity-50"
            onClick={handleDeleteTheme}
            disabled={deleting}
          >
            {deleting ? 'Deleting...' : 'Delete Empty Theme'}
          </button>
        </div>
      )}

      <div className="flex items-center justify-center border-t border-border py-1">
        <span className="text-xs text-muted">
          {expanded ? 'Click to collapse' : 'Click to expand'}
        </span>
      </div>
    </div>
  );
}
