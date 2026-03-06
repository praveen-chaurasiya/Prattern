interface StaleBannerProps {
  scanDate: string;
  refreshing?: boolean;
  refreshStage?: string;
  refreshDetail?: string;
  refreshError?: string | null;
  onRefresh?: () => void;
}

const API_KEY = import.meta.env.VITE_API_KEY || '';

export function StaleBanner({ scanDate, refreshing, refreshStage, refreshDetail, refreshError, onRefresh }: StaleBannerProps) {
  const isAdmin = !!API_KEY;

  return (
    <div className="bg-danger/15 border-b border-danger/30 px-4 py-2 text-sm text-danger">
      <div className="flex items-center justify-between">
        <span>
          {refreshing
            ? `Refreshing: ${refreshStage} — ${refreshDetail}`
            : refreshError
              ? `Refresh failed: ${refreshError}`
              : scanDate
                ? `Data is stale — last scan: ${scanDate}. Run the scanner to refresh.`
                : `No scan data found. Run the scanner to get started.`}
        </span>
        {isAdmin && onRefresh && (
          <button
            onClick={onRefresh}
            disabled={refreshing}
            className="ml-4 rounded bg-danger/80 px-3 py-1 text-xs font-semibold text-white transition-colors hover:bg-danger disabled:opacity-50"
          >
            {refreshing ? 'Refreshing...' : 'Refresh Scan'}
          </button>
        )}
      </div>
    </div>
  );
}
