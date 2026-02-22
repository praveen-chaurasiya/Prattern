import { Fragment, useState } from 'react';
import type { AnalyzedMover } from '../../types/movers';
import { MoverRow } from './MoverRow';
import { MoverDetail } from './MoverDetail';

type SortKey = 'ticker' | 'move_pct' | 'current_price' | 'category' | 'primary_theme' | 'sub_niche' | 'ecosystem_role';

interface MoversTableProps {
  movers: AnalyzedMover[];
}

const COLUMNS: { key: SortKey; label: string; hideClass?: string }[] = [
  { key: 'ticker', label: 'Ticker' },
  { key: 'move_pct', label: 'Move %' },
  { key: 'current_price', label: 'Price' },
  { key: 'category', label: 'Category' },
  { key: 'primary_theme', label: 'Theme' },
  { key: 'sub_niche', label: 'Sub-Niche', hideClass: 'hidden md:table-cell' },
  { key: 'ecosystem_role', label: 'Role', hideClass: 'hidden lg:table-cell' },
];

export function MoversTable({ movers }: MoversTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('move_pct');
  const [sortAsc, setSortAsc] = useState(false);
  const [expandedTicker, setExpandedTicker] = useState<string | null>(null);

  const sorted = [...movers].sort((a, b) => {
    const av = a[sortKey];
    const bv = b[sortKey];
    if (typeof av === 'number' && typeof bv === 'number') {
      return sortAsc ? av - bv : bv - av;
    }
    return sortAsc
      ? String(av).localeCompare(String(bv))
      : String(bv).localeCompare(String(av));
  });

  function handleSort(key: SortKey) {
    if (key === sortKey) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(false); }
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-border bg-surface-alt text-xs uppercase tracking-wider text-muted">
          <tr>
            <th className="px-3 py-2.5">#</th>
            {COLUMNS.map((col) => (
              <th
                key={col.key}
                className={`cursor-pointer px-3 py-2.5 transition-colors hover:text-text-bright ${col.hideClass || ''}`}
                onClick={() => handleSort(col.key)}
              >
                {col.label}
                {sortKey === col.key && (
                  <span className="ml-1">{sortAsc ? '\u25B2' : '\u25BC'}</span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((m, i) => {
            const isExpanded = expandedTicker === m.ticker;
            return (
              <Fragment key={m.ticker}>
                <MoverRow
                  mover={m}
                  index={i}
                  expanded={isExpanded}
                  onToggle={() => setExpandedTicker(isExpanded ? null : m.ticker)}
                />
                {isExpanded && (
                  <tr>
                    <td colSpan={8}>
                      <MoverDetail mover={m} />
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
