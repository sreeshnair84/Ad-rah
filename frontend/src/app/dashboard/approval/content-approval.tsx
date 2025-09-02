'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { Check, X, Eye, Clock, FileText, Image, Video, Monitor, MessageSquare } from 'lucide-react';
import { useContent } from '@/hooks/useContent';
import { useAuth } from '@/hooks/useAuth';

interface ContentItem {
  id: string;
  title: string;
  description?: string;
  owner_id: string;
  categories: string[];
  status: 'pending' | 'approved' | 'rejected';
  rejection_reason?: string;
  created_at: string;
  start_time?: string;
  end_time?: string;
  tags?: string[];
  metadata?: {
    file_type?: string;
    file_size?: number;
    duration?: number;
    dimensions?: { width: number; height: number };
  };
}

interface ApprovalFormData {
  action: 'approve' | 'reject';
  message?: string;
  category?: string;
  start_time?: string;
  end_time?: string;
}

export default function ContentApproval() {
  const [content, setContent] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedContent, setSelectedContent] = useState<ContentItem | null>(null);
  const [formData, setFormData] = useState<ApprovalFormData>({
    action: 'approve'
  });
  const [processing, setProcessing] = useState(false);

  const { getContentList, approveContent, rejectContent } = useContent();
  const { user } = useAuth();

  useEffect(() => {
    loadContent();
  }, []);

  const loadContent = async () => {
    try {
      setLoading(true);
      const data = await getContentList();
      // Filter for pending content
      const pendingContent = data.filter((item: ContentItem) => item.status === 'pending');
      setContent(pendingContent);
    } catch (error) {
      console.error('Failed to load content:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApproval = async (item: ContentItem, action: 'approve' | 'reject') => {
    if (!user?.id) return;

    setProcessing(true);
    try {
      if (action === 'approve') {
        await approveContent(item.id, {
          approved_by: user.id,
          message: formData.message,
          category: formData.category || item.categories[0],
          start_time: formData.start_time,
          end_time: formData.end_time
        });
      } else {
        await rejectContent(item.id, {
          rejected_by: user.id,
          reason: formData.message || 'Content does not meet guidelines'
        });
      }
      
      // Reload content list
      await loadContent();
      setSelectedContent(null);
      setFormData({ action: 'approve' });
    } catch (error) {
      console.error('Failed to process approval:', error);
    } finally {
      setProcessing(false);
    }
  };

  const getFileIcon = (fileType?: string) => {
    if (!fileType) return <FileText className="h-4 w-4" />;
    if (fileType.startsWith('image/')) return <Image className="h-4 w-4" aria-label="Image file" />;
    if (fileType.startsWith('video/')) return <Video className="h-4 w-4" />;
    if (fileType.includes('html')) return <Monitor className="h-4 w-4" />;
    return <FileText className="h-4 w-4" />;
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown size';
    const mb = bytes / 1024 / 1024;
    return `${mb.toFixed(2)} MB`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Content Approval</CardTitle>
          <CardDescription>Loading pending content...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Content Approval Queue</span>
            <Badge variant="outline">
              {content.length} pending
            </Badge>
          </CardTitle>
          <CardDescription>
            Review and approve advertiser content submissions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {content.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No content pending approval</p>
            </div>
          ) : (
            <div className="space-y-4">
              {content.map((item) => (
                <div key={item.id} className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        {getFileIcon(item.metadata?.file_type)}
                        <h3 className="font-semibold">{item.title}</h3>
                        <Badge variant="secondary">
                          {item.categories[0]}
                        </Badge>
                      </div>
                      
                      {item.description && (
                        <p className="text-sm text-gray-600 mb-2">{item.description}</p>
                      )}
                      
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {formatDate(item.created_at)}
                        </span>
                        {item.metadata?.file_size && (
                          <span>{formatFileSize(item.metadata.file_size)}</span>
                        )}
                        {item.metadata?.dimensions && (
                          <span>
                            {item.metadata.dimensions.width}×{item.metadata.dimensions.height}
                          </span>
                        )}
                      </div>
                      
                      {item.tags && item.tags.length > 0 && (
                        <div className="flex gap-1 mt-2">
                          {item.tags.map((tag, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex gap-2 ml-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSelectedContent(item)}
                      >
                        <Eye className="h-4 w-4 mr-1" />
                        Review
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Review Dialog */}
      <AlertDialog open={!!selectedContent} onOpenChange={() => setSelectedContent(null)}>
        <AlertDialogContent className="max-w-2xl">
          <AlertDialogHeader>
            <AlertDialogTitle>Review Content: {selectedContent?.title}</AlertDialogTitle>
            <AlertDialogDescription>
              Carefully review this content before making an approval decision.
            </AlertDialogDescription>
          </AlertDialogHeader>
          
          {selectedContent && (
            <div className="space-y-4">
              <div className="grid gap-4 py-4">
                <div className="space-y-2">
                  <Label>Content Details</Label>
                  <div className="bg-gray-50 p-3 rounded">
                    <p><strong>Title:</strong> {selectedContent.title}</p>
                    {selectedContent.description && (
                      <p><strong>Description:</strong> {selectedContent.description}</p>
                    )}
                    <p><strong>Category:</strong> {selectedContent.categories.join(', ')}</p>
                    <p><strong>Submitted:</strong> {formatDate(selectedContent.created_at)}</p>
                    {selectedContent.start_time && (
                      <p><strong>Requested Start:</strong> {formatDate(selectedContent.start_time)}</p>
                    )}
                    {selectedContent.end_time && (
                      <p><strong>Requested End:</strong> {formatDate(selectedContent.end_time)}</p>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="action">Decision</Label>
                  <Select 
                    value={formData.action} 
                    onValueChange={(value: 'approve' | 'reject') => setFormData({ ...formData, action: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="approve">
                        <div className="flex items-center gap-2">
                          <Check className="h-4 w-4 text-green-600" />
                          Approve Content
                        </div>
                      </SelectItem>
                      <SelectItem value="reject">
                        <div className="flex items-center gap-2">
                          <X className="h-4 w-4 text-red-600" />
                          Reject Content
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {formData.action === 'approve' && (
                  <>
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <Label htmlFor="category">Final Category</Label>
                        <Select 
                          value={formData.category || selectedContent.categories[0]} 
                          onValueChange={(value) => setFormData({ ...formData, category: value })}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select category" />
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

                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <Label htmlFor="start_time">Active Start Date</Label>
                        <Input
                          id="start_time"
                          type="datetime-local"
                          value={formData.start_time || ''}
                          onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label htmlFor="end_time">Active End Date</Label>
                        <Input
                          id="end_time"
                          type="datetime-local"
                          value={formData.end_time || ''}
                          onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                        />
                      </div>
                    </div>
                  </>
                )}

                <div className="space-y-2">
                  <Label htmlFor="message">
                    {formData.action === 'approve' ? 'Approval Notes (optional)' : 'Rejection Reason *'}
                  </Label>
                  <Textarea
                    id="message"
                    value={formData.message || ''}
                    onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                    placeholder={
                      formData.action === 'approve' 
                        ? 'Any notes or feedback for the advertiser...'
                        : 'Please explain why this content is being rejected...'
                    }
                    rows={3}
                    required={formData.action === 'reject'}
                  />
                </div>
              </div>
            </div>
          )}

          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => selectedContent && handleApproval(selectedContent, formData.action)}
              disabled={processing || (formData.action === 'reject' && !formData.message)}
              className={formData.action === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}
            >
              {processing ? 'Processing...' : (
                <>
                  {formData.action === 'approve' ? (
                    <>
                      <Check className="h-4 w-4 mr-2" />
                      Approve
                    </>
                  ) : (
                    <>
                      <X className="h-4 w-4 mr-2" />
                      Reject
                    </>
                  )}
                </>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
