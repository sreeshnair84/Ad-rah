'use client';

import React from 'react';
import { X, Clock, Upload, RefreshCw, Sparkles, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FileIcon } from './FileDropZone';
import { UploadedFile } from '@/hooks/useUpload';

interface FileListProps {
  files: UploadedFile[];
  onRemoveFile: (id: string) => void;
  formatFileSize: (bytes: number) => string;
  isUploading?: boolean;
}

export function FileList({ files, onRemoveFile, formatFileSize, isUploading = false }: FileListProps) {
  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'pending': return <Clock className="h-4 w-4 text-gray-500" />;
      case 'uploading': return <Upload className="h-4 w-4 text-blue-500" />;
      case 'processing': return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'ai_review': return <Sparkles className="h-4 w-4 text-purple-500" />;
      case 'human_review': return <AlertCircle className="h-4 w-4 text-orange-500" />;
      case 'approved': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'rejected': return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'error': return <AlertCircle className="h-4 w-4 text-red-500" />;
    }
  };

  const getStatusText = (status: UploadedFile['status']) => {
    switch (status) {
      case 'pending': return 'Ready to Upload';
      case 'uploading': return 'Uploading...';
      case 'processing': return 'Processing...';
      case 'ai_review': return 'AI Review';
      case 'human_review': return 'Human Review';
      case 'approved': return 'Approved';
      case 'rejected': return 'Rejected';
      case 'error': return 'Error';
    }
  };

  const getStatusColor = (status: UploadedFile['status']) => {
    switch (status) {
      case 'pending': return 'bg-gray-100 text-gray-800';
      case 'uploading': return 'bg-blue-100 text-blue-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'ai_review': return 'bg-purple-100 text-purple-800';
      case 'human_review': return 'bg-orange-100 text-orange-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'error': return 'bg-red-100 text-red-800';
    }
  };

  if (files.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload Queue ({files.length})</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {files.map((uploadedFile) => (
          <div key={uploadedFile.id} className="border rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <FileIcon file={uploadedFile.file} size="lg" />
                <div>
                  <p className="font-medium text-gray-900">{uploadedFile.file.name}</p>
                  <p className="text-sm text-gray-500">
                    {formatFileSize(uploadedFile.file.size)} • {uploadedFile.file.type}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Badge className={getStatusColor(uploadedFile.status)}>
                  {getStatusIcon(uploadedFile.status)}
                  <span className="ml-1">{getStatusText(uploadedFile.status)}</span>
                </Badge>
                {uploadedFile.status === 'pending' && !isUploading && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onRemoveFile(uploadedFile.id)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>

            {/* Progress Bar */}
            {(uploadedFile.status === 'uploading' || uploadedFile.status === 'processing') && (
              <Progress value={uploadedFile.progress} className="w-full" />
            )}

            {/* Error Message */}
            {uploadedFile.status === 'error' && uploadedFile.error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-800">{uploadedFile.error}</p>
              </div>
            )}

            {/* AI Analysis Results */}
            {uploadedFile.aiAnalysis && (
              <div className="bg-gray-50 rounded-lg p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium text-gray-900 flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-purple-500" />
                    AI Analysis Results
                  </h4>
                  <Badge variant="outline">
                    {Math.round(uploadedFile.aiAnalysis.confidence * 100)}% confidence
                  </Badge>
                </div>
                
                <p className="text-sm text-gray-700">{uploadedFile.aiAnalysis.reasoning}</p>
                
                {uploadedFile.aiAnalysis.categories.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-gray-600 mb-1">Detected Categories:</p>
                    <div className="flex gap-1 flex-wrap">
                      {uploadedFile.aiAnalysis.categories.map(category => (
                        <Badge key={category} variant="secondary" className="text-xs">
                          {category}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {uploadedFile.aiAnalysis.concerns.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-red-700 mb-1">Concerns:</p>
                    <ul className="text-xs text-red-600 list-disc list-inside">
                      {uploadedFile.aiAnalysis.concerns.map(concern => (
                        <li key={concern}>{concern.replace('_', ' ')}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {uploadedFile.aiAnalysis.suggestions.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-blue-700 mb-1">Suggestions:</p>
                    <ul className="text-xs text-blue-600 list-disc list-inside">
                      {uploadedFile.aiAnalysis.suggestions.map(suggestion => (
                        <li key={suggestion}>{suggestion}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Preview */}
            {uploadedFile.preview && (
              <img
                src={uploadedFile.preview}
                alt="Preview"
                className="w-full h-32 object-cover rounded-lg"
              />
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
