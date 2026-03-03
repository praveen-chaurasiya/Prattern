import { useCallback, useRef, useState } from 'react';
import { startScanRefresh, pollJob } from '../api';

interface ScanRefreshState {
  running: boolean;
  stage: string;
  detail: string;
  error: string | null;
}

export function useScanRefresh(onComplete?: () => void) {
  const [state, setState] = useState<ScanRefreshState>({
    running: false,
    stage: '',
    detail: '',
    error: null,
  });
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stop = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const start = useCallback(async () => {
    setState({ running: true, stage: 'starting', detail: 'Initiating scan...', error: null });

    try {
      const { job_id } = await startScanRefresh();

      timerRef.current = setInterval(async () => {
        try {
          const job = await pollJob(job_id);

          if (job.status === 'running') {
            setState({
              running: true,
              stage: job.progress.stage,
              detail: job.progress.detail,
              error: null,
            });
          } else if (job.status === 'complete') {
            stop();
            setState({ running: false, stage: 'complete', detail: 'Refresh complete', error: null });
            onComplete?.();
          } else if (job.status === 'failed') {
            stop();
            setState({ running: false, stage: '', detail: '', error: job.error || 'Refresh failed' });
          }
        } catch {
          stop();
          setState({ running: false, stage: '', detail: '', error: 'Lost connection to server' });
        }
      }, 2000);
    } catch (err) {
      setState({
        running: false,
        stage: '',
        detail: '',
        error: err instanceof Error ? err.message : 'Failed to start refresh',
      });
    }
  }, [onComplete, stop]);

  return { ...state, start };
}
