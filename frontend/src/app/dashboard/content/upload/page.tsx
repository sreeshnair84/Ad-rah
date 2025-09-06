'use client';

import React, { useState, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useAuth } from '@/hooks/useAuth';
import {
  Upload,
  FileImage,
  FileVideo,
  FileText,
  FileAudio,
  File,
  X,
  CheckCircle,
  AlertCircle,
  Clock,
  Sparkles,
  Eye,
  Share2,
  Calendar,
  Tag,
  User,
  Building,
  RefreshCw
} from 'lucide-react';

interface UploadedFile {
  file: File;
  id: string;
  preview?: string;
  status: 'pending' | 'uploading' | 'processing' | 'ai_review' | 'human_review' | 'approved' | 'rejected';
  progress: number;
  aiAnalysis?: {
    confidence: number;
    action: 'approved' | 'needs_review' | 'rejected';
    reasoning: string;
    categories: string[];
    concerns: string[];
    suggestions: string[];
    quality_score: number;
  };
  error?: string;
}

const ACCEPTED_TYPES = {
  'image/*': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'],
  'video/*': ['.mp4', '.webm', '.mov', '.avi'],
  'audio/*': ['.mp3', '.wav', '.ogg'],
  'application/pdf': ['.pdf'],
  'text/*': ['.txt', '.md']
};

const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB
const MAX_FILES = 10;

