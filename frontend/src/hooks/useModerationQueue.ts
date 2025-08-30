import { useState, useEffect } from 'react';
import { Ad, Review } from '@/types';

interface PendingAd extends Ad {
  review: Review;
}

export function useModerationQueue() {
  const [pendingAds, setPendingAds] = useState<PendingAd[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mock data - in real app this would come from API
    const mockPendingAds: PendingAd[] = [
      {
        id: '1',
        type: 'image',
        category_id: 'food',
        business_id: 'biz1',
        company_id: 'company1',
        status: 'pending',
        file_path: '/images/sample.jpg',
        metadata: { title: 'Pizza Ad', description: 'Delicious pizza offer' },
        review: {
          id: 'r1',
          ad_id: '1',
          ai_score: 0.85,
          status: 'needs_review',
          explanation: 'Potential trademark issue with logo'
        }
      },
      {
        id: '2',
        type: 'video',
        category_id: 'retail',
        business_id: 'biz2',
        company_id: 'company1',
        status: 'pending',
        file_path: '/images/sample.mp4',
        metadata: { title: 'Sale Video', description: 'Flash sale announcement' },
        review: {
          id: 'r2',
          ad_id: '2',
          ai_score: 0.92,
          status: 'needs_review',
          explanation: 'High confidence but flagged for manual review'
        }
      }
    ];

    setPendingAds(mockPendingAds);
    setLoading(false);
  }, []);

  const approveAd = (adId: string) => {
    setPendingAds(prev => prev.filter(ad => ad.id !== adId));
  };

  const rejectAd = (adId: string) => {
    setPendingAds(prev => prev.filter(ad => ad.id !== adId));
  };

  const getAIScoreBadge = (score: number) => {
    return score > 0.9 ? 'default' : 'secondary';
  };

  return {
    pendingAds,
    loading,
    approveAd,
    rejectAd,
    getAIScoreBadge,
  };
}
