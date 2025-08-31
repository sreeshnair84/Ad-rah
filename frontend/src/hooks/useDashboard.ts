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
    // TODO: Replace with actual API calls to fetch dashboard data
    const fetchDashboardData = async () => {
      try {
        // const response = await fetch('/api/dashboard/metrics');
        // const data = await response.json();
        // setPerformanceData(data.performanceData);
        // setCategoryData(data.categoryData);
        // setMetrics(data.metrics);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  return {
    performanceData,
    categoryData,
    metrics,
    loading,
  };
}
