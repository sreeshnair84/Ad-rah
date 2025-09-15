'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Monitor, 
  Activity, 
  Users, 
  Play, 
  Pause, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  Thermometer,
  Cpu,
  HardDrive,
  Wifi,
  Eye,
  Clock,
  TrendingUp,
  Calendar
} from 'lucide-react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

// Types for device analytics
interface DeviceMetrics {
  deviceId: string;
  deviceName: string;
  isOnline: boolean;
  lastHeartbeat: string;
  location: string;
  currentContent?: {
    id: string;
    name: string;
    type: string;
    startTime: string;
    duration: number;
    progress: number;
  };
  systemHealth: {
    cpuUsage: number;
    memoryUsage: number;
    diskUsage: number;
    temperature: number;
    networkLatency: number;
    overallScore: number;
    status: 'excellent' | 'good' | 'fair' | 'poor' | 'critical';
  };
  contentMetrics: {
    impressions: number;
    interactions: number;
    completions: number;
    errors: number;
    averageLoadTime: number;
  };
  audienceMetrics: {
    currentCount: number;
    totalDetections: number;
    averageDwellTime: number;
    peakCount: number;
    detectionConfidence: number;
  };
  monetization: {
    totalRevenue: number;
    adImpressions: number;
    clickthroughRate: number;
    averageCPM: number;
  };
}

interface AnalyticsSummary {
  totalDevices: number;
  onlineDevices: number;
  totalRevenue: number;
  totalImpressions: number;
  averageEngagement: number;
  totalAudience: number;
  averageHealth: number;
}

interface TimeSeriesData {
  timestamp: string;
  impressions: number;
  interactions: number;
  revenue: number;
  audienceCount: number;
}

