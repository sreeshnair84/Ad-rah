'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  Eye,
  Clock,
  Calendar,
  Monitor,
  MapPin,
  Download,
  RefreshCw,
  Filter,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';

interface RevenueData {
  period: string;
  revenue: number;
  bookings: number;
  impressions: number;
  occupancyRate: number;
}

interface LocationPerformance {
  locationId: string;
  locationName: string;
  revenue: number;
  impressions: number;
  bookings: number;
  averageRate: number;
  occupancyRate: number;
  growth: number;
}

interface AdSlotPerformance {
  slotId: string;
  slotName: string;
  locationName: string;
  revenue: number;
  impressions: number;
  bookings: number;
  averageRate: number;
  performanceScore: number;
  lastBooking: string;
}

interface AudienceInsights {
  demographic: string;
  percentage: number;
  revenue: number;
  impressions: number;
}

interface BookingTrends {
  month: string;
  bookings: number;
  revenue: number;
  averageBookingValue: number;
  repeatCustomers: number;
}

export default function RevenueAnalytics() {
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState('30days');
  const [selectedLocation, setSelectedLocation] = useState('all');
  const [analyticsData, setAnalyticsData] = useState<{
    summary: {
      totalRevenue: number;
      totalBookings: number;
      totalImpressions: number;
      averageBookingValue: number;
      occupancyRate: number;
      revenueGrowth: number;
      bookingGrowth: number;
      impressionGrowth: number;
    };
    revenueData: RevenueData[];
    locationPerformance: LocationPerformance[];
    adSlotPerformance: AdSlotPerformance[];
    audienceInsights: AudienceInsights[];
    bookingTrends: BookingTrends[];
  }>({
    summary: {
      totalRevenue: 0,
      totalBookings: 0,
      totalImpressions: 0,
      averageBookingValue: 0,
      occupancyRate: 0,
      revenueGrowth: 0,
      bookingGrowth: 0,
      impressionGrowth: 0
    },
    revenueData: [],
    locationPerformance: [],
    adSlotPerformance: [],
    audienceInsights: [],
    bookingTrends: []
  });

  useEffect(() => {
    fetchAnalyticsData();
  }, [dateRange, selectedLocation]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      
      const response = await fetch(`/api/host/analytics/revenue?range=${dateRange}&location=${selectedLocation}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAnalyticsData(data);
      } else {
        // Mock data for development
        setAnalyticsData({
          summary: {
            totalRevenue: 47850.75,
            totalBookings: 124,
            totalImpressions: 856000,
            averageBookingValue: 385.89,
            occupancyRate: 78.5,
            revenueGrowth: 12.8,
            bookingGrowth: 8.4,
            impressionGrowth: 15.2
          },
          revenueData: [
            { period: 'Week 1', revenue: 8450, bookings: 18, impressions: 145000, occupancyRate: 65 },
            { period: 'Week 2', revenue: 12600, bookings: 32, impressions: 220000, occupancyRate: 75 },
            { period: 'Week 3', revenue: 15200, bookings: 38, impressions: 258000, occupancyRate: 82 },
            { period: 'Week 4', revenue: 11600, bookings: 36, impressions: 233000, occupancyRate: 79 }
          ],
          locationPerformance: [
            {
              locationId: '1',
              locationName: 'Downtown Shopping Mall',
              revenue: 28450.00,
              impressions: 485000,
              bookings: 68,
              averageRate: 418.38,
              occupancyRate: 85.2,
              growth: 15.6
            },
            {
              locationId: '2',
              locationName: 'Airport Terminal A',
              revenue: 15680.25,
              impressions: 312000,
              bookings: 38,
              averageRate: 412.64,
              occupancyRate: 72.8,
              growth: 8.9
            },
            {
              locationId: '3',
              locationName: 'University Campus Center',
              revenue: 3720.50,
              impressions: 59000,
              bookings: 18,
              averageRate: 206.69,
              occupancyRate: 65.3,
              growth: -2.1
            }
          ],
          adSlotPerformance: [
            {
              slotId: '1',
              slotName: 'Main Entrance Banner',
              locationName: 'Downtown Shopping Mall',
              revenue: 12840.50,
              impressions: 225000,
              bookings: 32,
              averageRate: 401.27,
              performanceScore: 92,
              lastBooking: '2024-12-10'
            },
            {
              slotId: '2',
              slotName: 'Food Court Fullscreen',
              locationName: 'Downtown Shopping Mall',
              revenue: 15609.50,
              impressions: 260000,
              bookings: 36,
              averageRate: 433.60,
              performanceScore: 96,
              lastBooking: '2024-12-11'
            },
            {
              slotId: '3',
              slotName: 'Gate A12 Sidebar',
              locationName: 'Airport Terminal A',
              revenue: 15680.25,
              impressions: 312000,
              bookings: 38,
              averageRate: 412.64,
              performanceScore: 88,
              lastBooking: '2024-12-09'
            }
          ],
          audienceInsights: [
            { demographic: 'Young Professionals (25-35)', percentage: 32, revenue: 15312.24, impressions: 273920 },
            { demographic: 'Families with Children', percentage: 28, revenue: 13398.21, impressions: 239680 },
            { demographic: 'Business Travelers', percentage: 22, revenue: 10527.17, impressions: 188320 },
            { demographic: 'Students (18-25)', percentage: 12, revenue: 5742.09, impressions: 102720 },
            { demographic: 'Seniors (55+)', percentage: 6, revenue: 2871.04, impressions: 51360 }
          ],
          bookingTrends: [
            { month: 'Sep', bookings: 89, revenue: 34250, averageBookingValue: 384.83, repeatCustomers: 23 },
            { month: 'Oct', bookings: 102, revenue: 39680, averageBookingValue: 389.02, repeatCustomers: 31 },
            { month: 'Nov', bookings: 118, revenue: 43210, averageBookingValue: 366.19, repeatCustomers: 42 },
            { month: 'Dec', bookings: 124, revenue: 47850, averageBookingValue: 385.89, repeatCustomers: 48 }
          ]
        });
      }
    } catch (error) {
      console.error('Failed to fetch analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-US').format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const getGrowthIcon = (growth: number) => {
    if (growth > 0) {
      return <ArrowUpRight className="h-4 w-4 text-green-600" />;
    } else if (growth < 0) {
      return <ArrowDownRight className="h-4 w-4 text-red-600" />;
    }
    return null;
  };

  const getGrowthColor = (growth: number) => {
    if (growth > 0) return 'text-green-600';
    if (growth < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Revenue Analytics</h2>
          <p className="text-gray-600 mt-1">
            Track your digital signage revenue performance and insights
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <Select value={dateRange} onValueChange={setDateRange}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7days">Last 7 Days</SelectItem>
              <SelectItem value="30days">Last 30 Days</SelectItem>
              <SelectItem value="90days">Last 90 Days</SelectItem>
              <SelectItem value="year">This Year</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={selectedLocation} onValueChange={setSelectedLocation}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Locations</SelectItem>
              <SelectItem value="1">Downtown Shopping Mall</SelectItem>
              <SelectItem value="2">Airport Terminal A</SelectItem>
              <SelectItem value="3">University Campus Center</SelectItem>
            </SelectContent>
          </Select>
          
          <Button variant="outline" size="sm" className="gap-2">
            <Download className="h-4 w-4" />
            Export
          </Button>
          
          <Button variant="outline" size="sm" onClick={fetchAnalyticsData}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Revenue</p>
                <p className="text-2xl font-bold">{formatCurrency(analyticsData.summary.totalRevenue)}</p>
                <div className="flex items-center gap-1 mt-1">
                  {getGrowthIcon(analyticsData.summary.revenueGrowth)}
                  <span className={`text-sm ${getGrowthColor(analyticsData.summary.revenueGrowth)}`}>
                    {formatPercentage(Math.abs(analyticsData.summary.revenueGrowth))}
                  </span>
                </div>
              </div>
              <DollarSign className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Bookings</p>
                <p className="text-2xl font-bold">{formatNumber(analyticsData.summary.totalBookings)}</p>
                <div className="flex items-center gap-1 mt-1">
                  {getGrowthIcon(analyticsData.summary.bookingGrowth)}
                  <span className={`text-sm ${getGrowthColor(analyticsData.summary.bookingGrowth)}`}>
                    {formatPercentage(Math.abs(analyticsData.summary.bookingGrowth))}
                  </span>
                </div>
              </div>
              <Calendar className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Impressions</p>
                <p className="text-2xl font-bold">{formatNumber(analyticsData.summary.totalImpressions)}</p>
                <div className="flex items-center gap-1 mt-1">
                  {getGrowthIcon(analyticsData.summary.impressionGrowth)}
                  <span className={`text-sm ${getGrowthColor(analyticsData.summary.impressionGrowth)}`}>
                    {formatPercentage(Math.abs(analyticsData.summary.impressionGrowth))}
                  </span>
                </div>
              </div>
              <Eye className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Occupancy Rate</p>
                <p className="text-2xl font-bold">{formatPercentage(analyticsData.summary.occupancyRate)}</p>
                <p className="text-sm text-gray-500 mt-1">
                  Avg: {formatCurrency(analyticsData.summary.averageBookingValue)}
                </p>
              </div>
              <BarChart3 className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <Tabs defaultValue="revenue" className="space-y-6">
        <TabsList>
          <TabsTrigger value="revenue">Revenue Trends</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="audience">Audience</TabsTrigger>
          <TabsTrigger value="booking">Booking Trends</TabsTrigger>
        </TabsList>

        <TabsContent value="revenue" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Revenue Over Time</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={analyticsData.revenueData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="period" />
                    <YAxis />
                    <Tooltip formatter={(value: any) => [formatCurrency(value), 'Revenue']} />
                    <Area type="monotone" dataKey="revenue" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.3} />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Bookings & Occupancy</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={analyticsData.revenueData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="period" />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip />
                    <Bar yAxisId="left" dataKey="bookings" fill="#10B981" />
                    <Line yAxisId="right" type="monotone" dataKey="occupancyRate" stroke="#F59E0B" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Location Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analyticsData.locationPerformance.map((location, index) => (
                    <div key={location.locationId} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div>
                        <h4 className="font-semibold">{location.locationName}</h4>
                        <p className="text-sm text-gray-600">
                          {location.bookings} bookings • {formatPercentage(location.occupancyRate)} occupancy
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-green-600">{formatCurrency(location.revenue)}</p>
                        <div className="flex items-center gap-1">
                          {getGrowthIcon(location.growth)}
                          <span className={`text-sm ${getGrowthColor(location.growth)}`}>
                            {formatPercentage(Math.abs(location.growth))}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Top Performing Ad Slots</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analyticsData.adSlotPerformance.map((slot, index) => (
                    <div key={slot.slotId} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div>
                        <h4 className="font-semibold">{slot.slotName}</h4>
                        <p className="text-sm text-gray-600">{slot.locationName}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="outline" className="text-xs">
                            Score: {slot.performanceScore}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            Last: {slot.lastBooking}
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-green-600">{formatCurrency(slot.revenue)}</p>
                        <p className="text-sm text-gray-600">{slot.bookings} bookings</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="audience" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Audience Demographics</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={analyticsData.audienceInsights}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ demographic, percentage }) => `${demographic}: ${percentage}%`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="percentage"
                    >
                      {analyticsData.audienceInsights.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Revenue by Demographic</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analyticsData.audienceInsights.map((insight, index) => (
                    <div key={insight.demographic} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div 
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        />
                        <div>
                          <p className="font-medium">{insight.demographic}</p>
                          <p className="text-sm text-gray-600">{formatPercentage(insight.percentage)} of audience</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-green-600">{formatCurrency(insight.revenue)}</p>
                        <p className="text-sm text-gray-600">{formatNumber(insight.impressions)} views</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="booking" className="space-y-6">
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle>Booking Trends Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={analyticsData.bookingTrends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="bookings" fill="#3B82F6" name="Bookings" />
                  <Line yAxisId="right" type="monotone" dataKey="averageBookingValue" stroke="#10B981" name="Avg Booking Value" />
                  <Line yAxisId="left" type="monotone" dataKey="repeatCustomers" stroke="#F59E0B" name="Repeat Customers" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}