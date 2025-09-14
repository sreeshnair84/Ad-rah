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
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Authentication required for upload');
      }

      const formData = new FormData();
      formData.append('owner_id', ownerId);
      formData.append('file', file);  // Backend expects 'file' not 'files'

      const response = await fetch(`/api/content/upload-file`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Upload failed with status ${response.status}`);
      }

      const result = await response.json();
      // Transform the response to match expected format
      return {
        filename: result.uploaded?.[0]?.meta?.filename || file.name,
        status: 'success',
        message: 'File uploaded successfully'
      };
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
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Authentication required');
      }

      // Transform metadata to match backend expectations
      const backendMetadata = {
        id: metadata.id,
        title: metadata.title,
        description: metadata.description,
        owner_id: metadata.owner_id,
        categories: metadata.categories,
        start_time: metadata.start_time,
        end_time: metadata.end_time,
        tags: metadata.tags,
        // Add additional fields that might be expected
        filename: metadata.id, // Use ID as filename for now
        content_type: 'application/octet-stream', // Default content type
        size: 0, // Will be updated when file is uploaded
        status: 'pending'
      };

      const response = await fetch('/api/content/metadata', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(backendMetadata),
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
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch(`/api/content/${contentId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

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
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch('/api/content/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

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
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch(`/api/content/${contentId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Authorization': `Bearer ${token}`,
        },
        body: new URLSearchParams({ status }),
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

  const getContentList = useCallback(async (): Promise<ContentItem[]> => {
    return listMetadata();
  }, [listMetadata]);

  const approveContent = useCallback(async (contentId: string, approvalData: {
    approved_by: string;
    message?: string;
    category?: string;
    start_time?: string;
    end_time?: string;
  }): Promise<ContentItem> => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch(`/api/content/admin/approve/${contentId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(approvalData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to approve content with status ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to approve content';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const rejectContent = useCallback(async (contentId: string, rejectionData: {
    rejected_by: string;
    reason: string;
  }): Promise<ContentItem> => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch(`/api/content/admin/reject/${contentId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(rejectionData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to reject content with status ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to reject content';
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
    getContentList,
    approveContent,
    rejectContent,
  };
}
