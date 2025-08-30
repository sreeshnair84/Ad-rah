'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  BarChart,
  Bar,
} from 'recharts';
import { Download, FileText, BarChart3 } from 'lucide-react';

export default function PerformancePage() {
  // Mock data - in real app this would come from hooks
  const performanceData = [
    { name: "00:00", value: 120 },
    { name: "04:00", value: 180 },
    { name: "08:00", value: 420 },
    { name: "12:00", value: 640 },
    { name: "16:00", value: 510 },
    { name: "20:00", value: 380 },
  ];

  const topSitesData = [
    { name: "Mall of the Emirates", plays: 9800 },
    { name: "Dubai Mall", plays: 12900 },
    { name: "DIFC Gate", plays: 7200 },
    { name: "DXB T3", plays: 15400 },
  ];

  return (
    <div className="grid gap-6 p-6 lg:grid-cols-3 h-full">
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Performance Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={performanceData}>
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
          <CardTitle>Top Sites (This Week)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topSitesData}>
                <XAxis dataKey="name" hide />
                <YAxis />
                <Tooltip />
                <Bar dataKey="plays" radius={[8,8,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card className="lg:col-span-3">
        <CardHeader>
          <CardTitle>Detailed Analytics</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="engagement" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="engagement">Engagement Data</TabsTrigger>
              <TabsTrigger value="ctr">Ad CTR</TabsTrigger>
              <TabsTrigger value="utilization">Screen Utilization</TabsTrigger>
            </TabsList>
            <TabsContent value="engagement" className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-xl border p-4">
                  <p className="text-sm font-medium">Total Views</p>
                  <p className="text-2xl font-bold">45,678</p>
                  <p className="text-xs text-muted-foreground">+12% from last week</p>
                </div>
                <div className="rounded-xl border p-4">
                  <p className="text-sm font-medium">Avg. View Time</p>
                  <p className="text-2xl font-bold">24s</p>
                  <p className="text-xs text-muted-foreground">+5% from last week</p>
                </div>
                <div className="rounded-xl border p-4">
                  <p className="text-sm font-medium">Bounce Rate</p>
                  <p className="text-2xl font-bold">23%</p>
                  <p className="text-xs text-muted-foreground">-3% from last week</p>
                </div>
                <div className="rounded-xl border p-4">
                  <p className="text-sm font-medium">Interactions</p>
                  <p className="text-2xl font-bold">1,234</p>
                  <p className="text-xs text-muted-foreground">+8% from last week</p>
                </div>
              </div>
            </TabsContent>
            <TabsContent value="ctr" className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-xl border p-4">
                  <p className="text-sm font-medium">Overall CTR</p>
                  <p className="text-2xl font-bold">2.7%</p>
                  <p className="text-xs text-muted-foreground">+0.5% from last week</p>
                </div>
                <div className="rounded-xl border p-4">
                  <p className="text-sm font-medium">Top Performing Ad</p>
                  <p className="text-2xl font-bold">Pizza Ad</p>
                  <p className="text-xs text-muted-foreground">4.2% CTR</p>
                </div>
                <div className="rounded-xl border p-4">
                  <p className="text-sm font-medium">Worst Performing Ad</p>
                  <p className="text-2xl font-bold">Fashion Sale</p>
                  <p className="text-xs text-muted-foreground">1.1% CTR</p>
                </div>
                <div className="rounded-xl border p-4">
                  <p className="text-sm font-medium">Conversion Rate</p>
                  <p className="text-2xl font-bold">0.8%</p>
                  <p className="text-xs text-muted-foreground">+0.2% from last week</p>
                </div>
              </div>
            </TabsContent>
            <TabsContent value="utilization" className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-xl border p-4">
                  <p className="text-sm font-medium">Active Screens</p>
                  <p className="text-2xl font-bold">24/25</p>
                  <p className="text-xs text-muted-foreground">96% uptime</p>
                </div>
                <div className="rounded-xl border p-4">
                  <p className="text-sm font-medium">Avg. Utilization</p>
                  <p className="text-2xl font-bold">78%</p>
                  <p className="text-xs text-muted-foreground">+2% from last week</p>
                </div>
                <div className="rounded-xl border p-4">
                  <p className="text-sm font-medium">Peak Hours</p>
                  <p className="text-2xl font-bold">12PM-4PM</p>
                  <p className="text-xs text-muted-foreground">Highest activity</p>
                </div>
                <div className="rounded-xl border p-4">
                  <p className="text-sm font-medium">Maintenance Alerts</p>
                  <p className="text-2xl font-bold">2</p>
                  <p className="text-xs text-muted-foreground">Requires attention</p>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <Card className="lg:col-span-3">
        <CardHeader>
          <CardTitle>Export Data</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Button variant="outline" className="gap-2">
              <Download className="h-4 w-4" />
              Export CSV
            </Button>
            <Button variant="outline" className="gap-2">
              <FileText className="h-4 w-4" />
              Export PDF
            </Button>
            <Button variant="outline" className="gap-2">
              <BarChart3 className="h-4 w-4" />
              Power BI Link
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
