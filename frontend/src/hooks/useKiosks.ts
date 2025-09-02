import { useState, useEffect } from 'react';

interface Kiosk {
  id: string;
  name: string;
  location: string;
  status: 'online' | 'offline' | 'maintenance';
  lastSeen: string;
  currentAd: string;
  uptime: string;
}

interface KioskMetrics {
  totalKiosks: number;
  onlineCount: number;
  offlineCount: number;
  avgUptime: string;
}

export function useKiosks() {
  const [kiosks] = useState<Kiosk[]>([]); // TODO: Implement kiosk data fetching
  const [metrics] = useState<KioskMetrics>({ // TODO: Implement metrics calculation
    totalKiosks: 0,
    onlineCount: 0,
    offlineCount: 0,
    avgUptime: '0%',
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: Replace with actual API call to fetch kiosks data
    const fetchKiosks = async () => {
      try {
        // const response = await fetch('/api/kiosks');
        // const data = await response.json();
        // setKiosks(data.kiosks);
        // setMetrics(data.metrics);
      } catch (error) {
        console.error('Failed to fetch kiosks:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchKiosks();
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'online':
        return 'default';
      case 'offline':
        return 'destructive';
      case 'maintenance':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  const formatLastSeen = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  return {
    kiosks,
    metrics,
    loading,
    getStatusBadge,
    formatLastSeen,
  };
}
