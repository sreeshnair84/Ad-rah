'use client';

import React, { useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent } from '@/components/ui/card';
import { useAuth } from '@/hooks/useAuth';
import { useUpload, UploadFormData } from '@/hooks/useUpload';
import { FileDropZone, FileInput } from '@/components/upload/FileDropZone';
import { FileList } from '@/components/upload/FileList';
import { ContentForm } from '@/components/upload/ContentForm';
import {
  Upload,
  AlertCircle,
  User,
  Building,
  RefreshCw,
  Share2
} from 'lucide-react';

interface UnifiedUploadPageProps {
  mode?: 'simple' | 'advanced';
  title?: string;
  description?: string;
  showAI?: boolean;
  redirectPath?: string;
  onUploadComplete?: () => void;
}

export default function UnifiedUploadPage({
  mode = 'advanced',
  title = 'Upload Content',
  description = 'Upload images, videos, and documents for review and approval',
  showAI = true,
  redirectPath = '/dashboard/my-ads',
  onUploadComplete
}: UnifiedUploadPageProps) {
  const { user, hasPermission } = useAuth();
  const router = useRouter();
  
  const {
    files,
    isUploading,
    globalError,
    addFiles,
    removeFile,
    clearFiles,
    uploadAllFiles,
    uploadSingleLegacy,
    validateFile,
    formatFileSize,
    MAX_FILE_SIZE,
    MAX_FILES,
    ACCEPTED_TYPES,
    setGlobalError
  } = useUpload();

  const [formData, setFormData] = useState<UploadFormData>({
    title: '',
    description: '',
    category: '',
    tags: [],
    priority: 'medium'
  });
  
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle form data changes
  const handleFormDataChange = useCallback((data: Partial<UploadFormData>) => {
    setFormData(prev => ({ ...prev, ...data }));
  }, []);

  // Drag and drop handlers
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files) {
      addFiles(e.dataTransfer.files);
    }
  }, [addFiles]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      addFiles(e.target.files);
    }
  }, [addFiles]);

  // Upload handlers
  const handleAdvancedUpload = useCallback(async () => {
    try {
      await uploadAllFiles(formData, showAI);
      setUploadSuccess(true);
      
      if (onUploadComplete) {
        setTimeout(() => {
          onUploadComplete();
        }, 2000);
      } else {
        setTimeout(() => {
          router.push(redirectPath);
        }, 2000);
      }
    } catch (error) {
      // Error handling is done in the hook
    }
  }, [uploadAllFiles, formData, showAI, onUploadComplete, router, redirectPath]);

  const handleSimpleUpload = useCallback(async () => {
    if (files.length === 0) {
      setGlobalError('Please select a file to upload');
      return;
    }

    if (!formData.title.trim() || !formData.category) {
      setGlobalError('Please fill in all required fields');
      return;
    }

    try {
      await uploadSingleLegacy(files[0].file, formData);
      setUploadSuccess(true);
      
      if (onUploadComplete) {
        setTimeout(() => {
          onUploadComplete();
        }, 2000);
      } else {
        setTimeout(() => {
          router.push(redirectPath);
        }, 2000);
      }
    } catch (error) {
      setGlobalError(error instanceof Error ? error.message : 'Upload failed');
    }
  }, [files, formData, uploadSingleLegacy, onUploadComplete, router, redirectPath, setGlobalError]);

  const resetForm = useCallback(() => {
    setFormData({
      title: '',
      description: '',
      category: '',
      tags: [],
      priority: 'medium'
    });
    clearFiles();
    setUploadSuccess(false);
    setGlobalError(null);
  }, [clearFiles, setGlobalError]);

  // Permission check
  const canUpload = hasPermission('content', 'create');

  if (!canUpload) {
    return (
      <div className="flex items-center justify-center h-64">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            You don't have permission to upload content. Please contact your administrator.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const isSimpleMode = mode === 'simple';
  const multipleFiles = !isSimpleMode;
  const acceptString = Object.keys(ACCEPTED_TYPES).join(',');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <Upload className="h-8 w-8 text-blue-600" />
            {title}
          </h1>
          <p className="text-gray-600 mt-1">{description}</p>
        </div>
        {user && (
          <div className="flex items-center space-x-2">
            <User className="h-4 w-4 text-gray-500" />
            <span className="text-sm text-gray-600">{user.display_name || `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.email}</span>
            {user.company && (
              <>
                <Building className="h-4 w-4 text-gray-500 ml-4" />
                <span className="text-sm text-gray-600">{user.company.name}</span>
              </>
            )}
          </div>
        )}
      </div>

      {/* Success Alert */}
      {uploadSuccess && (
        <Alert className="border-green-200 bg-green-50">
          <AlertDescription className="text-green-800">
            Content uploaded successfully! Your content is now being processed and will be available shortly.
          </AlertDescription>
        </Alert>
      )}

      {/* Error Alert */}
      {globalError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{globalError}</AlertDescription>
        </Alert>
      )}

      <div className={`grid gap-6 ${isSimpleMode ? 'grid-cols-1 max-w-2xl mx-auto' : 'grid-cols-1 lg:grid-cols-3'}`}>
        {/* Upload Area */}
        <div className={`space-y-6 ${isSimpleMode ? '' : 'lg:col-span-2'}`}>
          {/* File Drop Zone */}
          <FileDropZone
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => fileInputRef.current?.click()}
            isDragOver={isDragOver}
            disabled={isUploading}
            maxFiles={MAX_FILES}
            maxFileSize={formatFileSize(MAX_FILE_SIZE)}
            acceptedTypes={ACCEPTED_TYPES}
            title={isSimpleMode ? "Select File" : "Select Files"}
            description={isSimpleMode 
              ? "Choose your content file to upload" 
              : "Drag and drop your files here or click to browse. Supports images, videos, audio, PDFs, and text files."
            }
          />

          <FileInput
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept={acceptString}
            multiple={multipleFiles}
            disabled={isUploading}
          />

          {/* File List */}
          <FileList
            files={files}
            onRemoveFile={removeFile}
            formatFileSize={formatFileSize}
            isUploading={isUploading}
          />
        </div>

        {/* Content Form */}
        <div className="space-y-6">
          <ContentForm
            formData={formData}
            onFormDataChange={handleFormDataChange}
            disabled={isUploading}
            showAdvanced={!isSimpleMode}
          />

          {/* Upload Actions */}
          <Card>
            <CardContent className="pt-6">
              <Button
                onClick={isSimpleMode ? handleSimpleUpload : handleAdvancedUpload}
                disabled={isUploading || files.length === 0 || !formData.title.trim() || !formData.category}
                className="w-full"
                size="lg"
              >
                {isUploading ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4 mr-2" />
                    Upload {files.length > 1 ? `${files.length} Files` : 'File'}
                  </>
                )}
              </Button>
              
              {!isSimpleMode && files.some(f => f.status === 'approved') && (
                <Button
                  variant="outline"
                  className="w-full mt-2"
                  onClick={() => {
                    window.location.href = '/dashboard/content-overlay';
                  }}
                >
                  <Share2 className="h-4 w-4 mr-2" />
                  Create Overlay & Deploy
                </Button>
              )}

              <Button
                variant="outline"
                onClick={resetForm}
                disabled={isUploading}
                className="w-full mt-2"
              >
                Reset Form
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
