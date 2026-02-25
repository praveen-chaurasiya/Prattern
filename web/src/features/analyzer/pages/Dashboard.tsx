import { useCallback, useMemo, useState } from 'react';
import type { AnalyzedMover } from '../../../shared/types/movers';
import { useMovers } from '../hooks/useMovers';
import { useScanStatus } from '../hooks/useScanStatus';
import { useAnalysisSSE } from '../hooks/useAnalysisSSE';
import { Header } from '../../../shared/components/Header';
import { Sidebar } from '../../../shared/components/Sidebar';
import { MoversTable } from '../components/MoversTable';
import { ThemeBreakdown } from '../components/ThemeBreakdown';
import { AnalysisProgress } from '../components/AnalysisProgress';
import { Spinner } from '../../../shared/components/Spinner';
import { EmptyState } from '../../../shared/components/EmptyState';

export function Dashboard() {
  const { movers, setMovers, loading, error } = useMovers();
  const scanStatus = useScanStatus();
  const [priceFilter, setPriceFilter] = useState(0);
  const [liveMode, setLiveMode] = useState(false);

  const onSSEComplete = useCallback(
    (analyzed: AnalyzedMover[]) => setMovers(analyzed),
    [setMovers],
  );
  const sse = useAnalysisSSE(onSSEComplete);

  function handleModeChange(live: boolean) {
    setLiveMode(live);
    if (live && !sse.running) sse.start();
  }

  const filtered = useMemo(
    () => movers.filter((m) => m.current_price >= priceFilter),
    [movers, priceFilter],
  );

  return (
    <div className="flex min-h-screen flex-col">
      <Header scanStatus={scanStatus} />
      <div className="flex flex-1">
        <Sidebar
          scanStatus={scanStatus}
          priceFilter={priceFilter}
          onPriceFilterChange={setPriceFilter}
          liveMode={liveMode}
          onLiveModeChange={handleModeChange}
          sseRunning={sse.running}
          filteredCount={filtered.length}
          totalCount={movers.length}
        />
        <main className="flex-1 space-y-4 p-4">
          {sse.running && sse.progress && (
            <AnalysisProgress progress={sse.progress} />
          )}
          {sse.error && (
            <div className="rounded-lg border border-danger/30 bg-danger/10 p-3 text-sm text-danger">
              {sse.error}
            </div>
          )}
          {loading ? (
            <Spinner />
          ) : error && movers.length === 0 ? (
            <EmptyState message={error} />
          ) : filtered.length === 0 ? (
            <EmptyState message={priceFilter > 0 ? 'No movers match the current filter' : 'No analyzed movers found. Run the scanner and analyzer first.'} />
          ) : (
            <>
              <MoversTable movers={filtered} />
              <ThemeBreakdown movers={filtered} />
            </>
          )}
        </main>
      </div>
    </div>
  );
}
