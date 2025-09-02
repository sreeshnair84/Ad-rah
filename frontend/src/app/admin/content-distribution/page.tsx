'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useContentUploadNotifications } from '@/hooks/useWebSocket';
import { 
  Send, 
  Monitor, 
  CheckCircle, 
  Clock, 
  Download, 
  AlertTriangle,
  Eye,
  Zap,
  BarChart3
} from 'lucide-react';

interface ContentItem {
  id: string;
  title?: string;
  filename: string;
  content_type: string;
  owner_id: string;
  status: string;
  size: number;
  created_at?: string;
}

interface Device {
  id: string;
  name: string;
  status: string;
  location?: string;
  last_seen?: string;
  company_id?: string;
}

interface DistributionRecord {
  id: string;
  content_id: string;
  device_id: string;
  status: string;
  device_name?: string;
  device_location?: string;
  created_at: string;
}

interface DistributionStats {
  total_distributions: number;
  total_devices: number;
  total_approved_content: number;
  active_devices: number;
  distribution_status: {
    queued: number;
    downloading: number;
    downloaded: number;
    displayed: number;
    failed: number;
  };
  success_rate: number;
}

export default function ContentDistributionPage() {
  const [approvedContent, setApprovedContent] = useState<ContentItem[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedContent, setSelectedContent] = useState<string[]>([]);
  const [selectedDevices, setSelectedDevices] = useState<string[]>([]);
  const [distributions, setDistributions] = useState<DistributionRecord[]>([]);
  const [stats, setStats] = useState<DistributionStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Real-time notifications
  const { uploadNotifications, isConnected } = useContentUploadNotifications();

  useEffect(() => {
    loadApprovedContent();
    loadDevices();
    loadDistributionStats();
  }, []);

  // React to real-time notifications
  useEffect(() => {
    const lastNotification = uploadNotifications[uploadNotifications.length - 1];
    if (lastNotification) {
      if (lastNotification.type === 'content_approved') {
        loadApprovedContent();
      } else if (lastNotification.type === 'content_status_update') {
        loadDistributionStats();
      }
    }
  }, [uploadNotifications]);

  const loadApprovedContent = async () => {
    try {
      const response = await fetch('/api/content/');
      if (!response.ok) throw new Error('Failed to load content');
      
      const data = await response.json();
      const approved = data.filter((item: ContentItem) => item.status === 'approved');
      setApprovedContent(approved);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load content');
    }
  };

  const loadDevices = async () => {
    try {
      const response = await fetch('/api/devices/');
      if (!response.ok) throw new Error('Failed to load devices');
      
      const data = await response.json();
      setDevices(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load devices');
    }
  };

  const loadDistributionStats = async () => {
    try {
      const response = await fetch('/api/content/distribution/stats');
      if (!response.ok) throw new Error('Failed to load stats');
      
      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Failed to load distribution stats:', err);
    }
  };

  const handleDistributeContent = async () => {
    if (selectedContent.length === 0 || selectedDevices.length === 0) {
      setError('Please select both content and devices');
      return;
    }

    try {
      setLoading(true);
      const formData = new FormData();
      
      selectedContent.forEach(contentId => {
        formData.append('content_ids', contentId);
      });
      
      selectedDevices.forEach(deviceId => {
        formData.append('device_ids', deviceId);
      });
      
      formData.append('priority', '1');

      const response = await fetch('/api/content/bulk-distribute', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Failed to distribute content');

      const result = await response.json();
      
      // Reset selections
      setSelectedContent([]);
      setSelectedDevices([]);
      
      // Reload stats
      await loadDistributionStats();
      
      setError(null);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Distribution failed');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'queued':
        return <Badge variant="outline" className="text-blue-600 border-blue-600">Queued</Badge>;
      case 'downloading':
        return <Badge variant="outline" className="text-yellow-600 border-yellow-600">Downloading</Badge>;
      case 'downloaded':
        return <Badge variant="outline" className="text-green-600 border-green-600">Downloaded</Badge>;
      case 'displayed':
        return <Badge variant="default" className="bg-green-600">Displayed</Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
      case 'active':
        return <Badge variant="default" className="bg-green-600">Active</Badge>;
      case 'offline':
        return <Badge variant="outline" className="text-gray-600 border-gray-600">Offline</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Content Distribution</h1>
            <p className="text-gray-600 mt-2">
              Distribute approved content to devices
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-gray-600">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </div>

      {error && (
        <Alert className="mb-6 border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      {/* Statistics Dashboard */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Content</p>
                  <p className="text-2xl font-bold">{stats.total_approved_content}</p>
                </div>
                <Eye className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Active Devices</p>
                  <p className="text-2xl font-bold">{stats.active_devices}</p>
                </div>
                <Monitor className="w-8 h-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Distributions</p>
                  <p className="text-2xl font-bold">{stats.total_distributions}</p>
                </div>
                <Send className="w-8 h-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Success Rate</p>
                  <p className="text-2xl font-bold">{stats.success_rate}%</p>
                </div>
                <BarChart3 className="w-8 h-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Content Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Approved Content ({approvedContent.length})</CardTitle>
            <CardDescription>
              Select content to distribute to devices
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {approvedContent.map((content) => (
                <div key={content.id} className="flex items-center space-x-3 p-3 border rounded-lg">
                  <Checkbox
                    checked={selectedContent.includes(content.id)}
                    onCheckedChange={(checked) => {
                      if (checked) {
                        setSelectedContent([...selectedContent, content.id]);
                      } else {
                        setSelectedContent(selectedContent.filter(id => id !== content.id));
                      }
                    }}
                  />
                  <div className="flex-1">
                    <p className="font-medium">{content.title || content.filename}</p>
                    <p className="text-sm text-gray-600">
                      {content.content_type} • {formatFileSize(content.size)}
                    </p>
                  </div>
                  {getStatusBadge(content.status)}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Device Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Available Devices ({devices.length})</CardTitle>
            <CardDescription>
              Select target devices for content distribution
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {devices.map((device) => (
                <div key={device.id} className="flex items-center space-x-3 p-3 border rounded-lg">
                  <Checkbox
                    checked={selectedDevices.includes(device.id)}
                    onCheckedChange={(checked) => {
                      if (checked) {
                        setSelectedDevices([...selectedDevices, device.id]);
                      } else {
                        setSelectedDevices(selectedDevices.filter(id => id !== device.id));
                      }
                    }}
                    disabled={device.status !== 'active'}
                  />
                  <Monitor className="w-5 h-5 text-gray-400" />
                  <div className="flex-1">
                    <p className="font-medium">{device.name}</p>
                    <p className="text-sm text-gray-600">
                      {device.location || 'Unknown Location'}
                    </p>
                  </div>
                  {getStatusBadge(device.status)}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Distribution Controls */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Distribution Settings</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <p className="text-sm text-gray-600">
                Selected: {selectedContent.length} content items, {selectedDevices.length} devices
              </p>
              <p className="text-sm text-gray-600">
                Total distributions: {selectedContent.length * selectedDevices.length}
              </p>
            </div>
            <Button
              onClick={handleDistributeContent}
              disabled={loading || selectedContent.length === 0 || selectedDevices.length === 0}
              className="flex items-center gap-2"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              ) : (
                <Send className="w-4 h-4" />
              )}
              Distribute Content
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Distribution Status */}
      {stats && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Distribution Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{stats.distribution_status.queued}</div>
                <div className="text-sm text-gray-600">Queued</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">{stats.distribution_status.downloading}</div>
                <div className="text-sm text-gray-600">Downloading</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{stats.distribution_status.downloaded}</div>
                <div className="text-sm text-gray-600">Downloaded</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-700">{stats.distribution_status.displayed}</div>
                <div className="text-sm text-gray-600">Displayed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{stats.distribution_status.failed}</div>
                <div className="text-sm text-gray-600">Failed</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Real-time Notifications */}
      {uploadNotifications.length > 0 && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Real-time Updates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-32 overflow-y-auto">
              {uploadNotifications.slice(-5).map((notification, index) => (
                <div key={index} className="flex items-center gap-2 text-sm p-2 bg-blue-50 rounded">
                  <Zap className="w-4 h-4 text-blue-500" />
                  <span>{notification.type.replace('_', ' ')}</span>
                  <span className="text-gray-600">
                    {new Date(notification.timestamp * 1000).toLocaleTimeString()}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
