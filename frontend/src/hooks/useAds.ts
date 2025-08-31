import { useState, useEffect } from 'react';
import { Ad } from '@/types';

export function useAds() {
  const [ads, setAds] = useState<Ad[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: Replace with actual API call to fetch ads
    const fetchAds = async () => {
      try {
        // const response = await fetch('/api/ads');
        // const data = await response.json();
        // setAds(data.ads);
      } catch (error) {
        console.error('Failed to fetch ads:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAds();
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'approved':
        return 'default';
      case 'pending':
        return 'secondary';
      case 'rejected':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const addAd = (adData: Omit<Ad, 'id'>) => {
    const newAd: Ad = {
      ...adData,
      id: Date.now().toString(),
    };
    setAds(prev => [...prev, newAd]);
  };

  const updateAdStatus = (adId: string, status: Ad['status']) => {
    setAds(prev => prev.map(ad =>
      ad.id === adId ? { ...ad, status } : ad
    ));
  };

  return {
    ads,
    loading,
    getStatusBadge,
    addAd,
    updateAdStatus,
  };
}
