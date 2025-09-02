'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useModeration } from '@/hooks/useModeration';
import { useContent } from '@/hooks/useContent';
import { useAuth } from '@/hooks/useAuth';

interface ContentItem {
  id: string;
  title?: string;
  description?: string;
  owner_id: string;
  categories: string[];
  tags: string[];
  status?: string;
  created_at?: string;
  filename?: string;
  content_type?: string;
  size?: number;
  uploaded_at?: string;
  updated_at?: string;
  content_id?: string; // Sometimes returned as content_id instead of id
}

interface ReviewItem {
  id?: string;
  content_id: string;
  ai_confidence?: number;
  action: string;
  reviewer_id?: string;
  notes?: string;
  created_at?: string;
}

export default function HostReviewPage() {
  const [pendingContent, setPendingContent] = useState<ContentItem[]>([]);
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [selectedContent, setSelectedContent] = useState<ContentItem | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const { getPendingReviews, postDecisionByContentId } = useModeration();
  const { listMetadata, updateContentStatus } = useContent();
  const { user } = useAuth();

  useEffect(() => {
    loadContentAndReviews();
  }, []);

  const loadContentAndReviews = async () => {
    try {
      setLoading(true);

      // Load all content
      const allContent = await listMetadata();

      // Filter content that needs review (pending status)
      const pendingItems = allContent.filter(item => item.status === 'pending');
      setPendingContent(pendingItems);

      // Load pending reviews only
      const pendingReviews = await getPendingReviews();
      setReviews(pendingReviews);

    } catch (error) {
      console.error('Failed to load content:', error);
      setMessage({ type: 'error', text: 'Failed to load content for review' });
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (contentId: string) => {
    if (!user?.id) return;

    try {
      setActionLoading(true);
      setMessage(null);

      // Update content status
      await updateContentStatus(contentId, 'approved');

      // Post review decision
      await postDecisionByContentId(contentId, 'approve', user.id, reviewNotes || 'Approved by Host');

      setMessage({ type: 'success', text: 'Content approved successfully' });
      setReviewNotes('');
      setSelectedContent(null);

      // Reload data
      await loadContentAndReviews();

    } catch (error) {
      console.error('Failed to approve content:', error);
      setMessage({ type: 'error', text: 'Failed to approve content' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async (contentId: string) => {
    if (!user?.id) return;

    try {
      setActionLoading(true);
      setMessage(null);

      // Update content status
      await updateContentStatus(contentId, 'rejected');

      // Post review decision
      await postDecisionByContentId(contentId, 'reject', user.id, reviewNotes || 'Rejected by Host');

      setMessage({ type: 'success', text: 'Content rejected' });
      setReviewNotes('');
      setSelectedContent(null);

      // Reload data
      await loadContentAndReviews();

    } catch (error) {
      console.error('Failed to reject content:', error);
      setMessage({ type: 'error', text: 'Failed to reject content' });
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
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

  const getAIConfidenceBadge = (confidence?: number) => {
    if (!confidence) return <Badge variant="outline">No AI Score</Badge>;

    if (confidence >= 0.9) return <Badge className="bg-green-500">High Confidence</Badge>;
    if (confidence >= 0.7) return <Badge variant="secondary">Medium Confidence</Badge>;
    return <Badge variant="destructive">Low Confidence</Badge>;
  };

  const renderContentPreview = (content: any) => {
    // Get content type and filename from the content object
    const contentType = content.content_type || content.type || '';
    const filename = content.filename || content.title || '';
    
    // Generate the file URL (API serves files from /api/uploads/files/ endpoint)
    const fileUrl = content.filename ? `/api/uploads/files/${content.filename}` : null;
    
    if (!fileUrl) {
      return (
        <div className="w-32 h-24 bg-gray-100 rounded-lg flex items-center justify-center text-gray-500 text-sm">
          No Preview
        </div>
      );
    }

    // Handle different content types
    if (contentType.startsWith('image/')) {
      return (
        <div className="w-32 h-24 bg-gray-100 rounded-lg overflow-hidden">
          <img
            src={fileUrl}
            alt={content.title || 'Content preview'}
            className="w-full h-full object-cover cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => window.open(fileUrl, '_blank')}
            onError={(e) => {
              (e.target as HTMLImageElement).src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTIxIDNIMTNMMTEgMUg1QzMuOSAxIDMgMS45IDMgM1YxOUM3IDNIOSM4IDEgMjEgM0MyMi4xIDMgMjMgMy45IDIzIDVWMTlDMjMgMjAuMSAyMi4xIDIxIDIxIDIxWiIgc3Ryb2tlPSIjNjY2IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K';
            }}
          />
        </div>
      );
    }
    
    if (contentType.startsWith('video/')) {
      return (
        <div className="w-32 h-24 bg-gray-100 rounded-lg overflow-hidden">
          <video
            src={fileUrl}
            className="w-full h-full object-cover cursor-pointer hover:opacity-80 transition-opacity"
            controls={false}
            muted
            onClick={() => window.open(fileUrl, '_blank')}
          />
        </div>
      );
    }
    
    if (contentType.startsWith('text/') || contentType === 'application/json') {
      return (
        <div className="w-32 h-24 bg-blue-50 rounded-lg flex items-center justify-center border-2 border-dashed border-blue-200 cursor-pointer hover:bg-blue-100 transition-colors"
             onClick={() => window.open(fileUrl, '_blank')}>
          <div className="text-center">
            <div className="text-blue-600 text-xs font-semibold">TEXT</div>
            <div className="text-blue-500 text-xs">{filename.split('.').pop()?.toUpperCase()}</div>
          </div>
        </div>
      );
    }
    
    // Default for other file types
    return (
      <div className="w-32 h-24 bg-gray-100 rounded-lg flex items-center justify-center border-2 border-dashed border-gray-300 cursor-pointer hover:bg-gray-200 transition-colors"
           onClick={() => window.open(fileUrl, '_blank')}>
        <div className="text-center">
          <div className="text-gray-600 text-xs font-semibold">FILE</div>
          <div className="text-gray-500 text-xs">{filename.split('.').pop()?.toUpperCase()}</div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading content for review...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6">
        <h2 className="text-3xl font-bold">Content Review Dashboard</h2>
        <p className="text-gray-600 mt-2">Review and approve content submissions from advertisers</p>
      </div>

      {message && (
        <Alert className={`mb-6 ${message.type === 'success' ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
          <AlertDescription className={message.type === 'success' ? 'text-green-800' : 'text-red-800'}>
            {message.text}
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="pending" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="pending">
            Pending Review ({pendingContent.length})
          </TabsTrigger>
          <TabsTrigger value="reviewed">
            Reviewed Today ({reviews.filter(r => {
              const today = new Date().toDateString();
              return r.created_at && new Date(r.created_at).toDateString() === today;
            }).length})
          </TabsTrigger>
          <TabsTrigger value="all">
            All Content ({pendingContent.length + reviews.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="pending" className="space-y-4">
          {pendingContent.length === 0 ? (
            <Card>
              <CardContent className="flex items-center justify-center h-32">
                <p className="text-gray-500">No content pending review</p>
              </CardContent>
            </Card>
          ) : (
            pendingContent.map((content) => (
              <Card key={content.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    {/* Content Preview */}
                    <div className="flex-shrink-0">
                      {renderContentPreview(content)}
                    </div>
                    
                    {/* Content Details */}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-lg font-semibold">{content.title || content.filename || 'Untitled Content'}</h3>
                        {getStatusBadge(content.status || 'unknown')}
                      </div>

                      {content.description && (
                        <p className="text-gray-600 mb-2">{content.description}</p>
                      )}
                      
                      {/* File info */}
                      {content.filename && (
                        <div className="text-sm text-gray-500 mb-2">
                          <span className="font-medium">File:</span> {content.filename}
                          {content.content_type && (
                            <span className="ml-2">({content.content_type})</span>
                          )}
                          {content.size && (
                            <span className="ml-2">• {(content.size / 1024).toFixed(1)} KB</span>
                          )}
                        </div>
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

                      <div className="text-sm text-gray-500">
                        Submitted: {content.created_at ? new Date(content.created_at).toLocaleDateString() : 'Unknown'}
                      </div>
                    </div>

                    <div className="flex gap-2 ml-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSelectedContent(content)}
                        disabled={actionLoading}
                      >
                        Review
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => handleApprove(content.id)}
                        disabled={actionLoading}
                        className="bg-green-600 hover:bg-green-700"
                      >
                        Quick Approve
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="reviewed" className="space-y-4">
          {reviews
            .filter(r => {
              const today = new Date().toDateString();
              return r.created_at && new Date(r.created_at).toDateString() === today;
            })
            .map((review) => {
              const content = pendingContent.find(c => c.id === review.content_id);
              return (
                <Card key={review.id}>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold">{content?.title || `Content ${review.content_id}`}</h3>
                        <div className="flex items-center gap-2 mt-1">
                          {getAIConfidenceBadge(review.ai_confidence)}
                          <Badge variant={review.action.includes('approve') ? 'default' : 'destructive'}>
                            {review.action}
                          </Badge>
                        </div>
                        {review.notes && (
                          <p className="text-sm text-gray-600 mt-1">{review.notes}</p>
                        )}
                      </div>
                      <div className="text-sm text-gray-500">
                        {review.created_at ? new Date(review.created_at).toLocaleTimeString() : 'Unknown time'}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
        </TabsContent>

        <TabsContent value="all" className="space-y-4">
          {/* Combined view of all content and reviews */}
          <div className="grid gap-4">
            {[...pendingContent, ...reviews.map(r => ({ ...r, type: 'review' as const }))].map((item) => (
              <Card key={item.id}>
                <CardContent className="p-4">
                  <div className="text-sm">
                    {'type' in item && item.type === 'review' ? 'Review' : 'Content'}: {'title' in item ? item.title || item.content_id : item.content_id}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      {/* Review Modal/Dialog */}
      {selectedContent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>Review Content: {selectedContent.title || selectedContent.filename || 'Untitled Content'}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-medium mb-2">Content Details</h4>
                <p className="text-sm text-gray-600 mb-2">{selectedContent.description}</p>
                <div className="flex flex-wrap gap-2">
                  {selectedContent.categories.map((category) => (
                    <Badge key={category} variant="outline">{category}</Badge>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Review Notes</label>
                <Textarea
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Add notes about your review decision..."
                  rows={3}
                />
              </div>

              <div className="flex gap-2 justify-end">
                <Button
                  variant="outline"
                  onClick={() => setSelectedContent(null)}
                  disabled={actionLoading}
                >
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => handleReject(selectedContent.id)}
                  disabled={actionLoading}
                >
                  {actionLoading ? 'Processing...' : 'Reject'}
                </Button>
                <Button
                  onClick={() => handleApprove(selectedContent.id)}
                  disabled={actionLoading}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {actionLoading ? 'Processing...' : 'Approve'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
