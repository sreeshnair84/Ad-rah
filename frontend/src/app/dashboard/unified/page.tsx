'use client';

import { useState, useEffect } from 'react';
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
  Activity
} from 'lucide-react';

// Import existing components
import UnifiedUploadPage from '@/components/upload/UnifiedUploadPage';
import OverlayManagement from '../overlays/overlay-management';
import ContentApproval from '../approval/content-approval';
import { ContentManager } from '@/components/content/ContentManager';
import DigitalTwinDashboard from '@/components/dashboard/DigitalTwinDashboard';

interface UnifiedDashboardProps {}

export default function UnifiedDashboard({}: UnifiedDashboardProps) {
  const { user, hasRole, isHostCompany, isAdvertiserCompany } = useAuth();
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
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
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
              {isAdvertiserCompany() ? 'Your ads' : 'All content'}
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
              {isHostCompany() ? 'Awaiting your review' : 'Under review'}
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
            {isAdvertiserCompany() && (
              <Button 
                onClick={() => setActiveTab('upload')} 
                className="h-20 flex flex-col gap-2"
              >
                <Upload className="h-6 w-6" />
                Upload New Ad
              </Button>
            )}
            
            {isHostCompany() && (
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
            
            {hasRole(CompanyRole.ADMIN) && (
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

      {/* Recent Activity - now pulling from real analytics */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Real-time metrics available</p>
                <p className="text-xs text-muted-foreground">Live device monitoring active</p>
              </div>
              <Badge variant="default">
                <Activity className="h-3 w-3 mr-1" />
                Live
              </Badge>
            </div>
            <div className="text-sm text-muted-foreground">
              Switch to Analytics tab for detailed device monitoring and performance metrics.
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
        redirectPath="/dashboard/unified"
        onUploadComplete={() => {
          fetchDashboardStats();
          setActiveTab('overview');
        }}
      />
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
              <TabsTrigger value="approve">Approve</TabsTrigger>
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
