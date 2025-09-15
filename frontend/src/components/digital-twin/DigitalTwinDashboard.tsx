'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Monitor,
  Wifi,
  WifiOff,
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  MapPin,
  Settings,
  Play,
  Pause,
  Square,
  Refresh,
  Download,
  Upload,
  Database,
  Image,
  Video,
  FileText,
  Users,
  BarChart3,
  Eye,
  Calendar,
  Filter,
  Search,
  ExternalLink
} from 'lucide-react';

interface Device {
  id: string;
  name: string;
  location: {
    name: string;
    coordinates?: { lat: number; lng: number };
    timezone: string;
  };
  status: 'online' | 'offline' | 'maintenance' | 'error';
  last_seen: string;
  company_name: string;
  company_id: string;
  specifications: {
    screen_resolution: string;
    screen_size_inches: number;
    os_version: string;
    hardware_model: string;
  };
  performance_metrics: {
    uptime_percentage: number;
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    network_status: string;
    temperature?: number;
  };
  current_content: {
    content_id?: string;
    content_title?: string;
    overlay_id?: string;
    schedule_id?: string;
    started_at?: string;
    estimated_duration?: number;
  };
  sync_status: {
    last_sync: string;
    sync_required: boolean;
    pending_updates: number;
  };
  analytics: {
    daily_views: number;
    total_interactions: number;
    avg_engagement_time: number;
    last_interaction?: string;
  };
}

interface DeviceCommand {
  type: 'refresh_content' | 'restart_playback' | 'enter_standby' | 'exit_standby' | 'sync_content' | 'restart_device';
  description: string;
  icon: React.ReactNode;
}

