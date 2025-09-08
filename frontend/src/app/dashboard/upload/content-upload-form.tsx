'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Upload, X, Check } from 'lucide-react';
import { useContent } from '@/hooks/useContent';
import { useAuth } from '@/hooks/useAuth';

interface ContentUploadFormProps {
  onUploadComplete?: () => void;
}

export default function ContentUploadForm({ onUploadComplete }: ContentUploadFormProps) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: '',
    tags: '',
    startTime: '',
    endTime: '',
  });
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'processing' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  // const router = useRouter(); // TODO: Add navigation after successful upload
  const { uploadFile, postMetadata } = useContent();
  const { user } = useAuth();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];

      // Validate file type
      const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'video/mp4', 'video/webm', 'text/html'];
      if (!allowedTypes.includes(selectedFile.type)) {
        setErrorMessage('Unsupported file type. Please upload images, videos, or HTML files.');
        return;
      }

      // Validate file size (max 100MB)
      const maxSize = 100 * 1024 * 1024; // 100MB
      if (selectedFile.size > maxSize) {
        setErrorMessage('File size too large. Maximum size is 100MB.');
        return;
      }

      setFile(selectedFile);
      setErrorMessage('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !formData.title || !formData.category) {
      setErrorMessage('Please fill in all required fields.');
      return;
    }

    if (!user?.id) {
      setErrorMessage('User not authenticated.');
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setUploadStatus('uploading');
    setErrorMessage('');

    try {
      // Step 1: Upload the file
      setUploadProgress(25);
      const uploadResponse = await uploadFile(file, user.id);

      if (uploadResponse.status === 'rejected') {
        throw new Error(uploadResponse.message || 'Upload rejected');
      }

      setUploadProgress(50);
      setUploadStatus('processing');

      // Step 2: Create metadata
      const metadata = {
        id: uploadResponse.filename,
        title: formData.title,
        description: formData.description || undefined,
        owner_id: user.id,
        categories: [formData.category],
        start_time: formData.startTime ? new Date(formData.startTime).toISOString() : undefined,
        end_time: formData.endTime ? new Date(formData.endTime).toISOString() : undefined,
        tags: formData.tags ? formData.tags.split(',').map(tag => tag.trim()) : []
      };

      setUploadProgress(75);
      await postMetadata(metadata);

      setUploadProgress(100);
      setUploadStatus('success');

      // Call completion callback
      setTimeout(() => {
        onUploadComplete?.();
      }, 2000);

    } catch (error) {
      console.error('Upload error:', error);
      setUploadStatus('error');
      setErrorMessage(error instanceof Error ? error.message : 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      category: '',
      tags: '',
      startTime: '',
      endTime: '',
    });
    setFile(null);
    setUploadProgress(0);
    setUploadStatus('idle');
    setErrorMessage('');
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="h-5 w-5" />
          Upload Advertisement Content
        </CardTitle>
        <CardDescription>
          Upload your content for review and approval by the host
        </CardDescription>
      </CardHeader>
      <CardContent>
        {uploadStatus === 'success' && (
          <Alert className="mb-6 border-green-200 bg-green-50">
            <Check className="h-4 w-4" />
            <AlertDescription className="text-green-800">
              Content uploaded successfully! Your content is now in the moderation queue.
            </AlertDescription>
          </Alert>
        )}

        {errorMessage && (
          <Alert className="mb-6 border-red-200 bg-red-50">
            <X className="h-4 w-4" />
            <AlertDescription className="text-red-800">
              {errorMessage}
            </AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="title">Content Title *</Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="Enter a descriptive title"
                required
                disabled={uploading}
              />
            </div>

            <div>
              <Label htmlFor="category">Category *</Label>
              <Select 
                value={formData.category} 
                onValueChange={(value) => setFormData({ ...formData, category: value })} 
                required 
                disabled={uploading}
                name="category"
              >
                <SelectTrigger id="category">
                  <SelectValue placeholder="Select a category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="food">Food & Dining</SelectItem>
                  <SelectItem value="retail">Retail</SelectItem>
                  <SelectItem value="entertainment">Entertainment</SelectItem>
                  <SelectItem value="services">Services</SelectItem>
                  <SelectItem value="healthcare">Healthcare</SelectItem>
                  <SelectItem value="education">Education</SelectItem>
                  <SelectItem value="technology">Technology</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe your content, target audience, and goals..."
              rows={3}
              disabled={uploading}
            />
          </div>

          <div>
            <Label htmlFor="tags">Tags</Label>
            <Input
              id="tags"
              value={formData.tags}
              onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
              placeholder="Enter tags separated by commas"
              disabled={uploading}
            />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="startTime">Start Date & Time</Label>
              <Input
                id="startTime"
                type="datetime-local"
                value={formData.startTime}
                onChange={(e) => setFormData({ ...formData, startTime: e.target.value })}
                disabled={uploading}
              />
            </div>
            <div>
              <Label htmlFor="endTime">End Date & Time</Label>
              <Input
                id="endTime"
                type="datetime-local"
                value={formData.endTime}
                onChange={(e) => setFormData({ ...formData, endTime: e.target.value })}
                disabled={uploading}
              />
            </div>
          </div>

          <div>
            <Label htmlFor="file">Content File *</Label>
            <Input
              id="file"
              type="file"
              accept="image/*,video/*,.html"
              onChange={handleFileChange}
              required
              disabled={uploading}
            />
            <p className="text-sm text-gray-600 mt-1">
              Supported: Images (JPEG, PNG, GIF), Videos (MP4, WebM), HTML5. Max: 100MB
            </p>
          </div>

          {file && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Selected: {file.name}</p>
                  <p className="text-xs text-gray-600">
                    Size: {(file.size / 1024 / 1024).toFixed(2)} MB • Type: {file.type}
                  </p>
                </div>
                <Badge variant="outline">Ready</Badge>
              </div>
            </div>
          )}

          {uploading && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>
                  {uploadStatus === 'uploading' && 'Uploading file...'}
                  {uploadStatus === 'processing' && 'Processing metadata...'}
                </span>
                <span>{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} className="w-full" />
            </div>
          )}

          <div className="flex gap-4">
            <Button
              type="submit"
              disabled={uploading || !file || !formData.title || !formData.category}
              className="flex-1"
            >
              {uploading ? 'Uploading...' : 'Upload Content'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={resetForm}
              disabled={uploading}
            >
              Reset
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
