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
  const [kiosks, setKiosks] = useState<Kiosk[]>([]);
  const [metrics, setMetrics] = useState<KioskMetrics>({
    totalKiosks: 0,
    onlineCount: 0,
    offlineCount: 0,
    avgUptime: '0%',
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mock data - in real app this would come from API
    const mockKiosks: Kiosk[] = [
      {
        id: 'KSK-001',
        name: 'Main Lobby Screen',
        location: 'Hotel Lobby - Dubai',
        status: 'online',
        lastSeen: '2025-08-27T10:30:00Z',
        currentAd: 'Summer Pizza Deal',
        uptime: '99.8%'
      },
      {
        id: 'KSK-002',
        name: 'Restaurant Display',
        location: 'Restaurant Area - Dubai',
        status: 'online',
        lastSeen: '2025-08-27T10:25:00Z',
        currentAd: 'Fashion Sale',
        uptime: '98.5%'
      },
      {
        id: 'KSK-003',
        name: 'Elevator Screen',
        location: 'Elevator Bank - Dubai',
        status: 'offline',
        lastSeen: '2025-08-26T18:45:00Z',
        currentAd: 'No Ad',
        uptime: '95.2%'
      },
      {
        id: 'KSK-004',
        name: 'Conference Room',
        location: 'Meeting Room A - Dubai',
        status: 'maintenance',
        lastSeen: '2025-08-27T09:15:00Z',
        currentAd: 'Restaurant Special',
        uptime: '97.1%'
      }
    ];

    const mockMetrics: KioskMetrics = {
      totalKiosks: mockKiosks.length,
      onlineCount: mockKiosks.filter(k => k.status === 'online').length,
      offlineCount: mockKiosks.filter(k => k.status === 'offline').length,
      avgUptime: '97.7%',
    };

    setKiosks(mockKiosks);
    setMetrics(mockMetrics);
    setLoading(false);
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
