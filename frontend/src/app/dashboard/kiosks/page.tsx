'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/hooks/useAuth';
import {
  MonitorSmartphone,
  Plus,
  Edit2,
  Trash2,
  Wifi,
  WifiOff,
  Settings,
  Activity,
  MapPin,
  Monitor,
  Smartphone,
  AlertCircle,
  CheckCircle2,
  Clock,
  Power,
  Search,
  Filter
} from 'lucide-react';

interface DigitalScreen {
  id: string;
  name: string;
  description?: string;
  company_id: string;
  location: string;
  resolution_width: number;
  resolution_height: number;
  orientation: 'landscape' | 'portrait';
  status: 'active' | 'inactive' | 'maintenance' | 'offline';
  ip_address?: string;
  mac_address?: string;
  last_seen?: string;
  created_at: string;
  updated_at: string;
}

interface ScreenFormData {
  name: string;
  description: string;
  company_id: string;
  location: string;
  resolution_width: number;
  resolution_height: number;
  orientation: 'landscape' | 'portrait';
  ip_address: string;
  mac_address: string;
}

export default function KiosksPage() {
  const { user } = useAuth();
  const [screens, setScreens] = useState<DigitalScreen[]>([]);
  const [filteredScreens, setFilteredScreens] = useState<DigitalScreen[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [selectedScreen, setSelectedScreen] = useState<DigitalScreen | null>(null);

  const [formData, setFormData] = useState<ScreenFormData>({
    name: '',
    description: '',
    company_id: user?.companies?.[0]?.id || '',
    location: '',
    resolution_width: 1920,
    resolution_height: 1080,
    orientation: 'landscape',
    ip_address: '',
    mac_address: ''
  });

  // Fetch screens from API
  const fetchScreens = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch('/api/screens', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch screens');
      }

      const data = await response.json();
      setScreens(data);
      setFilteredScreens(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch screens');
    } finally {
      setLoading(false);
    }
  };

  // Filter screens based on search and status
  useEffect(() => {
    let filtered = screens;

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(screen =>
        screen.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        screen.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
        screen.description?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(screen => screen.status === statusFilter);
    }

    setFilteredScreens(filtered);
  }, [screens, searchTerm, statusFilter]);

  useEffect(() => {
    fetchScreens();
  }, []);

  // Create new screen
  const handleCreateScreen = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/screens', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('Failed to create screen');
      }

      await fetchScreens();
      setIsCreateDialogOpen(false);
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create screen');
    }
  };

  // Update screen
  const handleUpdateScreen = async () => {
    if (!selectedScreen) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/screens/${selectedScreen.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('Failed to update screen');
      }

      await fetchScreens();
      setIsEditDialogOpen(false);
      setSelectedScreen(null);
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update screen');
    }
  };

  // Delete screen
  const handleDeleteScreen = async (screenId: string) => {
    if (!confirm('Are you sure you want to delete this screen?')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/screens/${screenId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete screen');
      }

      await fetchScreens();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete screen');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      company_id: user?.companies?.[0]?.id || '',
      location: '',
      resolution_width: 1920,
      resolution_height: 1080,
      orientation: 'landscape',
      ip_address: '',
      mac_address: ''
    });
  };

  const openEditDialog = (screen: DigitalScreen) => {
    setSelectedScreen(screen);
    setFormData({
      name: screen.name,
      description: screen.description || '',
      company_id: screen.company_id,
      location: screen.location,
      resolution_width: screen.resolution_width,
      resolution_height: screen.resolution_height,
      orientation: screen.orientation,
      ip_address: screen.ip_address || '',
      mac_address: screen.mac_address || ''
    });
    setIsEditDialogOpen(true);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'maintenance':
        return <Clock className="h-4 w-4 text-yellow-600" />;
      case 'inactive':
        return <Power className="h-4 w-4 text-gray-600" />;
      case 'offline':
        return <AlertCircle className="h-4 w-4 text-red-600" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-700 bg-green-50 border-green-200';
      case 'maintenance':
        return 'text-yellow-700 bg-yellow-50 border-yellow-200';
      case 'inactive':
        return 'text-gray-700 bg-gray-50 border-gray-200';
      case 'offline':
        return 'text-red-700 bg-red-50 border-red-200';
      default:
        return 'text-gray-700 bg-gray-50 border-gray-200';
    }
  };

  // Check if user can edit screens
  const canEditScreens = user?.roles?.some(role => 
    ['ADMIN', 'HOST'].includes(role.role)
  ) || false;

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading screens...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <MonitorSmartphone className="h-8 w-8 text-blue-600" />
            Digital Screens
          </h1>
          <p className="text-gray-600 mt-1">
            Manage your digital kiosk displays and monitor their status
          </p>
        </div>
        {canEditScreens && (
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700">
                <Plus className="h-4 w-4 mr-2" />
                Add Screen
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create New Digital Screen</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="name">Screen Name *</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="Main Lobby Display"
                    />
                  </div>
                  <div>
                    <Label htmlFor="location">Location *</Label>
                    <Input
                      id="location"
                      value={formData.location}
                      onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                      placeholder="Building A - Main Lobby"
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="description">Description</Label>
                  <Input
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Primary display for visitor information"
                  />
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="width">Width (px)</Label>
                    <Input
                      id="width"
                      type="number"
                      value={formData.resolution_width}
                      onChange={(e) => setFormData({ ...formData, resolution_width: parseInt(e.target.value) })}
                    />
                  </div>
                  <div>
                    <Label htmlFor="height">Height (px)</Label>
                    <Input
                      id="height"
                      type="number"
                      value={formData.resolution_height}
                      onChange={(e) => setFormData({ ...formData, resolution_height: parseInt(e.target.value) })}
                    />
                  </div>
                  <div>
                    <Label htmlFor="orientation">Orientation</Label>
                    <select
                      id="orientation"
                      className="w-full p-2 border border-gray-300 rounded-md"
                      value={formData.orientation}
                      onChange={(e) => setFormData({ ...formData, orientation: e.target.value as 'landscape' | 'portrait' })}
                    >
                      <option value="landscape">Landscape</option>
                      <option value="portrait">Portrait</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="ip">IP Address</Label>
                    <Input
                      id="ip"
                      value={formData.ip_address}
                      onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
                      placeholder="192.168.1.100"
                    />
                  </div>
                  <div>
                    <Label htmlFor="mac">MAC Address</Label>
                    <Input
                      id="mac"
                      value={formData.mac_address}
                      onChange={(e) => setFormData({ ...formData, mac_address: e.target.value })}
                      placeholder="00:1B:44:11:3A:B7"
                    />
                  </div>
                </div>

                <div className="flex justify-end space-x-2 pt-4">
                  <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreateScreen}>
                    Create Screen
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Search and Filter */}
      <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search screens by name, location, or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-gray-600" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="p-2 border border-gray-300 rounded-md bg-white"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="maintenance">Maintenance</option>
            <option value="inactive">Inactive</option>
            <option value="offline">Offline</option>
          </select>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Screens</p>
              <p className="text-2xl font-bold text-gray-900">{screens.length}</p>
            </div>
            <MonitorSmartphone className="h-8 w-8 text-blue-600" />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active</p>
              <p className="text-2xl font-bold text-green-600">
                {screens.filter(s => s.status === 'active').length}
              </p>
            </div>
            <CheckCircle2 className="h-8 w-8 text-green-600" />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Maintenance</p>
              <p className="text-2xl font-bold text-yellow-600">
                {screens.filter(s => s.status === 'maintenance').length}
              </p>
            </div>
            <Settings className="h-8 w-8 text-yellow-600" />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Offline</p>
              <p className="text-2xl font-bold text-red-600">
                {screens.filter(s => s.status === 'offline').length}
              </p>
            </div>
            <WifiOff className="h-8 w-8 text-red-600" />
          </div>
        </div>
      </div>

      {/* Screens Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredScreens.map((screen) => (
          <div key={screen.id} className="bg-white rounded-lg border border-gray-200 hover:shadow-lg transition-shadow">
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  {screen.orientation === 'landscape' ? 
                    <Monitor className="h-8 w-8 text-blue-600" /> :
                    <Smartphone className="h-8 w-8 text-blue-600" />
                  }
                  <div>
                    <h3 className="font-semibold text-gray-900">{screen.name}</h3>
                    <p className="text-sm text-gray-500">{screen.location}</p>
                  </div>
                </div>
                <div className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(screen.status)}`}>
                  <div className="flex items-center space-x-1">
                    {getStatusIcon(screen.status)}
                    <span className="capitalize">{screen.status}</span>
                  </div>
                </div>
              </div>

              {screen.description && (
                <p className="text-sm text-gray-600 mb-4">{screen.description}</p>
              )}

              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Resolution:</span>
                  <span className="font-medium">{screen.resolution_width} × {screen.resolution_height}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Orientation:</span>
                  <span className="font-medium capitalize">{screen.orientation}</span>
                </div>
                {screen.ip_address && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500">IP Address:</span>
                    <span className="font-medium">{screen.ip_address}</span>
                  </div>
                )}
                {screen.last_seen && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500">Last Seen:</span>
                    <span className="font-medium">
                      {new Date(screen.last_seen).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </div>

              {canEditScreens && (
                <div className="flex space-x-2 mt-4 pt-4 border-t border-gray-100">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openEditDialog(screen)}
                    className="flex-1"
                  >
                    <Edit2 className="h-3 w-3 mr-1" />
                    Edit
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDeleteScreen(screen.id)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="h-3 w-3 mr-1" />
                    Delete
                  </Button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {filteredScreens.length === 0 && (
        <div className="text-center py-12">
          <MonitorSmartphone className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No screens found</h3>
          <p className="text-gray-500 mb-6">
            {searchTerm || statusFilter !== 'all' 
              ? 'Try adjusting your search or filter criteria'
              : 'Get started by creating your first digital screen'
            }
          </p>
          {canEditScreens && !searchTerm && statusFilter === 'all' && (
            <Button onClick={() => setIsCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add First Screen
            </Button>
          )}
        </div>
      )}

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Digital Screen</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit-name">Screen Name *</Label>
                <Input
                  id="edit-name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="edit-location">Location *</Label>
                <Input
                  id="edit-location"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                />
              </div>
            </div>

            <div>
              <Label htmlFor="edit-description">Description</Label>
              <Input
                id="edit-description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="edit-width">Width (px)</Label>
                <Input
                  id="edit-width"
                  type="number"
                  value={formData.resolution_width}
                  onChange={(e) => setFormData({ ...formData, resolution_width: parseInt(e.target.value) })}
                />
              </div>
              <div>
                <Label htmlFor="edit-height">Height (px)</Label>
                <Input
                  id="edit-height"
                  type="number"
                  value={formData.resolution_height}
                  onChange={(e) => setFormData({ ...formData, resolution_height: parseInt(e.target.value) })}
                />
              </div>
              <div>
                <Label htmlFor="edit-orientation">Orientation</Label>
                <select
                  id="edit-orientation"
                  className="w-full p-2 border border-gray-300 rounded-md"
                  value={formData.orientation}
                  onChange={(e) => setFormData({ ...formData, orientation: e.target.value as 'landscape' | 'portrait' })}
                >
                  <option value="landscape">Landscape</option>
                  <option value="portrait">Portrait</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit-ip">IP Address</Label>
                <Input
                  id="edit-ip"
                  value={formData.ip_address}
                  onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="edit-mac">MAC Address</Label>
                <Input
                  id="edit-mac"
                  value={formData.mac_address}
                  onChange={(e) => setFormData({ ...formData, mac_address: e.target.value })}
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-4">
              <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleUpdateScreen}>
                Update Screen
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
