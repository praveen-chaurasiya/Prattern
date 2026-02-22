import { apiUrl, authHeaders } from './client';
import type { SSEProgress, SSEComplete, SSEError } from '../types/movers';

export interface SSECallbacks {
  onProgress: (data: SSEProgress) => void;
  onComplete: (data: SSEComplete) => void;
  onError: (data: SSEError) => void;
}

export async function streamAnalysis(callbacks: SSECallbacks, signal?: AbortSignal) {
  const res = await fetch(apiUrl('/movers/analyze'), {
    method: 'POST',
    headers: authHeaders(),
    signal,
  });

  if (!res.ok || !res.body) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    callbacks.onError({ error: body.detail || res.statusText });
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    let currentEvent = '';
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (currentEvent === 'progress') callbacks.onProgress(data);
        else if (currentEvent === 'complete') callbacks.onComplete(data);
        else if (currentEvent === 'error') callbacks.onError(data);
      }
    }
  }
}
