import { useState, useCallback } from 'react';

interface ApiState {
  loading: boolean;
  error: string | null;
}

export function useApi() {
  const [state, setState] = useState<ApiState>({
    loading: false,
    error: null,
  });

  const makeRequest = useCallback(async <T>(
    url: string,
    options: RequestInit = {}
  ): Promise<T> => {
    setState({ loading: true, error: null });

    try {
      const token = localStorage.getItem('access_token');
      const headers = {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
      };

      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setState({ loading: false, error: null });
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setState({ loading: false, error: errorMessage });
      throw err;
    }
  }, []);

  const get = useCallback(<T>(url: string): Promise<T> => {
    return makeRequest<T>(url, { method: 'GET' });
  }, [makeRequest]);

  const post = useCallback(<T, D = unknown>(url: string, data?: D): Promise<T> => {
    return makeRequest<T>(url, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }, [makeRequest]);

  const put = useCallback(<T, D = unknown>(url: string, data?: D): Promise<T> => {
    return makeRequest<T>(url, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }, [makeRequest]);

  const del = useCallback(<T>(url: string): Promise<T> => {
    return makeRequest<T>(url, { method: 'DELETE' });
  }, [makeRequest]);

  return {
    ...state,
    get,
    post,
    put,
    delete: del,
    makeRequest,
  };
}
