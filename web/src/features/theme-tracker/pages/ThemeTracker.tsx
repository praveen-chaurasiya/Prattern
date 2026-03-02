import { useMemo } from 'react';
import { Header } from '../../../shared/components/Header';
import { Spinner } from '../../../shared/components/Spinner';
import { EmptyState } from '../../../shared/components/EmptyState';
import { useThemeTracker } from '../hooks/useThemeTracker';
import { PeriodTabs } from '../components/PeriodTabs';
import { ThemeCard } from '../components/ThemeCard';
import { AdminSection } from '../components/AdminSection';

export function ThemeTracker() {
  const { themes, loading, error, period, setPeriod, refresh } = useThemeTracker();
  const themeNames = themes.map((t) => t.theme);

  const { best, worst } = useMemo(() => {
    const sorted = [...themes].sort((a, b) => b.avg_change_pct - a.avg_change_pct);
    const bestPerformers = sorted.filter((t) => t.avg_change_pct >= 0);
    const worstPerformers = sorted.filter((t) => t.avg_change_pct < 0);
    return { best: bestPerformers, worst: worstPerformers };
  }, [themes]);

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 space-y-4 p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-text-bright">Theme Tracker</h2>
          <PeriodTabs active={period} onChange={setPeriod} />
        </div>

        <AdminSection themeNames={themeNames} onUpdate={refresh} />

        {loading ? (
          <Spinner />
        ) : error ? (
          <EmptyState message={error} />
        ) : themes.length === 0 ? (
          <EmptyState message="No themes configured. Use Admin Controls above to create themes." />
        ) : (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <section>
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-accent">
                Best Performers
              </h3>
              <div className="space-y-4">
                {best.length > 0 ? best.map((theme) => (
                  <ThemeCard key={theme.theme} theme={theme} onUpdate={refresh} />
                )) : (
                  <p className="text-sm text-muted">No gainers this period</p>
                )}
              </div>
            </section>

            <section>
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-danger">
                Worst Performers
              </h3>
              <div className="space-y-4">
                {worst.length > 0 ? worst.map((theme) => (
                  <ThemeCard key={theme.theme} theme={theme} onUpdate={refresh} />
                )) : (
                  <p className="text-sm text-muted">No losers this period</p>
                )}
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
