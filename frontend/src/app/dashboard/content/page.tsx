'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useContent } from '@/hooks/useContent';
import { useAuth } from '@/hooks/useAuth';
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
  Globe
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

interface FilterState {
  search: string;
  status: string;
  contentType: string;
  company: string;
  ownedBy: string;
}

export default function ContentPage() {
  const [allContent, setAllContent] = useState<ContentItem[]>([]);
  const [filteredContent, setFilteredContent] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    status: 'all',
    contentType: 'all',
    company: 'all',
    ownedBy: 'all'
  });

  const { listMetadata } = useContent();
  const { user, isSuperUser, hasPermission } = useAuth();

  useEffect(() => {
    loadContent();
  }, [user]);

  useEffect(() => {
    applyFilters();
  }, [allContent, filters]);

  const loadContent = async () => {
    if (!user?.id) return;

    try {
      setLoading(true);
      const content = await listMetadata();
      setAllContent(content);
    } catch (error) {
      console.error('Failed to load content:', error);
      setMessage({ type: 'error', text: 'Failed to load content' });
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...allContent];

    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(item => 
        item.title.toLowerCase().includes(searchLower) ||
        item.description?.toLowerCase().includes(searchLower) ||
        item.tags.some(tag => tag.toLowerCase().includes(searchLower)) ||
        item.categories.some(cat => cat.toLowerCase().includes(searchLower))
      );
    }

    // Status filter
    if (filters.status !== 'all') {
      filtered = filtered.filter(item => item.status === filters.status);
    }

    // Content type filter
    if (filters.contentType !== 'all') {
      filtered = filtered.filter(item => item.content_type === filters.contentType);
    }

    // Company filter (super users can see all companies)
    if (filters.company !== 'all' && isSuperUser()) {
      filtered = filtered.filter(item => item.company_name === filters.company);
    }

    // Ownership filter
    if (filters.ownedBy === 'mine') {
      filtered = filtered.filter(item => item.owner_id === user?.id);
    } else if (filters.ownedBy === 'company' && !isSuperUser()) {
      // Show only company content for non-super users
      filtered = filtered.filter(item => item.owner_id !== user?.id);
    }

    setFilteredContent(filtered);
  };

  const handleSubmitForReview = async (contentId: string) => {
    try {
      setSubmitting(contentId);
      setMessage(null);

      const formData = new FormData();
      formData.append('content_id', contentId);
      formData.append('owner_id', user?.id || '');

      const response = await fetch('/api/content/submit-for-review', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to submit for review');
      }

      setMessage({ type: 'success', text: 'Content submitted for review successfully' });
      await loadContent();

    } catch (error) {
      console.error('Failed to submit for review:', error);
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Failed to submit for review'
      });
    } finally {
      setSubmitting(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'quarantine':
        return <Badge variant="destructive">Quarantined</Badge>;
      case 'pending':
        return <Badge variant="secondary">Pending Review</Badge>;
      case 'approved':
        return <Badge variant="default" className="bg-green-500">Approved</Badge>;
      case 'rejected':
        return <Badge variant="destructive">Rejected</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getContentTypeIcon = (type: string) => {
    switch (type) {
      case 'image':
        return <Image className="w-4 h-4" />;
      case 'video':
        return <Video className="w-4 h-4" />;
      case 'html5':
        return <Globe className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  const canSubmitForReview = (status: string) => {
    return status === 'quarantine' && hasPermission('content', 'create');
  };

  const canEdit = (content: ContentItem) => {
    return content.owner_id === user?.id || hasPermission('content', 'edit');
  };

  const canDelete = (content: ContentItem) => {
    return content.owner_id === user?.id || hasPermission('content', 'delete');
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown size';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const uniqueCompanies = [...new Set(allContent.map(item => item.company_name).filter(Boolean))];
  const uniqueStatuses = [...new Set(allContent.map(item => item.status).filter(Boolean))];
  const uniqueContentTypes = [...new Set(allContent.map(item => item.content_type).filter(Boolean))];

  // Content statistics
  const myContentCount = allContent.filter(item => item.owner_id === user?.id).length;
  const companyContentCount = allContent.filter(item => item.owner_id !== user?.id).length;
  const totalContentCount = allContent.length;

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            {isSuperUser() && <Crown className="w-8 h-8 text-purple-600" />}
            Content Management
          </h1>
          <p className="text-gray-600 mt-1">
            {isSuperUser() 
              ? "Manage all platform content with super user privileges" 
              : "Manage your content and view company-accessible content"
            }
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <Button onClick={() => window.location.href = '/dashboard/upload'}>
            <Upload className="w-4 h-4 mr-2" />
            Upload Content
          </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">My Content</p>
                <p className="text-2xl font-bold">{myContentCount}</p>
              </div>
              <Users className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        
        {!isSuperUser() && (
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Company Content</p>
                  <p className="text-2xl font-bold">{companyContentCount}</p>
                </div>
                <Building2 className="w-8 h-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
        )}
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Accessible</p>
                <p className="text-2xl font-bold">{totalContentCount}</p>
              </div>
              <Globe className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Filtered Results</p>
                <p className="text-2xl font-bold">{filteredContent.length}</p>
              </div>
              <Filter className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Search */}
            <div className="space-y-2">
              <Label htmlFor="search">Search</Label>
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  id="search"
                  placeholder="Search content..."
                  value={filters.search}
                  onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                  className="pl-9"
                />
              </div>
            </div>

            {/* Status Filter */}
            <div className="space-y-2">
              <Label>Status</Label>
              <Select value={filters.status} onValueChange={(value) => setFilters(prev => ({ ...prev, status: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  {uniqueStatuses.map(status => (
                    <SelectItem key={status} value={status}>{status}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Content Type Filter */}
            <div className="space-y-2">
              <Label>Content Type</Label>
              <Select value={filters.contentType} onValueChange={(value) => setFilters(prev => ({ ...prev, contentType: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="All types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {uniqueContentTypes.map(type => (
                    <SelectItem key={type} value={type}>{type}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Company Filter (Super Users Only) */}
            {isSuperUser() && (
              <div className="space-y-2">
                <Label>Company</Label>
                <Select value={filters.company} onValueChange={(value) => setFilters(prev => ({ ...prev, company: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="All companies" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Companies</SelectItem>
                    {uniqueCompanies.map(company => (
                      <SelectItem key={company} value={company}>{company}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Ownership Filter */}
            <div className="space-y-2">
              <Label>Ownership</Label>
              <Select value={filters.ownedBy} onValueChange={(value) => setFilters(prev => ({ ...prev, ownedBy: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="All content" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Content</SelectItem>
                  <SelectItem value="mine">My Content</SelectItem>
                  {!isSuperUser() && <SelectItem value="company">Company Content</SelectItem>}
                </SelectContent>
              </Select>
            </div>
          </div>
          
          {/* Reset Filters */}
          <div className="mt-4">
            <Button 
              variant="outline" 
              onClick={() => setFilters({ search: '', status: 'all', contentType: 'all', company: 'all', ownedBy: 'all' })}
            >
              Reset Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Messages */}
      {message && (
        <Alert className={`mb-6 ${message.type === 'success' ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
          <AlertDescription className={message.type === 'success' ? 'text-green-800' : 'text-red-800'}>
            {message.text}
          </AlertDescription>
        </Alert>
      )}

      {/* Content List */}
      <div className="space-y-4">
        {filteredContent.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <FileText className="w-12 h-12 text-gray-400 mb-4" />
              <p className="text-gray-500 mb-4">
                {allContent.length === 0 ? 'No content found' : 'No content matches your filters'}
              </p>
              {allContent.length === 0 && (
                <Button onClick={() => window.location.href = '/dashboard/upload'}>
                  Upload Your First Content
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          filteredContent.map((content) => (
            <Card key={content.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-3">
                    {/* Title and badges */}
                    <div className="flex items-center gap-3 flex-wrap">
                      <h3 className="text-lg font-semibold">{content.title}</h3>
                      
                      <div className="flex items-center gap-2">
                        {getContentTypeIcon(content.content_type || 'unknown')}
                        <Badge variant="outline" className="text-xs uppercase">
                          {content.content_type || 'unknown'}
                        </Badge>
                      </div>
                      
                      {getStatusBadge(content.status || 'unknown')}
                      
                      {content.owner_id === user?.id && (
                        <Badge variant="secondary" className="text-xs">
                          <Users className="w-3 h-3 mr-1" />
                          Mine
                        </Badge>
                      )}
                    </div>

                    {/* Description */}
                    {content.description && (
                      <p className="text-gray-600">{content.description}</p>
                    )}

                    {/* Categories and Tags */}
                    {(content.categories.length > 0 || content.tags.length > 0) && (
                      <div className="flex flex-wrap gap-2">
                        {content.categories.map((category) => (
                          <Badge key={category} variant="outline" className="text-xs">
                            {category}
                          </Badge>
                        ))}
                        {content.tags.map((tag) => (
                          <Badge key={tag} variant="secondary" className="text-xs">
                            #{tag}
                          </Badge>
                        ))}
                      </div>
                    )}

                    {/* Metadata */}
                    <div className="flex items-center gap-4 text-sm text-gray-500 flex-wrap">
                      {content.created_at && (
                        <span>Created: {new Date(content.created_at).toLocaleDateString()}</span>
                      )}
                      {content.size && (
                        <span>Size: {formatFileSize(content.size)}</span>
                      )}
                      {content.filename && (
                        <span>File: {content.filename}</span>
                      )}
                      {isSuperUser() && content.company_name && (
                        <span className="flex items-center gap-1">
                          <Building2 className="w-3 h-3" />
                          {content.company_name}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 ml-4">
                    {/* View */}
                    <Button variant="outline" size="sm">
                      <Eye className="w-4 h-4" />
                    </Button>

                    {/* Edit (if owner or has permission) */}
                    {canEdit(content) && (
                      <Button variant="outline" size="sm">
                        <Edit className="w-4 h-4" />
                      </Button>
                    )}

                    {/* Download */}
                    <Button variant="outline" size="sm">
                      <Download className="w-4 h-4" />
                    </Button>

                    {/* Submit for Review */}
                    {canSubmitForReview(content.status || '') && (
                      <Button
                        size="sm"
                        onClick={() => handleSubmitForReview(content.id)}
                        disabled={submitting === content.id}
                      >
                        {submitting === content.id ? 'Submitting...' : 'Submit for Review'}
                      </Button>
                    )}

                    {/* Approve/Reject (if has permission) */}
                    {hasPermission('content', 'approve') && content.status === 'pending' && (
                      <div className="flex gap-1">
                        <Button variant="outline" size="sm" className="text-green-600 hover:text-green-700">
                          <CheckCircle className="w-4 h-4" />
                        </Button>
                        <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700">
                          <XCircle className="w-4 h-4" />
                        </Button>
                      </div>
                    )}

                    {/* Share (if has permission) */}
                    {hasPermission('content', 'share') && (
                      <Button variant="outline" size="sm">
                        <Share2 className="w-4 h-4" />
                      </Button>
                    )}

                    {/* Delete (if owner or has permission) */}
                    {canDelete(content) && (
                      <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}