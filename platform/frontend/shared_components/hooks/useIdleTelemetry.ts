import { useEffect, useRef } from 'react';

interface UseIdleTelemetryOptions {
  enabled: boolean;
  timeoutMs: number;
  onIdle: () => void;
}

/**
 * Generic idle timer helper that fires `onIdle` once after `timeoutMs`
 * while `enabled` remains true. Automatically resets when dependencies change.
 */
export const useIdleTelemetry = ({ enabled, timeoutMs, onIdle }: UseIdleTelemetryOptions): void => {
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const firedRef = useRef(false);

  useEffect(() => {
    if (!enabled) {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      firedRef.current = false;
      return;
    }

    firedRef.current = false;
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    timerRef.current = setTimeout(() => {
      if (firedRef.current) {
        return;
      }
      firedRef.current = true;
      onIdle();
    }, timeoutMs);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [enabled, timeoutMs, onIdle]);
};
