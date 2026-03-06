const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY || '';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function authHeaders(): Record<string, string> {
  if (!API_KEY) return {};
  return { 'X-API-Key': API_KEY };
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = { ...authHeaders(), ...init?.headers };
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail || res.statusText);
  }
  return res.json();
}

export function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}
