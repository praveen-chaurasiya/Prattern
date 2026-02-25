import type { ScanStatus } from '../types/movers';
import { PriceFilter } from './PriceFilter';
import { ModeToggle } from '../../features/analyzer/components/ModeToggle';

interface SidebarProps {
  scanStatus: ScanStatus | null;
  priceFilter: number;
  onPriceFilterChange: (value: number) => void;
  liveMode: boolean;
  onLiveModeChange: (live: boolean) => void;
  sseRunning: boolean;
  filteredCount: number;
  totalCount: number;
}

export function Sidebar({
  scanStatus,
  priceFilter,
  onPriceFilterChange,
  liveMode,
  onLiveModeChange,
  sseRunning,
  filteredCount,
  totalCount,
}: SidebarProps) {
  return (
    <aside className="flex w-56 shrink-0 flex-col gap-5 border-r border-border bg-surface-alt p-4">
      <ModeToggle live={liveMode} onChange={onLiveModeChange} disabled={sseRunning} />
      <PriceFilter value={priceFilter} onChange={onPriceFilterChange} />

      <div className="text-xs text-muted">
        <p className="mb-1 font-medium uppercase tracking-wider">Stats</p>
        <p>Showing {filteredCount} of {totalCount}</p>
        {scanStatus?.movers && (
          <>
            <p className="mt-1">Universe: {scanStatus.movers.universe_size?.toLocaleString()}</p>
            <p>Scan: {scanStatus.movers.scan_time}</p>
          </>
        )}
        {scanStatus?.analysis?.analysis_duration_seconds != null && (
          <p>Analysis: {scanStatus.analysis.analysis_duration_seconds.toFixed(0)}s</p>
        )}
      </div>
    </aside>
  );
}
