import { useState, useCallback } from 'react';
import { useAuth } from './useAuth';
import { useContent } from './useContent';

export interface UploadedFile {
  file: File;
  id: string;
  preview?: string;
  status: 'pending' | 'uploading' | 'processing' | 'ai_review' | 'human_review' | 'approved' | 'rejected' | 'error';
  progress: number;
  error?: string;
  aiAnalysis?: {
    confidence: number;
    action: 'approved' | 'needs_review' | 'rejected';
    reasoning: string;
    categories: string[];
    concerns: string[];
    suggestions: string[];
    quality_score: number;
  };
}

export interface UploadFormData {
  title: string;
  description: string;
  category: string;
  tags: string[];
  startTime?: string;
  endTime?: string;
  priority: 'low' | 'medium' | 'high';
  scheduledDate?: string;
}

// Consolidated interfaces from useUploads.ts
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

interface FinalizeResponse {
  status: string;
  meta: {
    filename: string;
    content_type?: string;
    size?: number;
    upload_time?: string;
  };
  path: string;
}

const ACCEPTED_TYPES = {
  'image/*': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'],
  'video/*': ['.mp4', '.webm', '.mov', '.avi'],
  'audio/*': ['.mp3', '.wav', '.ogg'],
  'application/pdf': ['.pdf'],
  'text/*': ['.txt', '.md'],
  'text/html': ['.html']
};

const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB
const MAX_FILES = 10;

export function useUpload() {
  const { user } = useAuth();
  const { uploadFile: apiUploadFile, postMetadata } = useContent();

  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Utility functions
  const formatFileSize = useCallback((bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }, []);

  const validateFile = useCallback((file: File): string | null => {
    if (file.size > MAX_FILE_SIZE) {
      return `File size exceeds ${formatFileSize(MAX_FILE_SIZE)} limit`;
    }

    const isValidType = Object.keys(ACCEPTED_TYPES).some(type => {
      if (type.endsWith('/*')) {
        return file.type.startsWith(type.slice(0, -1));
      }
      return file.type === type;
    });

    if (!isValidType) {
      return 'File type not supported';
    }

    return null;
  }, [formatFileSize]);

  const createFilePreview = useCallback((file: File): Promise<string | undefined> => {
    return new Promise((resolve) => {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target?.result as string);
        reader.readAsDataURL(file);
      } else {
        resolve(undefined);
      }
    });
  }, []);

  // Presign upload functionality (consolidated from useUploads.ts)
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
    fileList: FileList
  ): Promise<UploadMediaResponse> => {
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('owner_id', ownerId);
      for (let i = 0; i < fileList.length; i++) {
        formData.append('files', fileList[i]);
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

  // File management
  const addFiles = useCallback(async (newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles);
    
    if (files.length + fileArray.length > MAX_FILES) {
      setGlobalError(`Cannot upload more than ${MAX_FILES} files at once`);
      return;
    }

    const validFiles: UploadedFile[] = [];
    
    for (const file of fileArray) {
      const validationError = validateFile(file);
      if (validationError) {
        setGlobalError(`${file.name}: ${validationError}`);
        continue;
      }

      const preview = await createFilePreview(file);
      validFiles.push({
        file,
        id: Math.random().toString(36).substr(2, 9),
        preview,
        status: 'pending',
        progress: 0
      });
    }

    setFiles(prev => [...prev, ...validFiles]);
    setGlobalError(null);
  }, [files.length, validateFile, createFilePreview]);

  const removeFile = useCallback((id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  }, []);

  const clearFiles = useCallback(() => {
    setFiles([]);
    setGlobalError(null);
  }, []);

  // Legacy single file upload for compatibility
  const uploadSingleLegacy = useCallback(async (file: File, formData: UploadFormData) => {
    if (!user?.id) {
      throw new Error('User not authenticated');
    }

    const uploadResponse = await apiUploadFile(file, user.id);
    
    if (uploadResponse.status === 'rejected') {
      throw new Error(uploadResponse.message || 'Upload rejected');
    }

    // Create metadata
    const metadata = {
      id: uploadResponse.filename,
      title: formData.title,
      description: formData.description || undefined,
      owner_id: user.id,
      categories: [formData.category],
      start_time: formData.startTime ? new Date(formData.startTime).toISOString() : undefined,
      end_time: formData.endTime ? new Date(formData.endTime).toISOString() : undefined,
      tags: formData.tags
    };

    await postMetadata(metadata);
    return uploadResponse;
  }, [user?.id, apiUploadFile, postMetadata]);

  return {
    // State
    files,
    isUploading,
    globalError,
    loading,
    error,
    
    // File management
    addFiles,
    removeFile,
    clearFiles,
    
    // Upload functions
    uploadSingleLegacy,
    presignUpload,
    finalizeUpload,
    uploadMedia,
    
    // Utility functions
    validateFile,
    formatFileSize,
    createFilePreview,
    
    // Constants
    MAX_FILE_SIZE,
    MAX_FILES,
    ACCEPTED_TYPES,
    
    // Setters
    setGlobalError
  };
}
