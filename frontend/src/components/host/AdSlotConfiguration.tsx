'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Monitor,
  Plus,
  Edit2,
  Trash2,
  Eye,
  MapPin,
  Clock,
  Calendar,
  DollarSign,
  Users,
  BarChart3,
  Settings,
  Play,
  Pause,
  AlertTriangle,
  CheckCircle,
  Search,
  Filter
} from 'lucide-react';

interface AdSlot {
  id: string;
  name: string;
  locationId: string;
  locationName: string;
  deviceId: string;
  deviceName: string;
  position: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  duration: number; // seconds
  slotType: 'fullscreen' | 'banner' | 'sidebar' | 'popup' | 'overlay';
  orientation: 'landscape' | 'portrait' | 'any';
  resolution: {
    width: number;
    height: number;
  };
  pricing: {
    baseRate: number;
    primeTimeMultiplier: number;
    weekendMultiplier: number;
    minimumBookingDuration: number; // hours
  };
  availability: {
    monday: { start: string; end: string; available: boolean };
    tuesday: { start: string; end: string; available: boolean };
    wednesday: { start: string; end: string; available: boolean };
    thursday: { start: string; end: string; available: boolean };
    friday: { start: string; end: string; available: boolean };
    saturday: { start: string; end: string; available: boolean };
    sunday: { start: string; end: string; available: boolean };
  };
  targetAudience: {
    ageGroups: string[];
    interests: string[];
    demographics: string[];
  };
  contentRestrictions: {
    allowedFormats: string[];
    maxFileSize: number;
    prohibitedContent: string[];
    requiresModeration: boolean;
  };
  analytics: {
    totalImpressions: number;
    uniqueViews: number;
    averageViewTime: number;
    engagementRate: number;
    revenue: number;
  };
  status: 'active' | 'inactive' | 'maintenance' | 'booked';
  isPublic: boolean;
  createdAt: string;
  updatedAt: string;
}

const defaultAvailability = {
  monday: { start: '09:00', end: '21:00', available: true },
  tuesday: { start: '09:00', end: '21:00', available: true },
  wednesday: { start: '09:00', end: '21:00', available: true },
  thursday: { start: '09:00', end: '21:00', available: true },
  friday: { start: '09:00', end: '22:00', available: true },
  saturday: { start: '10:00', end: '22:00', available: true },
  sunday: { start: '11:00', end: '20:00', available: true }
};

