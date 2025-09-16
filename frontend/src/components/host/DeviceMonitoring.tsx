'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Monitor,
  Wifi,
  Battery,
  HardDrive,
  Cpu,
  MemoryStick,
  Thermometer,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Power,
  Settings,
  RefreshCw,
  PlayCircle,
  PauseCircle,
  RotateCcw,
  Download,
  Upload,
  Search,
  Filter,
  MapPin,
  Clock,
  Activity,
  Zap,
  WifiOff,
  Eye,
  BarChart3
} from 'lucide-react';

interface Device {
  id: string;
  name: string;
  locationId: string;
  locationName: string;
  serialNumber: string;
  model: string;
  ipAddress: string;
  macAddress: string;
  status: 'online' | 'offline' | 'error' | 'maintenance';
  lastSeen: string;
  uptime: number; // hours
  health: {
    cpuUsage: number;
    memoryUsage: number;
    storageUsage: number;
    temperature: number;
    batteryLevel?: number;
    networkStrength: number;
  };
  currentContent: {
    contentId?: string;
    contentTitle?: string;
    playingSince?: string;
    nextContent?: string;
    scheduleStatus: 'on_schedule' | 'delayed' | 'paused' | 'error';
  };
  configuration: {
    resolution: string;
    orientation: 'landscape' | 'portrait';
    brightness: number;
    volume: number;
    autoRestart: boolean;
    maintenanceWindow: string;
  };
  analytics: {
    totalPlaytime: number;
    contentChanges: number;
    errors: number;
    averageUptime: number;
  };
  recentEvents: {
    timestamp: string;
    type: 'info' | 'warning' | 'error';
    message: string;
  }[];
}