interface DigitalTwinDashboardProps {
  timeRange?: '1h' | '24h' | '7d' | '30d';
  selectedDevice?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export default function DigitalTwinDashboard({
  timeRange = '24h',
  selectedDevice = 'all',
  autoRefresh = true,
  refreshInterval = 30000
}: DigitalTwinDashboardProps) {
  const [devices, setDevices] = useState<DeviceMetrics[]>([]);
  const [summary, setSummary] = useState<AnalyticsSummary>({
    totalDevices: 0,
    onlineDevices: 0,
    totalRevenue: 0,
    totalImpressions: 0,
    averageEngagement: 0,
    totalAudience: 0,
    averageHealth: 0
  });
  const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesData[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [selectedTab, setSelectedTab] = useState('overview');
  const [ws, setWs] = useState<WebSocket | null>(null);

  // Fetch analytics data from backend
  const fetchAnalyticsData = useCallback(async () => {
    try {
      const response = await fetch(`/api/analytics/dashboard?timeRange=${timeRange}&device=${selectedDevice}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setDevices(data.devices || []);
        setSummary(data.summary || summary);
        setTimeSeriesData(data.timeSeriesData || []);
        setLastUpdated(new Date());
      } else {
        console.error('Failed to fetch analytics data:', response.statusText);
      }
    } catch (error) {
      console.error('Error fetching analytics data:', error);
    } finally {
      setLoading(false);
    }
  }, [timeRange, selectedDevice]);

  // Setup WebSocket for real-time updates
  useEffect(() => {
    if (autoRefresh) {
      const websocket = new WebSocket(`ws://localhost:8000/api/analytics/stream`);
      
      websocket.onopen = () => {
        console.log('Connected to analytics WebSocket');
        websocket.send(JSON.stringify({
          type: 'subscribe_metrics',
          metric_types: ['device', 'content', 'audience', 'revenue']
        }));
      };

      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'metrics_update') {
          // Update specific device metrics in real-time
          setDevices(prev => prev.map(device => {
            const update = data.metrics.devices?.find((d: any) => d.deviceId === device.deviceId);
            return update ? { ...device, ...update } : device;
          }));
          
          if (data.metrics.summary) {
            setSummary(data.metrics.summary);
          }
        }
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      setWs(websocket);

      return () => {
        websocket.close();
      };
    }
  }, [autoRefresh]);

  // Initial data load and periodic refresh
  useEffect(() => {
    fetchAnalyticsData();
    
    if (autoRefresh && !ws) {
      const interval = setInterval(fetchAnalyticsData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchAnalyticsData, autoRefresh, refreshInterval, ws]);

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'excellent': return 'text-green-600';
      case 'good': return 'text-blue-600';
      case 'fair': return 'text-yellow-600';
      case 'poor': return 'text-orange-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'excellent': return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'good': return <CheckCircle className="h-4 w-4 text-blue-600" />;
      case 'fair': return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'poor': return <AlertTriangle className="h-4 w-4 text-orange-600" />;
      case 'critical': return <XCircle className="h-4 w-4 text-red-600" />;
      default: return <Activity className="h-4 w-4 text-gray-600" />;
    }
  };

  // Chart configurations
  const timeSeriesChartData = {
    labels: timeSeriesData.map(d => new Date(d.timestamp).toLocaleTimeString()),
    datasets: [
      {
        label: 'Impressions',
        data: timeSeriesData.map(d => d.impressions),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.1,
      },
      {
        label: 'Audience Count',
        data: timeSeriesData.map(d => d.audienceCount),
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.1,
        yAxisID: 'y1',
      },
    ],
  };

  const deviceHealthChartData = {
    labels: ['Excellent', 'Good', 'Fair', 'Poor', 'Critical'],
    datasets: [
      {
        data: [
          devices.filter(d => d.systemHealth.status === 'excellent').length,
          devices.filter(d => d.systemHealth.status === 'good').length,
          devices.filter(d => d.systemHealth.status === 'fair').length,
          devices.filter(d => d.systemHealth.status === 'poor').length,
          devices.filter(d => d.systemHealth.status === 'critical').length,
        ],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(234, 179, 8, 0.8)',
          'rgba(249, 115, 22, 0.8)',
          'rgba(239, 68, 68, 0.8)',
        ],
      },
    ],
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Digital Twin Dashboard</h1>
          <p className="text-muted-foreground">
            Real-time device monitoring and analytics • Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchAnalyticsData} disabled={loading}>
            <Activity className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Badge variant={autoRefresh ? "default" : "secondary"}>
            {autoRefresh ? "Live" : "Manual"}
          </Badge>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Devices</CardTitle>
            <Monitor className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.totalDevices}</div>
            <p className="text-xs text-muted-foreground">
              {summary.onlineDevices} online ({((summary.onlineDevices / summary.totalDevices) * 100).toFixed(1)}%)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${summary.totalRevenue.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              {summary.totalImpressions.toLocaleString()} impressions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Engagement</CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.averageEngagement.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              {summary.totalAudience.toLocaleString()} total viewers
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(summary.averageHealth * 100).toFixed(0)}%</div>
            <p className="text-xs text-muted-foreground">
              Average across all devices
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="devices">Device Details</TabsTrigger>
          <TabsTrigger value="content">Content Performance</TabsTrigger>
          <TabsTrigger value="audience">Audience Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            {/* Performance Trends */}
            <Card>
              <CardHeader>
                <CardTitle>Performance Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <Line 
                    data={timeSeriesChartData} 
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: {
                        y: {
                          type: 'linear',
                          display: true,
                          position: 'left',
                        },
                        y1: {
                          type: 'linear',
                          display: true,
                          position: 'right',
                          grid: {
                            drawOnChartArea: false,
                          },
                        },
                      },
                    }}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Device Health Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Device Health Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <Doughnut 
                    data={deviceHealthChartData} 
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                    }}
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Top Performing Devices */}
          <Card>
            <CardHeader>
              <CardTitle>Top Performing Devices</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {devices
                  .sort((a, b) => b.systemHealth.overallScore - a.systemHealth.overallScore)
                  .slice(0, 5)
                  .map((device) => (
                    <div key={device.deviceId} className="flex items-center justify-between p-3 rounded-lg border">
                      <div className="flex items-center gap-3">
                        {getHealthIcon(device.systemHealth.status)}
                        <div>
                          <p className="font-medium">{device.deviceName}</p>
                          <p className="text-sm text-muted-foreground">
                            {device.location} • {device.isOnline ? 'Online' : 'Offline'}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">{(device.systemHealth.overallScore * 100).toFixed(0)}%</p>
                        <p className="text-sm text-muted-foreground">
                          {device.contentMetrics.impressions.toLocaleString()} impressions
                        </p>
                      </div>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="devices" className="space-y-6">
          <div className="grid gap-6">
            {devices.map((device) => (
              <Card key={device.deviceId}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        {getHealthIcon(device.systemHealth.status)}
                        {device.deviceName}
                        <Badge variant={device.isOnline ? "default" : "secondary"}>
                          {device.isOnline ? "Online" : "Offline"}
                        </Badge>
                      </CardTitle>
                      <p className="text-sm text-muted-foreground">{device.location}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-muted-foreground">
                        Last heartbeat: {new Date(device.lastHeartbeat).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-3">
                    {/* Current Content */}
                    <div className="space-y-2">
                      <h4 className="font-medium">Current Content</h4>
                      {device.currentContent ? (
                        <div className="space-y-2">
                          <p className="text-sm">{device.currentContent.name}</p>
                          <Progress value={device.currentContent.progress} className="w-full" />
                          <p className="text-xs text-muted-foreground">
                            {device.currentContent.progress.toFixed(1)}% complete
                          </p>
                        </div>
                      ) : (
                        <p className="text-sm text-muted-foreground">No content playing</p>
                      )}
                    </div>

                    {/* System Health */}
                    <div className="space-y-2">
                      <h4 className="font-medium">System Health</h4>
                      <div className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span>CPU</span>
                          <span>{device.systemHealth.cpuUsage.toFixed(1)}%</span>
                        </div>
                        <Progress value={device.systemHealth.cpuUsage} className="w-full" />
                        
                        <div className="flex justify-between text-sm">
                          <span>Memory</span>
                          <span>{device.systemHealth.memoryUsage.toFixed(1)}%</span>
                        </div>
                        <Progress value={device.systemHealth.memoryUsage} className="w-full" />
                        
                        <div className="flex justify-between text-sm">
                          <span>Temperature</span>
                          <span>{device.systemHealth.temperature.toFixed(1)}°C</span>
                        </div>
                      </div>
                    </div>

                    {/* Performance Metrics */}
                    <div className="space-y-2">
                      <h4 className="font-medium">Performance</h4>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <p className="text-muted-foreground">Impressions</p>
                          <p className="font-medium">{device.contentMetrics.impressions.toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Interactions</p>
                          <p className="font-medium">{device.contentMetrics.interactions.toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Audience</p>
                          <p className="font-medium">{device.audienceMetrics.currentCount}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Revenue</p>
                          <p className="font-medium">${device.monetization.totalRevenue.toFixed(2)}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="content" className="space-y-6">
          <div className="grid gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Content Performance Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold">
                      {devices.reduce((sum, d) => sum + d.contentMetrics.impressions, 0).toLocaleString()}
                    </p>
                    <p className="text-sm text-muted-foreground">Total Impressions</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold">
                      {devices.reduce((sum, d) => sum + d.contentMetrics.interactions, 0).toLocaleString()}
                    </p>
                    <p className="text-sm text-muted-foreground">Total Interactions</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold">
                      {(devices.reduce((sum, d) => sum + d.contentMetrics.averageLoadTime, 0) / devices.length).toFixed(1)}s
                    </p>
                    <p className="text-sm text-muted-foreground">Avg Load Time</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold">
                      {((devices.reduce((sum, d) => sum + d.contentMetrics.completions, 0) / 
                         devices.reduce((sum, d) => sum + d.contentMetrics.impressions, 0)) * 100).toFixed(1)}%
                    </p>
                    <p className="text-sm text-muted-foreground">Completion Rate</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="audience" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Real-time Audience</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center space-y-4">
                  <div className="text-4xl font-bold">
                    {devices.reduce((sum, d) => sum + d.audienceMetrics.currentCount, 0)}
                  </div>
                  <p className="text-muted-foreground">People currently viewing</p>
                  <div className="grid grid-cols-2 gap-4 mt-4">
                    <div>
                      <p className="text-xl font-semibold">
                        {(devices.reduce((sum, d) => sum + d.audienceMetrics.averageDwellTime, 0) / devices.length).toFixed(1)}m
                      </p>
                      <p className="text-sm text-muted-foreground">Avg Dwell Time</p>
                    </div>
                    <div>
                      <p className="text-xl font-semibold">
                        {Math.max(...devices.map(d => d.audienceMetrics.peakCount))}
                      </p>
                      <p className="text-sm text-muted-foreground">Peak Count</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Detection Confidence</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {devices.map((device) => (
                    <div key={device.deviceId} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>{device.deviceName}</span>
                        <span>{(device.audienceMetrics.detectionConfidence * 100).toFixed(1)}%</span>
                      </div>
                      <Progress value={device.audienceMetrics.detectionConfidence * 100} className="w-full" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}