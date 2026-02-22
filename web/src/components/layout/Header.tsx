import type { ScanStatus } from '../../types/movers';
import { StaleBanner } from '../common/StaleBanner';

interface HeaderProps {
  scanStatus: ScanStatus | null;
}

export function Header({ scanStatus }: HeaderProps) {
  const isStale = scanStatus?.analysis?.is_stale ?? scanStatus?.movers?.is_stale ?? false;
  const scanDate = scanStatus?.analysis?.scan_date ?? scanStatus?.movers?.scan_date ?? '';

  return (
    <header>
      {isStale && <StaleBanner scanDate={scanDate} />}
      <div className="border-b border-border bg-surface-alt px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-text-bright">Prattern</h1>
            <p className="text-xs text-muted">Stock Mover Scanner + AI Classifier</p>
          </div>
          {scanStatus?.analysis && (
            <div className="text-right text-xs text-muted">
              <p>Scanned: {scanStatus.analysis.scan_date}</p>
              <p>{scanStatus.analysis.movers_count} movers analyzed</p>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
