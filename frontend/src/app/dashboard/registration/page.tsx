'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useAuth } from '@/hooks/useAuth';
import { 
  Building2, 
  Users, 
  FileText, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Upload,
  Eye,
  MessageSquare,
  Send,
  UserPlus,
  Shield,
  AlertCircle,
  Phone,
  Mail,
  MapPin,
  Globe,
  Loader2
} from 'lucide-react';

interface CompanyApplication {
  id: string;
  company_name: string;
  company_type: 'HOST' | 'ADVERTISER';
  applicant_name: string;
  applicant_email: string;
  applicant_phone: string;
  business_license: string;
  address: string;
  city: string;
  country: string;
  website?: string;
  description: string;
  status: 'pending' | 'under_review' | 'approved' | 'rejected';
  submitted_at: string;
  reviewed_at?: string;
  reviewer_id?: string;
  reviewer_notes?: string;
  documents: Record<string, string>;
  created_company_id?: string;
  created_user_id?: string;
  created_at: string;
  updated_at: string;
}

interface ApplicationStats {
  total: number;
  pending: number;
  under_review: number;
  approved: number;
  rejected: number;
  host_applications: number;
  advertiser_applications: number;
}

export default function RegistrationManagementPage() {
  const { user, hasRole } = useAuth();
  const [activeTab, setActiveTab] = useState('applications');
  const [selectedRequest, setSelectedRequest] = useState<CompanyApplication | null>(null);
  const [showReviewDialog, setShowReviewDialog] = useState(false);
  const [reviewNotes, setReviewNotes] = useState('');
  const [reviewDecision, setReviewDecision] = useState<'approved' | 'rejected'>('approved');
  
  // State for API data
  const [applications, setApplications] = useState<CompanyApplication[]>([]);
  const [stats, setStats] = useState<ApplicationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Fetch applications from API
  const fetchApplications = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/company-applications', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch applications');
      }

      const data = await response.json();
      setApplications(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch applications');
    }
  };

  // Fetch application statistics
  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/company-applications/stats/summary', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch statistics');
      }

      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  // Initial data fetch
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchApplications(), fetchStats()]);
      setLoading(false);
    };
    
    loadData();
  }, []);

  // Handle review submission
  const handleReviewSubmit = async () => {
    if (!selectedRequest) return;

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/company-applications/${selectedRequest.id}/review`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          decision: reviewDecision,
          notes: reviewNotes
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit review');
      }

      // Refresh data after successful review
      await Promise.all([fetchApplications(), fetchStats()]);
      
      setShowReviewDialog(false);
      setSelectedRequest(null);
      setReviewNotes('');
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit review');
    } finally {
      setSubmitting(false);
    }
  };

  const openReviewDialog = (request: CompanyApplication, decision: 'approved' | 'rejected') => {
    setSelectedRequest(request);
    setReviewDecision(decision);
    setReviewNotes('');
    setShowReviewDialog(true);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <Badge variant="secondary" className="gap-1"><Clock className="w-3 h-3" />Pending</Badge>;
      case 'under_review':
        return <Badge variant="default" className="gap-1"><Eye className="w-3 h-3" />Under Review</Badge>;
      case 'approved':
        return <Badge variant="default" className="gap-1 bg-green-100 text-green-800"><CheckCircle className="w-3 h-3" />Approved</Badge>;
      case 'rejected':
        return <Badge variant="destructive" className="gap-1"><XCircle className="w-3 h-3" />Rejected</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getCompanyTypeBadge = (type: string) => {
    return type === 'HOST' ? (
      <Badge variant="default" className="gap-1">
        <Building2 className="w-3 h-3" />Host
      </Badge>
    ) : (
      <Badge variant="secondary" className="gap-1">
        <Shield className="w-3 h-3" />Advertiser
      </Badge>
    );
  };

  // Check if user has admin access
  if (!hasRole('ADMIN')) {
    return (
      <div className="flex items-center justify-center h-full">
        <Alert className="max-w-md">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            You don't have permission to access registration management. Contact your administrator.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="flex items-center gap-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span className="text-gray-600">Loading applications...</span>
        </div>
      </div>
    );
  }

  const pendingCount = stats?.pending || 0;
  const underReviewCount = stats?.under_review || 0;
  const approvedCount = stats?.approved || 0;
  const rejectedCount = stats?.rejected || 0;

  return (
    <div className="p-6 space-y-6">
      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Registration Management</h1>
          <p className="text-muted-foreground">
            Review and approve Host and Advertiser company registrations
          </p>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="flex items-center p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                <Clock className="w-6 h-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{pendingCount}</p>
                <p className="text-sm text-muted-foreground">Pending Review</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <Eye className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{underReviewCount}</p>
                <p className="text-sm text-muted-foreground">Under Review</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{approvedCount}</p>
                <p className="text-sm text-muted-foreground">Approved</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                <XCircle className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{rejectedCount}</p>
                <p className="text-sm text-muted-foreground">Rejected</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="applications" className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Applications
          </TabsTrigger>
          <TabsTrigger value="approved" className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4" />
            Approved
          </TabsTrigger>
          <TabsTrigger value="rejected" className="flex items-center gap-2">
            <XCircle className="w-4 h-4" />
            Rejected
          </TabsTrigger>
        </TabsList>

        <TabsContent value="applications">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Registration Applications
              </CardTitle>
              <CardDescription>
                Review pending and ongoing registration requests
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Company</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Applicant</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Submitted</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {applications
                    .filter(r => r.status === 'pending' || r.status === 'under_review')
                    .map((request) => (
                    <TableRow key={request.id}>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium">{request.company_name}</span>
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <MapPin className="w-3 h-3" />
                            {request.city}, {request.country}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        {getCompanyTypeBadge(request.company_type)}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium">{request.applicant_name}</span>
                          <div className="flex items-center gap-1 text-sm text-muted-foreground">
                            <Mail className="w-3 h-3" />
                            {request.applicant_email}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(request.status)}
                      </TableCell>
                      <TableCell>
                        {new Date(request.submitted_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Dialog>
                            <DialogTrigger asChild>
                              <Button variant="ghost" size="sm">
                                <Eye className="w-4 h-4" />
                              </Button>
                            </DialogTrigger>
                            <DialogContent className="max-w-4xl">
                              <DialogHeader>
                                <DialogTitle>Registration Details - {request.company_name}</DialogTitle>
                                <DialogDescription>
                                  Review company registration information and documents
                                </DialogDescription>
                              </DialogHeader>
                              
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-4">
                                  <div>
                                    <h4 className="font-semibold mb-2">Company Information</h4>
                                    <div className="space-y-2 text-sm">
                                      <div className="flex items-center gap-2">
                                        <Building2 className="w-4 h-4 text-muted-foreground" />
                                        <span>{request.company_name}</span>
                                      </div>
                                      <div className="flex items-center gap-2">
                                        <MapPin className="w-4 h-4 text-muted-foreground" />
                                        <span>{request.address}, {request.city}, {request.country}</span>
                                      </div>
                                      {request.website && (
                                        <div className="flex items-center gap-2">
                                          <Globe className="w-4 h-4 text-muted-foreground" />
                                          <a href={request.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                                            {request.website}
                                          </a>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                  
                                  <div>
                                    <h4 className="font-semibold mb-2">Applicant Details</h4>
                                    <div className="space-y-2 text-sm">
                                      <div className="flex items-center gap-2">
                                        <Users className="w-4 h-4 text-muted-foreground" />
                                        <span>{request.applicant_name}</span>
                                      </div>
                                      <div className="flex items-center gap-2">
                                        <Mail className="w-4 h-4 text-muted-foreground" />
                                        <span>{request.applicant_email}</span>
                                      </div>
                                      <div className="flex items-center gap-2">
                                        <Phone className="w-4 h-4 text-muted-foreground" />
                                        <span>{request.applicant_phone}</span>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                                
                                <div className="space-y-4">
                                  <div>
                                    <h4 className="font-semibold mb-2">Business Description</h4>
                                    <p className="text-sm text-muted-foreground">{request.description}</p>
                                  </div>
                                  
                                  <div>
                                    <h4 className="font-semibold mb-2">Business License</h4>
                                    <p className="text-sm text-muted-foreground">{request.business_license}</p>
                                  </div>
                                  
                                  <div>
                                    <h4 className="font-semibold mb-2">Submitted Documents</h4>
                                    <div className="space-y-2">
                                      {Object.entries(request.documents).map(([type, filename]) => (
                                        filename && (
                                          <div key={type} className="flex items-center justify-between p-2 border rounded">
                                            <div className="flex items-center gap-2">
                                              <FileText className="w-4 h-4" />
                                              <span className="text-sm">
                                                {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}: {filename}
                                              </span>
                                            </div>
                                            <Button variant="ghost" size="sm">
                                              <Eye className="w-4 h-4" />
                                            </Button>
                                          </div>
                                        )
                                      ))}
                                    </div>
                                  </div>
                                </div>
                              </div>
                              
                              <DialogFooter>
                                <div className="flex gap-2 w-full">
                                  <Button 
                                    variant="outline" 
                                    onClick={() => openReviewDialog(request, 'rejected')}
                                    className="flex-1"
                                  >
                                    <XCircle className="w-4 h-4 mr-2" />
                                    Reject
                                  </Button>
                                  <Button 
                                    onClick={() => openReviewDialog(request, 'approved')}
                                    className="flex-1"
                                  >
                                    <CheckCircle className="w-4 h-4 mr-2" />
                                    Approve
                                  </Button>
                                </div>
                              </DialogFooter>
                            </DialogContent>
                          </Dialog>
                          
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openReviewDialog(request, 'approved')}
                          >
                            <CheckCircle className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openReviewDialog(request, 'rejected')}
                          >
                            <XCircle className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              {applications.filter(r => r.status === 'pending' || r.status === 'under_review').length === 0 && (
                <div className="text-center py-12">
                  <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No pending applications</h3>
                  <p className="text-gray-500">All applications have been reviewed</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="approved">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5" />
                Approved Companies
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Company</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Approved Date</TableHead>
                    <TableHead>Created Company ID</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {applications
                    .filter(r => r.status === 'approved')
                    .map((request) => (
                    <TableRow key={request.id}>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium">{request.company_name}</span>
                          <span className="text-sm text-muted-foreground">{request.applicant_name}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {getCompanyTypeBadge(request.company_type)}
                      </TableCell>
                      <TableCell>
                        {request.reviewed_at ? new Date(request.reviewed_at).toLocaleDateString() : '-'}
                      </TableCell>
                      <TableCell>
                        <span className="font-mono text-sm">{request.created_company_id || 'Pending'}</span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              {applications.filter(r => r.status === 'approved').length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <CheckCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No approved companies yet</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="rejected">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <XCircle className="w-5 h-5" />
                Rejected Applications
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Company</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Rejected Date</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {applications
                    .filter(r => r.status === 'rejected')
                    .map((request) => (
                    <TableRow key={request.id}>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium">{request.company_name}</span>
                          <span className="text-sm text-muted-foreground">{request.applicant_name}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {getCompanyTypeBadge(request.company_type)}
                      </TableCell>
                      <TableCell>
                        {request.reviewed_at ? new Date(request.reviewed_at).toLocaleDateString() : '-'}
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-muted-foreground">{request.reviewer_notes || 'No reason provided'}</span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              {applications.filter(r => r.status === 'rejected').length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <XCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No rejected applications</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Review Dialog */}
      <Dialog open={showReviewDialog} onOpenChange={setShowReviewDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {reviewDecision === 'approved' ? 'Approve' : 'Reject'} Registration
            </DialogTitle>
            <DialogDescription>
              {selectedRequest && `Review registration for ${selectedRequest.company_name}`}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label htmlFor="review-notes">Review Notes</Label>
              <Textarea
                id="review-notes"
                placeholder={`Enter ${reviewDecision === 'approved' ? 'approval' : 'rejection'} notes...`}
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                rows={4}
              />
            </div>
            
            {reviewDecision === 'approved' && (
              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>
                  Approving this registration will create a new company and send login credentials to the applicant.
                </AlertDescription>
              </Alert>
            )}
            
            {reviewDecision === 'rejected' && (
              <Alert variant="destructive">
                <XCircle className="h-4 w-4" />
                <AlertDescription>
                  Rejecting this registration will notify the applicant and archive the application.
                </AlertDescription>
              </Alert>
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowReviewDialog(false)} disabled={submitting}>
              Cancel
            </Button>
            <Button 
              onClick={handleReviewSubmit}
              variant={reviewDecision === 'approved' ? 'default' : 'destructive'}
              disabled={submitting}
            >
              {submitting ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : reviewDecision === 'approved' ? (
                <CheckCircle className="w-4 h-4 mr-2" />
              ) : (
                <XCircle className="w-4 h-4 mr-2" />
              )}
              {submitting ? 'Processing...' : reviewDecision === 'approved' ? 'Approve Registration' : 'Reject Application'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}