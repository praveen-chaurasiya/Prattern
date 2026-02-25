import { useCallback, useRef, useState } from 'react';
import { streamAnalysis } from '../api';
import type { AnalyzedMover, SSEProgress } from '../../../shared/types/movers';

export function useAnalysisSSE(onComplete: (movers: AnalyzedMover[]) => void) {
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState<SSEProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const start = useCallback(() => {
    setRunning(true);
    setProgress(null);
    setError(null);

    const controller = new AbortController();
    abortRef.current = controller;

    streamAnalysis(
      {
        onProgress: setProgress,
        onComplete: (data) => {
          setRunning(false);
          onComplete(data.movers);
        },
        onError: (data) => {
          setRunning(false);
          setError(data.error);
        },
      },
      controller.signal,
    ).catch((err) => {
      if (err.name !== 'AbortError') {
        setRunning(false);
        setError(err.message);
      }
    });
  }, [onComplete]);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setRunning(false);
  }, []);

  return { running, progress, error, start, cancel };
}
