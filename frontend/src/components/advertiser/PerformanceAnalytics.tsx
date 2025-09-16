'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Eye,
  MousePointer,
  Users,
  DollarSign,
  BarChart3,
  PieChart as PieChartIcon,
  Calendar,
  MapPin,
  Clock,
  Target,
  Star,
  Award,
  Download,
  Filter,
  RefreshCw,
  Zap,
  Activity,
  Layers,
  Globe,
  Settings,
  Video
} from 'lucide-react';

interface PerformanceMetric {
  impressions: number;
  clicks: number;
  ctr: number;
  reach: number;
  engagement: number;
  cost: number;
  revenue: number;
  roas: number;
}

interface CampaignPerformance {
  id: string;
  name: string;
  status: string;
  startDate: Date;
  endDate: Date;
  budget: number;
  spent: number;
  metrics: PerformanceMetric;
  locations: {
    name: string;
    city: string;
    performance: PerformanceMetric;
  }[];
}

interface TimeSeriesData {
  date: string;
  impressions: number;
  clicks: number;
  reach: number;
  cost: number;
  revenue: number;
}

interface DemographicData {
  segment: string;
  value: number;
  percentage: number;
  color: string;
}

export default function PerformanceAnalytics() {
  const [campaigns, setCampaigns] = useState<CampaignPerformance[]>([]);
  const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesData[]>([]);
  const [demographicData, setDemographicData] = useState<DemographicData[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<string>('all');
  const [dateRange, setDateRange] = useState<string>('30d');
  const [activeMetric, setActiveMetric] = useState<string>('impressions');

  // Mock data for development
  useEffect(() => {
    const mockCampaigns: CampaignPerformance[] = [
      {
        id: '1',
        name: 'Summer Sale 2024',
        status: 'active',
        startDate: new Date('2024-07-01'),
        endDate: new Date('2024-07-31'),
        budget: 5000,
        spent: 4185,
        metrics: {
          impressions: 83500,
          clicks: 3054,
          ctr: 3.66,
          reach: 60000,
          engagement: 1854,
          cost: 4185,
          revenue: 12875,
          roas: 3.08
        },
        locations: [
          {
            name: 'Downtown Shopping Mall',
            city: 'Seattle',
            performance: {
              impressions: 45000,
              clicks: 1200,
              ctr: 2.67,
              reach: 32000,
              engagement: 854,
              cost: 2325,
              revenue: 7250,
              roas: 3.12
            }
          },
          {
            name: 'Metro Food Hall',
            city: 'Seattle',
            performance: {
              impressions: 38500,
              clicks: 1854,
              ctr: 4.82,
              reach: 28000,
              engagement: 1000,
              cost: 1860,
              revenue: 5625,
              roas: 3.02
            }
          }
        ]
      },
      {
        id: '2',
        name: 'Brand Awareness Q3',
        status: 'pending',
        startDate: new Date('2024-08-01'),
        endDate: new Date('2024-09-30'),
        budget: 3000,
        spent: 0,
        metrics: {
          impressions: 0,
          clicks: 0,
          ctr: 0,
          reach: 0,
          engagement: 0,
          cost: 0,
          revenue: 0,
          roas: 0
        },
        locations: []
      }
    ];

    const mockTimeSeriesData: TimeSeriesData[] = [
      { date: '2024-07-01', impressions: 2500, clicks: 85, reach: 1800, cost: 125, revenue: 385 },
      { date: '2024-07-02', impressions: 2800, clicks: 102, reach: 2100, cost: 140, revenue: 425 },
      { date: '2024-07-03', impressions: 3200, clicks: 118, reach: 2400, cost: 160, revenue: 485 },
      { date: '2024-07-04', impressions: 2900, clicks: 95, reach: 2000, cost: 145, revenue: 395 },
      { date: '2024-07-05', impressions: 3500, clicks: 142, reach: 2650, cost: 175, revenue: 565 },
      { date: '2024-07-06', impressions: 3100, clicks: 125, reach: 2300, cost: 155, revenue: 485 },
      { date: '2024-07-07', impressions: 2700, clicks: 89, reach: 1950, cost: 135, revenue: 345 },
      { date: '2024-07-08', impressions: 3800, clicks: 156, reach: 2850, cost: 190, revenue: 625 },
      { date: '2024-07-09', impressions: 3400, clicks: 138, reach: 2500, cost: 170, revenue: 545 },
      { date: '2024-07-10', impressions: 3600, clicks: 148, reach: 2700, cost: 180, revenue: 585 }
    ];

    const mockDemographicData: DemographicData[] = [
      { segment: '18-24', value: 15420, percentage: 25.8, color: '#8884d8' },
      { segment: '25-34', value: 18750, percentage: 31.2, color: '#82ca9d' },
      { segment: '35-44', value: 14280, percentage: 23.8, color: '#ffc658' },
      { segment: '45-54', value: 8340, percentage: 13.9, color: '#ff7300' },
      { segment: '55+', value: 3210, percentage: 5.3, color: '#8dd1e1' }
    ];

    setCampaigns(mockCampaigns);
    setTimeSeriesData(mockTimeSeriesData);
    setDemographicData(mockDemographicData);
  }, []);

  const getSelectedCampaignData = () => {
    if (selectedCampaign === 'all') {
      return campaigns.reduce((total, campaign) => ({
        ...total,
        metrics: {
          impressions: total.metrics.impressions + campaign.metrics.impressions,
          clicks: total.metrics.clicks + campaign.metrics.clicks,
          ctr: campaigns.length > 0 ? 
            (total.metrics.clicks + campaign.metrics.clicks) / 
            (total.metrics.impressions + campaign.metrics.impressions) * 100 : 0,
          reach: total.metrics.reach + campaign.metrics.reach,
          engagement: total.metrics.engagement + campaign.metrics.engagement,
          cost: total.metrics.cost + campaign.metrics.cost,
          revenue: total.metrics.revenue + campaign.metrics.revenue,
          roas: total.metrics.cost > 0 ? 
            (total.metrics.revenue + campaign.metrics.revenue) / 
            (total.metrics.cost + campaign.metrics.cost) : 0
        },
        budget: total.budget + campaign.budget,
        spent: total.spent + campaign.spent
      }), {
        metrics: { impressions: 0, clicks: 0, ctr: 0, reach: 0, engagement: 0, cost: 0, revenue: 0, roas: 0 },
        budget: 0,
        spent: 0
      });
    }
    return campaigns.find(c => c.id === selectedCampaign);
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const getPerformanceColor = (current: number, benchmark: number) => {
    if (current > benchmark * 1.1) return 'text-green-600';
    if (current < benchmark * 0.9) return 'text-red-600';
    return 'text-yellow-600';
  };

  const selectedData = getSelectedCampaignData();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Performance Analytics</h2>
          <p className="text-gray-600">Monitor and analyze your campaign performance</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
          <Button variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex space-x-4">
        <Select value={selectedCampaign} onValueChange={setSelectedCampaign}>
          <SelectTrigger className="w-64">
            <SelectValue placeholder="Select Campaign" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Campaigns</SelectItem>
            {campaigns.map(campaign => (
              <SelectItem key={campaign.id} value={campaign.id}>
                {campaign.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        
        <Select value={dateRange} onValueChange={setDateRange}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Date Range" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7d">Last 7 days</SelectItem>
            <SelectItem value="30d">Last 30 days</SelectItem>
            <SelectItem value="90d">Last 90 days</SelectItem>
            <SelectItem value="1y">Last year</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Key Metrics */}
      {selectedData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Impressions</p>
                  <p className="text-2xl font-bold">
                    {formatNumber(selectedData.metrics.impressions)}
                  </p>
                  <p className="text-sm text-green-600 flex items-center mt-1">
                    <TrendingUp className="h-3 w-3 mr-1" />
                    +12.5% vs last period
                  </p>
                </div>
                <Eye className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Click-Through Rate</p>
                  <p className="text-2xl font-bold">
                    {selectedData.metrics.ctr.toFixed(2)}%
                  </p>
                  <p className="text-sm text-green-600 flex items-center mt-1">
                    <TrendingUp className="h-3 w-3 mr-1" />
                    +0.8% vs industry avg
                  </p>
                </div>
                <MousePointer className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Reach</p>
                  <p className="text-2xl font-bold">
                    {formatNumber(selectedData.metrics.reach)}
                  </p>
                  <p className="text-sm text-blue-600 flex items-center mt-1">
                    <Users className="h-3 w-3 mr-1" />
                    {((selectedData.metrics.reach / selectedData.metrics.impressions) * 100).toFixed(1)}% unique
                  </p>
                </div>
                <Users className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">ROAS</p>
                  <p className="text-2xl font-bold">
                    {selectedData.metrics.roas.toFixed(2)}x
                  </p>
                  <p className="text-sm text-green-600 flex items-center mt-1">
                    <DollarSign className="h-3 w-3 mr-1" />
                    {formatCurrency(selectedData.metrics.revenue)} revenue
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Charts Section */}
      <Tabs defaultValue="performance" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="performance">Performance Trends</TabsTrigger>
          <TabsTrigger value="demographics">Demographics</TabsTrigger>
          <TabsTrigger value="locations">Location Analysis</TabsTrigger>
          <TabsTrigger value="insights">Insights</TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Performance Over Time */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BarChart3 className="h-5 w-5 mr-2" />
                  Performance Over Time
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mb-4">
                  <Select value={activeMetric} onValueChange={setActiveMetric}>
                    <SelectTrigger className="w-48">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="impressions">Impressions</SelectItem>
                      <SelectItem value="clicks">Clicks</SelectItem>
                      <SelectItem value="reach">Reach</SelectItem>
                      <SelectItem value="revenue">Revenue</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={timeSeriesData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    />
                    <YAxis tickFormatter={formatNumber} />
                    <Tooltip 
                      labelFormatter={(value) => new Date(value).toLocaleDateString()}
                      formatter={(value: number) => [formatNumber(value), activeMetric]}
                    />
                    <Line 
                      type="monotone" 
                      dataKey={activeMetric} 
                      stroke="#8884d8" 
                      strokeWidth={2}
                      dot={{ fill: '#8884d8' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Cost vs Revenue */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <DollarSign className="h-5 w-5 mr-2" />
                  Cost vs Revenue
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={timeSeriesData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    />
                    <YAxis tickFormatter={(value) => `$${value}`} />
                    <Tooltip 
                      labelFormatter={(value) => new Date(value).toLocaleDateString()}
                      formatter={(value: number) => [`$${value}`, value === timeSeriesData[0]?.cost ? 'Cost' : 'Revenue']}
                    />
                    <Area type="monotone" dataKey="cost" stackId="1" stroke="#ff7300" fill="#ff7300" />
                    <Area type="monotone" dataKey="revenue" stackId="2" stroke="#82ca9d" fill="#82ca9d" />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="demographics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Age Demographics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <PieChartIcon className="h-5 w-5 mr-2" />
                  Audience Demographics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={demographicData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ segment, percentage }) => `${segment} (${percentage.toFixed(1)}%)`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {demographicData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => [formatNumber(value), 'Reach']} />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Engagement by Segment */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Activity className="h-5 w-5 mr-2" />
                  Engagement by Segment
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={demographicData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="segment" />
                    <YAxis />
                    <Tooltip formatter={(value: number) => [formatNumber(value), 'Engagement']} />
                    <Bar dataKey="value" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="locations" className="space-y-4">
          {selectedData && selectedData.locations && selectedData.locations.length > 0 && (
            <div className="space-y-4">
              {selectedData.locations.map((location, index) => (
                <Card key={index}>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <MapPin className="h-5 w-5 mr-2" />
                      {location.name} - {location.city}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <p className="text-2xl font-bold text-blue-600">
                          {formatNumber(location.performance.impressions)}
                        </p>
                        <p className="text-sm text-gray-600">Impressions</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-green-600">
                          {location.performance.ctr.toFixed(2)}%
                        </p>
                        <p className="text-sm text-gray-600">CTR</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-purple-600">
                          {formatNumber(location.performance.reach)}
                        </p>
                        <p className="text-sm text-gray-600">Reach</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-orange-600">
                          {location.performance.roas.toFixed(2)}x
                        </p>
                        <p className="text-sm text-gray-600">ROAS</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="insights" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Performance Insights */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Zap className="h-5 w-5 mr-2" />
                  Performance Insights
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Alert>
                  <TrendingUp className="h-4 w-4" />
                  <AlertDescription>
                    Your CTR is 18% above industry average. Consider expanding budget to high-performing time slots.
                  </AlertDescription>
                </Alert>
                <Alert>
                  <Target className="h-4 w-4" />
                  <AlertDescription>
                    Best performance between 2-4 PM. Consider shifting more budget to these hours.
                  </AlertDescription>
                </Alert>
                <Alert>
                  <Star className="h-4 w-4" />
                  <AlertDescription>
                    Metro Food Hall location shows 60% higher engagement than average.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>

            {/* Recommendations */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Award className="h-5 w-5 mr-2" />
                  Optimization Recommendations
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-3 bg-green-50 rounded-lg">
                  <h4 className="font-semibold text-green-800">Budget Optimization</h4>
                  <p className="text-sm text-green-700">
                    Increase budget by 25% to capture 40% more impressions during peak hours.
                  </p>
                </div>
                <div className="p-3 bg-blue-50 rounded-lg">
                  <h4 className="font-semibold text-blue-800">Content Strategy</h4>
                  <p className="text-sm text-blue-700">
                    Video content performs 35% better than static images. Consider more video campaigns.
                  </p>
                </div>
                <div className="p-3 bg-purple-50 rounded-lg">
                  <h4 className="font-semibold text-purple-800">Location Expansion</h4>
                  <p className="text-sm text-purple-700">
                    Similar venues in Bellevue show high engagement potential for your target audience.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Campaign Comparison */}
      {campaigns.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Campaign Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Campaign</th>
                    <th className="text-right py-2">Impressions</th>
                    <th className="text-right py-2">CTR</th>
                    <th className="text-right py-2">Reach</th>
                    <th className="text-right py-2">Spent</th>
                    <th className="text-right py-2">ROAS</th>
                    <th className="text-center py-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {campaigns.map((campaign) => (
                    <tr key={campaign.id} className="border-b">
                      <td className="py-3">
                        <div>
                          <p className="font-medium">{campaign.name}</p>
                          <p className="text-sm text-gray-600">
                            {campaign.startDate.toLocaleDateString()} - {campaign.endDate.toLocaleDateString()}
                          </p>
                        </div>
                      </td>
                      <td className="text-right py-3">
                        {formatNumber(campaign.metrics.impressions)}
                      </td>
                      <td className="text-right py-3">
                        {campaign.metrics.ctr.toFixed(2)}%
                      </td>
                      <td className="text-right py-3">
                        {formatNumber(campaign.metrics.reach)}
                      </td>
                      <td className="text-right py-3">
                        {formatCurrency(campaign.spent)}
                      </td>
                      <td className="text-right py-3">
                        {campaign.metrics.roas.toFixed(2)}x
                      </td>
                      <td className="text-center py-3">
                        <Badge variant={campaign.status === 'active' ? 'default' : 'secondary'}>
                          {campaign.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}