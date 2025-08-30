import { useState, useCallback } from 'react';

interface PresignResponse {
  upload_id: string;
  upload_url: string;
  filename: string;
  content_type?: string;
}

interface UploadMediaResponse {
  status: string;
  uploaded_files: Array<{
    filename: string;
    path: string;
    size: number;
  }>;
  message?: string;
}

interface UploadMetadata {
  filename: string;
  content_type?: string;
  size?: number;
  upload_time?: string;
}

interface FinalizeResponse {
  status: string;
  meta: UploadMetadata;
  path: string;
}

export function useUploads() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const presignUpload = useCallback(async (
    ownerId: string,
    filename: string,
    contentType?: string
  ): Promise<PresignResponse> => {
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('owner_id', ownerId);
      formData.append('filename', filename);
      if (contentType) formData.append('content_type', contentType);

      const response = await fetch('/api/uploads/presign', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to presign upload');
      }

      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to presign upload');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const finalizeUpload = useCallback(async (
    uploadId: string,
    ownerId: string,
    title?: string,
    description?: string,
    filename?: string,
    contentType?: string,
    size?: number
  ): Promise<FinalizeResponse> => {
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('upload_id', uploadId);
      formData.append('owner_id', ownerId);
      if (title) formData.append('title', title);
      if (description) formData.append('description', description);
      if (filename) formData.append('filename', filename);
      if (contentType) formData.append('content_type', contentType);
      if (size !== undefined) formData.append('size', size.toString());

      const response = await fetch('/api/uploads/finalize', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to finalize upload');
      }

      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to finalize upload');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const uploadMedia = useCallback(async (
    ownerId: string,
    files: FileList
  ): Promise<UploadMediaResponse> => {
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('owner_id', ownerId);
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }

      const response = await fetch('/api/uploads/media', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload media');
      }

      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload media');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    presignUpload,
    finalizeUpload,
    uploadMedia,
  };
}