export default function DeviceMonitoring() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [locations, setLocations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterLocation, setFilterLocation] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);

  useEffect(() => {
    fetchDevices();
    fetchLocations();
    
    // Set up real-time updates
    const interval = setInterval(fetchDevices, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchLocations = async () => {
    try {
      const response = await fetch('/api/host/locations', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
      });

      if (response.ok) {
        const data = await response.json();
        setLocations(data.locations || []);
      } else {
        setLocations([
          { id: '1', name: 'Downtown Shopping Mall' },
          { id: '2', name: 'Airport Terminal A' },
          { id: '3', name: 'University Campus Center' }
        ]);
      }
    } catch (error) {
      console.error('Failed to fetch locations:', error);
    }
  };

  const fetchDevices = async () => {
    try {
      setLoading(true);
      
      const response = await fetch('/api/host/devices/monitoring', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setDevices(data.devices || []);
      } else {
        // Mock data for development
        setDevices([
          {
            id: '1',
            name: 'Main Entrance Display',
            locationId: '1',
            locationName: 'Downtown Shopping Mall',
            serialNumber: 'DSP-001-2024',
            model: 'Samsung QB55R',
            ipAddress: '192.168.1.101',
            macAddress: '00:1B:44:11:3A:B7',
            status: 'online',
            lastSeen: '2024-12-12T10:30:00Z',
            uptime: 72.5,
            health: {
              cpuUsage: 35,
              memoryUsage: 68,
              storageUsage: 45,
              temperature: 42,
              networkStrength: 85
            },
            currentContent: {
              contentId: 'content-123',
              contentTitle: 'TechCorp Cloud Platform Ad',
              playingSince: '2024-12-12T09:00:00Z',
              nextContent: 'Fashion Sale Banner',
              scheduleStatus: 'on_schedule'
            },
            configuration: {
              resolution: '1920x1080',
              orientation: 'landscape',
              brightness: 80,
              volume: 70,
              autoRestart: true,
              maintenanceWindow: '02:00-04:00'
            },
            analytics: {
              totalPlaytime: 168.5,
              contentChanges: 45,
              errors: 2,
              averageUptime: 98.5
            },
            recentEvents: [
              { timestamp: '2024-12-12T10:25:00Z', type: 'info', message: 'Content transition completed successfully' },
              { timestamp: '2024-12-12T09:00:00Z', type: 'info', message: 'Started playing: TechCorp Cloud Platform Ad' },
              { timestamp: '2024-12-12T08:45:00Z', type: 'warning', message: 'Memory usage above 65%' }
            ]
          },
          {
            id: '2',
            name: 'Food Court Screen',
            locationId: '1',
            locationName: 'Downtown Shopping Mall',
            serialNumber: 'DSP-002-2024',
            model: 'LG 55UH5F',
            ipAddress: '192.168.1.102',
            macAddress: '00:1B:44:11:3A:B8',
            status: 'online',
            lastSeen: '2024-12-12T10:28:00Z',
            uptime: 96.2,
            health: {
              cpuUsage: 28,
              memoryUsage: 52,
              storageUsage: 38,
              temperature: 39,
              networkStrength: 92
            },
            currentContent: {
              contentId: 'content-456',
              contentTitle: 'QuickBite Holiday Special',
              playingSince: '2024-12-12T08:30:00Z',
              nextContent: 'Local Restaurant Promotion',
              scheduleStatus: 'on_schedule'
            },
            configuration: {
              resolution: '1920x1080',
              orientation: 'landscape',
              brightness: 85,
              volume: 75,
              autoRestart: true,
              maintenanceWindow: '03:00-05:00'
            },
            analytics: {
              totalPlaytime: 192.3,
              contentChanges: 38,
              errors: 1,
              averageUptime: 99.2
            },
            recentEvents: [
              { timestamp: '2024-12-12T10:20:00Z', type: 'info', message: 'System health check completed' },
              { timestamp: '2024-12-12T08:30:00Z', type: 'info', message: 'Started playing: QuickBite Holiday Special' }
            ]
          },
          {
            id: '3',
            name: 'Gate A12 Monitor',
            locationId: '2',
            locationName: 'Airport Terminal A',
            serialNumber: 'DSP-003-2024',
            model: 'Sharp PN-HM901',
            ipAddress: '192.168.2.201',
            macAddress: '00:1B:44:11:3A:C9',
            status: 'error',
            lastSeen: '2024-12-12T09:45:00Z',
            uptime: 12.3,
            health: {
              cpuUsage: 85,
              memoryUsage: 92,
              storageUsage: 78,
              temperature: 58,
              networkStrength: 45
            },
            currentContent: {
              contentId: 'content-789',
              contentTitle: 'Airport Service Announcement',
              playingSince: '2024-12-12T07:00:00Z',
              scheduleStatus: 'error'
            },
            configuration: {
              resolution: '1080x1920',
              orientation: 'portrait',
              brightness: 90,
              volume: 60,
              autoRestart: true,
              maintenanceWindow: '01:00-03:00'
            },
            analytics: {
              totalPlaytime: 145.8,
              contentChanges: 32,
              errors: 8,
              averageUptime: 89.5
            },
            recentEvents: [
              { timestamp: '2024-12-12T09:45:00Z', type: 'error', message: 'Content playback failed - file corrupted' },
              { timestamp: '2024-12-12T09:30:00Z', type: 'error', message: 'High CPU usage detected' },
              { timestamp: '2024-12-12T09:00:00Z', type: 'warning', message: 'Network connection unstable' }
            ]
          },
          {
            id: '4',
            name: 'Baggage Claim Display',
            locationId: '2',
            locationName: 'Airport Terminal A',
            serialNumber: 'DSP-004-2024',
            model: 'Samsung QM43R',
            ipAddress: '192.168.2.202',
            macAddress: '00:1B:44:11:3A:D0',
            status: 'offline',
            lastSeen: '2024-12-12T06:15:00Z',
            uptime: 0,
            health: {
              cpuUsage: 0,
              memoryUsage: 0,
              storageUsage: 0,
              temperature: 0,
              networkStrength: 0
            },
            currentContent: {
              scheduleStatus: 'error'
            },
            configuration: {
              resolution: '1920x1080',
              orientation: 'landscape',
              brightness: 75,
              volume: 65,
              autoRestart: true,
              maintenanceWindow: '02:00-04:00'
            },
            analytics: {
              totalPlaytime: 134.2,
              contentChanges: 28,
              errors: 12,
              averageUptime: 76.8
            },
            recentEvents: [
              { timestamp: '2024-12-12T06:15:00Z', type: 'error', message: 'Device went offline - power failure detected' },
              { timestamp: '2024-12-12T06:00:00Z', type: 'warning', message: 'Unexpected shutdown initiated' }
            ]
          },
          {
            id: '5',
            name: 'Student Center Kiosk',
            locationId: '3',
            locationName: 'University Campus Center',
            serialNumber: 'DSP-005-2024',
            model: 'Dell OptiPlex 7070',
            ipAddress: '10.0.1.50',
            macAddress: '00:1B:44:11:3A:E1',
            status: 'maintenance',
            lastSeen: '2024-12-12T10:00:00Z',
            uptime: 48.0,
            health: {
              cpuUsage: 15,
              memoryUsage: 35,
              storageUsage: 62,
              temperature: 35,
              batteryLevel: 85,
              networkStrength: 78
            },
            currentContent: {
              contentId: 'content-321',
              contentTitle: 'Campus Event Announcements',
              playingSince: '2024-12-12T08:00:00Z',
              scheduleStatus: 'paused'
            },
            configuration: {
              resolution: '1920x1080',
              orientation: 'landscape',
              brightness: 70,
              volume: 50,
              autoRestart: false,
              maintenanceWindow: '00:00-06:00'
            },
            analytics: {
              totalPlaytime: 98.5,
              contentChanges: 22,
              errors: 3,
              averageUptime: 94.2
            },
            recentEvents: [
              { timestamp: '2024-12-12T10:00:00Z', type: 'info', message: 'Maintenance mode activated by administrator' },
              { timestamp: '2024-12-12T08:00:00Z', type: 'info', message: 'Started playing: Campus Event Announcements' }
            ]
          }
        ]);
      }
    } catch (error) {
      console.error('Failed to fetch devices:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeviceAction = async (deviceId: string, action: 'restart' | 'pause' | 'resume' | 'maintenance') => {
    try {
      const response = await fetch(`/api/host/devices/${deviceId}/${action}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        await fetchDevices();
      } else {
        console.error(`Failed to ${action} device`);
      }
    } catch (error) {
      console.error(`Error ${action}ing device:`, error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'bg-green-100 text-green-800';
      case 'offline':
        return 'bg-red-100 text-red-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'maintenance':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online':
        return <CheckCircle className="h-4 w-4" />;
      case 'offline':
        return <XCircle className="h-4 w-4" />;
      case 'error':
        return <AlertTriangle className="h-4 w-4" />;
      case 'maintenance':
        return <Settings className="h-4 w-4" />;
      default:
        return <Monitor className="h-4 w-4" />;
    }
  };

  const getHealthColor = (value: number, type: 'usage' | 'temperature' | 'signal') => {
    if (type === 'usage') {
      if (value > 80) return 'text-red-600';
      if (value > 60) return 'text-yellow-600';
      return 'text-green-600';
    }
    if (type === 'temperature') {
      if (value > 50) return 'text-red-600';
      if (value > 40) return 'text-yellow-600';
      return 'text-green-600';
    }
    if (type === 'signal') {
      if (value < 30) return 'text-red-600';
      if (value < 60) return 'text-yellow-600';
      return 'text-green-600';
    }
    return 'text-gray-600';
  };

  const filteredDevices = devices.filter(device => {
    const matchesSearch = device.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         device.locationName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         device.serialNumber.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesLocation = filterLocation === 'all' || device.locationId === filterLocation;
    const matchesStatus = filterStatus === 'all' || device.status === filterStatus;
    return matchesSearch && matchesLocation && matchesStatus;
  });

  const renderDeviceDetails = () => {
    if (!selectedDevice) return null;

    return (
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="health">Health</TabsTrigger>
          <TabsTrigger value="content">Content</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h4 className="font-semibold mb-2">Device Information</h4>
              <div className="space-y-1 text-sm">
                <p><span className="text-gray-500">Name:</span> {selectedDevice.name}</p>
                <p><span className="text-gray-500">Location:</span> {selectedDevice.locationName}</p>
                <p><span className="text-gray-500">Model:</span> {selectedDevice.model}</p>
                <p><span className="text-gray-500">Serial:</span> {selectedDevice.serialNumber}</p>
              </div>
            </div>

            <div>
              <h4 className="font-semibold mb-2">Network</h4>
              <div className="space-y-1 text-sm">
                <p><span className="text-gray-500">IP Address:</span> {selectedDevice.ipAddress}</p>
                <p><span className="text-gray-500">MAC Address:</span> {selectedDevice.macAddress}</p>
                <p><span className="text-gray-500">Last Seen:</span> {new Date(selectedDevice.lastSeen).toLocaleString()}</p>
                <p><span className="text-gray-500">Uptime:</span> {selectedDevice.uptime.toFixed(1)} hours</p>
              </div>
            </div>

            <div>
              <h4 className="font-semibold mb-2">Configuration</h4>
              <div className="space-y-1 text-sm">
                <p><span className="text-gray-500">Resolution:</span> {selectedDevice.configuration.resolution}</p>
                <p><span className="text-gray-500">Orientation:</span> {selectedDevice.configuration.orientation}</p>
                <p><span className="text-gray-500">Brightness:</span> {selectedDevice.configuration.brightness}%</p>
                <p><span className="text-gray-500">Volume:</span> {selectedDevice.configuration.volume}%</p>
              </div>
            </div>

            <div>
              <h4 className="font-semibold mb-2">Analytics</h4>
              <div className="space-y-1 text-sm">
                <p><span className="text-gray-500">Total Playtime:</span> {selectedDevice.analytics.totalPlaytime.toFixed(1)}h</p>
                <p><span className="text-gray-500">Content Changes:</span> {selectedDevice.analytics.contentChanges}</p>
                <p><span className="text-gray-500">Errors:</span> {selectedDevice.analytics.errors}</p>
                <p><span className="text-gray-500">Avg Uptime:</span> {selectedDevice.analytics.averageUptime.toFixed(1)}%</p>
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDeviceAction(selectedDevice.id, 'restart')}
              className="gap-2"
            >
              <RotateCcw className="h-4 w-4" />
              Restart
            </Button>
            
            {selectedDevice.currentContent.scheduleStatus === 'paused' ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDeviceAction(selectedDevice.id, 'resume')}
                className="gap-2"
              >
                <PlayCircle className="h-4 w-4" />
                Resume
              </Button>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDeviceAction(selectedDevice.id, 'pause')}
                className="gap-2"
              >
                <PauseCircle className="h-4 w-4" />
                Pause
              </Button>
            )}
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDeviceAction(selectedDevice.id, 'maintenance')}
              className="gap-2"
            >
              <Settings className="h-4 w-4" />
              Maintenance
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="health" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Cpu className="h-5 w-5 text-blue-600" />
                    <span className="font-medium">CPU Usage</span>
                  </div>
                  <span className={`font-bold ${getHealthColor(selectedDevice.health.cpuUsage, 'usage')}`}>
                    {selectedDevice.health.cpuUsage}%
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <MemoryStick className="h-5 w-5 text-green-600" />
                    <span className="font-medium">Memory Usage</span>
                  </div>
                  <span className={`font-bold ${getHealthColor(selectedDevice.health.memoryUsage, 'usage')}`}>
                    {selectedDevice.health.memoryUsage}%
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <HardDrive className="h-5 w-5 text-purple-600" />
                    <span className="font-medium">Storage Usage</span>
                  </div>
                  <span className={`font-bold ${getHealthColor(selectedDevice.health.storageUsage, 'usage')}`}>
                    {selectedDevice.health.storageUsage}%
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Thermometer className="h-5 w-5 text-red-600" />
                    <span className="font-medium">Temperature</span>
                  </div>
                  <span className={`font-bold ${getHealthColor(selectedDevice.health.temperature, 'temperature')}`}>
                    {selectedDevice.health.temperature}°C
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Wifi className="h-5 w-5 text-blue-600" />
                    <span className="font-medium">Network Strength</span>
                  </div>
                  <span className={`font-bold ${getHealthColor(selectedDevice.health.networkStrength, 'signal')}`}>
                    {selectedDevice.health.networkStrength}%
                  </span>
                </div>
              </CardContent>
            </Card>

            {selectedDevice.health.batteryLevel && (
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Battery className="h-5 w-5 text-green-600" />
                      <span className="font-medium">Battery Level</span>
                    </div>
                    <span className={`font-bold ${getHealthColor(selectedDevice.health.batteryLevel, 'usage')}`}>
                      {selectedDevice.health.batteryLevel}%
                    </span>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="content" className="space-y-4">
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2">Currently Playing</h4>
              {selectedDevice.currentContent.contentTitle ? (
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="font-medium">{selectedDevice.currentContent.contentTitle}</p>
                  <p className="text-sm text-gray-600">
                    Playing since: {selectedDevice.currentContent.playingSince ? 
                      new Date(selectedDevice.currentContent.playingSince).toLocaleString() : 'Unknown'}
                  </p>
                  <Badge className="mt-2">
                    {selectedDevice.currentContent.scheduleStatus.replace('_', ' ')}
                  </Badge>
                </div>
              ) : (
                <p className="text-gray-500">No content currently playing</p>
              )}
            </div>

            {selectedDevice.currentContent.nextContent && (
              <div>
                <h4 className="font-semibold mb-2">Next Content</h4>
                <div className="p-4 bg-blue-50 rounded-lg">
                  <p className="font-medium">{selectedDevice.currentContent.nextContent}</p>
                </div>
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          <div className="space-y-2">
            {selectedDevice.recentEvents.map((event, index) => (
              <div key={index} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                <div className={`mt-1 ${
                  event.type === 'error' ? 'text-red-600' :
                  event.type === 'warning' ? 'text-yellow-600' : 'text-blue-600'
                }`}>
                  {event.type === 'error' ? <XCircle className="h-4 w-4" /> :
                   event.type === 'warning' ? <AlertTriangle className="h-4 w-4" /> :
                   <CheckCircle className="h-4 w-4" />}
                </div>
                <div className="flex-1">
                  <p className="text-sm">{event.message}</p>
                  <p className="text-xs text-gray-500">
                    {new Date(event.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading devices...</p>
        </div>
      </div>
    );
  }

  const statusCounts = {
    online: devices.filter(d => d.status === 'online').length,
    offline: devices.filter(d => d.status === 'offline').length,
    error: devices.filter(d => d.status === 'error').length,
    maintenance: devices.filter(d => d.status === 'maintenance').length
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Device Monitoring</h2>
          <p className="text-gray-600 mt-1">
            Monitor and manage your digital signage devices
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={fetchDevices} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
          
          <Button variant="outline" size="sm" className="gap-2">
            <Download className="h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Online</p>
                <p className="text-2xl font-bold text-green-600">{statusCounts.online}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Offline</p>
                <p className="text-2xl font-bold text-red-600">{statusCounts.offline}</p>
              </div>
              <XCircle className="h-8 w-8 text-red-600" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Errors</p>
                <p className="text-2xl font-bold text-red-600">{statusCounts.error}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-600" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Maintenance</p>
                <p className="text-2xl font-bold text-yellow-600">{statusCounts.maintenance}</p>
              </div>
              <Settings className="h-8 w-8 text-yellow-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search devices..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        
        <Select value={filterLocation} onValueChange={setFilterLocation}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="All Locations" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Locations</SelectItem>
            {locations.map(location => (
              <SelectItem key={location.id} value={location.id}>
                {location.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="All Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="online">Online</SelectItem>
            <SelectItem value="offline">Offline</SelectItem>
            <SelectItem value="error">Error</SelectItem>
            <SelectItem value="maintenance">Maintenance</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Devices Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredDevices.map((device) => (
          <Card key={device.id} className="border-0 shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <Monitor className="h-5 w-5 text-blue-600" />
                  <div>
                    <CardTitle className="text-lg">{device.name}</CardTitle>
                    <p className="text-sm text-gray-600">{device.locationName}</p>
                  </div>
                </div>
                <Badge className={getStatusColor(device.status)}>
                  {getStatusIcon(device.status)}
                  <span className="ml-1">{device.status}</span>
                </Badge>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-4">
              <div className="text-sm text-gray-600">
                <p className="flex items-center gap-1">
                  <MapPin className="h-3 w-3" />
                  {device.model} • {device.configuration.resolution}
                </p>
                <p className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  Uptime: {device.uptime.toFixed(1)}h
                </p>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">CPU</p>
                  <p className={`font-semibold ${getHealthColor(device.health.cpuUsage, 'usage')}`}>
                    {device.health.cpuUsage}%
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Memory</p>
                  <p className={`font-semibold ${getHealthColor(device.health.memoryUsage, 'usage')}`}>
                    {device.health.memoryUsage}%
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Temperature</p>
                  <p className={`font-semibold ${getHealthColor(device.health.temperature, 'temperature')}`}>
                    {device.health.temperature}°C
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Network</p>
                  <p className={`font-semibold ${getHealthColor(device.health.networkStrength, 'signal')}`}>
                    {device.health.networkStrength}%
                  </p>
                </div>
              </div>
              
              {device.currentContent.contentTitle && (
                <div className="text-sm">
                  <p className="text-gray-500">Currently Playing</p>
                  <p className="font-medium truncate">{device.currentContent.contentTitle}</p>
                  <Badge variant="outline" className="mt-1 text-xs">
                    {device.currentContent.scheduleStatus.replace('_', ' ')}
                  </Badge>
                </div>
              )}
              
              <div className="flex justify-between pt-2 border-t border-gray-100">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSelectedDevice(device);
                    setIsDetailsOpen(true);
                  }}
                  className="gap-1"
                >
                  <Eye className="h-3 w-3" />
                  Details
                </Button>
                
                <div className="flex gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDeviceAction(device.id, 'restart')}
                    className="gap-1"
                    disabled={device.status === 'offline'}
                  >
                    <RotateCcw className="h-3 w-3" />
                  </Button>
                  
                  {device.currentContent.scheduleStatus === 'paused' ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeviceAction(device.id, 'resume')}
                      className="gap-1"
                      disabled={device.status === 'offline'}
                    >
                      <PlayCircle className="h-3 w-3" />
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeviceAction(device.id, 'pause')}
                      className="gap-1"
                      disabled={device.status === 'offline'}
                    >
                      <PauseCircle className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredDevices.length === 0 && (
        <Card className="border-0 shadow-lg">
          <CardContent className="text-center py-12">
            <Monitor className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No devices found</h3>
            <p className="text-gray-600">
              {searchTerm || filterLocation !== 'all' || filterStatus !== 'all'
                ? 'Try adjusting your search or filter criteria.'
                : 'Add your first device to start monitoring.'}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Device Details Dialog */}
      <Dialog open={isDetailsOpen} onOpenChange={setIsDetailsOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Device Details</DialogTitle>
          </DialogHeader>
          {renderDeviceDetails()}
        </DialogContent>
      </Dialog>
    </div>
  );
}