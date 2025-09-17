'use client';

import React, { useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
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
  Share2,
  Check,
  X,
  FileText,
  Image,
  Video,
  Monitor
} from 'lucide-react';

interface UnifiedUploadManagerProps {
  mode?: 'simple' | 'advanced';
  title?: string;
  description?: string;
  showAI?: boolean;
  redirectPath?: string;
  onUploadComplete?: () => void;
  maxFiles?: number;
  maxFileSize?: number;
  acceptedTypes?: string[];
}

export default function UnifiedUploadManager({
  mode = 'advanced',
  title = 'Upload Content',
  description = 'Upload images, videos, and documents for review and approval',
  showAI = true,
  redirectPath = '/dashboard/content',
  onUploadComplete,
  maxFiles = 10,
  maxFileSize = 100 * 1024 * 1024, // 100MB
  acceptedTypes = ['image/*', 'video/*', 'audio/*', 'application/pdf', 'text/*']
}: UnifiedUploadManagerProps) {
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
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'processing' | 'success' | 'error'>('idle');

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
    if (files.length === 0) {
      setGlobalError('Please select files to upload');
      return;
    }

    if (!formData.title.trim()) {
      setGlobalError('Please enter a title for your content');
      return;
    }

    if (!formData.category) {
      setGlobalError('Please select a category');
      return;
    }

    try {
      setUploadStatus('uploading');
      setUploadProgress(0);

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      await uploadAllFiles(formData, showAI);

      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadStatus('success');
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
      setUploadStatus('error');
      setGlobalError(error instanceof Error ? error.message : 'Upload failed');
    }
  }, [uploadAllFiles, formData, showAI, onUploadComplete, router, redirectPath, files.length, setGlobalError]);

  const handleSimpleUpload = useCallback(async () => {
    if (files.length === 0) {
      setGlobalError('Please select a file to upload');
      return;
    }

    if (!formData.title.trim()) {
      setGlobalError('Please enter a title');
      return;
    }

    if (!formData.category) {
      setGlobalError('Please select a category');
      return;
    }

    try {
      setUploadStatus('uploading');
      setUploadProgress(0);

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 20, 90));
      }, 300);

      await uploadSingleLegacy(files[0].file, formData);

      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadStatus('success');
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
      setUploadStatus('error');
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
    setUploadProgress(0);
    setUploadStatus('idle');
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
  const acceptString = acceptedTypes.join(',');

  // Convert acceptedTypes array to the expected format for FileDropZone
  const acceptedTypesRecord = acceptedTypes.reduce((acc, type) => {
    const category = type.split('/')[0];
    if (!acc[category]) acc[category] = [];
    acc[category].push(type);
    return acc;
  }, {} as Record<string, string[]>);

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
          <Check className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            Content uploaded successfully! Your content is now being processed and will be available shortly.
          </AlertDescription>
        </Alert>
      )}

      {/* Error Alert */}
      {globalError && (
        <Alert variant="destructive">
          <X className="h-4 w-4" />
          <AlertDescription>{globalError}</AlertDescription>
        </Alert>
      )}

      {/* Upload Progress */}
      {uploadStatus !== 'idle' && uploadStatus !== 'success' && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">
                  {uploadStatus === 'uploading' && 'Uploading files...'}
                  {uploadStatus === 'processing' && 'Processing content...'}
                  {uploadStatus === 'error' && 'Upload failed'}
                </span>
                <span className="text-sm text-muted-foreground">{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} className="w-full" />
            </div>
          </CardContent>
        </Card>
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
            disabled={isUploading || uploadStatus !== 'idle'}
            maxFiles={maxFiles}
            maxFileSize={formatFileSize(maxFileSize)}
            acceptedTypes={acceptedTypesRecord}
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
            disabled={isUploading || uploadStatus !== 'idle'}
          />

          {/* File List */}
          <FileList
            files={files}
            onRemoveFile={removeFile}
            formatFileSize={formatFileSize}
            isUploading={isUploading || uploadStatus !== 'idle'}
          />

          {/* File Preview for Simple Mode */}
          {isSimpleMode && files.length > 0 && (
            <Card>
              <CardContent className="pt-6">
                <div className="space-y-4">
                  <Label className="text-sm font-medium">Selected File</Label>
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    {files[0].file.type.startsWith('image/') && (
                      <Image className="h-8 w-8 text-blue-500" />
                    )}
                    {files[0].file.type.startsWith('video/') && (
                      <Video className="h-8 w-8 text-purple-500" />
                    )}
                    {files[0].file.type === 'application/pdf' && (
                      <FileText className="h-8 w-8 text-red-500" />
                    )}
                    {files[0].file.type.includes('html') && (
                      <Monitor className="h-8 w-8 text-green-500" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{files[0].file.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(files[0].file.size)} • {files[0].file.type}
                      </p>
                    </div>
                    <Badge variant="outline">Ready</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Content Form */}
        <div className="space-y-6">
          <ContentForm
            formData={formData}
            onFormDataChange={handleFormDataChange}
            disabled={isUploading || uploadStatus !== 'idle'}
            showAdvanced={!isSimpleMode}
          />

          {/* Upload Actions */}
          <Card>
            <CardContent className="pt-6">
              <Button
                onClick={isSimpleMode ? handleSimpleUpload : handleAdvancedUpload}
                disabled={
                  isUploading ||
                  uploadStatus !== 'idle' ||
                  files.length === 0 ||
                  !formData.title.trim() ||
                  !formData.category
                }
                className="w-full"
                size="lg"
              >
                {isUploading || uploadStatus !== 'idle' ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    {uploadStatus === 'uploading' && 'Uploading...'}
                    {uploadStatus === 'processing' && 'Processing...'}
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
                disabled={isUploading || uploadStatus !== 'idle'}
                className="w-full mt-2"
              >
                Reset Form
              </Button>
            </CardContent>
          </Card>

          {/* Upload Guidelines */}
          <Card>
            <CardContent className="pt-6">
              <div className="space-y-3">
                <Label className="text-sm font-medium">Upload Guidelines</Label>
                <ul className="text-xs text-muted-foreground space-y-1">
                  <li>• Maximum file size: {formatFileSize(maxFileSize)}</li>
                  <li>• Maximum files: {maxFiles}</li>
                  <li>• Supported formats: Images, Videos, PDFs, Text files</li>
                  <li>• Content will be reviewed before approval</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
