'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Search,
  Calendar,
  DollarSign,
  Eye,
  Target,
  TrendingUp,
  MapPin,
  Clock,
  BarChart3,
  Camera,
  Play,
  Pause,
  Edit,
  Plus,
  Filter,
  Download,
  RefreshCw,
  Bell,
  CreditCard,
  Users,
  MonitorPlay,
  ChevronRight,
  Activity
} from 'lucide-react';

// Import advertiser dashboard components
import SlotDiscovery from '@/components/advertiser/SlotDiscovery';
import CampaignManagement from '@/components/advertiser/CampaignManagement';
import BookingManagement from '@/components/advertiser/BookingManagement';
import PerformanceAnalytics from '@/components/advertiser/PerformanceAnalytics';

interface DashboardStats {
  activeCampaigns: number;
  totalBookings: number;
  monthlySpend: number;
  impressions: number;
  clickThroughRate: number;
  conversionRate: number;
  averageCPM: number;
  reachGoal: number;
  pendingApprovals: number;
  creditBalance: number;
}

interface RecentActivity {
  id: string;
  type: 'booking' | 'campaign' | 'approval' | 'payment';
  title: string;
  description: string;
  timestamp: Date;
  status: 'success' | 'pending' | 'error' | 'info';
}

interface QuickAction {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  action: () => void;
  color: string;
}

