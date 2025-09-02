'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { 
  CheckCircle, 
  XCircle, 
  Clock,
  Eye, 
  AlertTriangle,
  FileText,
  Image,
  Video,
  Download,
  Zap
} from 'lucide-react';

interface ContentItem {
  id: string;
  title?: string;
  filename: string;
  content_type: string;
  owner_id: string;
  status: string;
  size: number;
  created_at?: string;
  updated_at?: string;
  review?: {
    id: string;
    ai_confidence: number;
    action: string;
    ai_analysis?: {
      reasoning: string;
      categories: string[];
      safety_scores: Record<string, number>;
      quality_score: number;
      brand_safety_score: number;
      compliance_score: number;
      concerns: string[];
      suggestions: string[];
      model_used: string;
      processing_time: number;
    };
  };
}

interface AIAgentStatus {
  current_primary: string;
  enabled_agents: string[];
  agents: Record<string, {
    enabled: boolean;
    health?: boolean;
  }>;
}

export default function ContentReviewPage() {
  const [pendingContent, setPendingContent] = useState<ContentItem[]>([]);
  const [selectedContent, setSelectedContent] = useState<ContentItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [aiStatus, setAIStatus] = useState<AIAgentStatus | null>(null);
  const [activeTab, setActiveTab] = useState('pending');

  // Load pending content
  useEffect(() => {
    loadPendingContent();
    loadAIStatus();
  }, []);

  const loadPendingContent = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/content/admin/pending');
      if (!response.ok) throw new Error('Failed to load pending content');
      
      const data = await response.json();
      setPendingContent(data.pending_content || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load content');
    } finally {
      setLoading(false);
    }
  };

  const loadAIStatus = async () => {
    try {
      const response = await fetch('/api/moderation/agents/status');
      if (response.ok) {
        const status = await response.json();
        setAIStatus(status);
      }
    } catch (err) {
      console.error('Failed to load AI status:', err);
    }
  };

  const handleContentDecision = async (contentId: string, decision: 'approve' | 'reject') => {
    try {
      setSubmitting(true);
      const formData = new FormData();
      formData.append('decision', decision);
      formData.append('reviewer_id', 'admin'); // TODO: Get from auth context
      if (reviewNotes) {
        formData.append('notes', reviewNotes);
      }

      const response = await fetch(`/api/moderation/content/${contentId}/decision`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error(`Failed to ${decision} content`);

      // If approved, also update content status
      if (decision === 'approve') {
        const statusFormData = new FormData();
        statusFormData.append('status', 'approved');
        
        await fetch(`/api/content/${contentId}/status`, {
          method: 'PUT',
          body: statusFormData,
        });
      }

      // Reload content list
      await loadPendingContent();
      setSelectedContent(null);
      setReviewNotes('');

    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${decision} content`);
    } finally {
      setSubmitting(false);
    }
  };

  const getContentIcon = (contentType: string) => {
    if (contentType.startsWith('image/')) return <Image className="w-4 h-4" aria-label="Image content" />;
    if (contentType.startsWith('video/')) return <Video className="w-4 h-4" />;
    return <FileText className="w-4 h-4" />;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'quarantine':
        return <Badge variant="outline" className="text-yellow-600 border-yellow-600">Quarantine</Badge>;
      case 'pending':
        return <Badge variant="outline" className="text-blue-600 border-blue-600">Pending Review</Badge>;
      case 'approved':
        return <Badge variant="default" className="bg-green-600">Approved</Badge>;
      case 'rejected':
        return <Badge variant="destructive">Rejected</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const renderAIAnalysis = (analysis: NonNullable<ContentItem['review']>['ai_analysis']) => {
    if (!analysis) return null;

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label className="text-sm font-medium">Quality Score</Label>
            <div className="text-2xl font-bold text-green-600">{(analysis.quality_score * 100).toFixed(1)}%</div>
          </div>
          <div>
            <Label className="text-sm font-medium">Brand Safety</Label>
            <div className="text-2xl font-bold text-blue-600">{(analysis.brand_safety_score * 100).toFixed(1)}%</div>
          </div>
        </div>

        <div>
          <Label className="text-sm font-medium">AI Reasoning</Label>
          <p className="text-sm text-gray-600 mt-1">{analysis.reasoning}</p>
        </div>

        {analysis.concerns && analysis.concerns.length > 0 && (
          <div>
            <Label className="text-sm font-medium">Concerns</Label>
            <ul className="list-disc list-inside text-sm text-red-600 mt-1">
              {analysis.concerns.map((concern: string, idx: number) => (
                <li key={idx}>{concern}</li>
              ))}
            </ul>
          </div>
        )}

        {analysis.suggestions && analysis.suggestions.length > 0 && (
          <div>
            <Label className="text-sm font-medium">Suggestions</Label>
            <ul className="list-disc list-inside text-sm text-green-600 mt-1">
              {analysis.suggestions.map((suggestion: string, idx: number) => (
                <li key={idx}>{suggestion}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex justify-between text-xs text-gray-500">
          <span>Model: {analysis.model_used}</span>
          <span>Processing: {analysis.processing_time}ms</span>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Content Review Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Review and moderate uploaded content with AI assistance
        </p>
      </div>

      {error && (
        <Alert className="mb-6 border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      {aiStatus && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="w-5 h-5" />
              AI Moderation Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div>
                <Label className="text-sm font-medium">Primary Agent</Label>
                <div className="font-semibold text-blue-600">{aiStatus.current_primary}</div>
              </div>
              <div>
                <Label className="text-sm font-medium">Active Agents</Label>
                <div className="flex gap-2 mt-1">
                  {Object.entries(aiStatus.agents).map(([name, config]) => (
                    <Badge 
                      key={name} 
                      variant={config.enabled ? "default" : "secondary"}
                      className={config.health === false ? "bg-red-500" : ""}
                    >
                      {name}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Content List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Pending Content ({pendingContent.length})</CardTitle>
              <CardDescription>
                Content awaiting human review and approval
              </CardDescription>
            </CardHeader>
            <CardContent>
              {pendingContent.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" />
                  <p>No content pending review!</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {pendingContent.map((content) => (
                    <div 
                      key={content.id}
                      className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                        selectedContent?.id === content.id 
                          ? 'border-blue-500 bg-blue-50' 
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => setSelectedContent(content)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          {getContentIcon(content.content_type)}
                          <div>
                            <h3 className="font-medium">
                              {content.title || content.filename}
                            </h3>
                            <p className="text-sm text-gray-600">
                              {content.content_type} • {formatFileSize(content.size)}
                            </p>
                            {content.review?.ai_confidence && (
                              <div className="flex items-center gap-2 mt-1">
                                <span className="text-xs text-gray-500">AI Confidence:</span>
                                <Badge variant="outline" className="text-xs">
                                  {(content.review.ai_confidence * 100).toFixed(1)}%
                                </Badge>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          {getStatusBadge(content.status)}
                          {content.review?.action === 'needs_review' && (
                            <Badge variant="outline" className="text-orange-600 border-orange-600">
                              <Clock className="w-3 h-3 mr-1" />
                              Manual Review
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Content Details */}
        <div>
          {selectedContent ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Eye className="w-5 h-5" />
                  Review Content
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-sm font-medium">Content Details</Label>
                  <div className="mt-2 space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Filename:</span>
                      <span className="text-sm font-medium">{selectedContent.filename}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Type:</span>
                      <span className="text-sm font-medium">{selectedContent.content_type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Size:</span>
                      <span className="text-sm font-medium">{formatFileSize(selectedContent.size)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Status:</span>
                      {getStatusBadge(selectedContent.status)}
                    </div>
                  </div>
                </div>

                {selectedContent.review?.ai_analysis && (
                  <div>
                    <Label className="text-sm font-medium">AI Analysis</Label>
                    <div className="mt-2 p-3 bg-gray-50 rounded-lg">
                      {renderAIAnalysis(selectedContent.review.ai_analysis)}
                    </div>
                  </div>
                )}

                <div>
                  <Label htmlFor="reviewNotes">Review Notes</Label>
                  <Textarea
                    id="reviewNotes"
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                    placeholder="Add your review comments..."
                    className="mt-1"
                  />
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={() => handleContentDecision(selectedContent.id, 'approve')}
                    disabled={submitting}
                    className="flex-1 bg-green-600 hover:bg-green-700"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Approve
                  </Button>
                  <Button
                    onClick={() => handleContentDecision(selectedContent.id, 'reject')}
                    disabled={submitting}
                    variant="destructive"
                    className="flex-1"
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    Reject
                  </Button>
                </div>

                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => window.open(`/api/content/download/${selectedContent.id}`, '_blank')}
                >
                  <Download className="w-4 h-4 mr-2" />
                  Preview Content
                </Button>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center h-64 text-gray-500">
                <div className="text-center">
                  <Eye className="w-12 h-12 mx-auto mb-4" />
                  <p>Select content to review</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