export default function AdSlotConfiguration() {
  const [adSlots, setAdSlots] = useState<AdSlot[]>([]);
  const [locations, setLocations] = useState<any[]>([]);
  const [devices, setDevices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterLocation, setFilterLocation] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState<AdSlot | null>(null);
  const [formData, setFormData] = useState<Partial<AdSlot>>({
    availability: defaultAvailability,
    pricing: {
      baseRate: 10,
      primeTimeMultiplier: 1.5,
      weekendMultiplier: 1.2,
      minimumBookingDuration: 1
    },
    contentRestrictions: {
      allowedFormats: ['image/jpeg', 'image/png', 'video/mp4'],
      maxFileSize: 50,
      prohibitedContent: [],
      requiresModeration: true
    }
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch locations, devices, and ad slots
      const [locationsRes, devicesRes, slotsRes] = await Promise.all([
        fetch('/api/host/locations', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
        }),
        fetch('/api/host/devices', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
        }),
        fetch('/api/host/ad-slots', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
        })
      ]);

      // Mock data for development
      setLocations([
        { id: '1', name: 'Downtown Shopping Mall' },
        { id: '2', name: 'Airport Terminal A' },
        { id: '3', name: 'University Campus Center' }
      ]);

      setDevices([
        { id: '1', name: 'Main Entrance Display', locationId: '1' },
        { id: '2', name: 'Food Court Screen', locationId: '1' },
        { id: '3', name: 'Gate A12 Monitor', locationId: '2' },
        { id: '4', name: 'Baggage Claim Display', locationId: '2' }
      ]);

      setAdSlots([
        {
          id: '1',
          name: 'Main Entrance Banner',
          locationId: '1',
          locationName: 'Downtown Shopping Mall',
          deviceId: '1',
          deviceName: 'Main Entrance Display',
          position: { x: 0, y: 0, width: 1920, height: 300 },
          duration: 15,
          slotType: 'banner',
          orientation: 'landscape',
          resolution: { width: 1920, height: 300 },
          pricing: {
            baseRate: 25,
            primeTimeMultiplier: 1.5,
            weekendMultiplier: 1.2,
            minimumBookingDuration: 2
          },
          availability: defaultAvailability,
          targetAudience: {
            ageGroups: ['25-35', '35-45'],
            interests: ['shopping', 'fashion', 'lifestyle'],
            demographics: ['urban professionals', 'families']
          },
          contentRestrictions: {
            allowedFormats: ['image/jpeg', 'image/png', 'video/mp4'],
            maxFileSize: 50,
            prohibitedContent: ['alcohol', 'gambling'],
            requiresModeration: true
          },
          analytics: {
            totalImpressions: 45000,
            uniqueViews: 32000,
            averageViewTime: 8.5,
            engagementRate: 12.3,
            revenue: 2840.50
          },
          status: 'active',
          isPublic: true,
          createdAt: '2024-01-15',
          updatedAt: '2024-12-10'
        },
        {
          id: '2',
          name: 'Food Court Fullscreen',
          locationId: '1',
          locationName: 'Downtown Shopping Mall',
          deviceId: '2',
          deviceName: 'Food Court Screen',
          position: { x: 0, y: 0, width: 1920, height: 1080 },
          duration: 30,
          slotType: 'fullscreen',
          orientation: 'landscape',
          resolution: { width: 1920, height: 1080 },
          pricing: {
            baseRate: 45,
            primeTimeMultiplier: 1.8,
            weekendMultiplier: 1.5,
            minimumBookingDuration: 1
          },
          availability: {
            ...defaultAvailability,
            friday: { start: '11:00', end: '22:00', available: true },
            saturday: { start: '11:00', end: '22:00', available: true }
          },
          targetAudience: {
            ageGroups: ['18-25', '25-35', '35-45'],
            interests: ['food', 'dining', 'entertainment'],
            demographics: ['students', 'families', 'young professionals']
          },
          contentRestrictions: {
            allowedFormats: ['image/jpeg', 'image/png', 'video/mp4'],
            maxFileSize: 100,
            prohibitedContent: ['competing restaurants'],
            requiresModeration: true
          },
          analytics: {
            totalImpressions: 38000,
            uniqueViews: 28000,
            averageViewTime: 12.8,
            engagementRate: 15.7,
            revenue: 4200.00
          },
          status: 'active',
          isPublic: true,
          createdAt: '2024-02-01',
          updatedAt: '2024-12-08'
        },
        {
          id: '3',
          name: 'Gate A12 Sidebar',
          locationId: '2',
          locationName: 'Airport Terminal A',
          deviceId: '3',
          deviceName: 'Gate A12 Monitor',
          position: { x: 1520, y: 0, width: 400, height: 1080 },
          duration: 20,
          slotType: 'sidebar',
          orientation: 'portrait',
          resolution: { width: 400, height: 1080 },
          pricing: {
            baseRate: 35,
            primeTimeMultiplier: 2.0,
            weekendMultiplier: 1.1,
            minimumBookingDuration: 3
          },
          availability: {
            monday: { start: '05:00', end: '23:00', available: true },
            tuesday: { start: '05:00', end: '23:00', available: true },
            wednesday: { start: '05:00', end: '23:00', available: true },
            thursday: { start: '05:00', end: '23:00', available: true },
            friday: { start: '05:00', end: '23:00', available: true },
            saturday: { start: '05:00', end: '23:00', available: true },
            sunday: { start: '05:00', end: '23:00', available: true }
          },
          targetAudience: {
            ageGroups: ['25-35', '35-45', '45-55'],
            interests: ['travel', 'business', 'technology'],
            demographics: ['business travelers', 'tourists']
          },
          contentRestrictions: {
            allowedFormats: ['image/jpeg', 'image/png', 'video/mp4'],
            maxFileSize: 75,
            prohibitedContent: ['airlines', 'competing travel services'],
            requiresModeration: true
          },
          analytics: {
            totalImpressions: 52000,
            uniqueViews: 41000,
            averageViewTime: 6.2,
            engagementRate: 9.8,
            revenue: 5680.25
          },
          status: 'booked',
          isPublic: true,
          createdAt: '2024-02-15',
          updatedAt: '2024-12-05'
        }
      ]);

    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSlot = async () => {
    try {
      const response = await fetch('/api/host/ad-slots', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        await fetchData();
        setIsAddDialogOpen(false);
        setFormData({
          availability: defaultAvailability,
          pricing: {
            baseRate: 10,
            primeTimeMultiplier: 1.5,
            weekendMultiplier: 1.2,
            minimumBookingDuration: 1
          }
        });
      }
    } catch (error) {
      console.error('Error adding ad slot:', error);
    }
  };

  const handleEditSlot = async () => {
    if (!selectedSlot) return;

    try {
      const response = await fetch(`/api/host/ad-slots/${selectedSlot.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        await fetchData();
        setIsEditDialogOpen(false);
        setSelectedSlot(null);
      }
    } catch (error) {
      console.error('Error updating ad slot:', error);
    }
  };

  const handleDeleteSlot = async (slotId: string) => {
    if (!confirm('Are you sure you want to delete this ad slot?')) return;

    try {
      const response = await fetch(`/api/host/ad-slots/${slotId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        await fetchData();
      }
    } catch (error) {
      console.error('Error deleting ad slot:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'inactive':
        return 'bg-gray-100 text-gray-800';
      case 'maintenance':
        return 'bg-yellow-100 text-yellow-800';
      case 'booked':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSlotTypeIcon = (type: string) => {
    switch (type) {
      case 'fullscreen':
        return '🖥️';
      case 'banner':
        return '📰';
      case 'sidebar':
        return '📋';
      case 'popup':
        return '💬';
      case 'overlay':
        return '🔄';
      default:
        return '📺';
    }
  };

  const filteredSlots = adSlots.filter(slot => {
    const matchesSearch = slot.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         slot.locationName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         slot.deviceName.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesLocation = filterLocation === 'all' || slot.locationId === filterLocation;
    const matchesStatus = filterStatus === 'all' || slot.status === filterStatus;
    return matchesSearch && matchesLocation && matchesStatus;
  });

  const renderSlotForm = () => (
    <Tabs defaultValue="basic" className="w-full">
      <TabsList className="grid w-full grid-cols-4">
        <TabsTrigger value="basic">Basic Info</TabsTrigger>
        <TabsTrigger value="position">Position & Size</TabsTrigger>
        <TabsTrigger value="pricing">Pricing</TabsTrigger>
        <TabsTrigger value="content">Content Rules</TabsTrigger>
      </TabsList>

      <TabsContent value="basic" className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <Label htmlFor="slotName">Slot Name *</Label>
            <Input
              id="slotName"
              value={formData.name || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="e.g., Main Entrance Banner"
            />
          </div>

          <div>
            <Label htmlFor="slotType">Slot Type *</Label>
            <Select 
              value={formData.slotType || ''} 
              onValueChange={(value) => setFormData(prev => ({ ...prev, slotType: value as any }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select slot type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="fullscreen">Full Screen</SelectItem>
                <SelectItem value="banner">Banner</SelectItem>
                <SelectItem value="sidebar">Sidebar</SelectItem>
                <SelectItem value="popup">Popup</SelectItem>
                <SelectItem value="overlay">Overlay</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="location">Location *</Label>
            <Select 
              value={formData.locationId || ''} 
              onValueChange={(value) => setFormData(prev => ({ ...prev, locationId: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select location" />
              </SelectTrigger>
              <SelectContent>
                {locations.map(location => (
                  <SelectItem key={location.id} value={location.id}>
                    {location.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="device">Device *</Label>
            <Select 
              value={formData.deviceId || ''} 
              onValueChange={(value) => setFormData(prev => ({ ...prev, deviceId: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select device" />
              </SelectTrigger>
              <SelectContent>
                {devices
                  .filter(device => !formData.locationId || device.locationId === formData.locationId)
                  .map(device => (
                    <SelectItem key={device.id} value={device.id}>
                      {device.name}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="duration">Duration (seconds) *</Label>
            <Input
              id="duration"
              type="number"
              value={formData.duration || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, duration: parseInt(e.target.value) || 0 }))}
              placeholder="15"
            />
          </div>

          <div>
            <Label htmlFor="orientation">Orientation</Label>
            <Select 
              value={formData.orientation || ''} 
              onValueChange={(value) => setFormData(prev => ({ ...prev, orientation: value as any }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select orientation" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="landscape">Landscape</SelectItem>
                <SelectItem value="portrait">Portrait</SelectItem>
                <SelectItem value="any">Any</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Switch
            id="isPublic"
            checked={formData.isPublic || false}
            onCheckedChange={(checked) => setFormData(prev => ({ ...prev, isPublic: checked }))}
          />
          <Label htmlFor="isPublic">Make this slot publicly available for booking</Label>
        </div>
      </TabsContent>

      <TabsContent value="position" className="space-y-4">
        <div className="grid gap-4 md:grid-cols-4">
          <div>
            <Label htmlFor="posX">X Position</Label>
            <Input
              id="posX"
              type="number"
              value={formData.position?.x || ''}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                position: { ...prev.position!, x: parseInt(e.target.value) || 0 }
              }))}
              placeholder="0"
            />
          </div>

          <div>
            <Label htmlFor="posY">Y Position</Label>
            <Input
              id="posY"
              type="number"
              value={formData.position?.y || ''}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                position: { ...prev.position!, y: parseInt(e.target.value) || 0 }
              }))}
              placeholder="0"
            />
          </div>

          <div>
            <Label htmlFor="width">Width (px)</Label>
            <Input
              id="width"
              type="number"
              value={formData.position?.width || ''}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                position: { ...prev.position!, width: parseInt(e.target.value) || 0 }
              }))}
              placeholder="1920"
            />
          </div>

          <div>
            <Label htmlFor="height">Height (px)</Label>
            <Input
              id="height"
              type="number"
              value={formData.position?.height || ''}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                position: { ...prev.position!, height: parseInt(e.target.value) || 0 }
              }))}
              placeholder="300"
            />
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <Label htmlFor="resWidth">Resolution Width</Label>
            <Input
              id="resWidth"
              type="number"
              value={formData.resolution?.width || ''}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                resolution: { ...prev.resolution!, width: parseInt(e.target.value) || 0 }
              }))}
              placeholder="1920"
            />
          </div>

          <div>
            <Label htmlFor="resHeight">Resolution Height</Label>
            <Input
              id="resHeight"
              type="number"
              value={formData.resolution?.height || ''}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                resolution: { ...prev.resolution!, height: parseInt(e.target.value) || 0 }
              }))}
              placeholder="300"
            />
          </div>
        </div>
      </TabsContent>

      <TabsContent value="pricing" className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <Label htmlFor="baseRate">Base Rate ($/hour) *</Label>
            <Input
              id="baseRate"
              type="number"
              step="0.01"
              value={formData.pricing?.baseRate || ''}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                pricing: { ...prev.pricing!, baseRate: parseFloat(e.target.value) || 0 }
              }))}
              placeholder="10.00"
            />
          </div>

          <div>
            <Label htmlFor="minimumDuration">Minimum Booking (hours)</Label>
            <Input
              id="minimumDuration"
              type="number"
              value={formData.pricing?.minimumBookingDuration || ''}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                pricing: { ...prev.pricing!, minimumBookingDuration: parseInt(e.target.value) || 1 }
              }))}
              placeholder="1"
            />
          </div>

          <div>
            <Label htmlFor="primeTimeMultiplier">Prime Time Multiplier</Label>
            <Input
              id="primeTimeMultiplier"
              type="number"
              step="0.1"
              value={formData.pricing?.primeTimeMultiplier || ''}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                pricing: { ...prev.pricing!, primeTimeMultiplier: parseFloat(e.target.value) || 1 }
              }))}
              placeholder="1.5"
            />
          </div>

          <div>
            <Label htmlFor="weekendMultiplier">Weekend Multiplier</Label>
            <Input
              id="weekendMultiplier"
              type="number"
              step="0.1"
              value={formData.pricing?.weekendMultiplier || ''}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                pricing: { ...prev.pricing!, weekendMultiplier: parseFloat(e.target.value) || 1 }
              }))}
              placeholder="1.2"
            />
          </div>
        </div>
      </TabsContent>

      <TabsContent value="content" className="space-y-4">
        <div>
          <Label htmlFor="maxFileSize">Maximum File Size (MB)</Label>
          <Input
            id="maxFileSize"
            type="number"
            value={formData.contentRestrictions?.maxFileSize || ''}
            onChange={(e) => setFormData(prev => ({ 
              ...prev, 
              contentRestrictions: { 
                ...prev.contentRestrictions!, 
                maxFileSize: parseInt(e.target.value) || 50 
              }
            }))}
            placeholder="50"
          />
        </div>

        <div className="flex items-center space-x-2">
          <Switch
            id="requiresModeration"
            checked={formData.contentRestrictions?.requiresModeration || false}
            onCheckedChange={(checked) => setFormData(prev => ({ 
              ...prev, 
              contentRestrictions: { 
                ...prev.contentRestrictions!, 
                requiresModeration: checked 
              }
            }))}
          />
          <Label htmlFor="requiresModeration">Require content moderation before display</Label>
        </div>
      </TabsContent>
    </Tabs>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading ad slots...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Ad Slot Configuration</h2>
          <p className="text-gray-600 mt-1">
            Configure and manage your digital advertising slots
          </p>
        </div>
        
        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              Create Ad Slot
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create New Ad Slot</DialogTitle>
            </DialogHeader>
            {renderSlotForm()}
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleAddSlot}>
                Create Slot
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search ad slots..."
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
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
            <SelectItem value="booked">Booked</SelectItem>
            <SelectItem value="maintenance">Maintenance</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Ad Slots Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredSlots.map((slot) => (
          <Card key={slot.id} className="border-0 shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{getSlotTypeIcon(slot.slotType)}</span>
                  <div>
                    <CardTitle className="text-lg">{slot.name}</CardTitle>
                    <p className="text-sm text-gray-600">{slot.locationName}</p>
                  </div>
                </div>
                <Badge className={getStatusColor(slot.status)}>
                  {slot.status}
                </Badge>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-4">
              <div className="text-sm text-gray-600">
                <p className="flex items-center gap-1">
                  <Monitor className="h-3 w-3" />
                  {slot.deviceName}
                </p>
                <p className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {slot.duration}s duration • {slot.orientation}
                </p>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Base Rate</p>
                  <p className="font-semibold text-green-600">
                    ${slot.pricing.baseRate}/hr
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Size</p>
                  <p className="font-semibold">
                    {slot.position.width}×{slot.position.height}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Monthly Revenue</p>
                  <p className="font-semibold text-green-600">
                    ${slot.analytics.revenue.toFixed(2)}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Impressions</p>
                  <p className="font-semibold">
                    {slot.analytics.totalImpressions.toLocaleString()}
                  </p>
                </div>
              </div>
              
              <div className="flex justify-between pt-2 border-t border-gray-100">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSelectedSlot(slot);
                    setFormData(slot);
                    setIsEditDialogOpen(true);
                  }}
                  className="gap-1"
                >
                  <Edit2 className="h-3 w-3" />
                  Edit
                </Button>
                
                <div className="flex gap-1">
                  <Button variant="outline" size="sm" className="gap-1">
                    <BarChart3 className="h-3 w-3" />
                    Analytics
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDeleteSlot(slot.id)}
                    className="gap-1 text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredSlots.length === 0 && (
        <Card className="border-0 shadow-lg">
          <CardContent className="text-center py-12">
            <Monitor className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No ad slots found</h3>
            <p className="text-gray-600 mb-4">
              {searchTerm || filterLocation !== 'all' || filterStatus !== 'all'
                ? 'Try adjusting your search or filter criteria.'
                : 'Create your first ad slot to start monetizing your displays.'}
            </p>
            {!searchTerm && filterLocation === 'all' && filterStatus === 'all' && (
              <Button onClick={() => setIsAddDialogOpen(true)} className="gap-2">
                <Plus className="h-4 w-4" />
                Create Your First Ad Slot
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Edit Ad Slot Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Ad Slot</DialogTitle>
          </DialogHeader>
          {renderSlotForm()}
          <div className="flex justify-end gap-3 pt-4">
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleEditSlot}>
              Save Changes
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}