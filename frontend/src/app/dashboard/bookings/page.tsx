'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { PermissionGate } from '@/components/PermissionGate';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Calendar } from '@/components/ui/calendar';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import {
  Plus,
  Calendar as CalendarIcon,
  Clock,
  DollarSign,
  MapPin,
  Monitor,
  User,
  CheckCircle,
  XCircle,
  AlertCircle,
  Eye,
  Edit,
  Filter,
  Search,
  Download,
  Play,
  Pause,
  Square,
  RefreshCw,
  TrendingUp,
  BarChart3
} from 'lucide-react';
import { format } from 'date-fns';

interface Booking {
  id: string;
  adSlotId: string;
  adSlotName: string;
  locationName: string;
  campaignId: string;
  campaignName: string;
  advertiserName: string;
  contentId: string;
  contentTitle: string;
  contentType: string;
  startDateTime: Date;
  endDateTime: Date;
  duration: number; // in minutes
  status: 'pending' | 'approved' | 'rejected' | 'scheduled' | 'playing' | 'completed' | 'cancelled';
  totalCost: number;
  pricePerHour: number;
  hostApproval: {
    status: 'pending' | 'approved' | 'rejected';
    approvedBy?: string;
    approvedAt?: Date;
    rejectionReason?: string;
  };
  contentModeration: {
    status: 'pending' | 'approved' | 'rejected' | 'requires_changes';
    moderatedBy?: string;
    moderatedAt?: Date;
    notes?: string;
  };
  playbackStats?: {
    impressions: number;
    viewTime: number;
    completionRate: number;
  };
  createdAt: Date;
  updatedAt: Date;
}

interface Campaign {
  id: string;
  name: string;
  status: 'draft' | 'active' | 'paused' | 'completed';
  totalBookings: number;
  totalSpent: number;
  totalImpressions: number;
}

