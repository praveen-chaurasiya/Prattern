export interface ThemeStock {
  ticker: string;
  change_pct: number;
  current_price: number;
  subtheme: string;
  role: string;
}

export interface ThemeStats {
  theme: string;
  description: string;
  avg_change_pct: number;
  stock_count: number;
  stocks: ThemeStock[];
}

export interface ThemeTrackerResponse {
  period: string;
  themes: ThemeStats[];
}

export interface ThemeSuggestion {
  ticker: string;
  primary_theme: string;
  sub_niche: string;
  category: string;
  move_pct: number;
}

export interface ThemeSuggestionsResponse {
  suggestions: ThemeSuggestion[];
}
