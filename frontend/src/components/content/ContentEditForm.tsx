'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { MediaPreview } from './MediaPreview';
import { FileReplacement } from './FileReplacement';
import { useAuth } from '@/hooks/useAuth';
import {
  Edit,
  Save,
  X,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Clock,
  User,
  Calendar,
  Tag,
  Folder,
  Settings,
  Upload,
  Eye,
  Trash2
} from 'lucide-react';

interface ContentEditFormProps {
  contentId: string;
  isOpen: boolean;
  onClose: () => void;
  onSaved?: () => void;
}

interface ContentData {
  id: string;
  title: string;
  description?: string;
  filename?: string;
  content_type?: string;
  size?: number;
  status?: string;
  categories: string[];
  tags: string[];
  owner_id: string;
  created_at?: string;
  updated_at?: string;
  start_time?: string;
  end_time?: string;
  target_age_min?: number;
  target_age_max?: number;
  target_gender?: string;
  content_rating?: string;
  production_notes?: string;
  usage_guidelines?: string;
  priority_level?: string;
  copyright_info?: string;
  license_type?: string;
  usage_rights?: string;
  preview_url?: string;
  file_info?: {
    is_image: boolean;
    is_video: boolean;
    is_text: boolean;
    is_audio: boolean;
    formatted_size: string;
  };
  permissions?: {
    can_edit: boolean;
    can_delete: boolean;
    can_approve: boolean;
    can_replace_file: boolean;
  };
}

const CATEGORIES = [
  { value: 'food', label: 'Food & Dining' },
  { value: 'retail', label: 'Retail' },
  { value: 'entertainment', label: 'Entertainment' },
  { value: 'services', label: 'Services' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'education', label: 'Education' },
  { value: 'technology', label: 'Technology' },
  { value: 'advertising', label: 'Advertising' },
  { value: 'promotional', label: 'Promotional' },
  { value: 'informational', label: 'Informational' },
  { value: 'other', label: 'Other' },
];

const CONTENT_RATINGS = [
  { value: 'G', label: 'G - General Audience' },
  { value: 'PG', label: 'PG - Parental Guidance' },
  { value: 'PG-13', label: 'PG-13 - Parents Strongly Cautioned' },
  { value: 'R', label: 'R - Restricted' },
];

const PRIORITY_LEVELS = [
  { value: 'low', label: 'Low Priority' },
  { value: 'medium', label: 'Medium Priority' },
  { value: 'high', label: 'High Priority' },
  { value: 'urgent', label: 'Urgent' },
];

const LICENSE_TYPES = [
  { value: 'commercial', label: 'Commercial License' },
  { value: 'creative_commons', label: 'Creative Commons' },
  { value: 'proprietary', label: 'Proprietary' },
];

