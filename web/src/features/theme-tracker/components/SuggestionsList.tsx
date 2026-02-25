import { useEffect, useState } from 'react';
import type { ThemeSuggestion } from '../../../shared/types/themes';
import { fetchSuggestions } from '../api';
import { SuggestionRow } from './SuggestionRow';

interface SuggestionsListProps {
  themeNames: string[];
  onUpdate: () => void;
}

export function SuggestionsList({ themeNames, onUpdate }: SuggestionsListProps) {
  const [suggestions, setSuggestions] = useState<ThemeSuggestion[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    fetchSuggestions()
      .then((data) => setSuggestions(data.suggestions || []))
      .catch(() => setSuggestions([]))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleAdded = () => {
    load();
    onUpdate();
  };

  // Group by primary_theme
  const grouped: Record<string, ThemeSuggestion[]> = {};
  for (const s of suggestions) {
    const key = s.primary_theme || 'Other';
    (grouped[key] ||= []).push(s);
  }

  if (loading) {
    return <p className="py-4 text-center text-sm text-muted">Loading suggestions...</p>;
  }

  if (suggestions.length === 0) {
    return <p className="py-4 text-center text-sm text-muted">All tickers already assigned to themes.</p>;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-text-bright">AI Suggestions</h4>
        <button
          className="rounded border border-border px-3 py-1 text-xs text-muted hover:text-text-bright"
          onClick={load}
        >
          Refresh
        </button>
      </div>
      {Object.entries(grouped).sort(([a], [b]) => a.localeCompare(b)).map(([theme, items]) => (
        <div key={theme} className="overflow-hidden rounded border border-border">
          <div className="bg-surface-alt px-3 py-1.5 text-xs font-semibold text-accent">
            {theme} ({items.length})
          </div>
          {items.map((s) => (
            <SuggestionRow
              key={s.ticker}
              suggestion={s}
              themeNames={themeNames}
              onAdded={handleAdded}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
