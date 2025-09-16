'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Calendar,
  Clock,
  MapPin,
  DollarSign,
  Eye,
  Edit,
  Trash2,
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  Download,
  Filter,
  Search,
  Plus,
  CreditCard,
  FileText,
  Monitor,
  Play,
  Pause,
  MoreHorizontal,
  History,
  TrendingUp,
  Users,
  Star
} from 'lucide-react';

interface Booking {
  id: string;
  campaignId: string;
  campaignName: string;
  adSlot: {
    id: string;
    name: string;
    location: {
      name: string;
      address: string;
      city: string;
    };
    device: {
      screenSize: string;
      type: string;
    };
  };
  schedule: {
    startDate: Date;
    endDate: Date;
    timeSlots: string[];
    duration: number; // minutes
    frequency: string; // daily, weekly, etc.
  };
  pricing: {
    basePrice: number;
    totalPrice: number;
    currency: string;
    discounts: number;
  };
  status: 'pending' | 'approved' | 'rejected' | 'confirmed' | 'active' | 'completed' | 'cancelled';
  payment: {
    status: 'pending' | 'processing' | 'completed' | 'failed' | 'refunded';
    method: string;
    transactionId?: string;
    dueDate: Date;
  };
  content: {
    id: string;
    name: string;
    type: string;
    status: string;
  }[];
  performance: {
    impressions: number;
    clicks: number;
    ctr: number;
    reach: number;
  };
  hostApproval: {
    required: boolean;
    status: 'pending' | 'approved' | 'rejected';
    notes?: string;
    respondedAt?: Date;
  };
  createdAt: Date;
  lastModified: Date;
  notes?: string;
}

interface BookingFilter {
  status: string;
  campaign: string;
  dateRange: string;
  location: string;
  paymentStatus: string;
}

