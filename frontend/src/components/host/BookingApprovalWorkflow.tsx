'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Calendar,
  Clock,
  DollarSign,
  Users,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Eye,
  MessageSquare,
  Filter,
  Search,
  ArrowRight,
  MapPin,
  Monitor,
  Info,
  Star,
  ThumbsUp,
  ThumbsDown,
  Ban
} from 'lucide-react';

interface BookingRequest {
  id: string;
  advertiserName: string;
  advertiserEmail: string;
  companyName: string;
  campaignName: string;
  adSlotId: string;
  adSlotName: string;
  locationName: string;
  deviceName: string;
  startDate: string;
  endDate: string;
  startTime: string;
  endTime: string;
  duration: number; // hours
  totalCost: number;
  baseRate: number;
  multipliers: {
    primeTime: number;
    weekend: number;
  };
  contentDetails: {
    title: string;
    description: string;
    formats: string[];
    estimatedFileSize: number;
    hasUploaded: boolean;
  };
  targetAudience: string[];
  specialRequests: string;
  status: 'pending' | 'approved' | 'rejected' | 'requires_modification' | 'expired';
  priority: 'low' | 'medium' | 'high';
  submittedAt: string;
  reviewedAt?: string;
  reviewedBy?: string;
  reviewNotes?: string;
  autoApprovalEligible: boolean;
  conflictWarnings: string[];
  analytics: {
    estimatedImpressions: number;
    estimatedReach: number;
    competitorAnalysis: string;
  };
}