export function ContentEditForm({ contentId, isOpen, onClose, onSaved }: ContentEditFormProps) {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [content, setContent] = useState<ContentData | null>(null);
  const [formData, setFormData] = useState<Partial<ContentData>>({});
  const [newTag, setNewTag] = useState('');
  const [activeTab, setActiveTab] = useState('basic');
  const [showFileReplacement, setShowFileReplacement] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Load content data
  useEffect(() => {
    if (isOpen && contentId) {
      loadContent();
    }
  }, [isOpen, contentId]);

  // Track form changes
  useEffect(() => {
    if (content && formData) {
      const hasChanges = Object.keys(formData).some(key => {
        const currentValue = formData[key as keyof ContentData];
        const originalValue = content[key as keyof ContentData];
        return JSON.stringify(currentValue) !== JSON.stringify(originalValue);
      });
      setHasUnsavedChanges(hasChanges);
    }
  }, [formData, content]);

  const loadContent = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/content/${contentId}?detailed=true`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load content');
      }

      const data = await response.json();
      setContent(data);
      setFormData(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load content';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!content || !formData) return;

    setSaving(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      
      // Prepare data for update (exclude computed fields)
      const updateData = {
        title: formData.title,
        description: formData.description,
        categories: formData.categories || [],
        tags: formData.tags || [],
        start_time: formData.start_time,
        end_time: formData.end_time,
        target_age_min: formData.target_age_min,
        target_age_max: formData.target_age_max,
        target_gender: formData.target_gender,
        content_rating: formData.content_rating,
        production_notes: formData.production_notes,
        usage_guidelines: formData.usage_guidelines,
        priority_level: formData.priority_level,
        copyright_info: formData.copyright_info,
        license_type: formData.license_type,
        usage_rights: formData.usage_rights,
      };

      const response = await fetch(`/api/content/${contentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || errorData.error || 'Failed to update content');
      }

      const updatedContent = await response.json();
      setContent(updatedContent);
      setFormData(updatedContent);
      setHasUnsavedChanges(false);
      
      onSaved?.();
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save content';
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleFormChange = (field: keyof ContentData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleAddTag = () => {
    if (newTag.trim() && formData.tags && !formData.tags.includes(newTag.trim())) {
      handleFormChange('tags', [...formData.tags, newTag.trim()]);
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    if (formData.tags) {
      handleFormChange('tags', formData.tags.filter(tag => tag !== tagToRemove));
    }
  };

  const handleFileReplaced = () => {
    setShowFileReplacement(false);
    loadContent(); // Reload content data after file replacement
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'quarantine': return 'bg-orange-100 text-orange-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'draft': return 'bg-gray-100 text-gray-800';
      default: return 'bg-blue-100 text-blue-800';
    }
  };

  const canEditContent = content?.permissions?.can_edit ?? false;
  const canReplaceFile = content?.permissions?.can_replace_file ?? false;

  if (loading) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-center p-8">
            <RefreshCw className="h-8 w-8 animate-spin mr-3" />
            Loading content...
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  if (!content) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-md">
          <div className="text-center p-6">
            <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">Content Not Found</h3>
            <p className="text-gray-600 mb-4">
              {error || 'The requested content could not be loaded.'}
            </p>
            <Button onClick={onClose}>Close</Button>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-7xl max-h-[95vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Edit className="h-5 w-5" />
            Edit Content: {content.title}
            <Badge className={getStatusColor(content.status)}>
              {content.status || 'Unknown'}
            </Badge>
          </DialogTitle>
        </DialogHeader>

        {!canEditContent && (
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              You have read-only access to this content. Contact the owner or an administrator to make changes.
            </AlertDescription>
          </Alert>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="grid gap-6 lg:grid-cols-5">
          {/* Media Preview - Left Side */}
          <div className="lg:col-span-2">
            <MediaPreview
              content={content}
              showFullScreen={true}
              showDownload={true}
              showMetadata={true}
              className="h-fit"
            />
            
            {canReplaceFile && (
              <Card className="mt-4">
                <CardContent className="pt-6">
                  <Button
                    variant="outline"
                    onClick={() => setShowFileReplacement(true)}
                    className="w-full"
                    disabled={saving}
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Replace File
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Content Form - Right Side */}
          <div className="lg:col-span-3">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="basic">Basic Info</TabsTrigger>
                <TabsTrigger value="targeting">Targeting</TabsTrigger>
                <TabsTrigger value="scheduling">Scheduling</TabsTrigger>
                <TabsTrigger value="advanced">Advanced</TabsTrigger>
              </TabsList>

              {/* Basic Information Tab */}
              <TabsContent value="basic" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Edit className="h-4 w-4" />
                      Basic Information
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label htmlFor="title">Title *</Label>
                      <Input
                        id="title"
                        value={formData.title || ''}
                        onChange={(e) => handleFormChange('title', e.target.value)}
                        placeholder="Content title"
                        disabled={!canEditContent}
                        required
                      />
                    </div>

                    <div>
                      <Label htmlFor="description">Description</Label>
                      <Textarea
                        id="description"
                        value={formData.description || ''}
                        onChange={(e) => handleFormChange('description', e.target.value)}
                        placeholder="Describe your content..."
                        rows={3}
                        disabled={!canEditContent}
                      />
                    </div>

                    <div>
                      <Label htmlFor="category">Primary Category</Label>
                      <Select
                        value={formData.categories?.[0] || ''}
                        onValueChange={(value) => handleFormChange('categories', [value])}
                        disabled={!canEditContent}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select a category" />
                        </SelectTrigger>
                        <SelectContent>
                          {CATEGORIES.map(cat => (
                            <SelectItem key={cat.value} value={cat.value}>
                              {cat.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label>Tags</Label>
                      <div className="space-y-2">
                        <div className="flex gap-2">
                          <Input
                            value={newTag}
                            onChange={(e) => setNewTag(e.target.value)}
                            placeholder="Add a tag..."
                            onKeyPress={(e) => {
                              if (e.key === 'Enter') {
                                e.preventDefault();
                                handleAddTag();
                              }
                            }}
                            disabled={!canEditContent}
                          />
                          <Button
                            type="button"
                            variant="outline"
                            onClick={handleAddTag}
                            disabled={!canEditContent || !newTag.trim()}
                          >
                            Add
                          </Button>
                        </div>
                        {formData.tags && formData.tags.length > 0 && (
                          <div className="flex gap-1 flex-wrap">
                            {formData.tags.map(tag => (
                              <Badge key={tag} variant="secondary" className="text-sm">
                                {tag}
                                {canEditContent && (
                                  <button
                                    type="button"
                                    onClick={() => handleRemoveTag(tag)}
                                    className="ml-1 hover:bg-gray-300 rounded-full"
                                  >
                                    <X className="h-3 w-3" />
                                  </button>
                                )}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="priority">Priority Level</Label>
                      <Select
                        value={formData.priority_level || 'medium'}
                        onValueChange={(value) => handleFormChange('priority_level', value)}
                        disabled={!canEditContent}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {PRIORITY_LEVELS.map(level => (
                            <SelectItem key={level.value} value={level.value}>
                              {level.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Targeting Tab */}
              <TabsContent value="targeting" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <User className="h-4 w-4" />
                      Audience Targeting
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label htmlFor="content_rating">Content Rating</Label>
                      <Select
                        value={formData.content_rating || ''}
                        onValueChange={(value) => handleFormChange('content_rating', value)}
                        disabled={!canEditContent}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select content rating" />
                        </SelectTrigger>
                        <SelectContent>
                          {CONTENT_RATINGS.map(rating => (
                            <SelectItem key={rating.value} value={rating.value}>
                              {rating.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <Label htmlFor="age_min">Minimum Age</Label>
                        <Input
                          id="age_min"
                          type="number"
                          min="0"
                          max="100"
                          value={formData.target_age_min || ''}
                          onChange={(e) => handleFormChange('target_age_min', parseInt(e.target.value) || undefined)}
                          placeholder="e.g., 18"
                          disabled={!canEditContent}
                        />
                      </div>
                      <div>
                        <Label htmlFor="age_max">Maximum Age</Label>
                        <Input
                          id="age_max"
                          type="number"
                          min="0"
                          max="100"
                          value={formData.target_age_max || ''}
                          onChange={(e) => handleFormChange('target_age_max', parseInt(e.target.value) || undefined)}
                          placeholder="e.g., 65"
                          disabled={!canEditContent}
                        />
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="target_gender">Target Gender</Label>
                      <Select
                        value={formData.target_gender || 'all'}
                        onValueChange={(value) => handleFormChange('target_gender', value)}
                        disabled={!canEditContent}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Genders</SelectItem>
                          <SelectItem value="male">Male</SelectItem>
                          <SelectItem value="female">Female</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Scheduling Tab */}
              <TabsContent value="scheduling" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      Content Scheduling
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <Label htmlFor="start_time">Start Date & Time</Label>
                        <Input
                          id="start_time"
                          type="datetime-local"
                          value={formData.start_time ? new Date(formData.start_time).toISOString().slice(0, 16) : ''}
                          onChange={(e) => handleFormChange('start_time', e.target.value ? new Date(e.target.value).toISOString() : undefined)}
                          disabled={!canEditContent}
                        />
                      </div>
                      <div>
                        <Label htmlFor="end_time">End Date & Time</Label>
                        <Input
                          id="end_time"
                          type="datetime-local"
                          value={formData.end_time ? new Date(formData.end_time).toISOString().slice(0, 16) : ''}
                          onChange={(e) => handleFormChange('end_time', e.target.value ? new Date(e.target.value).toISOString() : undefined)}
                          disabled={!canEditContent}
                        />
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="production_notes">Production Notes</Label>
                      <Textarea
                        id="production_notes"
                        value={formData.production_notes || ''}
                        onChange={(e) => handleFormChange('production_notes', e.target.value)}
                        placeholder="Notes for editors and content managers..."
                        rows={2}
                        disabled={!canEditContent}
                      />
                    </div>

                    <div>
                      <Label htmlFor="usage_guidelines">Usage Guidelines</Label>
                      <Textarea
                        id="usage_guidelines"
                        value={formData.usage_guidelines || ''}
                        onChange={(e) => handleFormChange('usage_guidelines', e.target.value)}
                        placeholder="Guidelines for content usage and display..."
                        rows={2}
                        disabled={!canEditContent}
                      />
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Advanced Tab */}
              <TabsContent value="advanced" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Settings className="h-4 w-4" />
                      Legal & Compliance
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label htmlFor="license_type">License Type</Label>
                      <Select
                        value={formData.license_type || ''}
                        onValueChange={(value) => handleFormChange('license_type', value)}
                        disabled={!canEditContent}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select license type" />
                        </SelectTrigger>
                        <SelectContent>
                          {LICENSE_TYPES.map(license => (
                            <SelectItem key={license.value} value={license.value}>
                              {license.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="copyright_info">Copyright Information</Label>
                      <Input
                        id="copyright_info"
                        value={formData.copyright_info || ''}
                        onChange={(e) => handleFormChange('copyright_info', e.target.value)}
                        placeholder="© 2025 Company Name"
                        disabled={!canEditContent}
                      />
                    </div>

                    <div>
                      <Label htmlFor="usage_rights">Usage Rights</Label>
                      <Textarea
                        id="usage_rights"
                        value={formData.usage_rights || ''}
                        onChange={(e) => handleFormChange('usage_rights', e.target.value)}
                        placeholder="Describe usage rights and restrictions..."
                        rows={2}
                        disabled={!canEditContent}
                      />
                    </div>
                  </CardContent>
                </Card>

                {/* Content Metadata */}
                <Card>
                  <CardHeader>
                    <CardTitle>Content Information</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="grid gap-2 text-sm">
                      <div className="flex justify-between">
                        <span className="font-medium">Created:</span>
                        <span>{content.created_at ? new Date(content.created_at).toLocaleString() : 'Unknown'}</span>
                      </div>
                      {content.updated_at && (
                        <div className="flex justify-between">
                          <span className="font-medium">Last Updated:</span>
                          <span>{new Date(content.updated_at).toLocaleString()}</span>
                        </div>
                      )}
                      <div className="flex justify-between">
                        <span className="font-medium">Owner:</span>
                        <span>{content.owner_id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="font-medium">Content ID:</span>
                        <span className="font-mono text-xs">{content.id}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between items-center pt-4 border-t">
          <div className="flex items-center gap-2">
            {hasUnsavedChanges && (
              <Badge variant="outline" className="text-orange-600 border-orange-200">
                <Clock className="h-3 w-3 mr-1" />
                Unsaved Changes
              </Badge>
            )}
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={saving}
            >
              {hasUnsavedChanges ? 'Discard Changes' : 'Close'}
            </Button>
            
            {canEditContent && (
              <Button
                onClick={handleSave}
                disabled={saving || !hasUnsavedChanges}
              >
                {saving ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Changes
                  </>
                )}
              </Button>
            )}
          </div>
        </div>

        {/* File Replacement Dialog */}
        <Dialog open={showFileReplacement} onOpenChange={setShowFileReplacement}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Replace Content File</DialogTitle>
            </DialogHeader>
            <FileReplacement
              contentId={contentId}
              currentFile={content.filename ? {
                filename: content.filename,
                content_type: content.content_type || '',
                size: content.size || 0
              } : undefined}
              onSuccess={handleFileReplaced}
              onCancel={() => setShowFileReplacement(false)}
            />
          </DialogContent>
        </Dialog>
      </DialogContent>
    </Dialog>
  );
}