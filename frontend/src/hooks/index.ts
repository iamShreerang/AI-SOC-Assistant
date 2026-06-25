import { useState, useEffect, useCallback } from 'react';
import { apiService } from '@/services/api';
import { useNotificationStore, useSettingsStore } from '@/store';

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
  interval: number = 30000
) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { settings } = useSettingsStore();

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const result = await fetchFn();
        setData(result);
        setError(null);
      } catch (err: any) {
        setError(err.response?.data?.detail || err.message);
      } finally {
        setLoading(false);
      }
    };

    fetch();

    if (settings.auto_refresh) {
      const timer = setInterval(fetch, settings.refresh_interval || interval);
      return () => clearInterval(timer);
    }
  }, [interval, settings.auto_refresh, settings.refresh_interval]);

  return { data, loading, error };
};

export const useDebounce = <T,>(value: T, delay: number = 500): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
};
