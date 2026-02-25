import { NavLink } from 'react-router-dom';
import type { ScanStatus } from '../types/movers';
import { StaleBanner } from './StaleBanner';

interface HeaderProps {
  scanStatus?: ScanStatus | null;
}

export function Header({ scanStatus }: HeaderProps) {
  const isStale = scanStatus?.analysis?.is_stale ?? scanStatus?.movers?.is_stale ?? false;
  const scanDate = scanStatus?.analysis?.scan_date ?? scanStatus?.movers?.scan_date ?? '';

  return (
    <header>
      {isStale && <StaleBanner scanDate={scanDate} />}
      <div className="border-b border-border bg-surface-alt px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div>
              <h1 className="text-xl font-bold text-text-bright">Prattern</h1>
              <p className="text-xs text-muted">Stock Mover Scanner + AI Classifier</p>
            </div>
            <nav className="flex gap-1">
              <NavLink
                to="/"
                end
                className={({ isActive }) =>
                  `rounded-md px-3 py-1.5 text-sm transition-colors ${isActive ? 'bg-accent/20 text-accent' : 'text-muted hover:text-text'}`
                }
              >
                Theme Tracker
              </NavLink>
              <NavLink
                to="/dashboard"
                className={({ isActive }) =>
                  `rounded-md px-3 py-1.5 text-sm transition-colors ${isActive ? 'bg-accent/20 text-accent' : 'text-muted hover:text-text'}`
                }
              >
                Dashboard
              </NavLink>
            </nav>
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
