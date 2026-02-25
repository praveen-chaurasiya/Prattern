import { useEffect, useState } from 'react';
import { getScanStatus } from '../api';
import type { ScanStatus } from '../../../shared/types/movers';

export function useScanStatus() {
  const [status, setStatus] = useState<ScanStatus | null>(null);

  useEffect(() => {
    getScanStatus().then(setStatus).catch(() => {});
  }, []);

  return status;
}
