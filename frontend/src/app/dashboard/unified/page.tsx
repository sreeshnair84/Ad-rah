'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
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
  Square
} from 'lucide-react';

// Import existing components
import ContentUploadForm from '../upload/content-upload-form';
import OverlayManagement from '../overlays/overlay-management';
import ContentApproval from '../approval/content-approval';

interface UnifiedDashboardProps {}

export default function UnifiedDashboard({}: UnifiedDashboardProps) {
  const { user, hasRole } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState({
    totalContent: 0,
    pendingApprovals: 0,
    activeScreens: 0,
    totalImpressions: 0
  });

  useEffect(() => {
    // Load dashboard stats
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const response = await fetch('/api/dashboard/stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to load dashboard stats:', error);
    }
  };

  const renderOverviewTab = () => (
    <div className="grid gap-6">
      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Content</CardTitle>
            <Upload className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalContent}</div>
            <p className="text-xs text-muted-foreground">
              {hasRole('ADVERTISER') ? 'Your ads' : 'All content'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Approvals</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.pendingApprovals}</div>
            <p className="text-xs text-muted-foreground">
              {hasRole('HOST') ? 'Awaiting your review' : 'Under review'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Screens</CardTitle>
            <MonitorSpeaker className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.activeScreens}</div>
            <p className="text-xs text-muted-foreground">
              Online displays
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Impressions</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalImpressions.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              This month
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {hasRole('ADVERTISER') && (
              <Button 
                onClick={() => setActiveTab('upload')} 
                className="h-20 flex flex-col gap-2"
              >
                <Upload className="h-6 w-6" />
                Upload New Ad
              </Button>
            )}
            
            {hasRole('HOST') && (
              <>
                <Button 
                  onClick={() => setActiveTab('approve')} 
                  className="h-20 flex flex-col gap-2"
                  variant="outline"
                >
                  <Check className="h-6 w-6" />
                  Review Ads
                </Button>
                <Button 
                  onClick={() => setActiveTab('overlay')} 
                  className="h-20 flex flex-col gap-2"
                  variant="outline"
                >
                  <Layers className="h-6 w-6" />
                  Design Overlays
                </Button>
              </>
            )}
            
            {hasRole('ADMIN') && (
              <Button 
                onClick={() => setActiveTab('manage')} 
                className="h-20 flex flex-col gap-2"
                variant="outline"
              >
                <Settings className="h-6 w-6" />
                System Settings
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { action: 'New ad uploaded', time: '2 min ago', status: 'pending' },
              { action: 'Ad approved by host', time: '15 min ago', status: 'approved' },
              { action: 'Screen came online', time: '1 hour ago', status: 'active' },
              { action: 'Overlay updated', time: '2 hours ago', status: 'updated' }
            ].map((activity, index) => (
              <div key={index} className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">{activity.action}</p>
                  <p className="text-xs text-muted-foreground">{activity.time}</p>
                </div>
                <Badge variant={activity.status === 'approved' ? 'default' : 'secondary'}>
                  {activity.status}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderUploadTab = () => (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold">Upload Content</h2>
        <p className="text-muted-foreground">
          Upload your advertisement content for review and approval by the host
        </p>
      </div>
      <ContentUploadForm onUploadComplete={() => {
        fetchDashboardStats();
        setActiveTab('overview');
      }} />
    </div>
  );

  const renderApprovalTab = () => (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold">Content Approval</h2>
        <p className="text-muted-foreground">
          Review and approve advertiser content for your screens
        </p>
      </div>
      <ContentApproval />
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
    <div className="grid gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Performance Analytics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4">
            <div className="flex items-center justify-between">
              <span className="text-sm">Content Engagement</span>
              <span className="text-sm font-medium">85%</span>
            </div>
            <Progress value={85} className="w-full" />
            
            <div className="flex items-center justify-between">
              <span className="text-sm">Screen Uptime</span>
              <span className="text-sm font-medium">98%</span>
            </div>
            <Progress value={98} className="w-full" />
            
            <div className="flex items-center justify-between">
              <span className="text-sm">Approval Rate</span>
              <span className="text-sm font-medium">92%</span>
            </div>
            <Progress value={92} className="w-full" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Top Performing Content</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { title: 'Summer Sale Campaign', impressions: 15420, engagement: '7.2%' },
              { title: 'New Product Launch', impressions: 12890, engagement: '6.8%' },
              { title: 'Holiday Special', impressions: 11230, engagement: '5.9%' }
            ].map((content, index) => (
              <div key={index} className="flex items-center justify-between p-3 rounded-lg border">
                <div>
                  <p className="font-medium">{content.title}</p>
                  <p className="text-sm text-muted-foreground">
                    {content.impressions.toLocaleString()} impressions • {content.engagement} engagement
                  </p>
                </div>
                <Badge>Top</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  if (!user) {
    return <div>Loading...</div>;
  }

  return (
    <div className="container mx-auto py-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">
          Welcome, {user.name || user.email}
        </h1>
        <p className="text-muted-foreground">
          {hasRole('ADMIN') && 'Manage the entire digital signage platform'}
          {hasRole('HOST') && 'Manage your screens and approve advertiser content'}
          {hasRole('ADVERTISER') && 'Upload and track your advertisement campaigns'}
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          {hasRole('ADVERTISER') && (
            <TabsTrigger value="upload">Upload</TabsTrigger>
          )}
          {hasRole('HOST') && (
            <>
              <TabsTrigger value="approve">Approve</TabsTrigger>
              <TabsTrigger value="overlay">Overlays</TabsTrigger>
            </>
          )}
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          {renderOverviewTab()}
        </TabsContent>

        {hasRole('ADVERTISER') && (
          <TabsContent value="upload" className="mt-6">
            {renderUploadTab()}
          </TabsContent>
        )}

        {hasRole('HOST') && (
          <>
            <TabsContent value="approve" className="mt-6">
              {renderApprovalTab()}
            </TabsContent>
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
