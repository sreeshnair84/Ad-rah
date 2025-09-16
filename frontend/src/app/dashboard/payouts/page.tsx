'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { PermissionGate } from '@/components/PermissionGate';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import {
  Wallet,
  DollarSign,
  Calendar,
  Receipt,
  Building2,
  TrendingUp,
  Download,
  Eye,
  Search,
  CheckCircle,
  Clock,
  AlertCircle
} from 'lucide-react';
import { format } from 'date-fns';

interface Payout {
  id: string;
  payoutPeriod: {
    start: Date;
    end: Date;
  };
  status: 'pending' | 'processing' | 'completed' | 'failed';
  totalRevenue: number;
  platformFee: number;
  hostShare: number;
  payoutAmount: number;
  bookingsCount: number;
  paymentMethod: string;
  bankDetails: {
    accountName: string;
    accountNumber: string;
    routingNumber: string;
  };
  processedAt?: Date;
  notes?: string;
  createdAt: Date;
}

export default function PayoutsPage() {
  const { user, isHostCompany } = useAuth();
  const [payouts, setPayouts] = useState<Payout[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    fetchPayouts();
  }, []);

  const fetchPayouts = async () => {
    try {
      setLoading(true);
      // Mock data for demo
      setPayouts([
        {
          id: '1',
          payoutPeriod: {
            start: new Date('2024-05-01'),
            end: new Date('2024-05-31')
          },
          status: 'completed',
          totalRevenue: 3500,
          platformFee: 1050,
          hostShare: 2450,
          payoutAmount: 2450,
          bookingsCount: 18,
          paymentMethod: 'Bank Transfer',
          bankDetails: {
            accountName: 'Downtown Mall LLC',
            accountNumber: '****1234',
            routingNumber: '****5678'
          },
          processedAt: new Date('2024-06-05'),
          createdAt: new Date('2024-06-01')
        },
        {
          id: '2',
          payoutPeriod: {
            start: new Date('2024-06-01'),
            end: new Date('2024-06-30')
          },
          status: 'pending',
          totalRevenue: 4200,
          platformFee: 1260,
          hostShare: 2940,
          payoutAmount: 2940,
          bookingsCount: 22,
          paymentMethod: 'Bank Transfer',
          bankDetails: {
            accountName: 'Downtown Mall LLC',
            accountNumber: '****1234',
            routingNumber: '****5678'
          },
          createdAt: new Date('2024-07-01')
        },
        {
          id: '3',
          payoutPeriod: {
            start: new Date('2024-07-01'),
            end: new Date('2024-07-31')
          },
          status: 'processing',
          totalRevenue: 2800,
          platformFee: 840,
          hostShare: 1960,
          payoutAmount: 1960,
          bookingsCount: 15,
          paymentMethod: 'Bank Transfer',
          bankDetails: {
            accountName: 'Downtown Mall LLC',
            accountNumber: '****1234',
            routingNumber: '****5678'
          },
          createdAt: new Date('2024-08-01')
        }
      ]);
    } catch (error) {
      console.error('Failed to fetch payouts:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return CheckCircle;
      case 'failed': return AlertCircle;
      default: return Clock;
    }
  };

  const filteredPayouts = payouts.filter(payout => {
    const matchesSearch = payout.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || payout.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const totalStats = payouts.reduce((acc, payout) => ({
    totalRevenue: acc.totalRevenue + payout.totalRevenue,
    totalPayout: acc.totalPayout + payout.payoutAmount,
    totalBookings: acc.totalBookings + payout.bookingsCount,
    pendingAmount: acc.pendingAmount + (payout.status === 'pending' ? payout.payoutAmount : 0)
  }), { totalRevenue: 0, totalPayout: 0, totalBookings: 0, pendingAmount: 0 });

  return (
    <PermissionGate permission={{ resource: "payouts", action: "read" }}>
      <div className="container mx-auto py-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold">Payouts</h2>
            <p className="text-muted-foreground">
              Your revenue sharing and payout history
            </p>
          </div>
        </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Earnings</CardTitle>
            <DollarSign className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              ${totalStats.totalPayout.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Payouts</CardTitle>
            <Wallet className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              ${totalStats.pendingAmount.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">Awaiting processing</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Revenue Generated</CardTitle>
            <TrendingUp className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${totalStats.totalRevenue.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">70% share to you</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Bookings</CardTitle>
            <Receipt className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {totalStats.totalBookings}
            </div>
            <p className="text-xs text-muted-foreground">Completed bookings</p>
          </CardContent>
        </Card>
      </div>

      {/* Revenue Share Info */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Revenue Sharing Model</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">100%</div>
              <div className="text-sm text-muted-foreground">Total Revenue</div>
            </div>
            <div className="p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">30%</div>
              <div className="text-sm text-muted-foreground">Platform Fee</div>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">70%</div>
              <div className="text-sm text-muted-foreground">Your Share</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search payouts..."
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
                <SelectItem value="processing">Processing</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Payouts List */}
      <div className="space-y-4">
        {filteredPayouts.map(payout => (
          <Card key={payout.id} className="hover:shadow-lg transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold">
                      Payout #{payout.id}
                    </h3>
                    <Badge className={getStatusColor(payout.status)}>
                      <div className="flex items-center gap-1">
                        {React.createElement(getStatusIcon(payout.status), { className: "h-3 w-3" })}
                        {payout.status}
                      </div>
                    </Badge>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      {format(payout.payoutPeriod.start, 'MMM dd')} - {format(payout.payoutPeriod.end, 'MMM dd, yyyy')}
                    </div>
                    <div className="flex items-center gap-2">
                      <Receipt className="h-4 w-4" />
                      {payout.bookingsCount} bookings
                    </div>
                    <div className="flex items-center gap-2">
                      <Building2 className="h-4 w-4" />
                      {payout.paymentMethod}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-green-600">
                    ${payout.payoutAmount.toLocaleString()}
                  </div>
                  {payout.processedAt && (
                    <div className="text-sm text-muted-foreground">
                      Paid on {format(payout.processedAt, 'MMM dd, yyyy')}
                    </div>
                  )}
                </div>
              </div>

              {/* Revenue Breakdown */}
              <div className="border-t pt-4 mb-4">
                <h4 className="text-sm font-medium mb-3">Revenue Breakdown</h4>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div className="text-center p-3 bg-gray-50 rounded">
                    <div className="text-lg font-bold">${payout.totalRevenue.toLocaleString()}</div>
                    <div className="text-muted-foreground">Total Revenue</div>
                  </div>
                  <div className="text-center p-3 bg-red-50 rounded">
                    <div className="text-lg font-bold text-red-600">-${payout.platformFee.toLocaleString()}</div>
                    <div className="text-muted-foreground">Platform Fee (30%)</div>
                  </div>
                  <div className="text-center p-3 bg-green-50 rounded">
                    <div className="text-lg font-bold text-green-600">${payout.hostShare.toLocaleString()}</div>
                    <div className="text-muted-foreground">Your Share (70%)</div>
                  </div>
                </div>
              </div>

              {/* Bank Details */}
              <div className="border-t pt-4 mb-4">
                <h4 className="text-sm font-medium mb-2">Payment Details</h4>
                <div className="text-sm text-muted-foreground">
                  <div>Account: {payout.bankDetails.accountName}</div>
                  <div>Ending in: {payout.bankDetails.accountNumber}</div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-end gap-2 pt-4 border-t">
                <PermissionGate permission={{ resource: "payouts", action: "read" }}>
                  <Button variant="outline" size="sm" className="gap-1">
                    <Eye className="h-3 w-3" />
                    View Details
                  </Button>
                </PermissionGate>
                <PermissionGate permission={{ resource: "payouts", action: "export" }}>
                  <Button variant="outline" size="sm" className="gap-1">
                    <Download className="h-3 w-3" />
                    Download Report
                  </Button>
                </PermissionGate>
                {payout.status === 'pending' && (
                  <PermissionGate permission={{ resource: "payouts", action: "request" }}>
                    <Button size="sm" className="gap-1">
                      <Wallet className="h-3 w-3" />
                      Request Payout
                    </Button>
                  </PermissionGate>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredPayouts.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <Wallet className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No payouts found</h3>
            <p className="text-muted-foreground">
              Payouts will appear here once you start earning revenue
            </p>
          </CardContent>
        </Card>
      )}
    </div>
    </PermissionGate>
  );
}