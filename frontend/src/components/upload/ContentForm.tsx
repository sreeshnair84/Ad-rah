'use client';

import React from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import { UploadFormData } from '@/hooks/useUpload';

interface ContentFormProps {
  formData: UploadFormData;
  onFormDataChange: (data: Partial<UploadFormData>) => void;
  disabled?: boolean;
  showAdvanced?: boolean;
}

const CATEGORIES = [
  { value: 'food', label: 'Food & Dining' },
  { value: 'retail', label: 'Retail' },
  { value: 'entertainment', label: 'Entertainment' },
  { value: 'services', label: 'Services' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'education', label: 'Education' },
  { value: 'technology', label: 'Technology' },
  { value: 'other', label: 'Other' }
];

export function ContentForm({ 
  formData, 
  onFormDataChange, 
  disabled = false, 
  showAdvanced = false 
}: ContentFormProps) {
  const addTag = (tag: string) => {
    if (tag.trim() && !formData.tags.includes(tag.trim())) {
      onFormDataChange({
        tags: [...formData.tags, tag.trim()]
      });
    }
  };

  const removeTag = (tagToRemove: string) => {
    onFormDataChange({
      tags: formData.tags.filter(tag => tag !== tagToRemove)
    });
  };

  const [newTag, setNewTag] = React.useState('');

  const handleAddTag = () => {
    addTag(newTag);
    setNewTag('');
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Content Details</CardTitle>
        <CardDescription>
          Provide details about your content for better organization and discovery
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Title - Required */}
        <div>
          <Label htmlFor="title">Title *</Label>
          <Input
            id="title"
            value={formData.title}
            onChange={(e) => onFormDataChange({ title: e.target.value })}
            placeholder="Enter content title..."
            className="mt-1"
            disabled={disabled}
            required
          />
        </div>

        {/* Description */}
        <div>
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            value={formData.description}
            onChange={(e) => onFormDataChange({ description: e.target.value })}
            placeholder="Describe your content..."
            rows={3}
            className="mt-1"
            disabled={disabled}
          />
        </div>

        {/* Category - Required */}
        <div>
          <Label htmlFor="category">Category *</Label>
          <Select 
            value={formData.category} 
            onValueChange={(value) => onFormDataChange({ category: value })}
            disabled={disabled}
            name="category"
          >
            <SelectTrigger className="mt-1" id="category">
              <SelectValue placeholder="Select a category" />
            </SelectTrigger>
            <SelectContent>
              {CATEGORIES.map(category => (
                <SelectItem key={category.value} value={category.value}>
                  {category.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Tags */}
        <div>
          <Label htmlFor="tags">Tags</Label>
          <div className="mt-1 space-y-2">
            <div className="flex gap-2">
              <Input
                id="tags"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                placeholder="Add a tag..."
                disabled={disabled}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddTag();
                  }
                }}
              />
              <Button
                type="button"
                variant="outline"
                onClick={handleAddTag}
                disabled={disabled || !newTag.trim()}
              >
                Add
              </Button>
            </div>
            {formData.tags.length > 0 && (
              <div className="flex gap-1 flex-wrap">
                {formData.tags.map(tag => (
                  <Badge key={tag} variant="secondary" className="text-sm">
                    {tag}
                    {!disabled && (
                      <button
                        type="button"
                        onClick={() => removeTag(tag)}
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

        {/* Advanced Fields */}
        {showAdvanced && (
          <>
            {/* Priority */}
            <div>
              <Label htmlFor="priority">Priority</Label>
              <Select
                value={formData.priority}
                onValueChange={(value: 'low' | 'medium' | 'high') => onFormDataChange({ priority: value })}
                disabled={disabled}
                name="priority"
              >
                <SelectTrigger className="mt-1" id="priority">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Scheduled Date */}
            <div>
              <Label htmlFor="scheduled">Scheduled Date (Optional)</Label>
              <Input
                id="scheduled"
                type="datetime-local"
                value={formData.scheduledDate || ''}
                onChange={(e) => onFormDataChange({ scheduledDate: e.target.value })}
                className="mt-1"
                disabled={disabled}
              />
            </div>

            {/* Start/End Time */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="startTime">Start Date & Time</Label>
                <Input
                  id="startTime"
                  type="datetime-local"
                  value={formData.startTime || ''}
                  onChange={(e) => onFormDataChange({ startTime: e.target.value })}
                  className="mt-1"
                  disabled={disabled}
                />
              </div>
              <div>
                <Label htmlFor="endTime">End Date & Time</Label>
                <Input
                  id="endTime"
                  type="datetime-local"
                  value={formData.endTime || ''}
                  onChange={(e) => onFormDataChange({ endTime: e.target.value })}
                  className="mt-1"
                  disabled={disabled}
                />
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
