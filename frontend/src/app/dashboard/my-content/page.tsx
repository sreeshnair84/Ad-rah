'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useContent } from '@/hooks/useContent';
import { useAuth } from '@/hooks/useAuth';

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
}

export default function MyContentPage() {
  const [myContent, setMyContent] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const { listMetadata } = useContent();
  const { user } = useAuth();

  useEffect(() => {
    loadMyContent();
  }, [user]);

  const loadMyContent = async () => {
    if (!user?.id) return;

    try {
      setLoading(true);
      const allContent = await listMetadata();

      // Filter content owned by current user
      const userContent = allContent.filter(item => item.owner_id === user.id);
      setMyContent(userContent);
    } catch (error) {
      console.error('Failed to load content:', error);
      setMessage({ type: 'error', text: 'Failed to load your content' });
    } finally {
      setLoading(false);
    }
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

      // Reload content to reflect status change
      await loadMyContent();

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

  const getStatusDescription = (status: string) => {
    switch (status) {
      case 'quarantine':
        return 'Content is being scanned for security issues';
      case 'pending':
        return 'Content is waiting for Host review';
      case 'approved':
        return 'Content has been approved and is ready for display';
      case 'rejected':
        return 'Content was rejected during review';
      default:
        return 'Unknown status';
    }
  };

  const canSubmitForReview = (status: string) => {
    return status === 'quarantine'; // Only allow submission from quarantine status
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading your content...</p>
        </div>
      </div>
    );
  }

  const quarantinedContent = myContent.filter(item => item.status === 'quarantine');
  const pendingContent = myContent.filter(item => item.status === 'pending');
  const approvedContent = myContent.filter(item => item.status === 'approved');
  const rejectedContent = myContent.filter(item => item.status === 'rejected');

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6">
        <h2 className="text-3xl font-bold">My Content</h2>
        <p className="text-gray-600 mt-2">Manage your uploaded content and track review status</p>
      </div>

      {message && (
        <Alert className={`mb-6 ${message.type === 'success' ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
          <AlertDescription className={message.type === 'success' ? 'text-green-800' : 'text-red-800'}>
            {message.text}
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="all" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="all">
            All ({myContent.length})
          </TabsTrigger>
          <TabsTrigger value="quarantine">
            Quarantined ({quarantinedContent.length})
          </TabsTrigger>
          <TabsTrigger value="pending">
            Pending ({pendingContent.length})
          </TabsTrigger>
          <TabsTrigger value="approved">
            Approved ({approvedContent.length})
          </TabsTrigger>
          <TabsTrigger value="rejected">
            Rejected ({rejectedContent.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4">
          {myContent.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center h-32">
                <p className="text-gray-500 mb-4">No content uploaded yet</p>
                <Button onClick={() => window.location.href = '/dashboard/upload'}>
                  Upload Your First Content
                </Button>
              </CardContent>
            </Card>
          ) : (
            myContent.map((content) => (
              <ContentCard
                key={content.id}
                content={content}
                onSubmitForReview={handleSubmitForReview}
                submitting={submitting}
                getStatusBadge={getStatusBadge}
                getStatusDescription={getStatusDescription}
                canSubmitForReview={canSubmitForReview}
              />
            ))
          )}
        </TabsContent>

        <TabsContent value="quarantine" className="space-y-4">
          {quarantinedContent.map((content) => (
            <ContentCard
              key={content.id}
              content={content}
              onSubmitForReview={handleSubmitForReview}
              submitting={submitting}
              getStatusBadge={getStatusBadge}
              getStatusDescription={getStatusDescription}
              canSubmitForReview={canSubmitForReview}
            />
          ))}
        </TabsContent>

        <TabsContent value="pending" className="space-y-4">
          {pendingContent.map((content) => (
            <ContentCard
              key={content.id}
              content={content}
              onSubmitForReview={handleSubmitForReview}
              submitting={submitting}
              getStatusBadge={getStatusBadge}
              getStatusDescription={getStatusDescription}
              canSubmitForReview={canSubmitForReview}
            />
          ))}
        </TabsContent>

        <TabsContent value="approved" className="space-y-4">
          {approvedContent.map((content) => (
            <ContentCard
              key={content.id}
              content={content}
              onSubmitForReview={handleSubmitForReview}
              submitting={submitting}
              getStatusBadge={getStatusBadge}
              getStatusDescription={getStatusDescription}
              canSubmitForReview={canSubmitForReview}
            />
          ))}
        </TabsContent>

        <TabsContent value="rejected" className="space-y-4">
          {rejectedContent.map((content) => (
            <ContentCard
              key={content.id}
              content={content}
              onSubmitForReview={handleSubmitForReview}
              submitting={submitting}
              getStatusBadge={getStatusBadge}
              getStatusDescription={getStatusDescription}
              canSubmitForReview={canSubmitForReview}
            />
          ))}
        </TabsContent>
      </Tabs>
    </div>
  );
}

interface ContentCardProps {
  content: ContentItem;
  onSubmitForReview: (contentId: string) => void;
  submitting: string | null;
  getStatusBadge: (status: string) => React.ReactElement;
  getStatusDescription: (status: string) => string;
  canSubmitForReview: (status: string) => boolean;
}

function ContentCard({
  content,
  onSubmitForReview,
  submitting,
  getStatusBadge,
  getStatusDescription,
  canSubmitForReview
}: ContentCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="text-lg font-semibold">{content.title}</h3>
              {getStatusBadge(content.status || 'unknown')}
            </div>

            {content.description && (
              <p className="text-gray-600 mb-2">{content.description}</p>
            )}

            <div className="flex flex-wrap gap-2 mb-3">
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

            <div className="text-sm text-gray-500 mb-2">
              {getStatusDescription(content.status || 'unknown')}
            </div>

            <div className="text-sm text-gray-500">
              Uploaded: {content.created_at ? new Date(content.created_at).toLocaleDateString() : 'Unknown'}
              {content.updated_at && content.updated_at !== content.created_at && (
                <> • Updated: {new Date(content.updated_at).toLocaleDateString()}</>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-2 ml-4">
            {canSubmitForReview(content.status || 'unknown') && (
              <Button
                size="sm"
                onClick={() => onSubmitForReview(content.id)}
                disabled={submitting === content.id}
                className="whitespace-nowrap"
              >
                {submitting === content.id ? 'Submitting...' : 'Submit for Review'}
              </Button>
            )}

            <Button
              variant="outline"
              size="sm"
              onClick={() => {/* TODO: Implement edit functionality */}}
              className="whitespace-nowrap"
            >
              Edit
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
