'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { CompanyRole } from '@/types/auth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import {
  Upload,
  MonitorSpeaker,
  Users,
  BarChart3,
  Settings,
  Plus,
  Eye,
  Check,
  X,
  Clock,
  Layers,
  Play,
  Pause,
  Square,
  Activity,
  FileText,
  Clock4,
  Monitor,
  TrendingUp,
  TrendingDown,
  Calendar,
  Filter,
  Share,
  Zap,
  Bell,
  Moon,
  Sun,
  Palette,
  User2,
  Target,
  ArrowUp,
  ArrowDown,
  Minus
} from 'lucide-react';

// Import existing components
import UnifiedUploadPage from '@/components/upload/UnifiedUploadPage';
import OverlayManagement from './overlays/overlay-management';
import { ContentManager } from '@/components/content/ContentManager';
import DigitalTwinDashboard from '@/components/dashboard/DigitalTwinDashboard';

export default function DashboardPage() {
  const { user, hasRole, isHostCompany, isAdvertiserCompany } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [timeFilter, setTimeFilter] = useState('month');
  const [darkMode, setDarkMode] = useState(false);
  const [stats, setStats] = useState({
    totalContent: 0,
    pendingApprovals: 0,
    activeScreens: 0,
    totalImpressions: 0,
    totalScreens: 0,
    approvalRate: 0,
    contentTrend: [0, 0] as number[],
    impressionsTrend: [0, 0] as number[],
    screensTrend: [0, 0] as number[],
    approvalsTrend: [0, 0] as number[]
  });
  const [recentActivity, setRecentActivity] = useState([
    { id: 1, type: 'upload', user: 'John Doe', action: 'uploaded new content', target: 'Summer Campaign Ad', time: '2 minutes ago', icon: Upload },
    { id: 2, type: 'approval', user: 'Sarah Smith', action: 'approved content', target: 'Product Launch Video', time: '15 minutes ago', icon: Check },
    { id: 3, type: 'screen', user: 'System', action: 'screen came online', target: 'Mall Entrance Display', time: '1 hour ago', icon: Monitor },
    { id: 4, type: 'review', user: 'Mike Johnson', action: 'submitted for review', target: 'Holiday Promotion', time: '2 hours ago', icon: Eye }
  ]);

  useEffect(() => {
    // Load dashboard stats
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const response = await fetch('/api/dashboard/stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      } else {
        // Mock data for demo purposes
        setStats({
          totalContent: 156,
          pendingApprovals: 8,
          activeScreens: 23,
          totalImpressions: 45670,
          totalScreens: 28,
          approvalRate: 92,
          contentTrend: [120, 132, 145, 151, 156],
          impressionsTrend: [38450, 41200, 43890, 44200, 45670],
          screensTrend: [22, 23, 21, 24, 23],
          approvalsTrend: [12, 9, 15, 6, 8]
        });
      }
    } catch (error) {
      console.error('Failed to load dashboard stats:', error);
      // Mock data fallback
      setStats({
        totalContent: 156,
        pendingApprovals: 8,
        activeScreens: 23,
        totalImpressions: 45670,
        totalScreens: 28,
        approvalRate: 92,
        contentTrend: [120, 132, 145, 151, 156],
        impressionsTrend: [38450, 41200, 43890, 44200, 45670],
        screensTrend: [22, 23, 21, 24, 23],
        approvalsTrend: [12, 9, 15, 6, 8]
      });
    }
  };

  // Helper functions for sparkline charts and card states
  const getCardColor = (type: string, value: number) => {
    switch (type) {
      case 'content':
        return value > 0 ? 'from-blue-500 to-blue-600' : 'from-gray-400 to-gray-500';
      case 'approvals':
        return value > 0 ? 'from-amber-500 to-amber-600' : 'from-green-500 to-green-600';
      case 'screens':
        return value > 0 ? 'from-green-500 to-green-600' : 'from-red-500 to-red-600';
      case 'impressions':
        return value > 0 ? 'from-purple-500 to-purple-600' : 'from-gray-400 to-gray-500';
      default:
        return 'from-gray-400 to-gray-500';
    }
  };

  const getTrendIcon = (trend: number[]) => {
    if (!trend || !Array.isArray(trend) || trend.length < 2) return Minus;
    const latest = trend[trend.length - 1];
    const previous = trend[trend.length - 2];
    if (latest > previous) return ArrowUp;
    if (latest < previous) return ArrowDown;
    return Minus;
  };

  const getTrendPercentage = (trend: number[]) => {
    if (!trend || !Array.isArray(trend) || trend.length < 2) return 0;
    const latest = trend[trend.length - 1];
    const previous = trend[trend.length - 2];
    if (previous === 0) return 0;
    return Math.round(((latest - previous) / previous) * 100);
  };

  const MiniSparkline = ({ data, color }: { data: number[], color: string }) => {
    if (!data || !Array.isArray(data) || data.length === 0) return null;

    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;

    const points = data.map((value, index) => {
      const x = (index / (data.length - 1)) * 60;
      const y = 20 - ((value - min) / range) * 20;
      return `${x},${y}`;
    }).join(' ');

    return (
      <div className="w-16 h-6">
        <svg width="60" height="20" className="overflow-visible">
          <polyline
            points={points}
            fill="none"
            stroke={`url(#gradient-${color})`}
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <defs>
            <linearGradient id={`gradient-${color}`} x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#8B5CF6" />
              <stop offset="100%" stopColor="#A855F7" />
            </linearGradient>
          </defs>
        </svg>
      </div>
    );
  };

  const renderOverviewTab = () => (
    <div className="grid gap-6">
      {/* Time Filter Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-bold text-gray-900">
            Welcome back, {user?.display_name || user?.first_name || 'User'}!
          </h2>
          <Badge variant="outline" className="text-xs">
            Last login: {new Date().toLocaleDateString()}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={darkMode ? "default" : "outline"}
            size="sm"
            onClick={() => setDarkMode(!darkMode)}
            className="gap-2"
          >
            {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            {darkMode ? 'Light' : 'Dark'}
          </Button>
          <div className="flex items-center border rounded-lg p-1 bg-muted/50">
            {['day', 'week', 'month'].map((period) => (
              <Button
                key={period}
                variant={timeFilter === period ? "default" : "ghost"}
                size="sm"
                onClick={() => setTimeFilter(period)}
                className="text-xs px-3 py-1 h-7"
              >
                {period.charAt(0).toUpperCase() + period.slice(1)}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* Enhanced Stats Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {/* Total Content Card */}
        <Card className="relative overflow-hidden border-0 shadow-lg">
          <div className={`absolute inset-0 bg-gradient-to-br ${getCardColor('content', stats.totalContent)} opacity-5`} />
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Content</CardTitle>
            <div className={`p-2 rounded-lg bg-gradient-to-br ${getCardColor('content', stats.totalContent)}`}>
              <FileText className="h-5 w-5 text-white" />
            </div>
          </CardHeader>
          <CardContent className="pb-4">
            <div className="flex items-baseline justify-between">
              <div className="text-3xl font-bold text-gray-900">{stats.totalContent}</div>
              <MiniSparkline data={stats.contentTrend} color="content" />
            </div>
            <div className="flex items-center justify-between mt-2">
              <p className="text-xs text-gray-500">
                {isAdvertiserCompany() ? 'Your ads' : 'All content'}
              </p>
              <div className="flex items-center gap-1">
                {React.createElement(getTrendIcon(stats.contentTrend), {
                  className: `h-3 w-3 ${getTrendPercentage(stats.contentTrend) >= 0 ? 'text-green-500' : 'text-red-500'}`
                })}
                <span className={`text-xs font-medium ${getTrendPercentage(stats.contentTrend) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {Math.abs(getTrendPercentage(stats.contentTrend))}%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Pending Approvals Card */}
        <Card className="relative overflow-hidden border-0 shadow-lg">
          <div className={`absolute inset-0 bg-gradient-to-br ${getCardColor('approvals', stats.pendingApprovals)} opacity-5`} />
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Pending Approvals</CardTitle>
            <div className={`p-2 rounded-lg bg-gradient-to-br ${getCardColor('approvals', stats.pendingApprovals)}`}>
              <Clock4 className="h-5 w-5 text-white" />
            </div>
          </CardHeader>
          <CardContent className="pb-4">
            <div className="flex items-baseline justify-between">
              <div className="text-3xl font-bold text-gray-900">{stats.pendingApprovals}</div>
              <MiniSparkline data={stats.approvalsTrend} color="approvals" />
            </div>
            <div className="flex items-center justify-between mt-2">
              <p className="text-xs text-gray-500">
                {isHostCompany() ? 'Awaiting review' : 'Under review'}
              </p>
              <div className="flex items-center gap-1">
                <Target className="h-3 w-3 text-blue-500" />
                <span className="text-xs font-medium text-blue-500">
                  {stats.approvalRate}% approval rate
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Active Screens Card */}
        <Card className="relative overflow-hidden border-0 shadow-lg">
          <div className={`absolute inset-0 bg-gradient-to-br ${getCardColor('screens', stats.activeScreens)} opacity-5`} />
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Active Screens</CardTitle>
            <div className={`p-2 rounded-lg bg-gradient-to-br ${getCardColor('screens', stats.activeScreens)}`}>
              <Monitor className="h-5 w-5 text-white" />
            </div>
          </CardHeader>
          <CardContent className="pb-4">
            <div className="flex items-baseline justify-between">
              <div className="text-3xl font-bold text-gray-900">{stats.activeScreens}</div>
              <MiniSparkline data={stats.screensTrend} color="screens" />
            </div>
            <div className="flex items-center justify-between mt-2">
              <p className="text-xs text-gray-500">
                of {stats.totalScreens} total
              </p>
              <div className="flex items-center gap-1">
                <span className={`text-xs font-medium ${stats.activeScreens === stats.totalScreens ? 'text-green-500' : 'text-amber-500'}`}>
                  {Math.round((stats.activeScreens / Math.max(stats.totalScreens, 1)) * 100)}% online
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Total Impressions Card */}
        <Card className="relative overflow-hidden border-0 shadow-lg">
          <div className={`absolute inset-0 bg-gradient-to-br ${getCardColor('impressions', stats.totalImpressions)} opacity-5`} />
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Impressions</CardTitle>
            <div className={`p-2 rounded-lg bg-gradient-to-br ${getCardColor('impressions', stats.totalImpressions)}`}>
              <BarChart3 className="h-5 w-5 text-white" />
            </div>
          </CardHeader>
          <CardContent className="pb-4">
            <div className="flex items-baseline justify-between">
              <div className="text-3xl font-bold text-gray-900">{stats.totalImpressions.toLocaleString()}</div>
              <MiniSparkline data={stats.impressionsTrend} color="impressions" />
            </div>
            <div className="flex items-center justify-between mt-2">
              <p className="text-xs text-gray-500">
                This {timeFilter}
              </p>
              <div className="flex items-center gap-1">
                {React.createElement(getTrendIcon(stats.impressionsTrend), {
                  className: `h-3 w-3 ${getTrendPercentage(stats.impressionsTrend) >= 0 ? 'text-green-500' : 'text-red-500'}`
                })}
                <span className={`text-xs font-medium ${getTrendPercentage(stats.impressionsTrend) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {Math.abs(getTrendPercentage(stats.impressionsTrend))}%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Enhanced Quick Actions */}
      <Card className="border-0 shadow-lg">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl font-semibold">Quick Actions</CardTitle>
            <Badge variant="secondary" className="text-xs">
              Most used actions
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {isAdvertiserCompany() && (
              <>
                <Card className="group hover:shadow-md transition-all cursor-pointer border-blue-100 hover:border-blue-200"
                      onClick={() => setActiveTab('upload')}>
                  <CardContent className="p-6 text-center">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                      <Upload className="h-6 w-6 text-white" />
                    </div>
                    <h3 className="font-semibold text-gray-900 mb-1">Upload Content</h3>
                    <p className="text-xs text-gray-500">Add new advertisements</p>
                  </CardContent>
                </Card>
                <Card className="group hover:shadow-md transition-all cursor-pointer border-green-100 hover:border-green-200"
                      onClick={() => setActiveTab('content')}>
                  <CardContent className="p-6 text-center">
                    <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                      <Eye className="h-6 w-6 text-white" />
                    </div>
                    <h3 className="font-semibold text-gray-900 mb-1">My Content</h3>
                    <p className="text-xs text-gray-500">View & manage ads</p>
                  </CardContent>
                </Card>
              </>
            )}

            {isHostCompany() && (
              <>
                <Card className="group hover:shadow-md transition-all cursor-pointer border-purple-100 hover:border-purple-200"
                      onClick={() => setActiveTab('overlay')}>
                  <CardContent className="p-6 text-center">
                    <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                      <Layers className="h-6 w-6 text-white" />
                    </div>
                    <h3 className="font-semibold text-gray-900 mb-1">Design Overlays</h3>
                    <p className="text-xs text-gray-500">Layout templates</p>
                  </CardContent>
                </Card>
                <Card className="group hover:shadow-md transition-all cursor-pointer border-indigo-100 hover:border-indigo-200"
                      onClick={() => setActiveTab('content')}>
                  <CardContent className="p-6 text-center">
                    <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                      <Share className="h-6 w-6 text-white" />
                    </div>
                    <h3 className="font-semibold text-gray-900 mb-1">Distribute</h3>
                    <p className="text-xs text-gray-500">Share to screens</p>
                  </CardContent>
                </Card>
              </>
            )}

            <Card className="group hover:shadow-md transition-all cursor-pointer border-gray-100 hover:border-gray-200"
                  onClick={() => setActiveTab('analytics')}>
              <CardContent className="p-6 text-center">
                <div className="w-12 h-12 bg-gradient-to-br from-gray-500 to-gray-600 rounded-xl flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                  <BarChart3 className="h-6 w-6 text-white" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">Analytics</h3>
                <p className="text-xs text-gray-500">View insights</p>
              </CardContent>
            </Card>

            {hasRole(CompanyRole.ADMIN) && (
              <Card className="group hover:shadow-md transition-all cursor-pointer border-red-100 hover:border-red-200">
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 bg-gradient-to-br from-red-500 to-red-600 rounded-xl flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                    <Settings className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-1">System Settings</h3>
                  <p className="text-xs text-gray-500">Platform admin</p>
                </CardContent>
              </Card>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Enhanced Recent Activity Timeline */}
      <Card className="border-0 shadow-lg">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl font-semibold">Recent Activity</CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="gap-1">
                <Activity className="h-3 w-3" />
                Live
              </Badge>
              <Button variant="ghost" size="sm" className="text-xs">
                <Filter className="h-3 w-3 mr-1" />
                Filter
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 max-h-80 overflow-y-auto">
            {recentActivity.map((activity, index) => (
              <div key={activity.id} className="flex items-start gap-4 p-3 rounded-lg bg-gray-50/50 hover:bg-gray-100/50 transition-colors">
                <div className="flex-shrink-0">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    activity.type === 'upload' ? 'bg-blue-100 text-blue-600' :
                    activity.type === 'approval' ? 'bg-green-100 text-green-600' :
                    activity.type === 'screen' ? 'bg-purple-100 text-purple-600' :
                    'bg-amber-100 text-amber-600'
                  }`}>
                    {React.createElement(activity.icon, { className: "h-5 w-5" })}
                  </div>
                </div>
                <div className="flex-grow min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="min-w-0 flex-grow">
                      <p className="text-sm font-medium text-gray-900 mb-1">
                        <span className="font-semibold text-blue-600">{activity.user}</span> {activity.action}
                      </p>
                      <p className="text-sm text-gray-600 truncate">"{activity.target}"</p>
                    </div>
                    <div className="flex-shrink-0 ml-4">
                      <span className="text-xs text-gray-500">{activity.time}</span>
                    </div>
                  </div>
                  {index < recentActivity.length - 1 && (
                    <div className="absolute left-9 mt-2 w-px h-6 bg-gray-200"></div>
                  )}
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t border-gray-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                Real-time activity monitoring active
              </div>
              <Button variant="ghost" size="sm" className="text-xs text-blue-600 hover:text-blue-700">
                View all activity →
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderUploadTab = () => (
    <div className="max-w-4xl mx-auto">
      <UnifiedUploadPage
        mode="simple"
        title="Upload Advertisement"
        description="Upload your advertisement content for review and approval by the host"
        redirectPath="/dashboard"
        onUploadComplete={() => {
          fetchDashboardStats();
          setActiveTab('overview');
        }}
      />
    </div>
  );

  const renderOverlayTab = () => (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold">Overlay Designer</h2>
        <p className="text-muted-foreground">
          Define where advertiser content should appear on your screens
        </p>
      </div>
      <OverlayManagement />
    </div>
  );

  const renderAnalyticsTab = () => (
    <div className="space-y-6">
      <DigitalTwinDashboard
        timeRange="24h"
        selectedDevice="all"
        autoRefresh={true}
        refreshInterval={30000}
      />
    </div>
  );

  if (!user) {
    return <div>Loading...</div>;
  }

  return (
    <div className="container mx-auto py-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">
          Welcome, {user.display_name || user.email}
        </h1>
        <p className="text-muted-foreground">
          {hasRole(CompanyRole.ADMIN) && 'Manage the entire digital signage platform'}
          {isHostCompany() && 'Manage your screens and approve advertiser content'}
          {isAdvertiserCompany() && 'Upload and track your advertisement campaigns'}
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="content">Content</TabsTrigger>
          {isAdvertiserCompany() && (
            <TabsTrigger value="upload">Upload</TabsTrigger>
          )}
          {isHostCompany() && (
            <>
              <TabsTrigger value="overlay">Overlays</TabsTrigger>
            </>
          )}
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          {renderOverviewTab()}
        </TabsContent>

        <TabsContent value="content" className="mt-6">
          <ContentManager mode="unified" />
        </TabsContent>

        {isAdvertiserCompany() && (
          <TabsContent value="upload" className="mt-6">
            {renderUploadTab()}
          </TabsContent>
        )}

        {isHostCompany() && (
          <>
            <TabsContent value="overlay" className="mt-6">
              {renderOverlayTab()}
            </TabsContent>
          </>
        )}

        <TabsContent value="analytics" className="mt-6">
          {renderAnalyticsTab()}
        </TabsContent>
      </Tabs>
    </div>
  );
}
