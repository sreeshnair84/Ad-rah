'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/hooks/useAuth';
import {
  Eye,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  Sparkles,
  MessageSquare,
  Filter,
  Search,
  Download,
  FileImage,
  FileVideo,
  FileText,
  File,
  User,
  Calendar,
  Tag,
  Target,
  Share2,
  RefreshCw,
  ArrowRight
} from 'lucide-react';

interface PendingContent {
  id: string;
  title: string;
  filename: string;
  content_type: string;
  size: number;
  owner_id: string;
  owner_name?: string;
  company_name?: string;
  status: 'quarantine' | 'pending' | 'approved' | 'rejected';
  created_at: string;
  updated_at: string;
  priority?: 'low' | 'medium' | 'high';
  categories?: string[];
  tags?: string[];
  description?: string;
  review?: {
    id: string;
    ai_confidence: number;
    action: 'approved' | 'needs_review' | 'rejected';
    ai_analysis?: {
      reasoning: string;
      categories: string[];
      safety_scores: Record<string, number>;
      quality_score: number;
      concerns: string[];
      suggestions: string[];
      model_used: string;
      processing_time: number;
    };
    reviewer_id?: string;
    notes?: string;
  };
}

export default function ReviewQueuePage() {
  const { user, hasPermission } = useAuth();
  const [pendingContent, setPendingContent] = useState<PendingContent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedContent, setSelectedContent] = useState<PendingContent | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [reviewNotes, setReviewNotes] = useState('');
  const [isReviewDialogOpen, setIsReviewDialogOpen] = useState(false);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  // Permission check
  const canReview = hasPermission('content', 'approve');

  useEffect(() => {
    if (canReview) {
      fetchPendingContent();
    }
  }, [canReview]);

  const fetchPendingContent = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/content/admin/pending', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch pending content');
      }

      const data = await response.json();
      setPendingContent(data.pending_content || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch pending content');
      setPendingContent([]);
    } finally {
      setLoading(false);
    }
  };

  const getFileIcon = (contentType: string) => {
    if (contentType.startsWith('image/')) return <FileImage className="h-5 w-5 text-blue-500" />;
    if (contentType.startsWith('video/')) return <FileVideo className="h-5 w-5 text-purple-500" />;
    if (contentType === 'application/pdf') return <FileText className="h-5 w-5 text-red-500" />;
    return <File className="h-5 w-5 text-gray-500" />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) return `${diffDays}d ago`;
    if (diffHours > 0) return `${diffHours}h ago`;
    return 'Just now';
  };

  const getPriorityColor = (priority?: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const handleApprove = async (contentId: string) => {
    try {
      setActionInProgress(contentId);
      const token = localStorage.getItem('access_token');
      const formData = new FormData();
      formData.append('reviewer_id', user?.id || '');
      formData.append('notes', reviewNotes || 'Approved by reviewer');

      const response = await fetch(`/api/content/admin/approve/${contentId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error('Failed to approve content');
      }

      // Remove from pending list
      setPendingContent(prev => prev.filter(c => c.id !== contentId));
      setIsReviewDialogOpen(false);
      setReviewNotes('');
      setSelectedContent(null);
      
      // Show success message (you might want to add a toast notification here)
      console.log('Content approved successfully');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve content');
    } finally {
      setActionInProgress(null);
    }
  };

  const handleReject = async (contentId: string) => {
    if (!reviewNotes.trim()) {
      setError('Please provide a reason for rejection');
      return;
    }

    try {
      setActionInProgress(contentId);
      const token = localStorage.getItem('access_token');
      const formData = new FormData();
      formData.append('reviewer_id', user?.id || '');
      formData.append('notes', reviewNotes);

      const response = await fetch(`/api/content/admin/reject/${contentId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error('Failed to reject content');
      }

      // Remove from pending list
      setPendingContent(prev => prev.filter(c => c.id !== contentId));
      setIsReviewDialogOpen(false);
      setReviewNotes('');
      setSelectedContent(null);
      
      // Show success message
      console.log('Content rejected successfully');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reject content');
    } finally {
      setActionInProgress(null);
    }
  };

  const openReviewDialog = (content: PendingContent) => {
    setSelectedContent(content);
    setReviewNotes('');
    setIsReviewDialogOpen(true);
  };

  const filteredContent = pendingContent.filter(content => {
    const matchesSearch = content.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         content.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         content.owner_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         content.company_name?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'all' || content.status === statusFilter;
    const matchesPriority = priorityFilter === 'all' || content.priority === priorityFilter;

    return matchesSearch && matchesStatus && matchesPriority;
  });

  const goToOverlayCreation = (content: PendingContent) => {
    // Store the approved content ID in session storage for overlay creation
    sessionStorage.setItem('selectedContentId', content.id);
    window.location.href = '/dashboard/content-overlay';
  };

  if (!canReview) {
    return (
      <div className="flex items-center justify-center h-64">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            You don't have permission to review content. Please contact your administrator.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Loading review queue...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <Eye className="h-8 w-8 text-blue-600" />
            Content Review Queue
          </h1>
          <p className="text-gray-600 mt-1">
            Review AI-analyzed content and approve for distribution
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <Button
            onClick={fetchPendingContent}
            variant="outline"
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <div className="text-sm text-gray-600">
            {filteredContent.length} items pending review
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-64">
              <Label htmlFor="search">Search</Label>
              <div className="relative mt-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  id="search"
                  placeholder="Search by title, filename, or owner..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="status">Status</Label>
              <select
                id="status"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="mt-1 border border-gray-300 rounded-md p-2 bg-white"
              >
                <option value="all">All Statuses</option>
                <option value="quarantine">Quarantine</option>
                <option value="pending">Pending Review</option>
              </select>
            </div>
            <div>
              <Label htmlFor="priority">Priority</Label>
              <select
                id="priority"
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="mt-1 border border-gray-300 rounded-md p-2 bg-white"
              >
                <option value="all">All Priorities</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Content List */}
      <div className="space-y-4">
        {filteredContent.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Eye className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Content to Review</h3>
              <p className="text-gray-500">
                {pendingContent.length === 0 
                  ? "There's no content pending review at the moment."
                  : "No content matches your current filters."
                }
              </p>
            </CardContent>
          </Card>
        ) : (
          filteredContent.map((content) => (
            <Card key={content.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4 flex-1">
                    {/* File Icon */}
                    <div className="flex-shrink-0">
                      {getFileIcon(content.content_type)}
                    </div>

                    {/* Content Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-lg font-medium text-gray-900 truncate">
                          {content.title || content.filename}
                        </h3>
                        {content.priority && (
                          <Badge className={getPriorityColor(content.priority)}>
                            {content.priority.toUpperCase()}
                          </Badge>
                        )}
                        <Badge variant="outline">
                          <Clock className="h-3 w-3 mr-1" />
                          {getTimeAgo(content.created_at)}
                        </Badge>
                      </div>

                      <div className="flex items-center text-sm text-gray-600 mb-2 space-x-4">
                        <span className="flex items-center">
                          <User className="h-4 w-4 mr-1" />
                          {content.owner_name || 'Unknown User'}
                        </span>
                        {content.company_name && (
                          <span className="flex items-center">
                            <Target className="h-4 w-4 mr-1" />
                            {content.company_name}
                          </span>
                        )}
                        <span>{formatFileSize(content.size)}</span>
                        <span>{content.content_type}</span>
                      </div>

                      {content.description && (
                        <p className="text-sm text-gray-600 mb-3">{content.description}</p>
                      )}

                      {content.categories && content.categories.length > 0 && (
                        <div className="flex flex-wrap gap-1 mb-3">
                          {content.categories.map(category => (
                            <Badge key={category} variant="secondary" className="text-xs">
                              <Tag className="h-3 w-3 mr-1" />
                              {category}
                            </Badge>
                          ))}
                        </div>
                      )}

                      {/* AI Analysis */}
                      {content.review && (
                        <div className="bg-purple-50 rounded-lg p-3 mt-3">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium text-purple-900 flex items-center gap-2">
                              <Sparkles className="h-4 w-4" />
                              AI Analysis
                            </h4>
                            <Badge 
                              variant="outline" 
                              className={getConfidenceColor(content.review.ai_confidence)}
                            >
                              {Math.round(content.review.ai_confidence * 100)}% confidence
                            </Badge>
                          </div>
                          
                          {content.review.ai_analysis && (
                            <>
                              <p className="text-sm text-purple-800 mb-2">
                                {content.review.ai_analysis.reasoning}
                              </p>
                              
                              {content.review.ai_analysis.concerns.length > 0 && (
                                <div className="mb-2">
                                  <p className="text-xs font-medium text-red-700 mb-1">Concerns:</p>
                                  <div className="flex flex-wrap gap-1">
                                    {content.review.ai_analysis.concerns.map(concern => (
                                      <Badge key={concern} variant="destructive" className="text-xs">
                                        {concern.replace('_', ' ')}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {content.review.ai_analysis.suggestions.length > 0 && (
                                <div>
                                  <p className="text-xs font-medium text-blue-700 mb-1">Suggestions:</p>
                                  <ul className="text-xs text-blue-600 list-disc list-inside">
                                    {content.review.ai_analysis.suggestions.map(suggestion => (
                                      <li key={suggestion}>{suggestion}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </>
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex-shrink-0 space-y-2">
                    <Button
                      onClick={() => openReviewDialog(content)}
                      variant="default"
                      size="sm"
                      disabled={actionInProgress === content.id}
                    >
                      <MessageSquare className="h-4 w-4 mr-2" />
                      Review
                    </Button>
                    
                    <Button
                      onClick={() => handleApprove(content.id)}
                      variant="outline"
                      size="sm"
                      className="w-full text-green-600 hover:text-green-700 hover:bg-green-50"
                      disabled={actionInProgress === content.id}
                    >
                      <CheckCircle2 className="h-4 w-4 mr-2" />
                      Quick Approve
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Review Dialog */}
      <Dialog open={isReviewDialogOpen} onOpenChange={setIsReviewDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Review Content: {selectedContent?.title || selectedContent?.filename}</DialogTitle>
          </DialogHeader>
          
          {selectedContent && (
            <div className="space-y-4">
              {/* Content Details */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium">File:</span> {selectedContent.filename}
                  </div>
                  <div>
                    <span className="font-medium">Size:</span> {formatFileSize(selectedContent.size)}
                  </div>
                  <div>
                    <span className="font-medium">Type:</span> {selectedContent.content_type}
                  </div>
                  <div>
                    <span className="font-medium">Owner:</span> {selectedContent.owner_name || 'Unknown'}
                  </div>
                  <div className="col-span-2">
                    <span className="font-medium">Uploaded:</span> {new Date(selectedContent.created_at).toLocaleString()}
                  </div>
                  {selectedContent.description && (
                    <div className="col-span-2">
                      <span className="font-medium">Description:</span> {selectedContent.description}
                    </div>
                  )}
                </div>
              </div>

              {/* AI Analysis */}
              {selectedContent.review?.ai_analysis && (
                <div className="bg-purple-50 rounded-lg p-4">
                  <h4 className="font-medium text-purple-900 mb-2 flex items-center gap-2">
                    <Sparkles className="h-4 w-4" />
                    AI Analysis ({Math.round(selectedContent.review.ai_confidence * 100)}% confidence)
                  </h4>
                  <p className="text-sm text-purple-800 mb-3">
                    {selectedContent.review.ai_analysis.reasoning}
                  </p>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium">Quality Score:</span>{' '}
                      {Math.round(selectedContent.review.ai_analysis.quality_score * 100)}%
                    </div>
                    <div>
                      <span className="font-medium">Model Used:</span>{' '}
                      {selectedContent.review.ai_analysis.model_used}
                    </div>
                  </div>
                </div>
              )}

              {/* Review Notes */}
              <div>
                <Label htmlFor="review-notes">Review Notes</Label>
                <Textarea
                  id="review-notes"
                  placeholder="Enter your review notes..."
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  rows={4}
                  className="mt-1"
                />
              </div>

              {/* Actions */}
              <div className="flex justify-end space-x-2 pt-4 border-t">
                <Button
                  variant="outline"
                  onClick={() => setIsReviewDialogOpen(false)}
                  disabled={actionInProgress === selectedContent.id}
                >
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => handleReject(selectedContent.id)}
                  disabled={actionInProgress === selectedContent.id || !reviewNotes.trim()}
                >
                  <XCircle className="h-4 w-4 mr-2" />
                  Reject
                </Button>
                <Button
                  onClick={() => handleApprove(selectedContent.id)}
                  disabled={actionInProgress === selectedContent.id}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  Approve
                </Button>
                <Button
                  onClick={() => {
                    handleApprove(selectedContent.id);
                    setTimeout(() => goToOverlayCreation(selectedContent), 1000);
                  }}
                  disabled={actionInProgress === selectedContent.id}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Share2 className="h-4 w-4 mr-2" />
                  Approve & Create Overlay
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
