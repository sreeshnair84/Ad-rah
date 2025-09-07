'use client';

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Area,
  AreaChart
} from 'recharts';
import { 
  TrendingUp, 
  Users, 
  Monitor, 
  DollarSign, 
  Clock, 
  Eye,
  MousePointer,
  Wifi,
  WifiOff,
  Calendar,
  Target,
  Activity
} from 'lucide-react';

interface DeviceAnalytics {
  deviceId: string;
  deviceName: string;
  isOnline: boolean;
  lastSeen: string;
  runtime: {
    totalHours: number;
    activeHours: number;
    idleHours: number;
  };
  contentMetrics: {
    impressions: number;
    interactions: number;
    completions: number;
    errors: number;
  };
  proximityData: {
    totalDetections: number;
    uniqueUsers: number;
    averageEngagementTime: number;
    peakHours: string[];
  };
  monetization: {
    totalRevenue: number;
    adImpressions: number;
    clickthrough: number;
    averageCPM: number;
  };
  systemHealth: {
    cpuUsage: number;
    memoryUsage: number;
    storageUsage: number;
    networkLatency: number;
  };
}

interface AnalyticsData {
  devices: DeviceAnalytics[];
  summary: {
    totalDevices: number;
    onlineDevices: number;
    totalRevenue: number;
    totalImpressions: number;
    averageEngagement: number;
  };
  timeSeriesData: Array<{
    timestamp: string;
    impressions: number;
    interactions: number;
    revenue: number;
    proximityDetections: number;
  }>;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

export default function AnalyticsDashboard() {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
  const [selectedDevice, setSelectedDevice] = useState<string>('all');

  useEffect(() => {
    fetchAnalyticsData();
    
    // Set up real-time updates
    const interval = setInterval(fetchAnalyticsData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, [selectedTimeRange, selectedDevice]);

  const fetchAnalyticsData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/analytics/dashboard?timeRange=${selectedTimeRange}&device=${selectedDevice}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch analytics data');
      }

      const data = await response.json();
      setAnalyticsData(data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching analytics:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const formatDuration = (hours: number) => {
    const h = Math.floor(hours);
    const m = Math.floor((hours - h) * 60);
    return `${h}h ${m}m`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="m-6">
        <CardContent className="pt-6">
          <div className="text-center text-red-600">
            <p>Error loading analytics: {error}</p>
            <button 
              onClick={fetchAnalyticsData}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Retry
            </button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!analyticsData) {
    return (
      <Card className="m-6">
        <CardContent className="pt-6">
          <p className="text-center text-gray-500">No analytics data available</p>
        </CardContent>
      </Card>
    );
  }

  const { devices, summary, timeSeriesData } = analyticsData;

  return (
    <div className="p-6 space-y-6">
      {/* Header with Controls */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600 mt-1">Digital Signage Platform Performance</p>
        </div>
        
        <div className="flex space-x-4">
          <select 
            value={selectedTimeRange} 
            onChange={(e) => setSelectedTimeRange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
          
          <select 
            value={selectedDevice} 
            onChange={(e) => setSelectedDevice(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Devices</option>
            {devices.map(device => (
              <option key={device.deviceId} value={device.deviceId}>
                {device.deviceName}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Devices</CardTitle>
            <Monitor className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.totalDevices}</div>
            <div className="flex items-center text-xs text-muted-foreground">
              <Wifi className="h-3 w-3 mr-1 text-green-500" />
              {summary.onlineDevices} online
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(summary.totalRevenue)}</div>
            <p className="text-xs text-muted-foreground">
              +12.3% from last period
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Impressions</CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(summary.totalImpressions)}</div>
            <p className="text-xs text-muted-foreground">
              Content views across all devices
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Engagement</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.averageEngagement.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              User interaction rate
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Live Activity</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {devices.filter(d => d.isOnline).length}
            </div>
            <p className="text-xs text-muted-foreground">
              Active devices now
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Time Series Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="col-span-1 lg:col-span-2">
          <CardHeader>
            <CardTitle>Performance Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={timeSeriesData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="timestamp" 
                  tickFormatter={(value) => new Date(value).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(value) => new Date(value).toLocaleString()}
                />
                <Legend />
                <Area type="monotone" dataKey="impressions" stackId="1" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
                <Area type="monotone" dataKey="interactions" stackId="1" stroke="#82ca9d" fill="#82ca9d" fillOpacity={0.6} />
                <Area type="monotone" dataKey="proximityDetections" stackId="1" stroke="#ffc658" fill="#ffc658" fillOpacity={0.6} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Revenue and Monetization */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Revenue by Device</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={devices.map(device => ({
                name: device.deviceName,
                revenue: device.monetization.totalRevenue,
                impressions: device.monetization.adImpressions
              }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value, name) => [
                  name === 'revenue' ? formatCurrency(value as number) : formatNumber(value as number),
                  name === 'revenue' ? 'Revenue' : 'Ad Impressions'
                ]} />
                <Legend />
                <Bar dataKey="revenue" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Device Status Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'Online', value: devices.filter(d => d.isOnline).length, color: '#00C49F' },
                    { name: 'Offline', value: devices.filter(d => !d.isOnline).length, color: '#FF8042' }
                  ]}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {[
                    { name: 'Online', value: devices.filter(d => d.isOnline).length, color: '#00C49F' },
                    { name: 'Offline', value: devices.filter(d => !d.isOnline).length, color: '#FF8042' }
                  ].map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Device Details Table */}
      <Card>
        <CardHeader>
          <CardTitle>Device Performance Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Device</th>
                  <th className="text-left p-2">Status</th>
                  <th className="text-left p-2">Runtime</th>
                  <th className="text-left p-2">Impressions</th>
                  <th className="text-left p-2">Interactions</th>
                  <th className="text-left p-2">Revenue</th>
                  <th className="text-left p-2">Users Detected</th>
                  <th className="text-left p-2">Avg Engagement</th>
                </tr>
              </thead>
              <tbody>
                {devices.map((device) => (
                  <tr key={device.deviceId} className="border-b hover:bg-gray-50">
                    <td className="p-2">
                      <div>
                        <div className="font-medium">{device.deviceName}</div>
                        <div className="text-gray-500 text-xs">{device.deviceId}</div>
                      </div>
                    </td>
                    <td className="p-2">
                      <div className="flex items-center">
                        {device.isOnline ? (
                          <Wifi className="h-4 w-4 text-green-500 mr-1" />
                        ) : (
                          <WifiOff className="h-4 w-4 text-red-500 mr-1" />
                        )}
                        <span className={device.isOnline ? 'text-green-600' : 'text-red-600'}>
                          {device.isOnline ? 'Online' : 'Offline'}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500">
                        Last seen: {new Date(device.lastSeen).toLocaleString()}
                      </div>
                    </td>
                    <td className="p-2">
                      <div>{formatDuration(device.runtime.totalHours)}</div>
                      <div className="text-xs text-gray-500">
                        Active: {formatDuration(device.runtime.activeHours)}
                      </div>
                    </td>
                    <td className="p-2">{formatNumber(device.contentMetrics.impressions)}</td>
                    <td className="p-2">{formatNumber(device.contentMetrics.interactions)}</td>
                    <td className="p-2">{formatCurrency(device.monetization.totalRevenue)}</td>
                    <td className="p-2">
                      <div>{formatNumber(device.proximityData.totalDetections)}</div>
                      <div className="text-xs text-gray-500">
                        Unique: {formatNumber(device.proximityData.uniqueUsers)}
                      </div>
                    </td>
                    <td className="p-2">
                      {formatDuration(device.proximityData.averageEngagementTime)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* System Health Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {devices.filter(d => d.isOnline).map((device) => (
          <Card key={device.deviceId}>
            <CardHeader>
              <CardTitle className="text-sm">{device.deviceName} Health</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-xs">CPU:</span>
                  <span className="text-xs font-medium">{device.systemHealth.cpuUsage.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${device.systemHealth.cpuUsage}%` }}
                  ></div>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-xs">Memory:</span>
                  <span className="text-xs font-medium">{device.systemHealth.memoryUsage.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-green-600 h-2 rounded-full" 
                    style={{ width: `${device.systemHealth.memoryUsage}%` }}
                  ></div>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-xs">Storage:</span>
                  <span className="text-xs font-medium">{device.systemHealth.storageUsage.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-yellow-600 h-2 rounded-full" 
                    style={{ width: `${device.systemHealth.storageUsage}%` }}
                  ></div>
                </div>
                
                <div className="flex justify-between pt-2">
                  <span className="text-xs">Latency:</span>
                  <span className="text-xs font-medium">{device.systemHealth.networkLatency}ms</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
