'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/hooks/useAuth';
import { PermissionGate } from '@/components/PermissionGate';
import {
  Monitor,
  Play,
  Pause,
  Square,
  RotateCcw,
  Settings,
  Wifi,
  WifiOff,
  Volume2,
  VolumeX,
  Maximize2,
  Minimize2,
  Eye,
  EyeOff,
  Layers,
  Clock,
  Activity,
  Plus,
  Edit2,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Info,
  Smartphone,
  MonitorSmartphone,
  TestTube2
} from 'lucide-react';

interface DigitalScreen {
  id: string;
  name: string;
  resolution_width: number;
  resolution_height: number;
  orientation: 'landscape' | 'portrait';
  status: string;
  location: string;
}

interface DigitalTwin {
  id: string;
  name: string;
  screen_id: string;
  company_id: string;
  description?: string;
  is_live_mirror: boolean;
  test_content_ids: string[];
  overlay_configs: string[];
  status: 'running' | 'stopped' | 'error';
  created_by: string;
  last_accessed?: string;
  created_at: string;
  updated_at: string;
}

interface TwinFormData {
  name: string;
  screen_id: string;
  company_id: string;
  description: string;
  is_live_mirror: boolean;
}

export default function DigitalTwinPage() {
  const { user } = useAuth();
  const twinViewRef = useRef<HTMLDivElement>(null);
  
  const [screens, setScreens] = useState<DigitalScreen[]>([]);
  const [twins, setTwins] = useState<DigitalTwin[]>([]);
  const [selectedTwin, setSelectedTwin] = useState<DigitalTwin | null>(null);
  const [selectedScreen, setSelectedScreen] = useState<DigitalScreen | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [twinStatus, setTwinStatus] = useState<'running' | 'stopped' | 'error'>('stopped');
  const [volume, setVolume] = useState(100);
  const [isMuted, setIsMuted] = useState(false);
  
  // Performance metrics for the twin
  const [metrics, setMetrics] = useState({
    fps: 60,
    cpuUsage: 25,
    memoryUsage: 512,
    networkLatency: 45,
    uptime: '2h 34m'
  });

  const [formData, setFormData] = useState<TwinFormData>({
    name: '',
    screen_id: '',
    company_id: user?.companies?.[0]?.id || '',
    description: '',
    is_live_mirror: false
  });

  // Fetch screens and twins
  const fetchData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Fetch screens
      const screensResponse = await fetch('/api/screens', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!screensResponse.ok) throw new Error('Failed to fetch screens');
      const screensData = await screensResponse.json();
      setScreens(screensData);

      // Fetch digital twins
      const twinsResponse = await fetch('/api/digital-twins', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (twinsResponse.ok) {
        const twinsData = await twinsResponse.json();
        setTwins(twinsData);
        if (twinsData.length > 0 && !selectedTwin) {
          setSelectedTwin(twinsData[0]);
          const associatedScreen = screensData.find((s: DigitalScreen) => s.id === twinsData[0].screen_id);
          setSelectedScreen(associatedScreen || null);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Simulate real-time metrics updates
  useEffect(() => {
    if (twinStatus === 'running') {
      const interval = setInterval(() => {
        setMetrics(prev => ({
          ...prev,
          fps: 58 + Math.random() * 4,
          cpuUsage: 20 + Math.random() * 10,
          memoryUsage: 480 + Math.random() * 60,
          networkLatency: 40 + Math.random() * 20
        }));
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [twinStatus]);

  // Create digital twin
  const handleCreateTwin = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/digital-twins', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) throw new Error('Failed to create digital twin');

      await fetchData();
      setIsCreateDialogOpen(false);
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create digital twin');
    }
  };

  // Start/Stop digital twin
  const handleToggleTwin = async () => {
    if (!selectedTwin) return;

    try {
      const newStatus = twinStatus === 'running' ? 'stopped' : 'running';
      const token = localStorage.getItem('token');
      
      const response = await fetch(`/api/digital-twins/${selectedTwin.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (!response.ok) throw new Error('Failed to update twin status');
      
      setTwinStatus(newStatus);
      
      // Update twin in state
      setTwins(prev => prev.map(twin => 
        twin.id === selectedTwin.id 
          ? { ...twin, status: newStatus, last_accessed: new Date().toISOString() }
          : twin
      ));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle twin');
    }
  };

  // Delete digital twin
  const handleDeleteTwin = async (twinId: string) => {
    if (!confirm('Are you sure you want to delete this digital twin?')) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/digital-twins/${twinId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to delete digital twin');

      await fetchData();
      if (selectedTwin?.id === twinId) {
        setSelectedTwin(null);
        setSelectedScreen(null);
        setTwinStatus('stopped');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete digital twin');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      screen_id: '',
      company_id: user?.companies?.[0]?.id || '',
      description: '',
      is_live_mirror: false
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'stopped':
        return <Square className="h-4 w-4 text-gray-600" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-600" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'text-green-700 bg-green-50 border-green-200';
      case 'stopped':
        return 'text-gray-700 bg-gray-50 border-gray-200';
      case 'error':
        return 'text-red-700 bg-red-50 border-red-200';
      default:
        return 'text-gray-700 bg-gray-50 border-gray-200';
    }
  };

  // Legacy permission check (keeping for backwards compatibility)
  const canManageTwins = user?.user_type === 'SUPER_USER' || user?.roles?.some(role => 
    ['ADMIN', 'HOST', 'ADVERTISER'].includes(role.role)
  ) || false;

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading digital twins...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <TestTube2 className="h-8 w-8 text-blue-600" />
            Digital Twin Testing
          </h1>
          <p className="text-gray-600 mt-1">
            Test and preview content in virtual screen environments
          </p>
        </div>
        <PermissionGate permission={{ resource: "digital_twin", action: "create" }}>
          <div className="flex items-center space-x-4">
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700">
                  <Plus className="h-4 w-4 mr-2" />
                  Create Twin
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-xl">
                <DialogHeader>
                  <DialogTitle>Create Digital Twin</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div>
                    <Label htmlFor="twin-name">Twin Name *</Label>
                    <Input
                      id="twin-name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="Main Lobby Twin"
                    />
                  </div>

                  <div>
                    <Label htmlFor="screen-select">Associated Screen *</Label>
                    <select
                      id="screen-select"
                      className="w-full p-2 border border-gray-300 rounded-md"
                      value={formData.screen_id}
                      onChange={(e) => setFormData({ ...formData, screen_id: e.target.value })}
                    >
                      <option value="">Select a screen...</option>
                      {screens.map(screen => (
                        <option key={screen.id} value={screen.id}>
                          {screen.name} - {screen.location}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <Label htmlFor="description">Description</Label>
                    <Input
                      id="description"
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      placeholder="Virtual testing environment for..."
                    />
                  </div>

                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="live-mirror"
                      checked={formData.is_live_mirror}
                      onChange={(e) => setFormData({ ...formData, is_live_mirror: e.target.checked })}
                      className="rounded"
                    />
                    <Label htmlFor="live-mirror">Live Mirror (sync with real screen)</Label>
                  </div>

                  <div className="flex justify-end space-x-2 pt-4">
                    <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleCreateTwin}>
                      Create Twin
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </PermissionGate>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Digital Twin List */}
        <div className="lg:col-span-1 space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Available Twins</h3>
          
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {twins.map((twin) => (
              <div
                key={twin.id}
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedTwin?.id === twin.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => {
                  setSelectedTwin(twin);
                  const associatedScreen = screens.find(s => s.id === twin.screen_id);
                  setSelectedScreen(associatedScreen || null);
                  setTwinStatus(twin.status);
                }}
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">{twin.name}</h4>
                  <div className={`px-2 py-1 rounded text-xs font-medium border ${getStatusColor(twin.status)}`}>
                    <div className="flex items-center space-x-1">
                      {getStatusIcon(twin.status)}
                      <span className="capitalize">{twin.status}</span>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-1 text-sm text-gray-600">
                  <div className="flex items-center space-x-2">
                    {selectedScreen?.orientation === 'landscape' ? 
                      <Monitor className="h-4 w-4" /> :
                      <Smartphone className="h-4 w-4" />
                    }
                    <span>{screens.find(s => s.id === twin.screen_id)?.name || 'Unknown Screen'}</span>
                  </div>
                  {twin.description && (
                    <p className="text-xs text-gray-500">{twin.description}</p>
                  )}
                  {twin.last_accessed && (
                    <p className="text-xs text-gray-500">
                      Last used: {new Date(twin.last_accessed).toLocaleDateString()}
                    </p>
                  )}
                </div>

                <div className="flex space-x-1 mt-3 pt-3 border-t border-gray-100">
                  <PermissionGate permission={{ resource: "digital_twin", action: "edit" }}>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        // Edit functionality
                      }}
                      className="flex-1 text-xs"
                    >
                      <Edit2 className="h-3 w-3 mr-1" />
                      Edit
                    </Button>
                  </PermissionGate>
                  <PermissionGate permission={{ resource: "digital_twin", action: "delete" }}>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteTwin(twin.id);
                      }}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50 text-xs"
                    >
                      <Trash2 className="h-3 w-3 mr-1" />
                      Delete
                    </Button>
                  </PermissionGate>
                </div>
              </div>
            ))}
          </div>

          {twins.length === 0 && (
            <div className="text-center py-8">
              <TestTube2 className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-500 mb-4">No digital twins yet</p>
              <PermissionGate permission={{ resource: "digital_twin", action: "create" }}>
                <Button size="sm" onClick={() => setIsCreateDialogOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create First Twin
                </Button>
              </PermissionGate>
            </div>
          )}
        </div>

        {/* Main Twin View */}
        <div className="lg:col-span-3 space-y-4">
          {selectedTwin && selectedScreen ? (
            <>
              {/* Twin Controls */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-4">
                  <PermissionGate permission={{ resource: "digital_twin", action: "control" }}>
                    <Button
                      onClick={handleToggleTwin}
                      className={`${
                        twinStatus === 'running' 
                          ? 'bg-red-600 hover:bg-red-700' 
                          : 'bg-green-600 hover:bg-green-700'
                      } text-white`}
                    >
                    {twinStatus === 'running' ? (
                      <>
                        <Square className="h-4 w-4 mr-2" />
                        Stop Twin
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4 mr-2" />
                        Start Twin
                      </>
                    )}
                  </Button>
                  </PermissionGate>

                  <PermissionGate permission={{ resource: "digital_twin", action: "control" }}>
                    <Button variant="outline" disabled={twinStatus !== 'running'}>
                      <RotateCcw className="h-4 w-4 mr-2" />
                      Restart
                    </Button>
                  </PermissionGate>

                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setIsMuted(!isMuted)}
                    >
                      {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
                    </Button>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={volume}
                      onChange={(e) => setVolume(parseInt(e.target.value))}
                      className="w-20"
                      disabled={isMuted}
                    />
                    <span className="text-sm text-gray-600">{isMuted ? '0' : volume}%</span>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsFullscreen(!isFullscreen)}
                  >
                    {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
                  </Button>
                  <Button variant="outline" size="sm">
                    <Settings className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* Twin Information */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white p-4 rounded-lg border">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Status</p>
                      <p className="text-lg font-bold capitalize">{twinStatus}</p>
                    </div>
                    {getStatusIcon(twinStatus)}
                  </div>
                </div>
                <div className="bg-white p-4 rounded-lg border">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Resolution</p>
                      <p className="text-lg font-bold">
                        {selectedScreen.resolution_width} × {selectedScreen.resolution_height}
                      </p>
                    </div>
                    {selectedScreen.orientation === 'landscape' ? 
                      <Monitor className="h-6 w-6 text-blue-600" /> :
                      <Smartphone className="h-6 w-6 text-blue-600" />
                    }
                  </div>
                </div>
                <div className="bg-white p-4 rounded-lg border">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Live Mirror</p>
                      <p className="text-lg font-bold">
                        {selectedTwin.is_live_mirror ? 'Enabled' : 'Disabled'}
                      </p>
                    </div>
                    {selectedTwin.is_live_mirror ? (
                      <Wifi className="h-6 w-6 text-green-600" />
                    ) : (
                      <WifiOff className="h-6 w-6 text-gray-400" />
                    )}
                  </div>
                </div>
              </div>

              {/* Virtual Screen Display */}
              <div 
                ref={twinViewRef}
                className={`bg-black rounded-lg border-2 transition-all duration-300 ${
                  twinStatus === 'running' 
                    ? 'border-green-400 shadow-lg shadow-green-400/20' 
                    : 'border-gray-300'
                } ${isFullscreen ? 'fixed inset-4 z-50' : 'relative'}`}
              >
                <div 
                  className="relative mx-auto bg-gray-900 rounded-lg overflow-hidden"
                  style={{
                    aspectRatio: `${selectedScreen.resolution_width} / ${selectedScreen.resolution_height}`,
                    maxHeight: isFullscreen ? '90vh' : '400px',
                    width: 'fit-content',
                    maxWidth: '100%'
                  }}
                >
                  {twinStatus === 'running' ? (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-center">
                        <div className="animate-pulse">
                          <div className="w-32 h-32 bg-blue-600 rounded-lg mb-4 mx-auto flex items-center justify-center">
                            <TestTube2 className="h-16 w-16 text-white" />
                          </div>
                          <h3 className="text-white text-xl font-semibold mb-2">
                            Virtual Display Active
                          </h3>
                          <p className="text-gray-300 text-sm">
                            Content simulation running...
                          </p>
                        </div>
                      </div>
                      
                      {/* Simulated content overlay */}
                      <div className="absolute top-4 left-4 right-4">
                        <div className="bg-blue-600/80 text-white p-4 rounded-lg">
                          <h4 className="font-semibold">Welcome to Our Digital Kiosk</h4>
                          <p className="text-sm opacity-90">Interactive content testing in progress</p>
                        </div>
                      </div>
                      
                      {/* Performance overlay */}
                      <div className="absolute bottom-4 right-4 bg-black/70 text-white p-2 rounded text-xs">
                        <div>FPS: {Math.round(metrics.fps)}</div>
                        <div>CPU: {Math.round(metrics.cpuUsage)}%</div>
                        <div>Latency: {Math.round(metrics.networkLatency)}ms</div>
                      </div>
                    </div>
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-center">
                        <Monitor className="h-16 w-16 text-gray-500 mx-auto mb-4" />
                        <h3 className="text-gray-400 text-lg font-semibold mb-2">
                          Digital Twin Stopped
                        </h3>
                        <p className="text-gray-500 text-sm">
                          Click &quot;Start Twin&quot; to begin virtual testing
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Performance Metrics */}
              {twinStatus === 'running' && (
                <div className="bg-white rounded-lg border p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <Activity className="h-5 w-5 text-blue-600" />
                    Performance Metrics
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-green-600">{Math.round(metrics.fps)}</p>
                      <p className="text-sm text-gray-600">FPS</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-blue-600">{Math.round(metrics.cpuUsage)}%</p>
                      <p className="text-sm text-gray-600">CPU Usage</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-purple-600">{Math.round(metrics.memoryUsage)}MB</p>
                      <p className="text-sm text-gray-600">Memory</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-orange-600">{Math.round(metrics.networkLatency)}ms</p>
                      <p className="text-sm text-gray-600">Latency</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-gray-600">{metrics.uptime}</p>
                      <p className="text-sm text-gray-600">Uptime</p>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-12">
              <TestTube2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Digital Twin Selected</h3>
              <p className="text-gray-500 mb-6">
                {twins.length === 0 
                  ? 'Create your first digital twin to start virtual testing'
                  : 'Select a digital twin from the list to begin testing'
                }
              </p>
              <PermissionGate permission={{ resource: "digital_twin", action: "create" }}>
                {twins.length === 0 && (
                  <Button onClick={() => setIsCreateDialogOpen(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Create Digital Twin
                  </Button>
                )}
              </PermissionGate>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}