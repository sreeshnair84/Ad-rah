import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/hooks/useAuth';
import { 
  PermissionGate, 
  SuperUserOnly, 
  CompanyAdminOnly, 
  ContentManagerOnly,
  ContentCreatorOnly,
  ContentApproverOnly 
} from '@/components/PermissionGate';
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
  Crown
} from 'lucide-react';

interface ContentItem {
  id: string;
  title: string;
  content_type: 'image' | 'video' | 'html5' | 'text';
  status: 'draft' | 'pending_review' | 'approved' | 'rejected' | 'archived';
  visibility_level: 'private' | 'shared' | 'public';
  company_name: string;
  created_by: string;
  created_at: string;
  file_size?: number;
  shared_with?: string[];
}

export function ContentManagementPage() {
  const { user, hasPermission, isSuperUser, getDisplayName, getRoleDisplay } = useAuth();

  // Sample content data - would come from API
  const sampleContent: ContentItem[] = [
    {
      id: '1',
      title: 'Summer Campaign Banner',
      content_type: 'image',
      status: 'approved',
      visibility_level: 'shared',
      company_name: 'Advertiser Corp',
      created_by: 'John Doe',
      created_at: '2025-09-01T10:30:00Z',
      file_size: 2048000,
      shared_with: ['Host Company A', 'Host Company B']
    },
    {
      id: '2',
      title: 'Product Demo Video',
      content_type: 'video',
      status: 'pending_review',
      visibility_level: 'private',
      company_name: 'Advertiser Corp',
      created_by: 'Jane Smith',
      created_at: '2025-09-02T14:15:00Z',
      file_size: 15360000
    },
    {
      id: '3',
      title: 'Interactive HTML5 Ad',
      content_type: 'html5',
      status: 'draft',
      visibility_level: 'private',
      company_name: 'My Company',
      created_by: 'Current User',
      created_at: '2025-09-02T16:45:00Z',
      file_size: 512000
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800';
      case 'pending_review': return 'bg-yellow-100 text-yellow-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'draft': return 'bg-gray-100 text-gray-800';
      case 'archived': return 'bg-gray-100 text-gray-600';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved': return <CheckCircle className="w-4 h-4" />;
      case 'pending_review': return <Clock className="w-4 h-4" />;
      case 'rejected': return <XCircle className="w-4 h-4" />;
      case 'draft': return <Edit className="w-4 h-4" />;
      default: return <Eye className="w-4 h-4" />;
    }
  };

  const getVisibilityIcon = (level: string) => {
    switch (level) {
      case 'shared': return <Share2 className="w-4 h-4 text-blue-600" />;
      case 'public': return <Users className="w-4 h-4 text-green-600" />;
      default: return <Building2 className="w-4 h-4 text-gray-600" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (!user) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="flex items-center justify-center py-8">
            <p className="text-muted-foreground">Please log in to access content management.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Content Management</h1>
          <p className="text-muted-foreground mt-1">
            Manage your digital signage content with enhanced RBAC controls
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          {/* User Info */}
          <div className="text-right">
            <div className="flex items-center gap-2">
              {isSuperUser() && <Crown className="w-4 h-4 text-purple-600" />}
              <span className="font-medium">{getDisplayName()}</span>
            </div>
            <span className="text-sm text-muted-foreground">{getRoleDisplay()}</span>
          </div>

          {/* Action Buttons */}
          <ContentCreatorOnly fallback={
            <Badge variant="outline" className="text-xs">
              No upload permission
            </Badge>
          }>
            <Button>
              <Upload className="w-4 h-4 mr-2" />
              Upload Content
            </Button>
          </ContentCreatorOnly>
        </div>
      </div>

      {/* Permission Overview */}
      <Card>
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

      {/* Content List */}
      <div className="grid gap-4">
        {sampleContent.map((content) => (
          <Card key={content.id} className="hover:shadow-md transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-semibold">{content.title}</h3>
                    <Badge variant="outline" className="text-xs uppercase">
                      {content.content_type}
                    </Badge>
                    <Badge className={`text-xs ${getStatusColor(content.status)}`}>
                      <span className="flex items-center gap-1">
                        {getStatusIcon(content.status)}
                        {content.status.replace('_', ' ')}
                      </span>
                    </Badge>
                  </div>

                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span>Created by {content.created_by}</span>
                    <span>•</span>
                    <span>{content.company_name}</span>
                    <span>•</span>
                    <span>{new Date(content.created_at).toLocaleDateString()}</span>
                    {content.file_size && (
                      <>
                        <span>•</span>
                        <span>{formatFileSize(content.file_size)}</span>
                      </>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    {getVisibilityIcon(content.visibility_level)}
                    <span className="text-sm capitalize">{content.visibility_level}</span>
                    {content.shared_with && content.shared_with.length > 0 && (
                      <span className="text-xs text-muted-foreground">
                        (shared with {content.shared_with.length} companies)
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {/* View Action - Available to all */}
                  <PermissionGate permission={{ resource: 'content', action: 'view' }}>
                    <Button variant="outline" size="sm">
                      <Eye className="w-4 h-4" />
                    </Button>
                  </PermissionGate>

                  {/* Edit Action - Content creators only */}
                  <PermissionGate permission={{ resource: 'content', action: 'edit' }}>
                    <Button variant="outline" size="sm">
                      <Edit className="w-4 h-4" />
                    </Button>
                  </PermissionGate>

                  {/* Approve Action - Reviewers and above */}
                  <ContentApproverOnly>
                    {content.status === 'pending_review' && (
                      <div className="flex gap-1">
                        <Button variant="outline" size="sm" className="text-green-600 hover:text-green-700">
                          <CheckCircle className="w-4 h-4" />
                        </Button>
                        <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700">
                          <XCircle className="w-4 h-4" />
                        </Button>
                      </div>
                    )}
                  </ContentApproverOnly>

                  {/* Share Action - Host companies only */}
                  <PermissionGate permission={{ resource: 'content', action: 'share' }}>
                    {content.visibility_level !== 'shared' && (
                      <Button variant="outline" size="sm">
                        <Share2 className="w-4 h-4" />
                      </Button>
                    )}
                  </PermissionGate>

                  {/* Download Action - Based on sharing permissions */}
                  <PermissionGate permission={{ resource: 'content', action: 'view' }}>
                    <Button variant="outline" size="sm">
                      <Download className="w-4 h-4" />
                    </Button>
                  </PermissionGate>

                  {/* Delete Action - Admin and content owner */}
                  <CompanyAdminOnly>
                    <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700">
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </CompanyAdminOnly>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Super User Only Section */}
      <SuperUserOnly>
        <Card className="border-purple-200 bg-purple-50/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-purple-800">
              <Crown className="w-5 h-5" />
              Super User Controls
            </CardTitle>
            <CardDescription>
              Platform-wide content management capabilities
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <Button variant="outline" className="border-purple-200 text-purple-700">
                View All Content
              </Button>
              <Button variant="outline" className="border-purple-200 text-purple-700">
                Content Analytics
              </Button>
              <Button variant="outline" className="border-purple-200 text-purple-700">
                Moderation Queue
              </Button>
              <Button variant="outline" className="border-purple-200 text-purple-700">
                System Settings
              </Button>
            </div>
          </CardContent>
        </Card>
      </SuperUserOnly>

      {/* Content Management Help */}
      <Card>
        <CardHeader>
          <CardTitle>Content Management Guide</CardTitle>
          <CardDescription>
            Understanding content permissions and sharing in the enhanced RBAC system
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold mb-2">Content Visibility Levels</h4>
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li>• <strong>Private:</strong> Only visible to your company</li>
                <li>• <strong>Shared:</strong> Shared with specific companies</li>
                <li>• <strong>Public:</strong> Visible to all (admin only)</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Role Capabilities</h4>
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li>• <strong>Viewer:</strong> View and upload content</li>
                <li>• <strong>Editor:</strong> Create and edit content</li>
                <li>• <strong>Reviewer:</strong> Approve/reject content</li>
                <li>• <strong>Admin:</strong> Full company content control</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
