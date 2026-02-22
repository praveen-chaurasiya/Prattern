import { apiFetch } from './client';
import type { AnalysisResponse, MoversResponse, ScanStatus } from '../types/movers';

export function getMovers() {
  return apiFetch<MoversResponse>('/movers');
}

export function getLatestAnalysis() {
  return apiFetch<AnalysisResponse>('/analysis/latest');
}

export function getScanStatus() {
  return apiFetch<ScanStatus>('/scan/status');
}
