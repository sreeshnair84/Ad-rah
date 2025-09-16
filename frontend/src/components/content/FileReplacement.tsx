'use client';

import React, { useState, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import {
  Upload,
  AlertTriangle,
  CheckCircle,
  X,
  FileText,
  Image,
  Video,
  Music,
  RefreshCw
} from 'lucide-react';

interface FileReplacementProps {
  contentId: string;
  currentFile?: {
    filename: string;
    content_type: string;
    size: number;
  };
  onSuccess?: () => void;
  onCancel?: () => void;
  className?: string;
}

export function FileReplacement({
  contentId,
  currentFile,
  onSuccess,
  onCancel,
  className = ''
}: FileReplacementProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const maxFileSize = 100 * 1024 * 1024; // 100MB
  const allowedTypes = [
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'video/mp4', 'video/webm', 'video/quicktime',
    'audio/mp3', 'audio/wav', 'audio/ogg',
    'text/plain', 'application/pdf'
  ];

  const getFileIcon = (type: string) => {
    if (type.startsWith('image/')) return <Image className="h-5 w-5 text-blue-500" />;
    if (type.startsWith('video/')) return <Video className="h-5 w-5 text-purple-500" />;
    if (type.startsWith('audio/')) return <Music className="h-5 w-5 text-green-500" />;
    return <FileText className="h-5 w-5 text-orange-500" />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  };

  const validateFile = (file: File): string | null => {
    if (file.size > maxFileSize) {
      return `File size (${formatFileSize(file.size)}) exceeds the maximum limit of ${formatFileSize(maxFileSize)}`;
    }

    if (!allowedTypes.includes(file.type)) {
      return `File type (${file.type}) is not supported. Allowed types: images, videos, audio, text, and PDF files.`;
    }

    return null;
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    setError(null);
    setSuccess(false);
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (!file) return;

    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    setError(null);
    setSuccess(false);
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
  };

  const resetSelection = () => {
    setSelectedFile(null);
    setError(null);
    setSuccess(false);
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`/api/content/${contentId}/replace-file`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      // Simulate progress for better UX
      const interval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(interval);
            return 90;
          }
          return prev + 10;
        });
      }, 100);

      const result = await response.json();
      clearInterval(interval);
      setUploadProgress(100);

      if (!response.ok) {
        throw new Error(result.detail || result.error || 'Upload failed');
      }

      setSuccess(true);
      setTimeout(() => {
        onSuccess?.();
      }, 1000);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      setError(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  if (success) {
    return (
      <Card className={`border-green-200 bg-green-50 ${className}`}>
        <CardContent className="pt-6">
          <div className="text-center">
            <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-3" />
            <h3 className="text-lg font-medium text-green-800 mb-2">File Replaced Successfully!</h3>
            <p className="text-green-700 mb-4">
              The file has been replaced and the content has been moved to quarantine for review.
            </p>
            <Button onClick={onSuccess} className="bg-green-600 hover:bg-green-700">
              Continue
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <RefreshCw className="h-5 w-5" />
          Replace File
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Current File Info */}
        {currentFile && (
          <div className="bg-gray-50 rounded-lg p-3">
            <h4 className="font-medium mb-2">Current File</h4>
            <div className="flex items-center gap-3">
              {getFileIcon(currentFile.content_type)}
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{currentFile.filename}</p>
                <p className="text-sm text-gray-500">
                  {formatFileSize(currentFile.size)} • {currentFile.content_type}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Upload Area */}
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            selectedFile 
              ? 'border-green-300 bg-green-50' 
              : 'border-gray-300 bg-gray-50 hover:border-gray-400'
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
        >
          {selectedFile ? (
            <div className="space-y-3">
              <div className="flex items-center justify-center gap-3">
                {getFileIcon(selectedFile.type)}
                <div className="text-left">
                  <p className="font-medium">{selectedFile.name}</p>
                  <p className="text-sm text-gray-500">
                    {formatFileSize(selectedFile.size)} • {selectedFile.type}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={resetSelection}
                  disabled={uploading}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              
              {uploading && (
                <div className="space-y-2">
                  <Progress value={uploadProgress} className="w-full" />
                  <p className="text-sm text-gray-600">
                    Uploading... {uploadProgress}%
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              <Upload className="h-12 w-12 text-gray-400 mx-auto" />
              <div>
                <p className="text-lg font-medium text-gray-700">Drop a new file here</p>
                <p className="text-gray-500">or click to browse</p>
              </div>
              <p className="text-sm text-gray-400">
                Max size: {formatFileSize(maxFileSize)}
              </p>
            </div>
          )}
          
          <input
            ref={fileInputRef}
            type="file"
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            onChange={handleFileSelect}
            accept={allowedTypes.join(',')}
            disabled={uploading}
          />
        </div>

        {/* Error Message */}
        {error && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Upload Warning */}
        {selectedFile && !uploading && !error && (
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <strong>Warning:</strong> Replacing this file will move the content back to quarantine 
              for review and approval. The previous file will be permanently replaced.
            </AlertDescription>
          </Alert>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2 pt-4">
          <Button
            variant="outline"
            onClick={onCancel}
            disabled={uploading}
            className="flex-1"
          >
            Cancel
          </Button>
          <Button
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
            className="flex-1"
          >
            {uploading ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="h-4 w-4 mr-2" />
                Replace File
              </>
            )}
          </Button>
        </div>

        {/* Supported File Types */}
        <div className="text-xs text-gray-500 mt-4">
          <p className="font-medium mb-1">Supported file types:</p>
          <p>Images: JPEG, PNG, GIF, WebP</p>
          <p>Videos: MP4, WebM, QuickTime</p>
          <p>Audio: MP3, WAV, OGG</p>
          <p>Documents: TXT, PDF</p>
        </div>
      </CardContent>
    </Card>
  );
}