export default function BookingsPage() {
  const { user, isHostCompany, isAdvertiserCompany } = useAuth();
  const [activeTab, setActiveTab] = useState('bookings');
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [dateRange, setDateRange] = useState<{ from?: Date; to?: Date }>({});
  const [showBookingDialog, setShowBookingDialog] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null);

  useEffect(() => {
    fetchBookings();
    fetchCampaigns();
  }, []);

  const fetchBookings = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/bookings', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setBookings(data.bookings || []);
      } else {
        // Mock data for demo
        setBookings([
          {
            id: 'book1',
            adSlotId: 'slot1',
            adSlotName: 'Mall Entrance - Main Display',
            locationName: 'Downtown Mall',
            campaignId: 'camp1',
            campaignName: 'Summer Sale 2024',
            advertiserName: 'TechCorp Solutions',
            contentId: 'content1',
            contentTitle: 'Summer Sale Banner',
            contentType: 'image',
            startDateTime: new Date('2024-03-20T09:00:00'),
            endDateTime: new Date('2024-03-20T11:00:00'),
            duration: 120,
            status: 'playing',
            totalCost: 50,
            pricePerHour: 25,
            hostApproval: {
              status: 'approved',
              approvedBy: 'Host Admin',
              approvedAt: new Date('2024-03-19T14:00:00')
            },
            contentModeration: {
              status: 'approved',
              moderatedBy: 'Content Moderator',
              moderatedAt: new Date('2024-03-19T15:00:00')
            },
            playbackStats: {
              impressions: 1250,
              viewTime: 15.2,
              completionRate: 87
            },
            createdAt: new Date('2024-03-19T10:00:00'),
            updatedAt: new Date()
          },
          {
            id: 'book2',
            adSlotId: 'slot2',
            adSlotName: 'Food Court - Digital Menu Board',
            locationName: 'Food Court',
            campaignId: 'camp2',
            campaignName: 'Brand Awareness Q1',
            advertiserName: 'Creative Ads Inc',
            contentId: 'content2',
            contentTitle: 'Brand Video 30s',
            contentType: 'video',
            startDateTime: new Date('2024-03-21T12:00:00'),
            endDateTime: new Date('2024-03-21T14:00:00'),
            duration: 120,
            status: 'scheduled',
            totalCost: 70,
            pricePerHour: 35,
            hostApproval: {
              status: 'approved',
              approvedBy: 'Host Admin',
              approvedAt: new Date('2024-03-20T16:00:00')
            },
            contentModeration: {
              status: 'approved',
              moderatedBy: 'Content Moderator',
              moderatedAt: new Date('2024-03-20T17:00:00')
            },
            createdAt: new Date('2024-03-20T11:00:00'),
            updatedAt: new Date()
          },
          {
            id: 'book3',
            adSlotId: 'slot1',
            adSlotName: 'Mall Entrance - Main Display',
            locationName: 'Downtown Mall',
            campaignId: 'camp3',
            campaignName: 'Product Launch',
            advertiserName: 'Digital Displays LLC',
            contentId: 'content3',
            contentTitle: 'New Product Announcement',
            contentType: 'video',
            startDateTime: new Date('2024-03-22T10:00:00'),
            endDateTime: new Date('2024-03-22T11:00:00'),
            duration: 60,
            status: 'pending',
            totalCost: 25,
            pricePerHour: 25,
            hostApproval: {
              status: 'pending'
            },
            contentModeration: {
              status: 'pending'
            },
            createdAt: new Date('2024-03-21T09:00:00'),
            updatedAt: new Date()
          }
        ]);
      }
    } catch (error) {
      console.error('Failed to fetch bookings:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCampaigns = async () => {
    try {
      const response = await fetch('/api/campaigns', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setCampaigns(data.campaigns || []);
      } else {
        // Mock data
        setCampaigns([
          {
            id: 'camp1',
            name: 'Summer Sale 2024',
            status: 'active',
            totalBookings: 5,
            totalSpent: 245,
            totalImpressions: 12500
          },
          {
            id: 'camp2',
            name: 'Brand Awareness Q1',
            status: 'active',
            totalBookings: 3,
            totalSpent: 180,
            totalImpressions: 8750
          },
          {
            id: 'camp3',
            name: 'Product Launch',
            status: 'draft',
            totalBookings: 1,
            totalSpent: 25,
            totalImpressions: 0
          }
        ]);
      }
    } catch (error) {
      console.error('Failed to fetch campaigns:', error);
    }
  };

  const filteredBookings = bookings.filter(booking => {
    const matchesSearch =
      booking.campaignName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      booking.adSlotName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      booking.advertiserName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      booking.contentTitle.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'all' || booking.status === statusFilter;

    const matchesDate = !dateRange.from || (
      booking.startDateTime >= dateRange.from &&
      (!dateRange.to || booking.startDateTime <= dateRange.to)
    );

    return matchesSearch && matchesStatus && matchesDate;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'scheduled': return 'bg-blue-100 text-blue-800';
      case 'playing': return 'bg-green-100 text-green-800 animate-pulse';
      case 'completed': return 'bg-gray-100 text-gray-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return AlertCircle;
      case 'approved':
      case 'scheduled': return CheckCircle;
      case 'rejected':
      case 'cancelled': return XCircle;
      case 'playing': return Play;
      case 'completed': return Square;
      default: return AlertCircle;
    }
  };

  const handleApproveBooking = async (bookingId: string) => {
    try {
      const response = await fetch(`/api/bookings/${bookingId}/approve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        await fetchBookings();
      }
    } catch (error) {
      console.error('Failed to approve booking:', error);
    }
  };

  const handleRejectBooking = async (bookingId: string, reason: string) => {
    try {
      const response = await fetch(`/api/bookings/${bookingId}/reject`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ reason })
      });

      if (response.ok) {
        await fetchBookings();
      }
    } catch (error) {
      console.error('Failed to reject booking:', error);
    }
  };

  const renderBookingsTab = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">
            {isHostCompany() ? 'Booking Requests' : 'My Bookings'}
          </h2>
          <p className="text-muted-foreground">
            {isHostCompany()
              ? 'Review and approve advertiser booking requests'
              : 'Manage your ad slot bookings and campaigns'
            }
          </p>
        </div>
        {isAdvertiserCompany() && (
          <Button className="gap-2">
            <Plus className="h-4 w-4" />
            New Booking
          </Button>
        )}
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search bookings..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="scheduled">Scheduled</SelectItem>
                <SelectItem value="playing">Playing</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="icon">
              <Filter className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards for Hosts */}
      {isHostCompany() && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending Requests</CardTitle>
              <AlertCircle className="h-4 w-4 text-yellow-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {bookings.filter(b => b.status === 'pending').length}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Today's Revenue</CardTitle>
              <DollarSign className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">$125</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Bookings</CardTitle>
              <Play className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {bookings.filter(b => b.status === 'playing').length}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Occupancy Rate</CardTitle>
              <BarChart3 className="h-4 w-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">78%</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Bookings List */}
      <div className="space-y-4">
        {filteredBookings.map(booking => (
          <Card key={booking.id} className="hover:shadow-md transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold">{booking.campaignName}</h3>
                    <Badge className={getStatusColor(booking.status)}>
                      <div className="flex items-center gap-1">
                        {React.createElement(getStatusIcon(booking.status), { className: "h-3 w-3" })}
                        {booking.status}
                      </div>
                    </Badge>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <User className="h-4 w-4" />
                      {booking.advertiserName}
                    </div>
                    <div className="flex items-center gap-2">
                      <MapPin className="h-4 w-4" />
                      {booking.locationName}
                    </div>
                    <div className="flex items-center gap-2">
                      <CalendarIcon className="h-4 w-4" />
                      {format(booking.startDateTime, 'MMM dd, yyyy')}
                    </div>
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      {format(booking.startDateTime, 'HH:mm')} - {format(booking.endDateTime, 'HH:mm')}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-green-600">
                    ${booking.totalCost}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    ${booking.pricePerHour}/hour
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="text-sm">
                    <span className="font-medium">Content:</span> {booking.contentTitle}
                  </div>
                  <div className="text-sm">
                    <span className="font-medium">Duration:</span> {booking.duration} minutes
                  </div>
                  {booking.playbackStats && (
                    <div className="text-sm">
                      <span className="font-medium">Impressions:</span> {booking.playbackStats.impressions.toLocaleString()}
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <PermissionGate permission={{ resource: "booking", action: "view" }}>
                    <Button variant="outline" size="sm" className="gap-1">
                      <Eye className="h-3 w-3" />
                      View Details
                    </Button>
                  </PermissionGate>

                  {isHostCompany() && booking.status === 'pending' && (
                    <>
                      <PermissionGate permission={{ resource: "booking", action: "approve" }}>
                        <Button
                          size="sm"
                          className="gap-1"
                          onClick={() => handleApproveBooking(booking.id)}
                        >
                          <CheckCircle className="h-3 w-3" />
                          Approve
                        </Button>
                      </PermissionGate>
                      <PermissionGate permission={{ resource: "booking", action: "reject" }}>
                        <Button
                          variant="destructive"
                          size="sm"
                          className="gap-1"
                          onClick={() => handleRejectBooking(booking.id, 'Rejected by host')}
                        >
                          <XCircle className="h-3 w-3" />
                          Reject
                        </Button>
                      </PermissionGate>
                    </>
                  )}

                  {isAdvertiserCompany() && ['pending', 'scheduled'].includes(booking.status) && (
                    <Button variant="outline" size="sm" className="gap-1">
                      <Edit className="h-3 w-3" />
                      Edit
                    </Button>
                  )}
                </div>
              </div>

              {/* Progress Bar for Playing Content */}
              {booking.status === 'playing' && (
                <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Currently Playing</span>
                    <span className="text-sm text-muted-foreground">
                      {Math.round((Date.now() - booking.startDateTime.getTime()) / (1000 * 60))} / {booking.duration} minutes
                    </span>
                  </div>
                  <Progress
                    value={Math.min(100, (Date.now() - booking.startDateTime.getTime()) / (booking.duration * 60 * 1000) * 100)}
                    className="h-2"
                  />
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredBookings.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <CalendarIcon className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No bookings found</h3>
            <p className="text-muted-foreground">
              {isHostCompany()
                ? 'No booking requests match your current filters'
                : 'You haven\'t made any bookings yet'
              }
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderCampaignsTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">My Campaigns</h2>
          <p className="text-muted-foreground">
            Organize your bookings into campaigns for better management
          </p>
        </div>
        <PermissionGate permission={{ resource: "campaign", action: "create" }}>
          <Button className="gap-2">
            <Plus className="h-4 w-4" />
            New Campaign
          </Button>
        </PermissionGate>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {campaigns.map(campaign => (
          <Card key={campaign.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <CardTitle className="text-lg">{campaign.name}</CardTitle>
                <Badge variant={campaign.status === 'active' ? 'default' : 'secondary'}>
                  {campaign.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold">{campaign.totalBookings}</div>
                  <div className="text-sm text-muted-foreground">Bookings</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    ${campaign.totalSpent}
                  </div>
                  <div className="text-sm text-muted-foreground">Spent</div>
                </div>
              </div>

              <div className="text-center border-t pt-4">
                <div className="text-xl font-bold">
                  {campaign.totalImpressions.toLocaleString()}
                </div>
                <div className="text-sm text-muted-foreground">Total Impressions</div>
              </div>

              <div className="flex gap-2">
                <PermissionGate permission={{ resource: "campaign", action: "view" }}>
                  <Button variant="outline" size="sm" className="flex-1 gap-1">
                    <Eye className="h-3 w-3" />
                    View
                  </Button>
                </PermissionGate>
                <PermissionGate permission={{ resource: "campaign", action: "edit" }}>
                  <Button variant="outline" size="sm" className="flex-1 gap-1">
                    <Edit className="h-3 w-3" />
                    Edit
                  </Button>
                </PermissionGate>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  return (
    <PermissionGate 
      permission={{ resource: "booking", action: "read" }}
      fallback={
        <div className="container mx-auto py-6">
          <Card>
            <CardContent className="p-6">
              <div className="text-center text-muted-foreground">
                You don't have permission to view bookings.
              </div>
            </CardContent>
          </Card>
        </div>
      }
    >
      <div className="container mx-auto py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="bookings">
              {isHostCompany() ? 'Booking Requests' : 'My Bookings'}
            </TabsTrigger>
            {isAdvertiserCompany() && (
              <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
            )}
          </TabsList>

          <TabsContent value="bookings" className="mt-6">
            {renderBookingsTab()}
          </TabsContent>

          {isAdvertiserCompany() && (
            <TabsContent value="campaigns" className="mt-6">
              {renderCampaignsTab()}
            </TabsContent>
          )}
        </Tabs>
      </div>
    </PermissionGate>
  );
}