import { useCallback, useEffect, useState } from 'react';
import { fetchThemeTracker } from '../api';
import type { ThemeStats } from '../../../shared/types/themes';

export function useThemeTracker() {
  const [themes, setThemes] = useState<ThemeStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState('1w');
  const [refreshKey, setRefreshKey] = useState(0);

  const refresh = useCallback(() => setRefreshKey((k) => k + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchThemeTracker(period)
      .then((data) => {
        if (!cancelled) setThemes(data.themes || []);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [period, refreshKey]);

  return { themes, loading, error, period, setPeriod, refresh };
}
