import { useCallback, useEffect, useRef, useState } from 'react';
import type { ApiServiceError as ApiErrorType } from '../services/api';

/**
 * Wraps an async service call with loading/error state.
 * Returns [run, state]; `run` triggers the call, state carries data/error.
 */
export function useApi<T>(initialData: T | null = null) {
  const [data, setData] = useState<T | null>(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiErrorType | null>(null);
  const mounted = useRef(true);

  useEffect(() => () => {
    mounted.current = false;
  }, []);

  const run = useCallback(
    async (fn: () => Promise<T>): Promise<T | null> => {
      setLoading(true);
      setError(null);
      try {
        const result = await fn();
        if (mounted.current) setData(result);
        return result;
      } catch (e) {
        if (mounted.current) {
          setError(
            e instanceof Error && 'status' in e
              ? (e as ApiErrorType)
              : ({ status: 0, message: e instanceof Error ? e.message : 'Unknown error' } as ApiErrorType)
          );
        }
        return null;
      } finally {
        if (mounted.current) setLoading(false);
      }
    },
    []
  );

  return { data, setData, loading, error, run };
}

/**
 * Polls an async producer on an interval (default 2 s — the dashboard
 * latest-result cadence). Stops on unmount. Skips while a tick is running.
 */
export function usePolling<T>(fn: () => Promise<T>, intervalMs = 2000, enabled = true) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiErrorType | null>(null);
  const running = useRef(false);
  const mounted = useRef(true);

  useEffect(() => () => {
    mounted.current = false;
  }, []);

  useEffect(() => {
    if (!enabled) return;
    let timer: ReturnType<typeof setTimeout>;

    const tick = async () => {
      if (running.current) {
        timer = setTimeout(tick, intervalMs);
        return;
      }
      running.current = true;
      try {
        const result = await fn();
        if (mounted.current) {
          setData(result);
          setError(null);
        }
      } catch (e) {
        if (mounted.current) {
          setError(
            e instanceof Error && 'status' in e
              ? (e as ApiErrorType)
              : ({ status: 0, message: e instanceof Error ? e.message : 'Unknown error' } as ApiErrorType)
          );
        }
      } finally {
        running.current = false;
        if (mounted.current) timer = setTimeout(tick, intervalMs);
      }
    };

    tick();
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, intervalMs]);

  return { data, error };
}