export default function BookingApprovalWorkflow() {
  const [bookingRequests, setBookingRequests] = useState<BookingRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('pending');
  const [filterPriority, setFilterPriority] = useState('all');
  const [selectedBooking, setSelectedBooking] = useState<BookingRequest | null>(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [actionType, setActionType] = useState<'approve' | 'reject' | 'modify' | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');

  useEffect(() => {
    fetchBookingRequests();
  }, []);

  const fetchBookingRequests = async () => {
    try {
      setLoading(true);
      
      const response = await fetch('/api/host/booking-requests', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setBookingRequests(data.requests || []);
      } else {
        // Mock data for development
        setBookingRequests([
          {
            id: '1',
            advertiserName: 'Sarah Johnson',
            advertiserEmail: 'sarah@techcorp.com',
            companyName: 'TechCorp Solutions',
            campaignName: 'New Product Launch Q1',
            adSlotId: '1',
            adSlotName: 'Main Entrance Banner',
            locationName: 'Downtown Shopping Mall',
            deviceName: 'Main Entrance Display',
            startDate: '2024-12-15',
            endDate: '2024-12-22',
            startTime: '09:00',
            endTime: '21:00',
            duration: 168, // 7 days * 12 hours
            totalCost: 5040.00,
            baseRate: 25,
            multipliers: {
              primeTime: 1.5,
              weekend: 1.2
            },
            contentDetails: {
              title: 'Revolutionary Cloud Platform',
              description: 'Promote our new enterprise cloud solution targeting IT professionals and business decision makers.',
              formats: ['video/mp4', 'image/png'],
              estimatedFileSize: 45,
              hasUploaded: false
            },
            targetAudience: ['business professionals', 'IT managers', 'entrepreneurs'],
            specialRequests: 'Would prefer prime time slots during lunch hours (12-2 PM) for maximum visibility.',
            status: 'pending',
            priority: 'high',
            submittedAt: '2024-12-10T10:30:00Z',
            autoApprovalEligible: true,
            conflictWarnings: [],
            analytics: {
              estimatedImpressions: 84000,
              estimatedReach: 62000,
              competitorAnalysis: 'No direct competitors in current schedule'
            }
          },
          {
            id: '2',
            advertiserName: 'Mike Chen',
            advertiserEmail: 'mike@fooddelivery.com',
            companyName: 'QuickBite Delivery',
            campaignName: 'Holiday Food Delivery Special',
            adSlotId: '2',
            adSlotName: 'Food Court Fullscreen',
            locationName: 'Downtown Shopping Mall',
            deviceName: 'Food Court Screen',
            startDate: '2024-12-20',
            endDate: '2024-12-25',
            startTime: '11:00',
            endTime: '22:00',
            duration: 66, // 6 days * 11 hours
            totalCost: 3564.00,
            baseRate: 45,
            multipliers: {
              primeTime: 1.8,
              weekend: 1.5
            },
            contentDetails: {
              title: 'Holiday Special - Free Delivery',
              description: 'Christmas promotion offering free delivery on all orders above $25.',
              formats: ['video/mp4'],
              estimatedFileSize: 78,
              hasUploaded: true
            },
            targetAudience: ['families', 'food enthusiasts', 'young professionals'],
            specialRequests: 'Content includes festive music - please ensure audio is enabled during food court hours.',
            status: 'pending',
            priority: 'medium',
            submittedAt: '2024-12-09T14:15:00Z',
            autoApprovalEligible: false,
            conflictWarnings: [
              'Overlaps with existing food vendor restrictions',
              'Christmas Day (Dec 25) may have reduced foot traffic'
            ],
            analytics: {
              estimatedImpressions: 52800,
              estimatedReach: 38000,
              competitorAnalysis: '2 competing food delivery services already scheduled'
            }
          },
          {
            id: '3',
            advertiserName: 'Elena Rodriguez',
            advertiserEmail: 'elena@fashionbrand.com',
            companyName: 'Urban Style Fashion',
            campaignName: 'Winter Collection 2024',
            adSlotId: '1',
            adSlotName: 'Main Entrance Banner',
            locationName: 'Downtown Shopping Mall',
            deviceName: 'Main Entrance Display',
            startDate: '2024-12-18',
            endDate: '2024-12-19',
            startTime: '10:00',
            endTime: '20:00',
            duration: 20, // 2 days * 10 hours
            totalCost: 600.00,
            baseRate: 25,
            multipliers: {
              primeTime: 1.5,
              weekend: 1.2
            },
            contentDetails: {
              title: 'Winter Fashion Sale - Up to 70% Off',
              description: 'High-quality fashion imagery showcasing winter collection with sale pricing.',
              formats: ['image/jpeg', 'image/png'],
              estimatedFileSize: 25,
              hasUploaded: true
            },
            targetAudience: ['fashion-conscious shoppers', 'young adults', 'women 25-45'],
            specialRequests: '',
            status: 'approved',
            priority: 'low',
            submittedAt: '2024-12-08T09:00:00Z',
            reviewedAt: '2024-12-08T15:30:00Z',
            reviewedBy: 'admin',
            reviewNotes: 'Approved - content quality excellent, good fit for location demographics.',
            autoApprovalEligible: true,
            conflictWarnings: [],
            analytics: {
              estimatedImpressions: 20000,
              estimatedReach: 15000,
              competitorAnalysis: 'Complementary to existing retail presence'
            }
          },
          {
            id: '4',
            advertiserName: 'David Park',
            advertiserEmail: 'david@cryptoexchange.com',
            companyName: 'CryptoTrade Pro',
            campaignName: 'Crypto Investment Platform',
            adSlotId: '3',
            adSlotName: 'Gate A12 Sidebar',
            locationName: 'Airport Terminal A',
            deviceName: 'Gate A12 Monitor',
            startDate: '2024-12-16',
            endDate: '2024-12-30',
            startTime: '06:00',
            endTime: '23:00',
            duration: 255, // 15 days * 17 hours
            totalCost: 12750.00,
            baseRate: 35,
            multipliers: {
              primeTime: 2.0,
              weekend: 1.1
            },
            contentDetails: {
              title: 'Secure Crypto Trading Platform',
              description: 'Investment platform advertisement targeting business travelers and tech-savvy individuals.',
              formats: ['video/mp4', 'image/png'],
              estimatedFileSize: 120,
              hasUploaded: false
            },
            targetAudience: ['business travelers', 'investors', 'tech professionals'],
            specialRequests: 'Prefer display during business hours when executive travelers are present.',
            status: 'requires_modification',
            priority: 'medium',
            submittedAt: '2024-12-07T16:45:00Z',
            reviewedAt: '2024-12-09T11:20:00Z',
            reviewedBy: 'admin',
            reviewNotes: 'Content requires modification - please remove any guarantees of returns and add required financial disclaimers.',
            autoApprovalEligible: false,
            conflictWarnings: [
              'Financial content requires additional compliance review',
              'Airport regulations restrict certain financial advertisements'
            ],
            analytics: {
              estimatedImpressions: 127500,
              estimatedReach: 95000,
              competitorAnalysis: 'No competing financial services in current schedule'
            }
          }
        ]);
      }
    } catch (error) {
      console.error('Failed to fetch booking requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBookingAction = async (bookingId: string, action: 'approve' | 'reject' | 'modify', notes: string) => {
    try {
      const response = await fetch(`/api/host/booking-requests/${bookingId}/${action}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ reviewNotes: notes })
      });

      if (response.ok) {
        await fetchBookingRequests();
        setIsDetailsOpen(false);
        setSelectedBooking(null);
        setReviewNotes('');
        setActionType(null);
      } else {
        console.error(`Failed to ${action} booking request`);
      }
    } catch (error) {
      console.error(`Error ${action}ing booking request:`, error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'requires_modification':
        return 'bg-blue-100 text-blue-800';
      case 'expired':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-orange-100 text-orange-800';
      case 'low':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-4 w-4" />;
      case 'approved':
        return <CheckCircle className="h-4 w-4" />;
      case 'rejected':
        return <XCircle className="h-4 w-4" />;
      case 'requires_modification':
        return <AlertTriangle className="h-4 w-4" />;
      case 'expired':
        return <Ban className="h-4 w-4" />;
      default:
        return <Info className="h-4 w-4" />;
    }
  };

  const filteredRequests = bookingRequests.filter(request => {
    const matchesSearch = request.campaignName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         request.advertiserName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         request.companyName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         request.adSlotName.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === 'all' || request.status === filterStatus;
    const matchesPriority = filterPriority === 'all' || request.priority === filterPriority;
    return matchesSearch && matchesStatus && matchesPriority;
  });

  const renderBookingDetails = () => {
    if (!selectedBooking) return null;

    return (
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="content">Content</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="review">Review</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h4 className="font-semibold mb-2">Advertiser Information</h4>
              <div className="space-y-1 text-sm">
                <p><span className="text-gray-500">Name:</span> {selectedBooking.advertiserName}</p>
                <p><span className="text-gray-500">Email:</span> {selectedBooking.advertiserEmail}</p>
                <p><span className="text-gray-500">Company:</span> {selectedBooking.companyName}</p>
              </div>
            </div>

            <div>
              <h4 className="font-semibold mb-2">Campaign Details</h4>
              <div className="space-y-1 text-sm">
                <p><span className="text-gray-500">Campaign:</span> {selectedBooking.campaignName}</p>
                <p><span className="text-gray-500">Status:</span> 
                  <Badge className={`ml-2 ${getStatusColor(selectedBooking.status)}`}>
                    {selectedBooking.status.replace('_', ' ')}
                  </Badge>
                </p>
                <p><span className="text-gray-500">Priority:</span> 
                  <Badge className={`ml-2 ${getPriorityColor(selectedBooking.priority)}`}>
                    {selectedBooking.priority}
                  </Badge>
                </p>
              </div>
            </div>

            <div>
              <h4 className="font-semibold mb-2">Ad Slot Information</h4>
              <div className="space-y-1 text-sm">
                <p className="flex items-center gap-1">
                  <Monitor className="h-3 w-3" />
                  {selectedBooking.adSlotName}
                </p>
                <p className="flex items-center gap-1">
                  <MapPin className="h-3 w-3" />
                  {selectedBooking.locationName}
                </p>
                <p className="text-gray-500">{selectedBooking.deviceName}</p>
              </div>
            </div>

            <div>
              <h4 className="font-semibold mb-2">Schedule & Pricing</h4>
              <div className="space-y-1 text-sm">
                <p className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {selectedBooking.startDate} to {selectedBooking.endDate}
                </p>
                <p className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {selectedBooking.startTime} - {selectedBooking.endTime}
                </p>
                <p className="flex items-center gap-1">
                  <DollarSign className="h-3 w-3" />
                  <span className="font-semibold text-green-600">
                    ${selectedBooking.totalCost.toFixed(2)}
                  </span>
                </p>
              </div>
            </div>
          </div>

          {selectedBooking.specialRequests && (
            <div>
              <h4 className="font-semibold mb-2">Special Requests</h4>
              <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
                {selectedBooking.specialRequests}
              </p>
            </div>
          )}

          {selectedBooking.conflictWarnings.length > 0 && (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <strong>Conflict Warnings:</strong>
                <ul className="list-disc list-inside mt-1">
                  {selectedBooking.conflictWarnings.map((warning, index) => (
                    <li key={index}>{warning}</li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>

        <TabsContent value="content" className="space-y-4">
          <div>
            <h4 className="font-semibold mb-2">Content Details</h4>
            <div className="space-y-3">
              <div>
                <Label>Title</Label>
                <p className="text-sm font-medium">{selectedBooking.contentDetails.title}</p>
              </div>
              
              <div>
                <Label>Description</Label>
                <p className="text-sm text-gray-700">{selectedBooking.contentDetails.description}</p>
              </div>
              
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label>Supported Formats</Label>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedBooking.contentDetails.formats.map((format, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {format}
                      </Badge>
                    ))}
                  </div>
                </div>
                
                <div>
                  <Label>File Size</Label>
                  <p className="text-sm">{selectedBooking.contentDetails.estimatedFileSize} MB</p>
                </div>
              </div>
              
              <div>
                <Label>Upload Status</Label>
                <div className="flex items-center gap-2 mt-1">
                  {selectedBooking.contentDetails.hasUploaded ? (
                    <>
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span className="text-sm text-green-600">Content uploaded</span>
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="h-4 w-4 text-orange-600" />
                      <span className="text-sm text-orange-600">Content pending upload</span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-semibold mb-2">Target Audience</h4>
            <div className="flex flex-wrap gap-1">
              {selectedBooking.targetAudience.map((audience, index) => (
                <Badge key={index} variant="outline">
                  <Users className="h-3 w-3 mr-1" />
                  {audience}
                </Badge>
              ))}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardContent className="p-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">
                    {selectedBooking.analytics.estimatedImpressions.toLocaleString()}
                  </p>
                  <p className="text-sm text-gray-600">Estimated Impressions</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600">
                    {selectedBooking.analytics.estimatedReach.toLocaleString()}
                  </p>
                  <p className="text-sm text-gray-600">Estimated Reach</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-purple-600">
                    ${(selectedBooking.totalCost / selectedBooking.analytics.estimatedImpressions * 1000).toFixed(2)}
                  </p>
                  <p className="text-sm text-gray-600">CPM</p>
                </div>
              </CardContent>
            </Card>
          </div>

          <div>
            <h4 className="font-semibold mb-2">Competitor Analysis</h4>
            <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
              {selectedBooking.analytics.competitorAnalysis}
            </p>
          </div>

          <div>
            <h4 className="font-semibold mb-2">Pricing Breakdown</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Base Rate ({selectedBooking.duration} hours):</span>
                <span>${(selectedBooking.baseRate * selectedBooking.duration).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>Prime Time Multiplier ({selectedBooking.multipliers.primeTime}x):</span>
                <span>+${((selectedBooking.baseRate * selectedBooking.duration) * (selectedBooking.multipliers.primeTime - 1)).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>Weekend Multiplier ({selectedBooking.multipliers.weekend}x):</span>
                <span>+${((selectedBooking.baseRate * selectedBooking.duration) * (selectedBooking.multipliers.weekend - 1)).toFixed(2)}</span>
              </div>
              <div className="border-t pt-2 flex justify-between font-semibold">
                <span>Total:</span>
                <span>${selectedBooking.totalCost.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="review" className="space-y-4">
          {selectedBooking.reviewedAt && (
            <div className="bg-gray-50 p-4 rounded">
              <h4 className="font-semibold mb-2">Previous Review</h4>
              <div className="space-y-1 text-sm">
                <p><span className="text-gray-500">Reviewed by:</span> {selectedBooking.reviewedBy}</p>
                <p><span className="text-gray-500">Date:</span> {new Date(selectedBooking.reviewedAt).toLocaleString()}</p>
                <p><span className="text-gray-500">Notes:</span> {selectedBooking.reviewNotes}</p>
              </div>
            </div>
          )}

          {selectedBooking.status === 'pending' && (
            <div className="space-y-4">
              <div>
                <Label htmlFor="reviewNotes">Review Notes</Label>
                <Textarea
                  id="reviewNotes"
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Add notes about your decision..."
                  rows={4}
                />
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={() => handleBookingAction(selectedBooking.id, 'approve', reviewNotes)}
                  className="gap-2 bg-green-600 hover:bg-green-700"
                >
                  <ThumbsUp className="h-4 w-4" />
                  Approve
                </Button>
                
                <Button
                  onClick={() => handleBookingAction(selectedBooking.id, 'modify', reviewNotes)}
                  variant="outline"
                  className="gap-2"
                >
                  <AlertTriangle className="h-4 w-4" />
                  Request Modification
                </Button>
                
                <Button
                  onClick={() => handleBookingAction(selectedBooking.id, 'reject', reviewNotes)}
                  variant="outline"
                  className="gap-2 text-red-600 hover:text-red-700"
                >
                  <ThumbsDown className="h-4 w-4" />
                  Reject
                </Button>
              </div>
            </div>
          )}

          {selectedBooking.autoApprovalEligible && selectedBooking.status === 'pending' && (
            <Alert>
              <Star className="h-4 w-4" />
              <AlertDescription>
                This booking request is eligible for auto-approval based on your criteria.
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>
      </Tabs>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading booking requests...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Booking Approval Workflow</h2>
        <p className="text-gray-600 mt-1">
          Review and manage advertising booking requests
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <Clock className="h-8 w-8 text-yellow-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold">
                  {bookingRequests.filter(r => r.status === 'pending').length}
                </p>
                <p className="text-sm text-gray-600">Pending Review</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <CheckCircle className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold">
                  {bookingRequests.filter(r => r.status === 'approved').length}
                </p>
                <p className="text-sm text-gray-600">Approved</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <AlertTriangle className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold">
                  {bookingRequests.filter(r => r.status === 'requires_modification').length}
                </p>
                <p className="text-sm text-gray-600">Need Changes</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <DollarSign className="h-8 w-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-2xl font-bold">
                  ${bookingRequests
                    .filter(r => r.status === 'approved')
                    .reduce((sum, r) => sum + r.totalCost, 0)
                    .toFixed(0)}
                </p>
                <p className="text-sm text-gray-600">Approved Value</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search booking requests..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="All Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
            <SelectItem value="requires_modification">Need Changes</SelectItem>
          </SelectContent>
        </Select>
        
        <Select value={filterPriority} onValueChange={setFilterPriority}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="All Priority" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Priority</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="low">Low</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Booking Requests List */}
      <div className="space-y-4">
        {filteredRequests.map((request) => (
          <Card key={request.id} className="border-0 shadow-lg hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold">{request.campaignName}</h3>
                    <Badge className={getStatusColor(request.status)}>
                      {getStatusIcon(request.status)}
                      <span className="ml-1">{request.status.replace('_', ' ')}</span>
                    </Badge>
                    <Badge className={getPriorityColor(request.priority)}>
                      {request.priority}
                    </Badge>
                    {request.autoApprovalEligible && (
                      <Badge variant="outline" className="text-blue-600">
                        <Star className="h-3 w-3 mr-1" />
                        Auto-eligible
                      </Badge>
                    )}
                  </div>
                  
                  <div className="grid gap-4 md:grid-cols-3 text-sm">
                    <div>
                      <p className="text-gray-500">Advertiser</p>
                      <p className="font-medium">{request.advertiserName}</p>
                      <p className="text-gray-600">{request.companyName}</p>
                    </div>
                    
                    <div>
                      <p className="text-gray-500">Ad Slot</p>
                      <p className="font-medium">{request.adSlotName}</p>
                      <p className="text-gray-600">{request.locationName}</p>
                    </div>
                    
                    <div>
                      <p className="text-gray-500">Schedule</p>
                      <p className="font-medium">{request.startDate} - {request.endDate}</p>
                      <p className="text-gray-600">{request.startTime} - {request.endTime}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-6 mt-4 text-sm">
                    <div className="flex items-center gap-1">
                      <DollarSign className="h-4 w-4 text-green-600" />
                      <span className="font-semibold text-green-600">
                        ${request.totalCost.toFixed(2)}
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-1">
                      <Users className="h-4 w-4 text-blue-600" />
                      <span>{request.analytics.estimatedImpressions.toLocaleString()} impressions</span>
                    </div>
                    
                    <div className="flex items-center gap-1">
                      <Calendar className="h-4 w-4 text-gray-600" />
                      <span>Submitted {new Date(request.submittedAt).toLocaleDateString()}</span>
                    </div>
                  </div>
                  
                  {request.conflictWarnings.length > 0 && (
                    <Alert className="mt-4">
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        {request.conflictWarnings.length} warning(s) require attention
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
                
                <div className="flex gap-2 ml-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedBooking(request);
                      setIsDetailsOpen(true);
                    }}
                    className="gap-1"
                  >
                    <Eye className="h-3 w-3" />
                    View Details
                  </Button>
                  
                  {request.status === 'pending' && (
                    <>
                      <Button
                        size="sm"
                        onClick={() => handleBookingAction(request.id, 'approve', '')}
                        className="gap-1 bg-green-600 hover:bg-green-700"
                      >
                        <CheckCircle className="h-3 w-3" />
                        Approve
                      </Button>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleBookingAction(request.id, 'reject', '')}
                        className="gap-1 text-red-600 hover:text-red-700"
                      >
                        <XCircle className="h-3 w-3" />
                        Reject
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredRequests.length === 0 && (
        <Card className="border-0 shadow-lg">
          <CardContent className="text-center py-12">
            <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No booking requests found</h3>
            <p className="text-gray-600">
              {searchTerm || filterStatus !== 'all' || filterPriority !== 'all'
                ? 'Try adjusting your search or filter criteria.'
                : 'New booking requests will appear here when advertisers submit them.'}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Booking Details Dialog */}
      <Dialog open={isDetailsOpen} onOpenChange={setIsDetailsOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Booking Request Details</DialogTitle>
          </DialogHeader>
          {renderBookingDetails()}
        </DialogContent>
      </Dialog>
    </div>
  );
}