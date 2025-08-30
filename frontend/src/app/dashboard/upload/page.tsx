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
import { useContent } from '@/hooks/useContent';
import { useAuth } from '@/hooks/useAuth';

export default function UploadPage() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');
  const [tags, setTags] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'processing' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [uploadedContentId, setUploadedContentId] = useState<string | null>(null);

  const router = useRouter();
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
    if (!file || !title || !category) {
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
        id: uploadResponse.filename, // Use filename as content ID for now
        title,
        description: description || undefined,
        owner_id: user.id,
        categories: [category],
        start_time: startTime ? new Date(startTime).toISOString() : undefined,
        end_time: endTime ? new Date(endTime).toISOString() : undefined,
        tags: tags ? tags.split(',').map(tag => tag.trim()) : []
      };

      setUploadProgress(75);
      await postMetadata(metadata);

      setUploadProgress(100);
      setUploadStatus('success');
      setUploadedContentId(uploadResponse.filename);

      // Redirect to content management page after a delay
      setTimeout(() => {
        router.push('/dashboard/my-ads');
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
    setTitle('');
    setDescription('');
    setCategory('');
    setTags('');
    setStartTime('');
    setEndTime('');
    setFile(null);
    setUploadProgress(0);
    setUploadStatus('idle');
    setErrorMessage('');
    setUploadedContentId(null);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h2 className="text-3xl font-bold">Upload New Content</h2>
        <p className="text-gray-600 mt-2">Upload your advertisement content for review and approval</p>
      </div>

      {uploadStatus === 'success' && (
        <Alert className="mb-6 border-green-200 bg-green-50">
          <AlertDescription className="text-green-800">
            Content uploaded successfully! {uploadedContentId && `Content ID: ${uploadedContentId}`}
            <br />
            Your content is now in the moderation queue and will be reviewed by our team.
          </AlertDescription>
        </Alert>
      )}

      {errorMessage && (
        <Alert className="mb-6 border-red-200 bg-red-50">
          <AlertDescription className="text-red-800">
            {errorMessage}
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Content Details</CardTitle>
          <CardDescription>
            Provide information about your content and set scheduling options
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <Label htmlFor="title">Content Title *</Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter a descriptive title for your content"
                required
                disabled={uploading}
              />
            </div>

            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe your content, target audience, and goals..."
                rows={3}
                disabled={uploading}
              />
            </div>

            <div>
              <Label htmlFor="category">Category *</Label>
              <Select value={category} onValueChange={setCategory} required disabled={uploading}>
                <SelectTrigger>
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

            <div>
              <Label htmlFor="tags">Tags</Label>
              <Input
                id="tags"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="Enter tags separated by commas (e.g., promotion, seasonal, local)"
                disabled={uploading}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="startTime">Start Date & Time</Label>
                <Input
                  id="startTime"
                  type="datetime-local"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  disabled={uploading}
                />
              </div>
              <div>
                <Label htmlFor="endTime">End Date & Time</Label>
                <Input
                  id="endTime"
                  type="datetime-local"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
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
                Supported formats: Images (JPEG, PNG, GIF), Videos (MP4, WebM), HTML5
                <br />
                Maximum file size: 100MB
              </p>
            </div>

            {file && (
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Selected file: {file.name}</p>
                    <p className="text-xs text-gray-600">
                      Size: {(file.size / 1024 / 1024).toFixed(2)} MB • Type: {file.type}
                    </p>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    Ready to upload
                  </Badge>
                </div>
              </div>
            )}

            {uploading && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Uploading...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} className="w-full" />
                <p className="text-xs text-gray-600">
                  {uploadStatus === 'uploading' && 'Uploading file to server...'}
                  {uploadStatus === 'processing' && 'Processing metadata...'}
                </p>
              </div>
            )}

            <div className="flex gap-4">
              <Button
                type="submit"
                disabled={uploading || !file || !title || !category}
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
    </div>
  );
}