interface DigitalTwinDashboardProps {
  companyFilter?: string;
  deviceFilter?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export function DigitalTwinDashboard({
  companyFilter,
  deviceFilter,
  autoRefresh = true,
  refreshInterval = 30000
}: DigitalTwinDashboardProps) {
  const [devices, setDevices] = useState<Device[]>([]);
  const [filteredDevices, setFilteredDevices] = useState<Device[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters and search
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [companyFilter_, setCompanyFilter_] = useState(companyFilter || 'all');
  const [locationFilter, setLocationFilter] = useState('all');

  // UI state
  const [showDeviceDetails, setShowDeviceDetails] = useState(false);
  const [selectedDeviceForCommand, setSelectedDeviceForCommand] = useState<string | null>(null);
  const [commandLoading, setCommandLoading] = useState<string | null>(null);

  const availableCommands: DeviceCommand[] = [
    {
      type: 'refresh_content',
      description: 'Refresh Content',
      icon: <Refresh className="w-4 h-4" />
    },
    {
      type: 'sync_content',
      description: 'Force Sync',
      icon: <Download className="w-4 h-4" />
    },
    {
      type: 'restart_playback',
      description: 'Restart Playback',
      icon: <Play className="w-4 h-4" />
    },
    {
      type: 'enter_standby',
      description: 'Enter Standby',
      icon: <Pause className="w-4 h-4" />
    },
    {
      type: 'exit_standby',
      description: 'Exit Standby',
      icon: <Play className="w-4 h-4" />
    },
    {
      type: 'restart_device',
      description: 'Restart Device',
      icon: <Settings className="w-4 h-4" />
    }
  ];

  const fetchDevices = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/devices/status', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setDevices(data.devices || []);
        setError(null);
      } else {
        throw new Error('Failed to fetch devices');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDevices();

    if (autoRefresh) {
      const interval = setInterval(fetchDevices, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchDevices, autoRefresh, refreshInterval]);

  useEffect(() => {
    let filtered = devices;

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(device =>
        device.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        device.location.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        device.company_name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(device => device.status === statusFilter);
    }

    // Apply company filter
    if (companyFilter_ !== 'all') {
      filtered = filtered.filter(device => device.company_id === companyFilter_);
    }

    // Apply location filter
    if (locationFilter !== 'all') {
      filtered = filtered.filter(device => device.location.name === locationFilter);
    }

    setFilteredDevices(filtered);
  }, [devices, searchTerm, statusFilter, companyFilter_, locationFilter]);

  const sendDeviceCommand = async (deviceId: string, command: DeviceCommand['type']) => {
    try {
      setCommandLoading(deviceId);
      const token = localStorage.getItem('access_token');

      const response = await fetch(`/api/devices/${deviceId}/command`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ command })
      });

      if (response.ok) {
        // Refresh devices to get updated status
        await fetchDevices();
      } else {
        throw new Error('Failed to send command');
      }
    } catch (err) {
      console.error('Command failed:', err);
    } finally {
      setCommandLoading(null);
    }
  };

  const getStatusColor = (status: Device['status']) => {
    switch (status) {
      case 'online': return 'bg-green-100 text-green-800';
      case 'offline': return 'bg-red-100 text-red-800';
      case 'maintenance': return 'bg-yellow-100 text-yellow-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: Device['status']) => {
    switch (status) {
      case 'online': return <CheckCircle className="w-4 h-4" />;
      case 'offline': return <WifiOff className="w-4 h-4" />;
      case 'maintenance': return <Settings className="w-4 h-4" />;
      case 'error': return <AlertTriangle className="w-4 h-4" />;
      default: return <Monitor className="w-4 h-4" />;
    }
  };

  const formatLastSeen = (lastSeen: string) => {
    const date = new Date(lastSeen);
    const now = new Date();
    const diffMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));

    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  const getUniqueCompanies = () => {
    const companies = devices.map(d => ({ id: d.company_id, name: d.company_name }));
    return companies.filter((company, index, self) =>
      index === self.findIndex(c => c.id === company.id)
    );
  };

  const getUniqueLocations = () => {
    return [...new Set(devices.map(d => d.location.name))];
  };

  const renderDeviceCard = (device: Device) => (
    <Card
      key={device.id}
      className="hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => {
        setSelectedDevice(device);
        setShowDeviceDetails(true);
      }}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg flex items-center gap-2">
              <Monitor className="w-5 h-5" />
              {device.name}
            </CardTitle>
            <CardDescription className="flex items-center gap-1 mt-1">
              <MapPin className="w-3 h-3" />
              {device.location.name}
            </CardDescription>
          </div>
          <Badge className={getStatusColor(device.status)}>
            {getStatusIcon(device.status)}
            <span className="ml-1">{device.status}</span>
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {/* Current Content */}
          {device.current_content?.content_title && (
            <div className="flex items-center gap-2 text-sm">
              <Play className="w-4 h-4 text-blue-600" />
              <span className="font-medium">Now Playing:</span>
              <span className="truncate">{device.current_content.content_title}</span>
            </div>
          )}

          {/* Performance Metrics */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center justify-between">
              <span>Uptime:</span>
              <span className="font-medium">{device.performance_metrics.uptime_percentage}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span>CPU:</span>
              <span className="font-medium">{Math.round(device.performance_metrics.cpu_usage * 100)}%</span>
            </div>
          </div>

          {/* Last Seen */}
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Last seen:
            </span>
            <span>{formatLastSeen(device.last_seen)}</span>
          </div>

          {/* Company */}
          <div className="flex items-center justify-between text-xs">
            <span className="flex items-center gap-1">
              <Users className="w-3 h-3" />
              Company:
            </span>
            <span className="font-medium">{device.company_name}</span>
          </div>

          {/* Quick Actions */}
          <div className="flex gap-1 pt-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                sendDeviceCommand(device.id, 'refresh_content');
              }}
              disabled={commandLoading === device.id}
            >
              <Refresh className="w-3 h-3" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                setSelectedDeviceForCommand(device.id);
              }}
            >
              <Settings className="w-3 h-3" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                // Open analytics for device
              }}
            >
              <BarChart3 className="w-3 h-3" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderFilters = () => (
    <div className="flex flex-wrap items-center gap-4 mb-6">
      <div className="flex-1 min-w-[200px]">
        <Input
          placeholder="Search devices..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full"
        />
      </div>

      <Select value={statusFilter} onValueChange={setStatusFilter}>
        <SelectTrigger className="w-[120px]">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Status</SelectItem>
          <SelectItem value="online">Online</SelectItem>
          <SelectItem value="offline">Offline</SelectItem>
          <SelectItem value="maintenance">Maintenance</SelectItem>
          <SelectItem value="error">Error</SelectItem>
        </SelectContent>
      </Select>

      <Select value={companyFilter_} onValueChange={setCompanyFilter_}>
        <SelectTrigger className="w-[150px]">
          <SelectValue placeholder="Company" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Companies</SelectItem>
          {getUniqueCompanies().map((company) => (
            <SelectItem key={company.id} value={company.id}>
              {company.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={locationFilter} onValueChange={setLocationFilter}>
        <SelectTrigger className="w-[150px]">
          <SelectValue placeholder="Location" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Locations</SelectItem>
          {getUniqueLocations().map((location) => (
            <SelectItem key={location} value={location}>
              {location}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Button variant="outline" onClick={fetchDevices}>
        <Refresh className="w-4 h-4 mr-1" />
        Refresh
      </Button>
    </div>
  );

  const renderOverview = () => {
    const totalDevices = devices.length;
    const onlineDevices = devices.filter(d => d.status === 'online').length;
    const offlineDevices = devices.filter(d => d.status === 'offline').length;
    const errorDevices = devices.filter(d => d.status === 'error').length;
    const avgUptime = devices.reduce((sum, d) => sum + d.performance_metrics.uptime_percentage, 0) / (totalDevices || 1);

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Devices</p>
                <p className="text-2xl font-bold">{totalDevices}</p>
              </div>
              <Monitor className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Online</p>
                <p className="text-2xl font-bold text-green-600">{onlineDevices}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Offline</p>
                <p className="text-2xl font-bold text-red-600">{offlineDevices}</p>
              </div>
              <WifiOff className="w-8 h-8 text-red-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Avg Uptime</p>
                <p className="text-2xl font-bold">{Math.round(avgUptime)}%</p>
              </div>
              <Activity className="w-8 h-8 text-blue-600" />
            </div>
            <Progress value={avgUptime} className="mt-2" />
          </CardContent>
        </Card>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Monitor className="w-8 h-8 animate-pulse mx-auto mb-2" />
          <p>Loading devices...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Failed to load devices: {error}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      {renderOverview()}

      {/* Filters */}
      {renderFilters()}

      {/* Devices Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {filteredDevices.map(renderDeviceCard)}
      </div>

      {filteredDevices.length === 0 && (
        <Card>
          <CardContent className="p-8 text-center">
            <Monitor className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No devices found</h3>
            <p className="text-muted-foreground">
              {devices.length === 0
                ? "No devices have been registered yet."
                : "No devices match the current filters."
              }
            </p>
          </CardContent>
        </Card>
      )}

      {/* Device Details Dialog */}
      <Dialog open={showDeviceDetails} onOpenChange={setShowDeviceDetails}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Monitor className="w-5 h-5" />
              {selectedDevice?.name}
            </DialogTitle>
          </DialogHeader>
          {selectedDevice && (
            <Tabs defaultValue="overview" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="content">Content</TabsTrigger>
                <TabsTrigger value="performance">Performance</TabsTrigger>
                <TabsTrigger value="control">Control</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Device Information</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Status:</span>
                        <Badge className={getStatusColor(selectedDevice.status)}>
                          {selectedDevice.status}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span>Last Seen:</span>
                        <span>{formatLastSeen(selectedDevice.last_seen)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Company:</span>
                        <span>{selectedDevice.company_name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Location:</span>
                        <span>{selectedDevice.location.name}</span>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Specifications</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Resolution:</span>
                        <span>{selectedDevice.specifications.screen_resolution}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Screen Size:</span>
                        <span>{selectedDevice.specifications.screen_size_inches}"</span>
                      </div>
                      <div className="flex justify-between">
                        <span>OS:</span>
                        <span>{selectedDevice.specifications.os_version}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Model:</span>
                        <span>{selectedDevice.specifications.hardware_model}</span>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              <TabsContent value="content" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Current Content</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {selectedDevice.current_content?.content_title ? (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <Play className="w-4 h-4 text-green-600" />
                          <span className="font-medium">{selectedDevice.current_content.content_title}</span>
                        </div>
                        {selectedDevice.current_content.started_at && (
                          <p className="text-sm text-muted-foreground">
                            Started: {new Date(selectedDevice.current_content.started_at).toLocaleString()}
                          </p>
                        )}
                        {selectedDevice.current_content.overlay_id && (
                          <p className="text-sm text-muted-foreground">
                            Overlay: Active
                          </p>
                        )}
                      </div>
                    ) : (
                      <p className="text-muted-foreground">No content currently playing</p>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Sync Status</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Last Sync:</span>
                      <span>{formatLastSeen(selectedDevice.sync_status.last_sync)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Sync Required:</span>
                      <Badge variant={selectedDevice.sync_status.sync_required ? "destructive" : "default"}>
                        {selectedDevice.sync_status.sync_required ? "Yes" : "No"}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Pending Updates:</span>
                      <span>{selectedDevice.sync_status.pending_updates}</span>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="performance" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">System Resources</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>CPU Usage</span>
                          <span>{Math.round(selectedDevice.performance_metrics.cpu_usage * 100)}%</span>
                        </div>
                        <Progress value={selectedDevice.performance_metrics.cpu_usage * 100} />
                      </div>
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Memory Usage</span>
                          <span>{Math.round(selectedDevice.performance_metrics.memory_usage * 100)}%</span>
                        </div>
                        <Progress value={selectedDevice.performance_metrics.memory_usage * 100} />
                      </div>
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Disk Usage</span>
                          <span>{Math.round(selectedDevice.performance_metrics.disk_usage * 100)}%</span>
                        </div>
                        <Progress value={selectedDevice.performance_metrics.disk_usage * 100} />
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Performance Metrics</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Uptime:</span>
                        <span>{selectedDevice.performance_metrics.uptime_percentage}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Network:</span>
                        <Badge variant={selectedDevice.performance_metrics.network_status === 'connected' ? 'default' : 'destructive'}>
                          {selectedDevice.performance_metrics.network_status}
                        </Badge>
                      </div>
                      {selectedDevice.performance_metrics.temperature && (
                        <div className="flex justify-between">
                          <span>Temperature:</span>
                          <span>{selectedDevice.performance_metrics.temperature}°C</span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Analytics</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Daily Views:</span>
                      <span>{selectedDevice.analytics.daily_views}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Total Interactions:</span>
                      <span>{selectedDevice.analytics.total_interactions}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Avg Engagement:</span>
                      <span>{Math.round(selectedDevice.analytics.avg_engagement_time)}s</span>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="control" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Device Commands</CardTitle>
                    <CardDescription>
                      Send commands to control the device remotely
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-2">
                      {availableCommands.map((command) => (
                        <Button
                          key={command.type}
                          variant="outline"
                          className="justify-start"
                          onClick={() => sendDeviceCommand(selectedDevice.id, command.type)}
                          disabled={commandLoading === selectedDevice.id}
                        >
                          {command.icon}
                          {command.description}
                        </Button>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}