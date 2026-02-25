import type { SSEProgress } from '../../../shared/types/movers';

interface AnalysisProgressProps {
  progress: SSEProgress;
}

export function AnalysisProgress({ progress }: AnalysisProgressProps) {
  const pct = progress.total > 0 ? (progress.current / progress.total) * 100 : 0;

  return (
    <div className="rounded-lg border border-border bg-surface-alt p-4">
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="text-text-bright">{progress.stage}</span>
        <span className="text-muted">{progress.current} / {progress.total}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-surface">
        <div
          className="h-full rounded-full bg-accent transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
      {progress.detail && (
        <p className="mt-1.5 text-xs text-muted">{progress.detail}</p>
      )}
    </div>
  );
}
