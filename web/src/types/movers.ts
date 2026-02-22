export interface Mover {
  ticker: string;
  current_price: number;
  price_5d_ago: number;
  move_pct: number;
  date: string;
  headlines: string[];
}

export interface AnalyzedMover extends Mover {
  category: string;
  summary: string;
  primary_theme: string;
  sub_niche: string;
  ecosystem_role: string;
  micro_theme: string;
}

export interface ScanStatusSection {
  scan_date: string;
  scan_time?: string;
  analysis_time?: string;
  analysis_duration_seconds?: number;
  universe_size?: number;
  movers_count: number;
  is_stale: boolean;
}

export interface ScanStatus {
  today: string;
  movers: ScanStatusSection | null;
  analysis: ScanStatusSection | null;
}

export interface AnalysisResponse {
  scan_date: string;
  analysis_time: string;
  analysis_duration_seconds: number;
  movers_count: number;
  movers: AnalyzedMover[];
}

export interface MoversResponse {
  scan_date: string;
  scan_time: string;
  universe_size: number;
  threshold: number;
  movers_found: number;
  movers: Mover[];
}

export interface SSEProgress {
  stage: string;
  current: number;
  total: number;
  detail: string;
}

export interface SSEComplete {
  movers_count: number;
  movers: AnalyzedMover[];
}

export interface SSEError {
  error: string;
}
