'use client';

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

  const simulateAIAnalysis = useCallback(async (): Promise<UploadedFile['aiAnalysis']> => {
    // Simulate AI processing delay
    await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 3000));
    
    const confidence = 0.3 + Math.random() * 0.7; // 30-100%
    const quality_score = 0.5 + Math.random() * 0.5; // 50-100%
    
    let action: 'approved' | 'needs_review' | 'rejected';
    if (confidence > 0.9) action = 'approved';
    else if (confidence > 0.6) action = 'needs_review';
    else action = 'rejected';

    const categories = ['advertising', 'promotional', 'informational', 'entertainment'];
    const selectedCategories = categories.filter(() => Math.random() > 0.5);
    
    const allConcerns = ['inappropriate_content', 'poor_quality', 'copyright_concern', 'text_readability'];
    const concerns = action === 'approved' ? [] : allConcerns.filter(() => Math.random() > 0.8);

    const suggestions = concerns.length > 0 ? [
      'Improve image quality',
      'Verify copyright permissions',
      'Enhance text contrast',
      'Review content guidelines'
    ].filter(() => Math.random() > 0.5) : [];

    return {
      confidence,
      action,
      reasoning: action === 'approved' 
        ? 'Content meets all quality and safety standards'
        : action === 'rejected'
        ? 'Content violates platform guidelines and quality standards'
        : 'Content requires human review for final approval',
      categories: selectedCategories,
      concerns,
      suggestions,
      quality_score
    };
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
      const error = validateFile(file);
      if (error) {
        setGlobalError(`${file.name}: ${error}`);
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

  // Upload functionality
  const uploadSingleFile = useCallback(async (uploadedFile: UploadedFile, formData: UploadFormData, withAI: boolean = false) => {
    if (!user?.id) {
      throw new Error('User not authenticated');
    }

    try {
      const formDataUpload = new FormData();
      formDataUpload.append('file', uploadedFile.file);
      formDataUpload.append('owner_id', user.id);
      formDataUpload.append('title', formData.title || uploadedFile.file.name);
      formDataUpload.append('description', formData.description);
      formDataUpload.append('categories', JSON.stringify([formData.category]));
      formDataUpload.append('tags', JSON.stringify(formData.tags));
      formDataUpload.append('priority', formData.priority);
      
      if (formData.scheduledDate) {
        formDataUpload.append('scheduled_date', formData.scheduledDate);
      }

      // Upload progress simulation
      const xhr = new XMLHttpRequest();
      
      return new Promise<void>((resolve, reject) => {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const progress = Math.round((e.loaded / e.total) * 100);
            setFiles(prev => prev.map(f => 
              f.id === uploadedFile.id 
                ? { ...f, status: 'uploading', progress }
                : f
            ));
          }
        });

        xhr.addEventListener('load', async () => {
          if (xhr.status === 200) {
            // Move to AI processing if enabled
            if (withAI) {
              setFiles(prev => prev.map(f => 
                f.id === uploadedFile.id 
                  ? { ...f, status: 'ai_review', progress: 100 }
                  : f
              ));

              // Simulate AI analysis
              const aiAnalysis = await simulateAIAnalysis();
              
              setFiles(prev => prev.map(f => 
                f.id === uploadedFile.id 
                  ? { 
                      ...f, 
                      status: aiAnalysis?.action === 'approved' ? 'approved' : 'human_review',
                      aiAnalysis 
                    }
                  : f
              ));
            } else {
              setFiles(prev => prev.map(f => 
                f.id === uploadedFile.id 
                  ? { ...f, status: 'approved', progress: 100 }
                  : f
              ));
            }

            resolve();
          } else {
            reject(new Error(`Upload failed: ${xhr.status}`));
          }
        });

        xhr.addEventListener('error', () => {
          setFiles(prev => prev.map(f => 
            f.id === uploadedFile.id 
              ? { ...f, status: 'error', error: 'Upload failed' }
              : f
          ));
          reject(new Error('Upload failed'));
        });

        xhr.open('POST', '/api/content/upload-file');
        const token = localStorage.getItem('access_token');
        if (token) {
          xhr.setRequestHeader('Authorization', `Bearer ${token}`);
        }
        xhr.send(formDataUpload);
      });
    } catch (error) {
      setFiles(prev => prev.map(f => 
        f.id === uploadedFile.id 
          ? { ...f, status: 'error', error: error instanceof Error ? error.message : 'Upload failed' }
          : f
      ));
      throw error;
    }
  }, [user?.id, simulateAIAnalysis]);

  const uploadAllFiles = useCallback(async (formData: UploadFormData, withAI: boolean = false) => {
    if (files.length === 0) {
      throw new Error('No files to upload');
    }

    if (!formData.title.trim()) {
      throw new Error('Please provide a title for your content');
    }

    setIsUploading(true);
    setGlobalError(null);

    try {
      const pendingFiles = files.filter(f => f.status === 'pending');
      for (const file of pendingFiles) {
        await uploadSingleFile(file, formData, withAI);
      }
    } catch (error) {
      setGlobalError(error instanceof Error ? error.message : 'Upload failed');
      throw error;
    } finally {
      setIsUploading(false);
    }
  }, [files, uploadSingleFile]);

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
    
    // File management
    addFiles,
    removeFile,
    clearFiles,
    
    // Upload functions
    uploadAllFiles,
    uploadSingleLegacy,
    
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