export default function BookingManagement() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [filteredBookings, setFilteredBookings] = useState<Booking[]>([]);
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  const [filters, setFilters] = useState<BookingFilter>({
    status: 'all',
    campaign: 'all',
    dateRange: 'all',
    location: 'all',
    paymentStatus: 'all'
  });

  // Mock data for development
  useEffect(() => {
    const mockBookings: Booking[] = [
      {
        id: '1',
        campaignId: 'camp1',
        campaignName: 'Summer Sale 2024',
        adSlot: {
          id: 'slot1',
          name: 'Main Entrance Display',
          location: {
            name: 'Downtown Shopping Mall',
            address: '123 Main St',
            city: 'Seattle'
          },
          device: {
            screenSize: '55"',
            type: 'LED Display'
          }
        },
        schedule: {
          startDate: new Date('2024-07-01'),
          endDate: new Date('2024-07-31'),
          timeSlots: ['09:00-12:00', '14:00-17:00'],
          duration: 30,
          frequency: 'daily'
        },
        pricing: {
          basePrice: 25.00,
          totalPrice: 2325.00,
          currency: 'USD',
          discounts: 175.00
        },
        status: 'active',
        payment: {
          status: 'completed',
          method: 'Credit Card',
          transactionId: 'txn_123456789',
          dueDate: new Date('2024-06-25')
        },
        content: [
          {
            id: 'content1',
            name: 'Summer Sale Hero Video',
            type: 'video',
            status: 'approved'
          }
        ],
        performance: {
          impressions: 45000,
          clicks: 1200,
          ctr: 2.67,
          reach: 32000
        },
        hostApproval: {
          required: true,
          status: 'approved',
          notes: 'Content looks great, approved for display',
          respondedAt: new Date('2024-06-20')
        },
        createdAt: new Date('2024-06-15'),
        lastModified: new Date('2024-06-20')
      },
      {
        id: '2',
        campaignId: 'camp2',
        campaignName: 'Brand Awareness Q3',
        adSlot: {
          id: 'slot2',
          name: 'Gym Entry Monitor',
          location: {
            name: 'FitLife Gymnasium',
            address: '789 Health St',
            city: 'Bellevue'
          },
          device: {
            screenSize: '43"',
            type: 'LED Display'
          }
        },
        schedule: {
          startDate: new Date('2024-08-01'),
          endDate: new Date('2024-09-30'),
          timeSlots: ['06:00-09:00', '17:00-21:00'],
          duration: 15,
          frequency: 'daily'
        },
        pricing: {
          basePrice: 15.00,
          totalPrice: 1830.00,
          currency: 'USD',
          discounts: 120.00
        },
        status: 'pending',
        payment: {
          status: 'pending',
          method: 'Bank Transfer',
          dueDate: new Date('2024-07-25')
        },
        content: [
          {
            id: 'content2',
            name: 'Brand Logo Animation',
            type: 'video',
            status: 'under_review'
          }
        ],
        performance: {
          impressions: 0,
          clicks: 0,
          ctr: 0,
          reach: 0
        },
        hostApproval: {
          required: true,
          status: 'pending',
          notes: 'Waiting for host review'
        },
        createdAt: new Date('2024-07-10'),
        lastModified: new Date('2024-07-10')
      },
      {
        id: '3',
        campaignId: 'camp1',
        campaignName: 'Summer Sale 2024',
        adSlot: {
          id: 'slot3',
          name: 'Food Court Central',
          location: {
            name: 'Metro Food Hall',
            address: '456 Broadway Ave',
            city: 'Seattle'
          },
          device: {
            screenSize: '65"',
            type: 'Interactive Display'
          }
        },
        schedule: {
          startDate: new Date('2024-06-15'),
          endDate: new Date('2024-07-15'),
          timeSlots: ['12:00-14:00', '18:00-20:00'],
          duration: 30,
          frequency: 'daily'
        },
        pricing: {
          basePrice: 20.00,
          totalPrice: 1860.00,
          currency: 'USD',
          discounts: 140.00
        },
        status: 'completed',
        payment: {
          status: 'completed',
          method: 'Credit Card',
          transactionId: 'txn_987654321',
          dueDate: new Date('2024-06-10')
        },
        content: [
          {
            id: 'content1',
            name: 'Summer Sale Hero Video',
            type: 'video',
            status: 'approved'
          }
        ],
        performance: {
          impressions: 38500,
          clicks: 1854,
          ctr: 4.82,
          reach: 28000
        },
        hostApproval: {
          required: true,
          status: 'approved',
          notes: 'Excellent performance, approved',
          respondedAt: new Date('2024-06-12')
        },
        createdAt: new Date('2024-06-05'),
        lastModified: new Date('2024-07-15')
      }
    ];

    setBookings(mockBookings);
    setFilteredBookings(mockBookings);
  }, []);

  // Filter bookings based on current filters
  useEffect(() => {
    let filtered = [...bookings];

    // Text search
    if (searchTerm) {
      filtered = filtered.filter(booking =>
        booking.campaignName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        booking.adSlot.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        booking.adSlot.location.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        booking.adSlot.location.city.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Status filter
    if (filters.status !== 'all') {
      filtered = filtered.filter(booking => booking.status === filters.status);
    }

    // Payment status filter
    if (filters.paymentStatus !== 'all') {
      filtered = filtered.filter(booking => booking.payment.status === filters.paymentStatus);
    }

    setFilteredBookings(filtered);
  }, [searchTerm, filters, bookings]);

  const getStatusColor = (status: Booking['status']) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'completed': return 'bg-blue-100 text-blue-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: Booking['status']) => {
    switch (status) {
      case 'active': return <Play className="h-3 w-3" />;
      case 'completed': return <CheckCircle className="h-3 w-3" />;
      case 'pending': return <Clock className="h-3 w-3" />;
      case 'approved': return <CheckCircle className="h-3 w-3" />;
      case 'rejected': return <XCircle className="h-3 w-3" />;
      case 'cancelled': return <XCircle className="h-3 w-3" />;
      default: return <AlertCircle className="h-3 w-3" />;
    }
  };

  const getPaymentStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'refunded': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleBookingAction = (bookingId: string, action: string) => {
    setBookings(prev =>
      prev.map(booking => {
        if (booking.id === bookingId) {
          switch (action) {
            case 'cancel':
              return { ...booking, status: 'cancelled' as const };
            case 'extend':
              // Simulate extending booking
              return {
                ...booking,
                schedule: {
                  ...booking.schedule,
                  endDate: new Date(booking.schedule.endDate.getTime() + 30 * 24 * 60 * 60 * 1000)
                }
              };
            default:
              return booking;
          }
        }
        return booking;
      })
    );
  };

  const handleViewDetails = (booking: Booking) => {
    setSelectedBooking(booking);
    setShowDetailsDialog(true);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Booking Management</h2>
          <p className="text-gray-600">Track and manage your ad slot bookings</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            New Booking
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex space-x-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search bookings..."
            className="pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <Select
          value={filters.status}
          onValueChange={(value) => setFilters(prev => ({ ...prev, status: value }))}
        >
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={filters.paymentStatus}
          onValueChange={(value) => setFilters(prev => ({ ...prev, paymentStatus: value }))}
        >
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Payment Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Payments</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="processing">Processing</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Bookings</p>
                <p className="text-2xl font-bold">{bookings.length}</p>
              </div>
              <Calendar className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Bookings</p>
                <p className="text-2xl font-bold">
                  {bookings.filter(b => b.status === 'active').length}
                </p>
              </div>
              <Play className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Spent</p>
                <p className="text-2xl font-bold">
                  ${bookings.reduce((sum, b) => sum + b.pricing.totalPrice, 0).toLocaleString()}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Performance</p>
                <p className="text-2xl font-bold">
                  {(bookings.reduce((sum, b) => sum + b.performance.ctr, 0) / bookings.length).toFixed(2)}%
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Bookings List */}
      <div className="space-y-4">
        {filteredBookings.map((booking) => (
          <Card key={booking.id} className="hover:shadow-md transition-shadow">
            <CardContent className="p-6">
              <div className="flex justify-between items-start">
                <div className="flex-1 space-y-3">
                  <div className="flex items-center space-x-3">
                    <h3 className="font-semibold text-lg">{booking.campaignName}</h3>
                    <Badge className={getStatusColor(booking.status)}>
                      {getStatusIcon(booking.status)}
                      <span className="ml-1 capitalize">{booking.status}</span>
                    </Badge>
                    <Badge className={getPaymentStatusColor(booking.payment.status)}>
                      <CreditCard className="h-3 w-3 mr-1" />
                      {booking.payment.status}
                    </Badge>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Ad Slot</p>
                      <p className="font-medium">{booking.adSlot.name}</p>
                      <p className="text-gray-500">
                        <MapPin className="h-3 w-3 inline mr-1" />
                        {booking.adSlot.location.city}
                      </p>
                    </div>
                    
                    <div>
                      <p className="text-gray-600">Schedule</p>
                      <p className="font-medium">
                        {booking.schedule.startDate.toLocaleDateString()} - {booking.schedule.endDate.toLocaleDateString()}
                      </p>
                      <p className="text-gray-500">
                        <Clock className="h-3 w-3 inline mr-1" />
                        {booking.schedule.timeSlots.length} time slots
                      </p>
                    </div>
                    
                    <div>
                      <p className="text-gray-600">Investment</p>
                      <p className="font-medium text-green-600">
                        ${booking.pricing.totalPrice.toLocaleString()}
                      </p>
                      <p className="text-gray-500">
                        {booking.pricing.discounts > 0 && (
                          <span className="text-green-600">-${booking.pricing.discounts} discount</span>
                        )}
                      </p>
                    </div>
                    
                    <div>
                      <p className="text-gray-600">Performance</p>
                      <p className="font-medium">
                        {booking.performance.impressions.toLocaleString()} impressions
                      </p>
                      <p className="text-gray-500">
                        CTR: {booking.performance.ctr.toFixed(2)}%
                      </p>
                    </div>
                  </div>

                  {/* Host Approval Status */}
                  {booking.hostApproval.required && (
                    <div className="flex items-center space-x-2 text-sm">
                      <span className="text-gray-600">Host Approval:</span>
                      <Badge className={getStatusColor(booking.hostApproval.status as any)}>
                        {booking.hostApproval.status}
                      </Badge>
                      {booking.hostApproval.notes && (
                        <span className="text-gray-500">- {booking.hostApproval.notes}</span>
                      )}
                    </div>
                  )}
                </div>

                <div className="flex space-x-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => handleViewDetails(booking)}
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    Details
                  </Button>
                  
                  {booking.status === 'pending' && (
                    <Button variant="outline" size="sm">
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                  )}
                  
                  {(booking.status === 'active' || booking.status === 'pending') && (
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleBookingAction(booking.id, 'cancel')}
                    >
                      <XCircle className="h-4 w-4 mr-2" />
                      Cancel
                    </Button>
                  )}
                  
                  <Button variant="outline" size="sm">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {filteredBookings.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <Calendar className="h-12 w-12 mx-auto text-gray-400" />
            <h3 className="text-lg font-semibold mt-4">No bookings found</h3>
            <p className="text-gray-600 mt-2">
              {searchTerm || filters.status !== 'all' 
                ? 'Try adjusting your search or filters'
                : 'Create your first booking to get started'
              }
            </p>
            {!searchTerm && filters.status === 'all' && (
              <Button className="mt-4">
                <Plus className="h-4 w-4 mr-2" />
                Create Booking
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Booking Details Dialog */}
      <Dialog open={showDetailsDialog} onOpenChange={setShowDetailsDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Booking Details</DialogTitle>
          </DialogHeader>
          
          {selectedBooking && (
            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="schedule">Schedule</TabsTrigger>
                <TabsTrigger value="content">Content</TabsTrigger>
                <TabsTrigger value="performance">Performance</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="space-y-4">
                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <Label className="text-base font-semibold">Campaign</Label>
                      <p className="text-lg">{selectedBooking.campaignName}</p>
                    </div>
                    
                    <div>
                      <Label className="text-base font-semibold">Ad Slot</Label>
                      <p className="text-lg">{selectedBooking.adSlot.name}</p>
                      <p className="text-gray-600">
                        {selectedBooking.adSlot.location.name}
                      </p>
                      <p className="text-gray-600">
                        {selectedBooking.adSlot.location.address}, {selectedBooking.adSlot.location.city}
                      </p>
                    </div>
                    
                    <div>
                      <Label className="text-base font-semibold">Device</Label>
                      <p>{selectedBooking.adSlot.device.screenSize} {selectedBooking.adSlot.device.type}</p>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <Label className="text-base font-semibold">Status</Label>
                      <div className="flex space-x-2 mt-1">
                        <Badge className={getStatusColor(selectedBooking.status)}>
                          {getStatusIcon(selectedBooking.status)}
                          <span className="ml-1 capitalize">{selectedBooking.status}</span>
                        </Badge>
                        <Badge className={getPaymentStatusColor(selectedBooking.payment.status)}>
                          {selectedBooking.payment.status}
                        </Badge>
                      </div>
                    </div>
                    
                    <div>
                      <Label className="text-base font-semibold">Investment</Label>
                      <p className="text-2xl font-bold text-green-600">
                        ${selectedBooking.pricing.totalPrice.toLocaleString()}
                      </p>
                      {selectedBooking.pricing.discounts > 0 && (
                        <p className="text-green-600">
                          Savings: ${selectedBooking.pricing.discounts}
                        </p>
                      )}
                    </div>
                    
                    <div>
                      <Label className="text-base font-semibold">Payment</Label>
                      <p>{selectedBooking.payment.method}</p>
                      {selectedBooking.payment.transactionId && (
                        <p className="text-gray-600 text-sm">
                          ID: {selectedBooking.payment.transactionId}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="schedule" className="space-y-4">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <Label className="text-base font-semibold">Campaign Duration</Label>
                    <p className="text-lg">
                      {selectedBooking.schedule.startDate.toLocaleDateString()} - {selectedBooking.schedule.endDate.toLocaleDateString()}
                    </p>
                    <p className="text-gray-600">
                      {Math.ceil((selectedBooking.schedule.endDate.getTime() - selectedBooking.schedule.startDate.getTime()) / (1000 * 60 * 60 * 24))} days
                    </p>
                  </div>
                  
                  <div>
                    <Label className="text-base font-semibold">Time Slots</Label>
                    <div className="space-y-1">
                      {selectedBooking.schedule.timeSlots.map((slot, index) => (
                        <p key={index} className="flex items-center">
                          <Clock className="h-4 w-4 mr-2" />
                          {slot}
                        </p>
                      ))}
                    </div>
                  </div>
                </div>
                
                <div>
                  <Label className="text-base font-semibold">Frequency</Label>
                  <p className="capitalize">{selectedBooking.schedule.frequency}</p>
                  <p className="text-gray-600">{selectedBooking.schedule.duration} seconds per slot</p>
                </div>
              </TabsContent>

              <TabsContent value="content" className="space-y-4">
                <div className="space-y-3">
                  {selectedBooking.content.map((content) => (
                    <Card key={content.id}>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            {content.type === 'video' ? (
                              <Video className="h-6 w-6" />
                            ) : (
                              <FileText className="h-6 w-6" />
                            )}
                            <div>
                              <p className="font-medium">{content.name}</p>
                              <p className="text-sm text-gray-600 capitalize">{content.type}</p>
                            </div>
                          </div>
                          <Badge className={getStatusColor(content.status as any)}>
                            {content.status}
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </TabsContent>

              <TabsContent value="performance" className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Card>
                    <CardContent className="p-4 text-center">
                      <Eye className="h-8 w-8 mx-auto text-blue-500" />
                      <p className="text-2xl font-bold mt-2">
                        {selectedBooking.performance.impressions.toLocaleString()}
                      </p>
                      <p className="text-sm text-gray-600">Impressions</p>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardContent className="p-4 text-center">
                      <Monitor className="h-8 w-8 mx-auto text-green-500" />
                      <p className="text-2xl font-bold mt-2">
                        {selectedBooking.performance.clicks.toLocaleString()}
                      </p>
                      <p className="text-sm text-gray-600">Clicks</p>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardContent className="p-4 text-center">
                      <TrendingUp className="h-8 w-8 mx-auto text-purple-500" />
                      <p className="text-2xl font-bold mt-2">
                        {selectedBooking.performance.ctr.toFixed(2)}%
                      </p>
                      <p className="text-sm text-gray-600">CTR</p>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardContent className="p-4 text-center">
                      <Users className="h-8 w-8 mx-auto text-orange-500" />
                      <p className="text-2xl font-bold mt-2">
                        {selectedBooking.performance.reach.toLocaleString()}
                      </p>
                      <p className="text-sm text-gray-600">Reach</p>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
            </Tabs>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}