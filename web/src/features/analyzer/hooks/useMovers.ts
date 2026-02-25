import { useEffect, useState } from 'react';
import { getLatestAnalysis } from '../api';
import type { AnalyzedMover } from '../../../shared/types/movers';

export function useMovers() {
  const [movers, setMovers] = useState<AnalyzedMover[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
  }, []);

  return { movers, setMovers, loading, error };
}
