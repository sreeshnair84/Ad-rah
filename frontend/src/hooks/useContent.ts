import { useState, useCallback } from 'react';

interface ContentMetadata {
  id?: string;
  title: string;
  description?: string;
  owner_id: string;
  categories: string[];
  start_time?: string;
  end_time?: string;
  tags: string[];
}

interface UploadResponse {
  filename: string;
  status: string;
  message?: string;
}

interface ContentItem extends ContentMetadata {
  id: string;
  created_at?: string;
  updated_at?: string;
  status?: string;
}

export function useContent() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const uploadFile = useCallback(async (file: File, ownerId: string): Promise<UploadResponse> => {
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('owner_id', ownerId);

      const response = await fetch('/api/content/upload-file', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Upload failed with status ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const postMetadata = useCallback(async (metadata: ContentMetadata): Promise<ContentMetadata> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/content/metadata', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(metadata),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to save metadata with status ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save metadata';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const getMetadata = useCallback(async (contentId: string): Promise<ContentItem> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/content/${contentId}`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to get metadata with status ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get metadata';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const listMetadata = useCallback(async (): Promise<ContentItem[]> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/content/');

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to list metadata with status ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to list metadata';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateContentStatus = useCallback(async (contentId: string, status: string): Promise<ContentItem> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/content/${contentId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to update status with status ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update status';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    uploadFile,
    postMetadata,
    getMetadata,
    listMetadata,
    updateContentStatus,
  };
}
