import { useEffect, useState } from 'react';
import { getScanStatus } from '../api/movers';
import type { ScanStatus } from '../types/movers';

export function useScanStatus() {
  const [status, setStatus] = useState<ScanStatus | null>(null);

  useEffect(() => {
    getScanStatus().then(setStatus).catch(() => {});
  }, []);

  return status;
}
