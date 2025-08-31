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
    // TODO: Replace with actual API call to fetch ads for approval
    const fetchAdsForApproval = async () => {
      try {
        // const response = await fetch('/api/ads/pending-approval');
        // const data = await response.json();
        // setAds(data.ads);
      } catch (error) {
        console.error('Failed to fetch ads for approval:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAdsForApproval();
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
