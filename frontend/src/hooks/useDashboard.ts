import { useState, useEffect } from 'react';

interface PerformanceData {
  name: string;
  impressions: number;
  clicks: number;
}

interface CategoryData {
  name: string;
  value: number;
  color: string;
}

interface DashboardMetrics {
  totalUsers: number;
  activeKiosks: number;
  pendingReviews: number;
  systemUptime: string;
  hostKiosks: number;
  hostAdsForReview: number;
  hostAnalytics: number;
  advertiserAds: number;
  advertiserPerformance: number;
  advertiserPendingReviews: number;
}

export function useDashboard() {
  const [performanceData, setPerformanceData] = useState<PerformanceData[]>([]);
  const [categoryData, setCategoryData] = useState<CategoryData[]>([]);
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    totalUsers: 0,
    activeKiosks: 0,
    pendingReviews: 0,
    systemUptime: '0%',
    hostKiosks: 0,
    hostAdsForReview: 0,
    hostAnalytics: 0,
    advertiserAds: 0,
    advertiserPerformance: 0,
    advertiserPendingReviews: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mock data - in real app this would come from API
    const mockPerformanceData: PerformanceData[] = [
      { name: 'Mon', impressions: 4000, clicks: 240 },
      { name: 'Tue', impressions: 3000, clicks: 139 },
      { name: 'Wed', impressions: 2000, clicks: 980 },
      { name: 'Thu', impressions: 2780, clicks: 390 },
      { name: 'Fri', impressions: 1890, clicks: 480 },
      { name: 'Sat', impressions: 2390, clicks: 380 },
      { name: 'Sun', impressions: 3490, clicks: 430 },
    ];

    const mockCategoryData: CategoryData[] = [
      { name: 'Food', value: 35, color: '#3b82f6' },
      { name: 'Retail', value: 25, color: '#10b981' },
      { name: 'Services', value: 20, color: '#f59e0b' },
      { name: 'Events', value: 12, color: '#ef4444' },
      { name: 'Other', value: 8, color: '#8b5cf6' },
    ];

    const mockMetrics: DashboardMetrics = {
      totalUsers: 1234,
      activeKiosks: 89,
      pendingReviews: 23,
      systemUptime: '99.9%',
      hostKiosks: 12,
      hostAdsForReview: 8,
      hostAnalytics: 1234,
      advertiserAds: 5,
      advertiserPerformance: 15678,
      advertiserPendingReviews: 2,
    };

    setPerformanceData(mockPerformanceData);
    setCategoryData(mockCategoryData);
    setMetrics(mockMetrics);
    setLoading(false);
  }, []);

  return {
    performanceData,
    categoryData,
    metrics,
    loading,
  };
}