export default function ContentUploadPage() {
  const { user, hasPermission } = useAuth();
  
  // All useState hooks first
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [categories, setCategories] = useState<string[]>([]);
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');
  const [scheduledDate, setScheduledDate] = useState('');
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium');

  // useRef hooks
  const fileInputRef = useRef<HTMLInputElement>(null);

  // All useCallback hooks - utility functions
  const getFileIcon = useCallback((file: File) => {
    if (file.type.startsWith('image/')) return <FileImage className="h-8 w-8 text-blue-500" />;
    if (file.type.startsWith('video/')) return <FileVideo className="h-8 w-8 text-purple-500" />;
    if (file.type.startsWith('audio/')) return <FileAudio className="h-8 w-8 text-green-500" />;
    if (file.type === 'application/pdf') return <FileText className="h-8 w-8 text-red-500" />;
    return <File className="h-8 w-8 text-gray-500" />;
  }, []);

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

  const simulateAIAnalysis = useCallback(async (uploadedFile: UploadedFile): Promise<UploadedFile['aiAnalysis']> => {
    // Simulate AI processing delay
    await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 3000));
    
    const confidence = 0.3 + Math.random() * 0.7; // 30-100%
    const quality_score = 0.5 + Math.random() * 0.5; // 50-100%
    
    let action: 'approved' | 'needs_review' | 'rejected';
    if (confidence > 0.9) action = 'approved';
    else if (confidence > 0.6) action = 'needs_review';
    else action = 'rejected';

    const categories = ['advertising', 'promotional', 'informational', 'entertainment'];
    const selectedCategories = categories.filter(() => Math.random() > 0.7);

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

  const uploadFile = useCallback(async (uploadedFile: UploadedFile) => {
    try {
      const formData = new FormData();
      formData.append('file', uploadedFile.file);
      formData.append('owner_id', user?.id || '');
      formData.append('title', title || uploadedFile.file.name);
      formData.append('description', description);
      formData.append('categories', JSON.stringify(categories));
      formData.append('tags', JSON.stringify(tags));
      formData.append('priority', priority);
      if (scheduledDate) {
        formData.append('scheduled_date', scheduledDate);
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
            // Move to AI processing
            setFiles(prev => prev.map(f => 
              f.id === uploadedFile.id 
                ? { ...f, status: 'ai_review', progress: 100 }
                : f
            ));

            // Simulate AI analysis
            const aiAnalysis = await simulateAIAnalysis(uploadedFile);
            
            setFiles(prev => prev.map(f => 
              f.id === uploadedFile.id 
                ? { 
                    ...f, 
                    status: aiAnalysis?.action === 'approved' ? 'approved' : 'human_review',
                    aiAnalysis 
                  }
                : f
            ));

            resolve();
          } else {
            reject(new Error(`Upload failed: ${xhr.status}`));
          }
        });

        xhr.addEventListener('error', () => {
          reject(new Error('Upload failed'));
        });

        xhr.open('POST', '/api/content/upload-file');
        const token = localStorage.getItem('token');
        if (token) {
          xhr.setRequestHeader('Authorization', `Bearer ${token}`);
        }
        xhr.send(formData);
      });
    } catch (error) {
      throw error;
    }
  }, [user?.id, title, description, categories, tags, priority, scheduledDate, simulateAIAnalysis, setFiles]);

  const handleUpload = useCallback(async () => {
    if (files.length === 0) {
      setGlobalError('Please select files to upload');
      return;
    }

    if (!title.trim()) {
      setGlobalError('Please provide a title for your content');
      return;
    }

    setIsUploading(true);
    setGlobalError(null);

    try {
      for (const file of files.filter(f => f.status === 'pending')) {
        await uploadFile(file);
      }
    } catch (error) {
      setGlobalError(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  }, [files, title, uploadFile, setFiles, setIsUploading, setGlobalError]);

  const addTag = useCallback(() => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      setTags([...tags, newTag.trim()]);
      setNewTag('');
    }
  }, [newTag, tags, setTags, setNewTag]);

  const removeTag = useCallback((tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove));
  }, [tags, setTags]);

  const getStatusIcon = useCallback((status: UploadedFile['status']) => {
    switch (status) {
      case 'pending': return <Clock className="h-4 w-4 text-gray-500" />;
      case 'uploading': return <Upload className="h-4 w-4 text-blue-500" />;
      case 'processing': return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'ai_review': return <Sparkles className="h-4 w-4 text-purple-500" />;
      case 'human_review': return <Eye className="h-4 w-4 text-yellow-500" />;
      case 'approved': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'rejected': return <AlertCircle className="h-4 w-4 text-red-500" />;
    }
  }, []);

  const getStatusColor = useCallback((status: UploadedFile['status']) => {
    switch (status) {
      case 'pending': return 'bg-gray-100 text-gray-800';
      case 'uploading': return 'bg-blue-100 text-blue-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'ai_review': return 'bg-purple-100 text-purple-800';
      case 'human_review': return 'bg-yellow-100 text-yellow-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
    }
  }, []);

  const getStatusText = useCallback((status: UploadedFile['status']) => {
    switch (status) {
      case 'pending': return 'Ready to Upload';
      case 'uploading': return 'Uploading...';
      case 'processing': return 'Processing...';
      case 'ai_review': return 'AI Review';
      case 'human_review': return 'Human Review';
      case 'approved': return 'Approved';
      case 'rejected': return 'Rejected';
    }
  }, []);

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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <Upload className="h-8 w-8 text-blue-600" />
            Upload Content
          </h1>
          <p className="text-gray-600 mt-1">
            Upload images, videos, and documents for AI review and approval
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <User className="h-4 w-4 text-gray-500" />
          <span className="text-sm text-gray-600">{user?.first_name} {user?.last_name}</span>
          {user?.company && (
            <>
              <Building className="h-4 w-4 text-gray-500 ml-4" />
              <span className="text-sm text-gray-600">{user.company.name}</span>
            </>
          )}
        </div>
      </div>

      {/* Error Alert */}
      {globalError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{globalError}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Area */}
        <div className="lg:col-span-2 space-y-6">
          {/* File Drop Zone */}
          <Card>
            <CardHeader>
              <CardTitle>Select Files</CardTitle>
              <CardDescription>
                Drag and drop your files here or click to browse. Supports images, videos, audio, PDFs, and text files.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  isDragOver
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onDrop={handleDrop}
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragOver(true);
                }}
                onDragLeave={() => setIsDragOver(false)}
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Drop files here or click to upload
                </h3>
                <p className="text-sm text-gray-500 mb-4">
                  Maximum {MAX_FILES} files, {formatFileSize(MAX_FILE_SIZE)} each
                </p>
                <Button variant="outline">
                  Select Files
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept={Object.keys(ACCEPTED_TYPES).join(',')}
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>
            </CardContent>
          </Card>

          {/* File List */}
          {files.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Upload Queue ({files.length})</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {files.map((uploadedFile) => (
                  <div key={uploadedFile.id} className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        {getFileIcon(uploadedFile.file)}
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
                        {uploadedFile.status === 'pending' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeFile(uploadedFile.id)}
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
                        <p className="text-sm text-gray-600">{uploadedFile.aiAnalysis.reasoning}</p>
                        
                        {uploadedFile.aiAnalysis.categories.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-gray-700 mb-1">Categories:</p>
                            <div className="flex flex-wrap gap-1">
                              {uploadedFile.aiAnalysis.categories.map(cat => (
                                <Badge key={cat} variant="secondary" className="text-xs">
                                  {cat}
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
          )}
        </div>

        {/* Metadata Form */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Content Details</CardTitle>
              <CardDescription>
                Provide details about your content for better organization and discovery
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="title">Title *</Label>
                <Input
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Enter content title..."
                  className="mt-1"
                />
              </div>

              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe your content..."
                  rows={3}
                  className="mt-1"
                />
              </div>

              <div>
                <Label htmlFor="categories">Categories</Label>
                <select
                  id="categories"
                  multiple
                  value={categories}
                  onChange={(e) => setCategories(Array.from(e.target.selectedOptions, opt => opt.value))}
                  className="mt-1 w-full border border-gray-300 rounded-md p-2 h-24"
                >
                  <option value="advertising">Advertising</option>
                  <option value="promotional">Promotional</option>
                  <option value="informational">Informational</option>
                  <option value="entertainment">Entertainment</option>
                  <option value="educational">Educational</option>
                  <option value="news">News</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">Hold Ctrl/Cmd to select multiple</p>
              </div>

              <div>
                <Label htmlFor="tags">Tags</Label>
                <div className="mt-1 flex flex-wrap gap-2 mb-2">
                  {tags.map(tag => (
                    <Badge key={tag} variant="secondary" className="text-xs">
                      <Tag className="h-3 w-3 mr-1" />
                      {tag}
                      <button
                        onClick={() => removeTag(tag)}
                        className="ml-1 hover:text-red-600"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
                <div className="flex space-x-2">
                  <Input
                    id="tags"
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    placeholder="Add tag..."
                    onKeyPress={(e) => e.key === 'Enter' && addTag()}
                  />
                  <Button onClick={addTag} variant="outline" size="sm">
                    Add
                  </Button>
                </div>
              </div>

              <div>
                <Label htmlFor="priority">Priority</Label>
                <select
                  id="priority"
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as 'low' | 'medium' | 'high')}
                  className="mt-1 w-full border border-gray-300 rounded-md p-2"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>

              <div>
                <Label htmlFor="scheduled">Scheduled Date (Optional)</Label>
                <Input
                  id="scheduled"
                  type="datetime-local"
                  value={scheduledDate}
                  onChange={(e) => setScheduledDate(e.target.value)}
                  className="mt-1"
                />
              </div>
            </CardContent>
          </Card>

          {/* Upload Actions */}
          <Card>
            <CardContent className="pt-6">
              <Button
                onClick={handleUpload}
                disabled={isUploading || files.length === 0 || !title.trim()}
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
                    Upload {files.length} File{files.length !== 1 ? 's' : ''}
                  </>
                )}
              </Button>
              
              {files.some(f => f.status === 'approved') && (
                <Button
                  variant="outline"
                  className="w-full mt-2"
                  onClick={() => {
                    // Navigate to overlay creation
                    window.location.href = '/dashboard/content-overlay';
                  }}
                >
                  <Share2 className="h-4 w-4 mr-2" />
                  Create Overlay & Deploy
                </Button>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
