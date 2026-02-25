const PERIODS = [
  { key: 'today', label: 'Today' },
  { key: '1w', label: '1W' },
  { key: '1m', label: '1M' },
  { key: '3m', label: '3M' },
  { key: 'ytd', label: 'YTD' },
];

interface PeriodTabsProps {
  active: string;
  onChange: (period: string) => void;
}

export function PeriodTabs({ active, onChange }: PeriodTabsProps) {
  return (
    <div className="flex gap-1 rounded-lg border border-border bg-surface-alt p-1">
      {PERIODS.map((p) => (
        <button
          key={p.key}
          onClick={() => onChange(p.key)}
          className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
            active === p.key
              ? 'bg-accent/20 text-accent'
              : 'text-muted hover:text-text'
          }`}
        >
          {p.label}
        </button>
      ))}
    </div>
  );
}
