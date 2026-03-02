import { useCallback, useEffect, useState } from 'react';
import { getLatestAnalysis } from '../api';
import type { AnalyzedMover } from '../../../shared/types/movers';

export function useMovers() {
  const [movers, setMovers] = useState<AnalyzedMover[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trigger, setTrigger] = useState(0);

  const reload = useCallback(() => {
    setLoading(true);
    setError(null);
    setTrigger((n) => n + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;
    getLatestAnalysis()
      .then((data) => {
        if (!cancelled) setMovers(data.movers || []);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [trigger]);

  return { movers, setMovers, loading, error, reload };
}