export default function AdvertiserDashboard() {
  const { user, loading } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [activities, setActivities] = useState<RecentActivity[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  // Mock data for development
  useEffect(() => {
    const mockStats: DashboardStats = {
      activeCampaigns: 8,
      totalBookings: 24,
      monthlySpend: 12750,
      impressions: 156800,
      clickThroughRate: 2.4,
      conversionRate: 0.8,
      averageCPM: 8.15,
      reachGoal: 85,
      pendingApprovals: 3,
      creditBalance: 5420
    };

    const mockActivities: RecentActivity[] = [
      {
        id: '1',
        type: 'booking',
        title: 'New Booking Approved',
        description: 'Downtown Mall - Premium Slot',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
        status: 'success'
      },
      {
        id: '2',
        type: 'campaign',
        title: 'Campaign Performance Alert',
        description: 'Summer Sale campaign exceeding CTR goals',
        timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
        status: 'info'
      },
      {
        id: '3',
        type: 'approval',
        title: 'Content Under Review',
        description: 'Black Friday promotion pending approval',
        timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000),
        status: 'pending'
      },
      {
        id: '4',
        type: 'payment',
        title: 'Payment Processed',
        description: '$2,450 charged for November campaigns',
        timestamp: new Date(Date.now() - 12 * 60 * 60 * 1000),
        status: 'success'
      }
    ];

    setStats(mockStats);
    setActivities(mockActivities);
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setRefreshing(false);
  };

  const quickActions: QuickAction[] = [
    {
      id: 'discover',
      title: 'Discover Slots',
      description: 'Find available ad slots',
      icon: <Search className="h-5 w-5" />,
      action: () => setActiveTab('discovery'),
      color: 'bg-blue-500'
    },
    {
      id: 'campaign',
      title: 'Create Campaign',
      description: 'Launch new advertising campaign',
      icon: <Plus className="h-5 w-5" />,
      action: () => setActiveTab('campaigns'),
      color: 'bg-green-500'
    },
    {
      id: 'analytics',
      title: 'View Analytics',
      description: 'Check performance metrics',
      icon: <BarChart3 className="h-5 w-5" />,
      action: () => setActiveTab('analytics'),
      color: 'bg-purple-500'
    },
    {
      id: 'bookings',
      title: 'Manage Bookings',
      description: 'View and edit bookings',
      icon: <Calendar className="h-5 w-5" />,
      action: () => setActiveTab('bookings'),
      color: 'bg-orange-500'
    }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Advertiser Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Welcome back, {user?.name || 'Advertiser'}! Manage your campaigns and track performance.
          </p>
        </div>
        <div className="flex space-x-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button size="sm">
            <Bell className="h-4 w-4 mr-2" />
            Notifications
          </Button>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {quickActions.map((action) => (
          <Card key={action.id} className="cursor-pointer hover:shadow-md transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-center space-x-3">
                <div className={`${action.color} text-white p-2 rounded-lg`}>
                  {action.icon}
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-sm">{action.title}</h3>
                  <p className="text-xs text-gray-600">{action.description}</p>
                </div>
                <ChevronRight className="h-4 w-4 text-gray-400" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="discovery">Slot Discovery</TabsTrigger>
          <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
          <TabsTrigger value="bookings">Bookings</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Campaigns</CardTitle>
                <Target className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.activeCampaigns}</div>
                <Badge variant="secondary" className="mt-1">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  +2 this week
                </Badge>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Monthly Spend</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">${stats?.monthlySpend.toLocaleString()}</div>
                <Badge variant="secondary" className="mt-1">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  +12% vs last month
                </Badge>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Impressions</CardTitle>
                <Eye className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.impressions.toLocaleString()}</div>
                <Badge variant="secondary" className="mt-1">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  +8% this week
                </Badge>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Click Rate</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.clickThroughRate}%</div>
                <Badge variant="secondary" className="mt-1">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  Above average
                </Badge>
              </CardContent>
            </Card>
          </div>

          {/* Performance Overview */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BarChart3 className="h-5 w-5 mr-2" />
                  Campaign Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Conversion Rate</span>
                    <span className="text-sm font-semibold">{stats?.conversionRate}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full" 
                      style={{ width: `${(stats?.conversionRate || 0) * 10}%` }}
                    ></div>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Average CPM</span>
                    <span className="text-sm font-semibold">${stats?.averageCPM}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${((stats?.averageCPM || 0) / 15) * 100}%` }}
                    ></div>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-sm">Reach Goal</span>
                    <span className="text-sm font-semibold">{stats?.reachGoal}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-purple-600 h-2 rounded-full" 
                      style={{ width: `${stats?.reachGoal}%` }}
                    ></div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Activity className="h-5 w-5 mr-2" />
                  Recent Activity
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {activities.map((activity) => (
                    <div key={activity.id} className="flex items-start space-x-3">
                      <div className={`w-2 h-2 rounded-full mt-2 ${
                        activity.status === 'success' ? 'bg-green-500' :
                        activity.status === 'pending' ? 'bg-yellow-500' :
                        activity.status === 'error' ? 'bg-red-500' :
                        'bg-blue-500'
                      }`}></div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                        <p className="text-sm text-gray-500">{activity.description}</p>
                        <p className="text-xs text-gray-400">
                          {activity.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Account Status */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <CreditCard className="h-5 w-5 mr-2" />
                  Account Balance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  ${stats?.creditBalance.toLocaleString()}
                </div>
                <p className="text-sm text-gray-600 mt-1">Available credit</p>
                <Button size="sm" className="mt-3">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Funds
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Clock className="h-5 w-5 mr-2" />
                  Pending Approvals
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-orange-600">
                  {stats?.pendingApprovals}
                </div>
                <p className="text-sm text-gray-600 mt-1">Content reviews</p>
                <Button variant="outline" size="sm" className="mt-3">
                  <Eye className="h-4 w-4 mr-2" />
                  View Details
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <MonitorPlay className="h-5 w-5 mr-2" />
                  Active Slots
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">
                  {stats?.totalBookings}
                </div>
                <p className="text-sm text-gray-600 mt-1">Currently booked</p>
                <Button variant="outline" size="sm" className="mt-3">
                  <MapPin className="h-4 w-4 mr-2" />
                  View Map
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="discovery">
          <SlotDiscovery />
        </TabsContent>

        <TabsContent value="campaigns">
          <CampaignManagement />
        </TabsContent>

        <TabsContent value="bookings">
          <BookingManagement />
        </TabsContent>

        <TabsContent value="analytics">
          <PerformanceAnalytics />
        </TabsContent>
      </Tabs>
    </div>
  );
}