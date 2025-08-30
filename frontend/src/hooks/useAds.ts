import { useState, useEffect } from 'react';
import { Ad } from '@/types';

export function useAds() {
  const [ads, setAds] = useState<Ad[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mock data - in real app this would come from API
    const mockAds: Ad[] = [
      {
        id: '1',
        type: 'image',
        category_id: 'food',
        business_id: 'biz1',
        company_id: 'company1',
        status: 'approved',
        file_path: '/images/sample.jpg',
        metadata: { title: 'Delicious Pizza', description: 'Hot and fresh pizza' }
      },
      {
        id: '2',
        type: 'video',
        category_id: 'retail',
        business_id: 'biz1',
        company_id: 'company1',
        status: 'pending',
        file_path: '/images/sample.mp4',
        metadata: { title: 'Fashion Sale', description: '50% off on all items' }
      },
      {
        id: '3',
        type: 'image',
        category_id: 'entertainment',
        business_id: 'biz1',
        company_id: 'company1',
        status: 'rejected',
        file_path: '/images/sample2.jpg',
        metadata: { title: 'Movie Night', description: 'Watch latest movies' }
      }
    ];

    setAds(mockAds);
    setLoading(false);
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
