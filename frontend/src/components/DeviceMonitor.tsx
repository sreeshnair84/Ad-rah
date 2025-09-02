'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Monitor, 
  Wifi, 
  WifiOff, 
  Battery, 
  Thermometer, 
  HardDrive,
  Cpu,
  AlertTriangle,
  // CheckCircle, // Unused import
  RefreshCw,
  MapPin
} from 'lucide-react';

interface DeviceHeartbeat {
  timestamp: string;
  status: string;
  cpu_usage?: number;
  memory_usage?: number;
  storage_usage?: number;
  temperature?: number;
  network_strength?: number;
  performance_score?: number;
  current_content_id?: string;
  content_errors: number;
  error_logs: string[];
  latitude?: number;
  longitude?: number;
}

interface Device {
  device_id: string;
  name: string;
  company_name: string;
  is_online: boolean;
  latest_heartbeat?: DeviceHeartbeat;
  performance_score?: number;
  has_valid_credentials: boolean;
}

interface DeviceMonitorProps {
  companyId?: string;
  autoRefresh?: boolean;
  refreshInterval?: number; // seconds
}

export default function DeviceMonitor({ 
  companyId, 
  autoRefresh = true, 
  refreshInterval = 30 
}: DeviceMonitorProps) {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!autoRefresh) return;

    const connectWebSocket = () => {
      const token = localStorage.getItem('token');
      if (!token) return;

      const wsUrl = `ws://localhost:8000/api/ws/admin?token=${token}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('Connected to device monitor WebSocket');
        setWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onclose = () => {
        console.log('Device monitor WebSocket disconnected');
        setWsConnected(false);
        // Reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsConnected(false);
      };

      wsRef.current = ws;
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [autoRefresh]);

  const handleWebSocketMessage = (message: { type: string; data: any; device_id: string }) => {
    const { type, data, device_id } = message;

    switch (type) {
      case 'device_status_summary':
        setDevices(data);
        setLastUpdate(new Date());
        break;
        
      case 'device_connected':
        setDevices(prev => prev.map(device => 
          device.device_id === device_id 
            ? { ...device, is_online: true }
            : device
        ));
        break;
        
      case 'device_disconnected':
        setDevices(prev => prev.map(device => 
          device.device_id === device_id 
            ? { ...device, is_online: false }
            : device
        ));
        break;
        
      case 'device_heartbeat':
        setDevices(prev => prev.map(device => 
          device.device_id === device_id 
            ? { 
                ...device, 
                latest_heartbeat: data,
                performance_score: message.performance_score,
                is_online: true
              }
            : device
        ));
        break;
        
      case 'device_error':
        // Handle device error alerts
        console.error(`Device ${device_id} error:`, data);
        break;
        
      case 'offline_devices_alert':
        // Handle offline devices alert
        console.warn(`${message.count} devices are offline`);
        break;
    }
  };

  // Fetch device data
  const fetchDevices = async () => {
    try {
      setLoading(true);
      setError(null);

      const endpoint = companyId 
        ? `/api/device/organization/${companyId}/devices`
        : '/api/device/all'; // You'd need to implement this endpoint

      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch devices: ${response.status}`);
      }

      const data = await response.json();
      setDevices(data.devices || []);
      setLastUpdate(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch devices');
    } finally {
      setLoading(false);
    }
  };

  // Initial data fetch
  useEffect(() => {
    fetchDevices();
  }, [companyId, fetchDevices]);

  // Auto refresh fallback (in case WebSocket fails)
  useEffect(() => {
    if (!autoRefresh || wsConnected) return;

    const interval = setInterval(fetchDevices, refreshInterval * 1000);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, wsConnected, fetchDevices]);

  const getStatusColor = (device: Device) => {
    if (!device.is_online) return 'bg-red-500';
    if (!device.has_valid_credentials) return 'bg-yellow-500';
    if (device.performance_score && device.performance_score < 70) return 'bg-orange-500';
    return 'bg-green-500';
  };

  const getStatusText = (device: Device) => {
    if (!device.is_online) return 'Offline';
    if (!device.has_valid_credentials) return 'Auth Issue';
    return 'Online';
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return 'Never';
    return new Date(timestamp).toLocaleString();
  };

  const getPerformanceColor = (score?: number) => {
    if (!score) return 'text-gray-500';
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading && devices.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Monitor className="h-5 w-5" />
            Device Monitor
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-blue-600" />
            <span className="ml-2">Loading devices...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Monitor className="h-5 w-5" />
              <CardTitle>Device Monitor</CardTitle>
              {wsConnected ? (
                <Badge variant="outline" className="text-green-600">
                  <Wifi className="h-3 w-3 mr-1" />
                  Live
                </Badge>
              ) : (
                <Badge variant="outline" className="text-gray-500">
                  <WifiOff className="h-3 w-3 mr-1" />
                  Offline
                </Badge>
              )}
            </div>
            <Button onClick={fetchDevices} disabled={loading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
          <CardDescription>
            Real-time monitoring of digital signage devices
            {lastUpdate && ` • Last updated: ${lastUpdate.toLocaleTimeString()}`}
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Device Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {devices.map((device) => (
          <Card key={device.device_id} className="relative">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium">
                  {device.name}
                </CardTitle>
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${getStatusColor(device)}`} />
                  <Badge variant={device.is_online ? 'default' : 'secondary'}>
                    {getStatusText(device)}
                  </Badge>
                </div>
              </div>
              <CardDescription className="text-xs">
                {device.company_name}
              </CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-3">
              {/* Performance Score */}
              {device.performance_score !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Performance</span>
                  <span className={`font-medium ${getPerformanceColor(device.performance_score)}`}>
                    {device.performance_score.toFixed(0)}%
                  </span>
                </div>
              )}

              {/* System Metrics */}
              {device.latest_heartbeat && (
                <div className="space-y-2 text-sm">
                  {device.latest_heartbeat.cpu_usage !== undefined && (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1">
                        <Cpu className="h-3 w-3 text-gray-500" />
                        <span>CPU</span>
                      </div>
                      <span>{device.latest_heartbeat.cpu_usage.toFixed(0)}%</span>
                    </div>
                  )}

                  {device.latest_heartbeat.memory_usage !== undefined && (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1">
                        <Battery className="h-3 w-3 text-gray-500" />
                        <span>Memory</span>
                      </div>
                      <span>{device.latest_heartbeat.memory_usage.toFixed(0)}%</span>
                    </div>
                  )}

                  {device.latest_heartbeat.storage_usage !== undefined && (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1">
                        <HardDrive className="h-3 w-3 text-gray-500" />
                        <span>Storage</span>
                      </div>
                      <span>{device.latest_heartbeat.storage_usage.toFixed(0)}%</span>
                    </div>
                  )}

                  {device.latest_heartbeat.temperature !== undefined && (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1">
                        <Thermometer className="h-3 w-3 text-gray-500" />
                        <span>Temp</span>
                      </div>
                      <span>{device.latest_heartbeat.temperature.toFixed(1)}°C</span>
                    </div>
                  )}

                  {/* Location */}
                  {device.latest_heartbeat.latitude && device.latest_heartbeat.longitude && (
                    <div className="flex items-center gap-1 text-xs text-gray-500">
                      <MapPin className="h-3 w-3" />
                      <span>
                        {device.latest_heartbeat.latitude.toFixed(4)}, {device.latest_heartbeat.longitude.toFixed(4)}
                      </span>
                    </div>
                  )}

                  {/* Content Errors */}
                  {device.latest_heartbeat.content_errors > 0 && (
                    <div className="flex items-center gap-1 text-red-600 text-xs">
                      <AlertTriangle className="h-3 w-3" />
                      <span>{device.latest_heartbeat.content_errors} content errors</span>
                    </div>
                  )}
                </div>
              )}

              {/* Last Heartbeat */}
              <div className="text-xs text-gray-500 border-t pt-2">
                Last seen: {formatTimestamp(device.latest_heartbeat?.timestamp)}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* No Devices */}
      {devices.length === 0 && !loading && (
        <Card>
          <CardContent className="text-center py-8">
            <Monitor className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No devices found</p>
            <p className="text-sm text-gray-500 mt-1">
              Devices will appear here once they are registered and come online
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}