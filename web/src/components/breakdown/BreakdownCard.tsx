interface BreakdownCardProps {
  title: string;
  items: { label: string; count: number }[];
  maxItems?: number;
}

export function BreakdownCard({ title, items, maxItems = 10 }: BreakdownCardProps) {
  const shown = items.slice(0, maxItems);
  const total = items.reduce((s, i) => s + i.count, 0);

  return (
    <div className="rounded-lg border border-border bg-surface-alt p-4">
      <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-muted">{title}</h3>
      <div className="space-y-1.5">
        {shown.map((item) => {
          const pct = total > 0 ? (item.count / total) * 100 : 0;
          return (
            <div key={item.label} className="flex items-center gap-2 text-sm">
              <div className="relative h-1.5 flex-1 overflow-hidden rounded-full bg-surface">
                <div className="h-full rounded-full bg-accent/40" style={{ width: `${pct}%` }} />
              </div>
              <span className="w-20 truncate text-text" title={item.label}>{item.label}</span>
              <span className="w-6 text-right font-mono text-xs text-muted">{item.count}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
