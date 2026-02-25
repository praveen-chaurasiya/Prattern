import { useEffect, useState } from 'react';
import { fetchThemeTracker } from '../api';

export function useThemeNames() {
  const [names, setNames] = useState<string[]>([]);

  useEffect(() => {
    fetchThemeTracker('1w')
      .then((data) => setNames(data.themes.map((t) => t.theme)))
      .catch(() => {});
  }, []);

  const refresh = () => {
    fetchThemeTracker('1w')
      .then((data) => setNames(data.themes.map((t) => t.theme)))
      .catch(() => {});
  };

  return { names, refresh };
}
