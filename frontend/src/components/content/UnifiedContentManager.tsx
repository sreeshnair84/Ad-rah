'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { Textarea } from '@/components/ui/textarea';
import { useContent } from '@/hooks/useContent';
import { useAuth } from '@/hooks/useAuth';
import { PageLayout } from '@/components/shared/PageLayout';
import {
  Upload,
  Eye,
  Share2,
  CheckCircle,
  XCircle,
  Edit,
  Trash2,
  Download,
  Clock,
  Users,
  Building2,
  Crown,
  Search,
  Filter,
  FileText,
  Image,
  Video,
  Globe,
  Play,
  Pause,
  Square,
  Check,
  X,
  MessageSquare,
  Monitor
} from 'lucide-react';

interface ContentItem {
  id: string;
  title: string;
  description?: string;
  instructions?: string;
  owner_id: string;
  categories: string[];
  tags: string[];
  status?: 'draft' | 'pending_review' | 'quarantine' | 'approved' | 'rejected' | 'archived';
  created_at?: string;
  updated_at?: string;
  filename?: string;
  content_type?: string;
  size?: number;
  company_name?: string;
  created_by?: string;
  visibility_level?: 'private' | 'shared' | 'public';
  rejection_reason?: string;
  metadata?: {
    file_type?: string;
    file_size?: number;
    duration?: number;
    dimensions?: { width: number; height: number };
  };
}

interface UnifiedContentManagerProps {
  mode?: 'all' | 'user' | 'review' | 'upload' | 'unified';
  showUpload?: boolean;
  showFilters?: boolean;
  showActions?: boolean;
  compactView?: boolean;
  onContentSelect?: (content: ContentItem) => void;
}

