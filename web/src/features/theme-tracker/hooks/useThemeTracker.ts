import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchThemeTracker } from '../api';
import type { ThemeStats } from '../../../shared/types/themes';

const ALL_PERIODS = ['today', '1w', '1m', '3m', 'ytd'] as const;

interface CachedResult {
  themes: ThemeStats[];
  timestamp: number;
}

const CACHE_TTL_MARKET_OPEN = 5 * 60 * 1000;   // 5 minutes
const CACHE_TTL_MARKET_CLOSED = 24 * 60 * 60 * 1000; // 24 hours

function isMarketOpen(): boolean {
  const now = new Date();
  const et = new Date(now.toLocaleString('en-US', { timeZone: 'America/New_York' }));
  const day = et.getDay();
  if (day === 0 || day === 6) return false; // weekend
  const minutes = et.getHours() * 60 + et.getMinutes();
  return minutes >= 570 && minutes <= 960; // 9:30 AM - 4:00 PM
}

function getCacheTtl(): number {
  return isMarketOpen() ? CACHE_TTL_MARKET_OPEN : CACHE_TTL_MARKET_CLOSED;
}

export function useThemeTracker() {
  const [themes, setThemes] = useState<ThemeStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState('today');
  const [refreshKey, setRefreshKey] = useState(0);
  const cache = useRef<Record<string, CachedResult>>({});

  const refresh = useCallback(() => {
    // Clear cache on manual refresh so we get fresh data
    cache.current = {};
    setRefreshKey((k) => k + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;

    const cached = cache.current[period];
    if (cached && Date.now() - cached.timestamp < getCacheTtl()) {
      // Instant switch from cache
      setThemes(cached.themes);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    fetchThemeTracker(period)
      .then((data) => {
        if (cancelled) return;
        const result = data.themes || [];
        setThemes(result);
        cache.current[period] = { themes: result, timestamp: Date.now() };
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [period, refreshKey]);

  // Prefetch other periods in background after initial load completes
  useEffect(() => {
    if (loading) return;

    const prefetch = ALL_PERIODS.filter((p) => p !== period && !cache.current[p]);
    for (const p of prefetch) {
      fetchThemeTracker(p)
        .then((data) => {
          cache.current[p] = { themes: data.themes || [], timestamp: Date.now() };
        })
        .catch(() => { /* silent — prefetch is best-effort */ });
    }
  }, [loading, period, refreshKey]);

  return { themes, loading, error, period, setPeriod, refresh };
}
