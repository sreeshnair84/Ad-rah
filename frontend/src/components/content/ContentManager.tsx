'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
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
  Square
} from 'lucide-react';

interface ContentItem {
  id: string;
  title: string;
  description?: string;
  owner_id: string;
  categories: string[];
  tags: string[];
  status?: string;
  created_at?: string;
  updated_at?: string;
  filename?: string;
  content_type?: string;
  size?: number;
  company_name?: string;
  created_by?: string;
  visibility_level?: 'private' | 'shared' | 'public';
}

interface ContentManagerProps {
  mode: 'all' | 'user' | 'review' | 'upload' | 'unified';
  showUpload?: boolean;
  showFilters?: boolean;
  showActions?: boolean;
  compactView?: boolean;
  onContentSelect?: (content: ContentItem) => void;
}

export function ContentManager({
  mode = 'all',
  showUpload = true,
  showFilters = true,
  showActions = true,
  compactView = false,
  onContentSelect
}: ContentManagerProps) {
  const { user, hasRole, hasPermission } = useAuth();
  const { loading, error, uploadFile } = useContent();
  
  const [content, setContent] = useState<ContentItem[]>([]);
  const [filteredContent, setFilteredContent] = useState<ContentItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [showUploadDialog, setShowUploadDialog] = useState(false);

  const fetchContent = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const response = await fetch('/api/content/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setContent(data.content || []);
      }
    } catch (err) {
      console.error('Failed to fetch content:', err);
    }
  }, []);

  useEffect(() => {
    fetchContent();
  }, [fetchContent]);

  useEffect(() => {
    let filtered = content || [];

    // Filter by mode
    if (mode === 'user' && user?.id) {
      filtered = filtered.filter(item => item.owner_id === user.id);
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
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'draft': return 'bg-gray-100 text-gray-800';
      default: return 'bg-blue-100 text-blue-800';
    }
  };

  const getContentTypeIcon = (contentType?: string) => {
    if (!contentType) return <FileText className="h-4 w-4" />;
    if (contentType.startsWith('image/')) return <Image className="h-4 w-4" />;
    if (contentType.startsWith('video/')) return <Video className="h-4 w-4" />;
    return <FileText className="h-4 w-4" />;
  };

  const handleContentClick = (content: ContentItem) => {
    if (onContentSelect) {
      onContentSelect(content);
    }
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
            <DialogContent className="max-w-4xl">
              <DialogHeader>
                <DialogTitle>Upload New Content</DialogTitle>
              </DialogHeader>
              {/* Upload form would go here */}
              <div className="p-4 text-center text-muted-foreground">
                Upload functionality will be integrated here
              </div>
            </DialogContent>
          </Dialog>
        )}
      </div>
    );
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
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
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
          </SelectContent>
        </Select>
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
                    <Button variant="ghost" size="sm">
                      <Edit className="h-4 w-4" />
                    </Button>
                  )}
                  {hasPermission("content", "delete") && (
                    <Button variant="ghost" size="sm">
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

  if (mode === 'unified') {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Content Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {filteredContent.filter(c => c.status === 'approved').length}
                </div>
                <div className="text-sm text-muted-foreground">Approved</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {filteredContent.filter(c => c.status === 'pending').length}
                </div>
                <div className="text-sm text-muted-foreground">Pending</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {filteredContent.filter(c => c.status === 'rejected').length}
                </div>
                <div className="text-sm text-muted-foreground">Rejected</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {renderFilters()}
        {renderContentGrid()}
      </div>
    );
  }

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
    </PageLayout>
  );
}