export function UnifiedContentManager({
  mode = 'all',
  showUpload = true,
  showFilters = true,
  showActions = true,
  compactView = false,
  onContentSelect
}: UnifiedContentManagerProps) {
  const { user, hasRole, hasPermission, isSuperUser, getDisplayName, getRoleDisplay } = useAuth();
  const { loading, error, uploadFile, getContentList, approveContent, rejectContent } = useContent();

  const [content, setContent] = useState<ContentItem[]>([]);
  const [filteredContent, setFilteredContent] = useState<ContentItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedContent, setSelectedContent] = useState<ContentItem | null>(null);
  const [showApprovalDialog, setShowApprovalDialog] = useState(false);
  const [approvalFormData, setApprovalFormData] = useState({
    action: 'approve' as 'approve' | 'reject',
    message: '',
    category: '',
    start_time: '',
    end_time: ''
  });

  // Upload form data
  const [uploadFormData, setUploadFormData] = useState({
    title: '',
    description: '',
    instructions: '',
    category: '',
    tags: [] as string[],
    priority: 'medium' as 'low' | 'medium' | 'high'
  });

  // Edit form data
  const [editFormData, setEditFormData] = useState({
    title: '',
    description: '',
    instructions: '',
    category: '',
    tags: [] as string[],
    priority: 'medium' as 'low' | 'medium' | 'high'
  });

  // Map backend status to frontend status
  const mapBackendStatus = (status?: string) => {
    switch (status) {
      case 'quarantine': return 'pending_review';
      case 'approved': return 'approved';
      case 'rejected': return 'rejected';
      case 'draft': return 'draft';
      case 'archived': return 'archived';
      default: return 'pending_review';
    }
  };

  const fetchContent = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      let endpoint = '/api/content/';
      if (mode === 'user' && user?.id) {
        endpoint = `/api/content/user/${user.id}`;
      } else if (mode === 'review') {
        endpoint = '/api/content/admin/pending';
      }

      const response = await fetch(endpoint, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        const contentList = data.content || data || [];

        // Map backend statuses to frontend statuses
        const mappedContent = contentList.map((item: any) => ({
          ...item,
          status: mapBackendStatus(item.status)
        }));

        setContent(mappedContent);
      }
    } catch (err) {
      console.error('Failed to fetch content:', err);
    }
  }, [mode, user?.id]);

  useEffect(() => {
    fetchContent();
  }, [fetchContent]);

  useEffect(() => {
    let filtered = content || [];

    // Filter by mode
    if (mode === 'user' && user?.id) {
      filtered = filtered.filter(item => item.owner_id === user.id);
    }
    if (mode === 'review') {
      filtered = filtered.filter(item => item.status === 'pending_review' || item.status === 'quarantine');
    }

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(item =>
        item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Filter by status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(item => item.status === statusFilter);
    }

    // Filter by category
    if (categoryFilter !== 'all') {
      filtered = filtered.filter(item => item.categories.includes(categoryFilter));
    }

    setFilteredContent(filtered);
  }, [content, searchTerm, statusFilter, categoryFilter, mode, user?.id]);

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800';
      case 'pending_review': return 'bg-yellow-100 text-yellow-800';
      case 'quarantine': return 'bg-orange-100 text-orange-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'draft': return 'bg-gray-100 text-gray-800';
      case 'archived': return 'bg-gray-100 text-gray-600';
      default: return 'bg-blue-100 text-blue-800';
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'approved': return <CheckCircle className="w-4 h-4" />;
      case 'pending_review': return <Clock className="w-4 h-4" />;
      case 'quarantine': return <MessageSquare className="w-4 h-4" />;
      case 'rejected': return <XCircle className="w-4 h-4" />;
      case 'draft': return <Edit className="w-4 h-4" />;
      default: return <Eye className="w-4 h-4" />;
    }
  };

  const getContentTypeIcon = (contentType?: string) => {
    if (!contentType) return <FileText className="h-4 w-4" />;
    if (contentType.startsWith('image/')) return <Image className="h-4 w-4" />;
    if (contentType.startsWith('video/')) return <Video className="h-4 w-4" />;
    return <FileText className="h-4 w-4" />;
  };

  const getVisibilityIcon = (level?: string) => {
    switch (level) {
      case 'shared': return <Share2 className="w-4 h-4 text-blue-600" />;
      case 'public': return <Users className="w-4 h-4 text-green-600" />;
      default: return <Building2 className="w-4 h-4 text-gray-600" />;
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleContentClick = (content: ContentItem) => {
    if (onContentSelect) {
      onContentSelect(content);
    } else {
      setSelectedContent(content);
    }
  };

  const handleEditContent = (content: ContentItem) => {
    setSelectedContent(content);
    setEditFormData({
      title: content.title || '',
      description: content.description || '',
      instructions: content.instructions || '',
      category: content.categories[0] || '',
      tags: content.tags || [],
      priority: 'medium'
    });
    setShowEditDialog(true);
  };

  const handleDeleteContent = async (contentId: string) => {
    if (!confirm('Are you sure you want to delete this content? This action cannot be undone.')) {
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const response = await fetch(`/api/content/${contentId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        await fetchContent(); // Refresh the content list
      } else {
        console.error('Failed to delete content');
      }
    } catch (error) {
      console.error('Failed to delete content:', error);
    }
  };

  const handleApproval = async () => {
    if (!selectedContent || !user?.id) return;

    try {
      if (approvalFormData.action === 'approve') {
        await approveContent(selectedContent.id, {
          approved_by: user.id,
          message: approvalFormData.message,
          category: approvalFormData.category || selectedContent.categories[0],
          start_time: approvalFormData.start_time,
          end_time: approvalFormData.end_time
        });
      } else {
        await rejectContent(selectedContent.id, {
          rejected_by: user.id,
          reason: approvalFormData.message || 'Content does not meet guidelines'
        });
      }

      await fetchContent();
      setShowApprovalDialog(false);
      setSelectedContent(null);
      setApprovalFormData({
        action: 'approve',
        message: '',
        category: '',
        start_time: '',
        end_time: ''
      });
    } catch (error) {
      console.error('Failed to process approval:', error);
    }
  };

  const renderFilters = () => {
    if (!showFilters) return null;

    return (
      <div className="flex items-center gap-4 mb-6">
        <div className="flex-1">
          <Input
            placeholder="Search content..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="max-w-sm"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="pending_review">Pending</SelectItem>
            <SelectItem value="quarantine">Quarantine</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="archived">Archived</SelectItem>
          </SelectContent>
        </Select>
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            <SelectItem value="advertising">Advertising</SelectItem>
            <SelectItem value="promotional">Promotional</SelectItem>
            <SelectItem value="informational">Informational</SelectItem>
            <SelectItem value="entertainment">Entertainment</SelectItem>
            <SelectItem value="food">Food & Dining</SelectItem>
            <SelectItem value="retail">Retail</SelectItem>
            <SelectItem value="services">Services</SelectItem>
            <SelectItem value="healthcare">Healthcare</SelectItem>
            <SelectItem value="education">Education</SelectItem>
            <SelectItem value="technology">Technology</SelectItem>
            <SelectItem value="other">Other</SelectItem>
          </SelectContent>
        </Select>
      </div>
    );
  };

  const renderActions = () => {
    if (!showActions) return null;

    return (
      <div className="flex items-center gap-2">
        {showUpload && hasPermission("content", "upload") && (
          <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
            <DialogTrigger asChild>
              <Button>
                <Upload className="h-4 w-4 mr-2" />
                Upload Content
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Upload New Content</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <Label>Title *</Label>
                    <Input
                      value={uploadFormData.title}
                      onChange={(e) => setUploadFormData({...uploadFormData, title: e.target.value})}
                      placeholder="Content title"
                    />
                  </div>
                  <div>
                    <Label>Category *</Label>
                    <Select
                      value={uploadFormData.category}
                      onValueChange={(value) => setUploadFormData({...uploadFormData, category: value})}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="advertising">Advertising</SelectItem>
                        <SelectItem value="promotional">Promotional</SelectItem>
                        <SelectItem value="informational">Informational</SelectItem>
                        <SelectItem value="entertainment">Entertainment</SelectItem>
                        <SelectItem value="food">Food & Dining</SelectItem>
                        <SelectItem value="retail">Retail</SelectItem>
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
                  <Label>Description</Label>
                  <Textarea
                    value={uploadFormData.description}
                    onChange={(e) => setUploadFormData({...uploadFormData, description: e.target.value})}
                    placeholder="Content description"
                    rows={3}
                  />
                </div>
                <div>
                  <Label>Instructions</Label>
                  <Textarea
                    value={uploadFormData.instructions}
                    onChange={(e) => setUploadFormData({...uploadFormData, instructions: e.target.value})}
                    placeholder="Special instructions for content display, timing, or scheduling"
                    rows={2}
                  />
                </div>
                <div className="text-center text-muted-foreground">
                  Upload functionality will be integrated here
                </div>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </div>
    );
  };

  const renderContentGrid = () => {
    if (compactView) {
      return (
        <div className="space-y-2">
          {filteredContent.map((item) => (
            <div
              key={item.id}
              className="flex items-center gap-3 p-3 border rounded-lg hover:bg-muted/50 cursor-pointer"
              onClick={() => handleContentClick(item)}
            >
              {getContentTypeIcon(item.content_type)}
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{item.title}</p>
                <p className="text-sm text-muted-foreground truncate">
                  {item.description}
                </p>
              </div>
              <Badge className={getStatusColor(item.status)}>
                {item.status || 'Unknown'}
              </Badge>
            </div>
          ))}
        </div>
      );
    }

    return (
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredContent.map((item) => (
          <Card
            key={item.id}
            className="hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => handleContentClick(item)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  {getContentTypeIcon(item.content_type)}
                  <CardTitle className="text-lg line-clamp-2">{item.title}</CardTitle>
                </div>
                <Badge className={getStatusColor(item.status)}>
                  {item.status || 'Unknown'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {item.description && (
                <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                  {item.description}
                </p>
              )}

              <div className="flex items-center justify-between text-xs text-muted-foreground mb-3">
                <span>By {item.created_by || 'Unknown'}</span>
                <span>{item.created_at ? new Date(item.created_at).toLocaleDateString() : 'Unknown'}</span>
              </div>

              {item.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-3">
                  {item.tags.slice(0, 3).map((tag, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                  {item.tags.length > 3 && (
                    <Badge variant="outline" className="text-xs">
                      +{item.tags.length - 3} more
                    </Badge>
                  )}
                </div>
              )}

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Building2 className="h-3 w-3" />
                  {item.company_name || 'Unknown Company'}
                </div>
                <div className="flex items-center gap-1">
                  <Button variant="ghost" size="sm">
                    <Eye className="h-4 w-4" />
                  </Button>
                  {hasPermission("content", "edit") && (
                    <Button variant="ghost" size="sm" onClick={(e) => {
                      e.stopPropagation();
                      handleEditContent(item);
                    }}>
                      <Edit className="h-4 w-4" />
                    </Button>
                  )}
                  {hasPermission("content", "delete") && (
                    <Button variant="ghost" size="sm" onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteContent(item.id);
                    }}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };

  const renderApprovalDialog = () => (
    <AlertDialog open={showApprovalDialog} onOpenChange={setShowApprovalDialog}>
      <AlertDialogContent className="max-w-2xl">
        <AlertDialogHeader>
          <AlertDialogTitle>
            Review Content: {selectedContent?.title}
          </AlertDialogTitle>
          <AlertDialogDescription>
            Review and approve or reject this content submission.
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
                  <p><strong>Submitted:</strong> {selectedContent.created_at ? new Date(selectedContent.created_at).toLocaleString() : 'Unknown'}</p>
                  {selectedContent.size && (
                    <p><strong>Size:</strong> {formatFileSize(selectedContent.size)}</p>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <Label>Decision</Label>
                <Select
                  value={approvalFormData.action}
                  onValueChange={(value: 'approve' | 'reject') => setApprovalFormData({...approvalFormData, action: value})}
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

              {approvalFormData.action === 'approve' && (
                <>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <Label>Final Category</Label>
                      <Select
                        value={approvalFormData.category || selectedContent.categories[0]}
                        onValueChange={(value) => setApprovalFormData({...approvalFormData, category: value})}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select category" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="advertising">Advertising</SelectItem>
                          <SelectItem value="promotional">Promotional</SelectItem>
                          <SelectItem value="informational">Informational</SelectItem>
                          <SelectItem value="entertainment">Entertainment</SelectItem>
                          <SelectItem value="food">Food & Dining</SelectItem>
                          <SelectItem value="retail">Retail</SelectItem>
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
                      <Label>Active Start Date</Label>
                      <Input
                        type="datetime-local"
                        value={approvalFormData.start_time}
                        onChange={(e) => setApprovalFormData({...approvalFormData, start_time: e.target.value})}
                      />
                    </div>
                    <div>
                      <Label>Active End Date</Label>
                      <Input
                        type="datetime-local"
                        value={approvalFormData.end_time}
                        onChange={(e) => setApprovalFormData({...approvalFormData, end_time: e.target.value})}
                      />
                    </div>
                  </div>
                </>
              )}

              <div className="space-y-2">
                <Label>
                  {approvalFormData.action === 'approve' ? 'Approval Notes (optional)' : 'Rejection Reason *'}
                </Label>
                <Textarea
                  value={approvalFormData.message}
                  onChange={(e) => setApprovalFormData({...approvalFormData, message: e.target.value})}
                  placeholder={
                    approvalFormData.action === 'approve'
                      ? 'Any notes or feedback for the advertiser...'
                      : 'Please explain why this content is being rejected...'
                  }
                  rows={3}
                  required={approvalFormData.action === 'reject'}
                />
              </div>
            </div>
          </div>
        )}

        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleApproval}
            disabled={approvalFormData.action === 'reject' && !approvalFormData.message}
            className={approvalFormData.action === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}
          >
            {approvalFormData.action === 'approve' ? (
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
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );

  const getPageTitle = () => {
    switch (mode) {
      case 'user': return 'My Content';
      case 'review': return 'Content Review';
      case 'upload': return 'Upload Content';
      default: return 'Content Management';
    }
  };

  const getPageDescription = () => {
    switch (mode) {
      case 'user': return 'Manage your uploaded content';
      case 'review': return 'Review and approve content submissions';
      case 'upload': return 'Upload new content to the platform';
      default: return 'View and manage all platform content';
    }
  };

  return (
    <PageLayout
      title={getPageTitle()}
      description={getPageDescription()}
      actions={renderActions()}
      loading={loading}
      error={error}
    >
      {/* Permission Overview for non-compact view */}
      {!compactView && mode === 'all' && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Your Permissions
            </CardTitle>
            <CardDescription>
              Current access level and available actions based on your role
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${hasPermission('content', 'view') ? 'bg-green-500' : 'bg-gray-300'}`} />
                <span className="text-sm">View Content</span>
              </div>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${hasPermission('content', 'create') ? 'bg-green-500' : 'bg-gray-300'}`} />
                <span className="text-sm">Create Content</span>
              </div>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${hasPermission('content', 'approve') ? 'bg-green-500' : 'bg-gray-300'}`} />
                <span className="text-sm">Approve Content</span>
              </div>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${hasPermission('content', 'share') ? 'bg-green-500' : 'bg-gray-300'}`} />
                <span className="text-sm">Share Content</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {renderFilters()}

      {filteredContent.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No content found</h3>
            <p className="text-muted-foreground mb-4">
              {mode === 'user'
                ? "You haven't uploaded any content yet."
                : "No content matches your current filters."
              }
            </p>
            {mode === 'user' && showUpload && (
              <Button onClick={() => setShowUploadDialog(true)}>
                <Upload className="h-4 w-4 mr-2" />
                Upload Your First Content
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        renderContentGrid()
      )}

      {/* Content Detail Dialog */}
      <Dialog open={!!selectedContent && !showApprovalDialog && !showEditDialog} onOpenChange={() => setSelectedContent(null)}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>{selectedContent?.title}</DialogTitle>
          </DialogHeader>
          {selectedContent && (
            <div className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label className="text-sm font-medium">Status</Label>
                  <div className="flex items-center gap-2 mt-1">
                    {getStatusIcon(selectedContent.status)}
                    <Badge className={getStatusColor(selectedContent.status)}>
                      {selectedContent.status || 'Unknown'}
                    </Badge>
                  </div>
                </div>
                <div>
                  <Label className="text-sm font-medium">Visibility</Label>
                  <div className="flex items-center gap-2 mt-1">
                    {getVisibilityIcon(selectedContent.visibility_level)}
                    <span className="capitalize">{selectedContent.visibility_level || 'private'}</span>
                  </div>
                </div>
              </div>

              {selectedContent.description && (
                <div>
                  <Label className="text-sm font-medium">Description</Label>
                  <p className="text-sm text-muted-foreground mt-1">{selectedContent.description}</p>
                </div>
              )}

              <div className="grid gap-4 md:grid-cols-3">
                <div>
                  <Label className="text-sm font-medium">Created By</Label>
                  <p className="text-sm text-muted-foreground mt-1">{selectedContent.created_by || 'Unknown'}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium">Company</Label>
                  <p className="text-sm text-muted-foreground mt-1">{selectedContent.company_name || 'Unknown'}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium">File Size</Label>
                  <p className="text-sm text-muted-foreground mt-1">{formatFileSize(selectedContent.size)}</p>
                </div>
              </div>

              {selectedContent.tags.length > 0 && (
                <div>
                  <Label className="text-sm font-medium">Tags</Label>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedContent.tags.map((tag, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Approval Actions for Review Mode */}
              {mode === 'review' && (selectedContent.status === 'pending_review' || selectedContent.status === 'quarantine') && (
                <div className="flex gap-2 pt-4 border-t">
                  <Button
                    onClick={() => {
                      setApprovalFormData({...approvalFormData, action: 'approve'});
                      setShowApprovalDialog(true);
                    }}
                    className="flex-1 bg-green-600 hover:bg-green-700"
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Approve
                  </Button>
                  <Button
                    onClick={() => {
                      setApprovalFormData({...approvalFormData, action: 'reject'});
                      setShowApprovalDialog(true);
                    }}
                    variant="destructive"
                    className="flex-1"
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    Reject
                  </Button>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit Content Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Content</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label>Title *</Label>
                <Input
                  value={editFormData.title}
                  onChange={(e) => setEditFormData({...editFormData, title: e.target.value})}
                  placeholder="Content title"
                />
              </div>
              <div>
                <Label>Category *</Label>
                <Select
                  value={editFormData.category}
                  onValueChange={(value) => setEditFormData({...editFormData, category: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="advertising">Advertising</SelectItem>
                    <SelectItem value="promotional">Promotional</SelectItem>
                    <SelectItem value="informational">Informational</SelectItem>
                    <SelectItem value="entertainment">Entertainment</SelectItem>
                    <SelectItem value="food">Food & Dining</SelectItem>
                    <SelectItem value="retail">Retail</SelectItem>
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
              <Label>Description</Label>
              <Textarea
                value={editFormData.description}
                onChange={(e) => setEditFormData({...editFormData, description: e.target.value})}
                placeholder="Content description"
                rows={3}
              />
            </div>
            <div>
              <Label>Instructions</Label>
              <Textarea
                value={editFormData.instructions}
                onChange={(e) => setEditFormData({...editFormData, instructions: e.target.value})}
                placeholder="Special instructions for content display, timing, or scheduling"
                rows={2}
              />
            </div>
            <div className="flex gap-2 pt-4">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => setShowEditDialog(false)}
              >
                Cancel
              </Button>
              <Button className="flex-1">
                Save Changes
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {renderApprovalDialog()}
    </PageLayout>
  );
}
