import { useState, useEffect } from 'react';
import { Ad, Review } from '@/types';

interface PendingAd extends Ad {
  review: Review;
}

export function useModerationQueue() {
  const [pendingAds, setPendingAds] = useState<PendingAd[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: Replace with actual API call to fetch pending ads for moderation
    const fetchPendingAds = async () => {
      try {
        // const response = await fetch('/api/moderation/pending');
        // const data = await response.json();
        // setPendingAds(data.pendingAds);
      } catch (error) {
        console.error('Failed to fetch pending ads:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPendingAds();
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
