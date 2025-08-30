'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useAuth } from '@/hooks/useAuth';
import { useDashboard } from '@/hooks/useDashboard';
import { PlaySquare } from 'lucide-react';

export default function DashboardPage() {
  const { user, hasRole } = useAuth();
  const { performanceData, categoryData, metrics, loading: dashboardLoading } = useDashboard();

  if (!user || dashboardLoading) return <div>Loading...</div>;

  // Transform data for charts
  const demoLine = performanceData.map(item => ({
    name: item.name,
    value: item.impressions || 0
  }));

  const demoBars = performanceData.slice(0, 4).map(item => ({
    name: item.name,
    plays: item.impressions || 0
  }));

  const demoPie = categoryData.map(item => ({
    name: item.name,
    value: item.value
  }));

  const renderAdminDashboard = () => (
    <div className="grid gap-6 p-6 sm:grid-cols-2 lg:grid-cols-4">
      <Card className="col-span-2">
        <CardHeader>
          <CardTitle>Plays vs Time (Today)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={demoLine}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="value" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Top Locations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={demoBars}>
                <XAxis dataKey="name" hide />
                <YAxis />
                <Tooltip />
                <Bar dataKey="plays" radius={[8,8,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Category Split</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={demoPie} dataKey="value" nameKey="name" outerRadius={70}>
                  {demoPie.map((_, i) => (
                    <Cell key={i} fill={`hsl(${i * 45}, 70%, 50%)`} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card className="col-span-2 lg:col-span-4">
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1,2,3,4,5,6,7,8].map((i) => (
            <div key={i} className="flex items-center gap-3 rounded-xl border p-4">
              <PlaySquare className="h-5 w-5" />
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">Ad #{i} played in Dubai Mall</p>
                <p className="text-xs text-muted-foreground">2 min ago</p>
              </div>
              <Badge className="ml-auto" variant="outline">OK</Badge>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );

  const renderHostDashboard = () => (
    <div className="grid gap-6 p-6 lg:grid-cols-3">
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Screen Management</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="h-80 w-full rounded-2xl border bg-muted" />
          <div className="grid gap-3 sm:grid-cols-2">
            {["Dubai Mall — Atrium A", "Mall of the Emirates — G2", "DIFC Gate", "DXB T3 – Concourse A"].map((s, i) => (
              <div key={i} className="flex items-center justify-between rounded-xl border p-4">
                <div className="flex items-center gap-2">
                  <PlaySquare className="h-5 w-5" />
                  <div>
                    <p className="text-sm font-medium">{s}</p>
                    <p className="text-xs text-muted-foreground">Online • 4K Portrait</p>
                  </div>
                </div>
                <Badge variant="outline">Active</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Quick Stats</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-xl border p-4">
            <p className="text-sm font-medium">Active Screens</p>
            <p className="text-2xl font-bold">{metrics.activeKiosks}</p>
          </div>
          <div className="rounded-xl border p-4">
            <p className="text-sm font-medium">Ads for Review</p>
            <p className="text-2xl font-bold">{metrics.pendingReviews}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderAdvertiserDashboard = () => (
    <div className="grid gap-6 p-6 lg:grid-cols-3">
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>My Campaigns</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="rounded-2xl border p-4">
                <div className="aspect-video rounded-xl border bg-muted" />
                <div className="mt-3 flex items-center gap-2">
                  <Badge variant="secondary">Video</Badge>
                  <Badge>Retail</Badge>
                  <Badge variant="outline">EN/AR</Badge>
                </div>
                <div className="mt-2 flex items-center gap-2 text-sm">
                  <span>Dubai Mall, DIFC</span>
                </div>
                <div className="mt-3 flex items-center gap-2">
                  <Badge variant="outline">Active</Badge>
                  <span className="text-sm text-muted-foreground">1.2K plays</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Performance</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-xl border p-4">
            <p className="text-sm font-medium">Total Impressions</p>
            <p className="text-2xl font-bold">{metrics.advertiserPerformance.toLocaleString()}</p>
          </div>
          <div className="rounded-xl border p-4">
            <p className="text-sm font-medium">Active Campaigns</p>
            <p className="text-2xl font-bold">{metrics.advertiserAds}</p>
          </div>
          <div className="rounded-xl border p-4">
            <p className="text-sm font-medium">Pending Reviews</p>
            <p className="text-2xl font-bold">{metrics.advertiserPendingReviews}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div>
      {hasRole('ADMIN') && renderAdminDashboard()}
      {hasRole('HOST') && renderHostDashboard()}
      {hasRole('ADVERTISER') && renderAdvertiserDashboard()}
    </div>
  );
}
