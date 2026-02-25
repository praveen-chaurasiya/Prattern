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
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {themes.map((theme) => (
              <ThemeCard key={theme.theme} theme={theme} onUpdate={refresh} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
