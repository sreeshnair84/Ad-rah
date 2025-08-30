import { useState, useEffect } from 'react';
import { Ad } from '@/types';

interface AdsApprovalItem extends Ad {
  advertiser: string;
  submittedDate: string;
}

export function useAdsApproval() {
  const [ads, setAds] = useState<AdsApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mock data - in real app this would come from API
    const mockAds: AdsApprovalItem[] = [
      {
        id: 'AD-001',
        type: 'image',
        category_id: 'food',
        business_id: 'biz1',
        company_id: '1',
        status: 'pending',
        file_path: '/images/pizza-ad.jpg',
        metadata: { title: 'Special Pizza Deal', description: '50% off on all pizzas' },
        advertiser: 'Mario\'s Pizza',
        submittedDate: '2025-08-26'
      },
      {
        id: 'AD-002',
        type: 'video',
        category_id: 'fashion',
        business_id: 'biz2',
        company_id: '2',
        status: 'pending',
        file_path: '/images/fashion-sale.mp4',
        metadata: { title: 'Summer Fashion Sale', description: 'Up to 70% off on summer collection' },
        advertiser: 'Fashion Hub',
        submittedDate: '2025-08-25'
      },
      {
        id: 'AD-003',
        type: 'image',
        category_id: 'services',
        business_id: 'biz3',
        company_id: '3',
        status: 'pending',
        file_path: '/images/cleaning-service.jpg',
        metadata: { title: 'Professional Cleaning', description: 'Expert cleaning services for your home' },
        advertiser: 'CleanPro Services',
        submittedDate: '2025-08-24'
      }
    ];

    setAds(mockAds);
    setLoading(false);
  }, []);

  const handleApprove = (adId: string) => {
    setAds(ads => ads.map(ad =>
      ad.id === adId ? { ...ad, status: 'approved' as const } : ad
    ));
  };

  const handleReject = (adId: string) => {
    setAds(ads => ads.filter(ad => ad.id !== adId));
  };

  const pendingAds = ads.filter(ad => ad.status === 'pending');
  const approvedToday = ads.filter(ad =>
    ad.status === 'approved' &&
    new Date(ad.submittedDate).toDateString() === new Date().toDateString()
  ).length;

  const rejectedThisWeek = ads.filter(ad =>
    ad.status === 'rejected' &&
    new Date(ad.submittedDate) >= new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
  ).length;

  return {
    ads,
    pendingAds,
    loading,
    handleApprove,
    handleReject,
    metrics: {
      pendingCount: pendingAds.length,
      approvedToday,
      rejectedThisWeek
    }
  };
}
