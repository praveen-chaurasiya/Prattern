import { apiFetch } from '../../shared/api/client';
import type { ThemeTrackerResponse, ThemeSuggestionsResponse } from '../../shared/types/themes';

export function fetchThemeTracker(period: string = '1w') {
  return apiFetch<ThemeTrackerResponse>(`/themes/tracker?period=${period}`);
}

export function addTickerToTheme(theme: string, ticker: string) {
  return apiFetch(`/themes/${encodeURIComponent(theme)}/tickers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ticker }),
  });
}

export function removeTickerFromTheme(theme: string, ticker: string) {
  return apiFetch(`/themes/${encodeURIComponent(theme)}/tickers/${encodeURIComponent(ticker)}`, {
    method: 'DELETE',
  });
}

export function fetchSuggestions() {
  return apiFetch<ThemeSuggestionsResponse>('/themes/suggestions');
}

export function createTheme(name: string, description: string = '') {
  return apiFetch('/themes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description }),
  });
}

export function deleteTheme(theme: string) {
  return apiFetch(`/themes/${encodeURIComponent(theme)}`, {
    method: 'DELETE',
  });
}
