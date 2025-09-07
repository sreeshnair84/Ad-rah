'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Loader2, Monitor, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';
import { useDevice } from '@/hooks/useDevice';

interface Device {
  id: string;
  name: string;
  location: string;
  status: 'online' | 'offline' | 'error';
  company_id: string;
  device_type: string;
  last_seen?: string;
}

export default function DeviceManagementPage() {
  const { loading, error, registerDevice, listDevices, distributeContent } = useDevice();
  const [devices, setDevices] = useState<Device[]>([]);
  const [showRegistration, setShowRegistration] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    device_type: 'display',
    company_id: ''
  });

  useEffect(() => {
    loadDevices();
  }, []);

  const loadDevices = async () => {
    try {
      const deviceList = await listDevices();
      setDevices(deviceList);
    } catch (err) {
      console.error('Failed to load devices:', err);
    }
  };

  const handleRegisterDevice = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await registerDevice(formData);
      setFormData({ name: '', location: '', device_type: 'display', company_id: '' });
      setShowRegistration(false);
      loadDevices();
    } catch (err) {
      console.error('Failed to register device:', err);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'offline':
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Monitor className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'offline':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Device Management</h1>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={loadDevices}
            disabled={loading}
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Refresh
          </Button>
          <Button onClick={() => setShowRegistration(true)}>
            Register New Device
          </Button>
        </div>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-red-700">
              <AlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {showRegistration && (
        <Card>
          <CardHeader>
            <CardTitle>Register New Device</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleRegisterDevice} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Device Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Lobby Display 1"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="location">Location</Label>
                  <Input
                    id="location"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    placeholder="e.g., Main Lobby"
                    required
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="device_type">Device Type</Label>
                  <Select value={formData.device_type} onValueChange={(value) => setFormData({ ...formData, device_type: value })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="display">Display</SelectItem>
                      <SelectItem value="kiosk">Kiosk</SelectItem>
                      <SelectItem value="tablet">Tablet</SelectItem>
                      <SelectItem value="tv">TV</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="company_id">Company ID</Label>
                  <Input
                    id="company_id"
                    value={formData.company_id}
                    onChange={(e) => setFormData({ ...formData, company_id: e.target.value })}
                    placeholder="Company ID"
                    required
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <Button type="submit" disabled={loading}>
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                  Register Device
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowRegistration(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Registered Devices ({devices.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && devices.length === 0 ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="h-8 w-8 animate-spin" />
              <span className="ml-2">Loading devices...</span>
            </div>
          ) : devices.length === 0 ? (
            <div className="text-center p-8 text-gray-500">
              <Monitor className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No devices registered yet.</p>
              <Button className="mt-4" onClick={() => setShowRegistration(true)}>
                Register First Device
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {devices.map((device) => (
                <Card key={device.id} className="border-2">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Monitor className="h-5 w-5 text-gray-600" />
                        <h3 className="font-semibold">{device.name}</h3>
                      </div>
                      <div className="flex items-center gap-1">
                        {getStatusIcon(device.status)}
                        <Badge className={getStatusBadgeColor(device.status)}>
                          {device.status}
                        </Badge>
                      </div>
                    </div>
                    <div className="space-y-1 text-sm text-gray-600">
                      <p><span className="font-medium">Location:</span> {device.location}</p>
                      <p><span className="font-medium">Type:</span> {device.device_type}</p>
                      <p><span className="font-medium">ID:</span> {device.id}</p>
                      {device.last_seen && (
                        <p><span className="font-medium">Last Seen:</span> {new Date(device.last_seen).toLocaleString()}</p>
                      )}
                    </div>
                    <div className="mt-4 flex gap-2">
                      <Button size="sm" variant="outline" className="flex-1">
                        View Content
                      </Button>
                      <Button size="sm" variant="outline" className="flex-1">
                        Configure
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
