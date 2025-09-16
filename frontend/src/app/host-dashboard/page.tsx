'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  MapPin,
  Monitor,
  Calendar,
  DollarSign,
  Eye,
  CheckCircle,
  Clock,
  XCircle,
  TrendingUp,
  Users,
  Activity,
  Settings,
  Plus,
  Filter,
  Download,
  RefreshCw,
  Bell
} from 'lucide-react';

// Import host dashboard components
import LocationManagement from '@/components/host/LocationManagement';
import AdSlotConfiguration from '@/components/host/AdSlotConfiguration';
import BookingApprovalWorkflow from '@/components/host/BookingApprovalWorkflow';
import RevenueAnalytics from '@/components/host/RevenueAnalytics';
import DeviceMonitoring from '@/components/host/DeviceMonitoring';

interface DashboardStats {
  locations: number;
  totalSlots: number;
  activeSlots: number;
  pendingBookings: number;
  monthlyRevenue: number;
  totalDevices: number;
  onlineDevices: number;
  approvalRate: number;
  revenueGrowth: number;
}

interface RecentActivity {
  id: string;
  type: 'booking' | 'payment' | 'device' | 'approval';
  title: string;
  description: string;
  timestamp: string;
  status: 'success' | 'pending' | 'error';
}

export default function HostDashboardPage() {
  const { user, hasRole } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats>({
    locations: 0,
    totalSlots: 0,
    activeSlots: 0,
    pendingBookings: 0,
    monthlyRevenue: 0,
    totalDevices: 0,
    onlineDevices: 0,
    approvalRate: 0,
    revenueGrowth: 0
  });
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch dashboard statistics
      const statsResponse = await fetch('/api/host/dashboard/stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      } else {
        // Mock data for development
        setStats({
          locations: 8,
          totalSlots: 24,
          activeSlots: 18,
          pendingBookings: 5,
          monthlyRevenue: 12450.50,
          totalDevices: 24,
          onlineDevices: 22,
          approvalRate: 87.5,
          revenueGrowth: 15.3
        });
      }

      // Fetch recent activity
      const activityResponse = await fetch('/api/host/recent-activity', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (activityResponse.ok) {
        const activityData = await activityResponse.json();
        setRecentActivity(activityData);
      } else {
        // Mock data for development
        setRecentActivity([
          {
            id: '1',
            type: 'booking',
            title: 'New Booking Request',
            description: 'TechCorp wants to book Prime Mall Entrance for Dec 15-20',
            timestamp: '5 minutes ago',
            status: 'pending'
          },
          {
            id: '2',
            type: 'payment',
            title: 'Payment Received',
            description: '$2,450.00 from FashionBrand for November campaign',
            timestamp: '1 hour ago',
            status: 'success'
          },
          {
            id: '3',
            type: 'device',
            title: 'Device Back Online',
            description: 'Shopping Center Screen #3 reconnected',
            timestamp: '2 hours ago',
            status: 'success'
          },
          {
            id: '4',
            type: 'approval',
            title: 'Content Approved',
            description: 'Holiday Sale advertisement cleared moderation',
            timestamp: '3 hours ago',
            status: 'success'
          }
        ]);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'booking':
        return Calendar;
      case 'payment':
        return DollarSign;
      case 'device':
        return Monitor;
      case 'approval':
        return CheckCircle;
      default:
        return Activity;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'text-green-600 bg-green-100';
      case 'pending':
        return 'text-amber-600 bg-amber-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.first_name || 'Host'}!
          </h1>
          <p className="text-gray-600 mt-1">
            Manage your digital signage locations and ad slot bookings
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchDashboardData}
            disabled={loading}
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button className="gap-2">
            <Plus className="h-4 w-4" />
            Add Location
          </Button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {/* Locations Card */}
        <Card className="border-0 shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Active Locations</CardTitle>
            <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600">
              <MapPin className="h-5 w-5 text-white" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">{stats.locations}</div>
            <p className="text-sm text-gray-500 mt-1">Operational venues</p>
          </CardContent>
        </Card>

        {/* Ad Slots Card */}
        <Card className="border-0 shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Ad Slots</CardTitle>
            <div className="p-2 rounded-lg bg-gradient-to-br from-green-500 to-green-600">
              <Monitor className="h-5 w-5 text-white" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">{stats.activeSlots}</div>
            <p className="text-sm text-gray-500 mt-1">
              of {stats.totalSlots} total slots
            </p>
            <div className="mt-2">
              <div className="flex items-center justify-between text-xs">
                <span>Utilization</span>
                <span>{Math.round((stats.activeSlots / stats.totalSlots) * 100)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1 mt-1">
                <div 
                  className="bg-green-500 h-1 rounded-full" 
                  style={{ width: `${(stats.activeSlots / stats.totalSlots) * 100}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Pending Bookings Card */}
        <Card className="border-0 shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Pending Bookings</CardTitle>
            <div className="p-2 rounded-lg bg-gradient-to-br from-amber-500 to-amber-600">
              <Clock className="h-5 w-5 text-white" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">{stats.pendingBookings}</div>
            <p className="text-sm text-gray-500 mt-1">Awaiting approval</p>
            {stats.pendingBookings > 0 && (
              <Button 
                variant="link" 
                size="sm" 
                className="p-0 h-auto text-amber-600 hover:text-amber-700"
                onClick={() => setActiveTab('bookings')}
              >
                Review now →
              </Button>
            )}
          </CardContent>
        </Card>

        {/* Monthly Revenue Card */}
        <Card className="border-0 shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Monthly Revenue</CardTitle>
            <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500 to-purple-600">
              <DollarSign className="h-5 w-5 text-white" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              ${stats.monthlyRevenue.toLocaleString()}
            </div>
            <div className="flex items-center gap-1 mt-1">
              <TrendingUp className="h-3 w-3 text-green-500" />
              <span className="text-sm text-green-600 font-medium">
                +{stats.revenueGrowth}%
              </span>
              <span className="text-sm text-gray-500">vs last month</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Device Status Overview */}
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2 border-0 shadow-lg">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-xl">Device Status Overview</CardTitle>
              <Badge variant="secondary" className="gap-1">
                <Activity className="h-3 w-3" />
                Live Monitoring
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Online Devices</span>
                  <span className="text-sm text-green-600 font-semibold">
                    {stats.onlineDevices}/{stats.totalDevices}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-green-500 h-2 rounded-full" 
                    style={{ width: `${(stats.onlineDevices / stats.totalDevices) * 100}%` }}
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Approval Rate</span>
                  <span className="text-sm text-blue-600 font-semibold">
                    {stats.approvalRate}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-500 h-2 rounded-full" 
                    style={{ width: `${stats.approvalRate}%` }}
                  />
                </div>
              </div>
            </div>
            
            <div className="mt-4 pt-4 border-t border-gray-100">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setActiveTab('devices')}
                className="w-full"
              >
                View Device Details
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="text-xl">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button 
              variant="outline" 
              className="w-full justify-start gap-2"
              onClick={() => setActiveTab('locations')}
            >
              <MapPin className="h-4 w-4" />
              Manage Locations
            </Button>
            
            <Button 
              variant="outline" 
              className="w-full justify-start gap-2"
              onClick={() => setActiveTab('slots')}
            >
              <Monitor className="h-4 w-4" />
              Configure Ad Slots
            </Button>
            
            <Button 
              variant="outline" 
              className="w-full justify-start gap-2"
              onClick={() => setActiveTab('bookings')}
            >
              <Calendar className="h-4 w-4" />
              Review Bookings
              {stats.pendingBookings > 0 && (
                <Badge className="ml-auto bg-amber-500">
                  {stats.pendingBookings}
                </Badge>
              )}
            </Button>
            
            <Button 
              variant="outline" 
              className="w-full justify-start gap-2"
              onClick={() => setActiveTab('analytics')}
            >
              <TrendingUp className="h-4 w-4" />
              View Analytics
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card className="border-0 shadow-lg">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl">Recent Activity</CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="gap-1">
                <Bell className="h-3 w-3" />
                {recentActivity.length} updates
              </Badge>
              <Button variant="ghost" size="sm">
                <Filter className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentActivity.slice(0, 5).map((activity) => {
              const IconComponent = getActivityIcon(activity.type);
              return (
                <div key={activity.id} className="flex items-start gap-4 p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${getStatusColor(activity.status)}`}>
                    <IconComponent className="h-5 w-5" />
                  </div>
                  <div className="flex-grow min-w-0">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-medium text-gray-900">{activity.title}</h4>
                      <span className="text-xs text-gray-500">{activity.timestamp}</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{activity.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
          
          {recentActivity.length > 5 && (
            <div className="mt-4 pt-4 border-t border-gray-100 text-center">
              <Button variant="ghost" size="sm" className="text-blue-600 hover:text-blue-700">
                View all activity →
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  // Check if user has host permissions
  if (!hasRole('host') && !hasRole('admin')) {
    return (
      <div className="container mx-auto py-6">
        <Alert className="border-red-200 bg-red-50">
          <XCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            You don't have permission to access the host dashboard. 
            Please contact your administrator if you believe this is an error.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-6 mb-8">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="locations">Locations</TabsTrigger>
          <TabsTrigger value="slots">Ad Slots</TabsTrigger>
          <TabsTrigger value="bookings">Bookings</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="devices">Devices</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          {renderOverviewTab()}
        </TabsContent>

        <TabsContent value="locations" className="mt-6">
          <LocationManagement />
        </TabsContent>

        <TabsContent value="slots" className="mt-6">
          <AdSlotConfiguration />
        </TabsContent>

        <TabsContent value="bookings" className="mt-6">
          <BookingApprovalWorkflow />
        </TabsContent>

        <TabsContent value="analytics" className="mt-6">
          <RevenueAnalytics />
        </TabsContent>

        <TabsContent value="devices" className="mt-6">
          <DeviceMonitoring />
        </TabsContent>
      </Tabs>
    </div>
  );
}