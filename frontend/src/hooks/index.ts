import { useState, useEffect, useCallback, useRef } from 'react';

import { useNotificationStore } from '@/store';

export const useFetch = <T,>(
  fetchFn: () => Promise<T>,
  dependencies: any[] = []
) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { addNotification } = useNotificationStore();

  const fetch = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await fetchFn();
      setData(result);
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'An error occurred';
      setError(message);
      addNotification({
        type: 'error',
        title: 'Error',
        message,
      });
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
};

export const usePolling = <T,>(
  fetchFn: () => Promise<T>,
  interval: number = 5000
) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true); // true only on first fetch
  const [error, setError] = useState<string | null>(null);
  const fetchFnRef = useRef(fetchFn);
  fetchFnRef.current = fetchFn;

  const execute = useCallback(async (isFirst: boolean) => {
    try {
      if (isFirst) setLoading(true);
      const result = await fetchFnRef.current();
      setData(result);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      if (isFirst) setLoading(false);
    }
  }, []);

  useEffect(() => {
    execute(true); // first load — show spinner once
    if (interval > 0) {
      const timer = setInterval(() => execute(false), interval); // subsequent — silent
      return () => clearInterval(timer);
    }
  }, [interval, execute]);

  const refetch = useCallback(() => execute(false), [execute]);

  return { data, loading, error, refetch };
};

export const useDebounce = <T,>(value: T, delay: number = 500): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
};
