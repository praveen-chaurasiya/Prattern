interface PriceFilterProps {
  value: number;
  onChange: (value: number) => void;
}

const OPTIONS = [
  { label: 'No filter', value: 0 },
  { label: '> $1', value: 1 },
  { label: '> $5', value: 5 },
  { label: '> $10', value: 10 },
  { label: '> $20', value: 20 },
];

export function PriceFilter({ value, onChange }: PriceFilterProps) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium uppercase tracking-wider text-muted">
        Min Price
      </label>
      <select
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text focus:border-accent focus:outline-none"
      >
        {OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}
