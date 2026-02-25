import { useState } from 'react';
import type { ThemeSuggestion } from '../../../shared/types/themes';
import { addTickerToTheme } from '../api';
import { formatPercent } from '../../../shared/utils/format';

interface SuggestionRowProps {
  suggestion: ThemeSuggestion;
  themeNames: string[];
  onAdded: () => void;
}

export function SuggestionRow({ suggestion, themeNames, onAdded }: SuggestionRowProps) {
  const [selectedTheme, setSelectedTheme] = useState(themeNames[0] || '');
  const [adding, setAdding] = useState(false);

  const handleAdd = async () => {
    if (!selectedTheme) return;
    setAdding(true);
    try {
      await addTickerToTheme(selectedTheme, suggestion.ticker);
      onAdded();
    } catch {
      // ignore
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="flex items-center gap-3 border-t border-border px-3 py-1.5 text-sm">
      <span className="w-16 font-mono font-bold text-text-bright">{suggestion.ticker}</span>
      <span className="w-16 font-mono text-accent">{formatPercent(suggestion.move_pct)}</span>
      <span className="w-28 text-xs text-muted">{suggestion.category}</span>
      {themeNames.length > 0 ? (
        <>
          <select
            className="rounded border border-border bg-surface px-2 py-1 text-xs text-text-bright"
            value={selectedTheme}
            onChange={(e) => setSelectedTheme(e.target.value)}
          >
            {themeNames.map((name) => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
          <button
            className="rounded bg-accent px-3 py-1 text-xs font-medium text-white disabled:opacity-50"
            onClick={handleAdd}
            disabled={adding}
          >
            {adding ? '...' : 'Add'}
          </button>
        </>
      ) : (
        <span className="text-xs text-muted">Create a theme first</span>
      )}
    </div>
  );
}
