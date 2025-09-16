'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { PermissionGate } from '@/components/PermissionGate';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import {
  Plus,
  MapPin,
  Monitor,
  Calendar,
  Clock,
  DollarSign,
  Users,
  Activity,
  Filter,
  Search,
  Edit,
  Eye,
  Trash2,
  Power,
  PowerOff,
  BarChart3,
  Settings,
  Maximize2,
  Wifi,
  WifiOff
} from 'lucide-react';

interface AdSlot {
  id: string;
  name: string;
  locationId: string;
  locationName: string;
  deviceId: string;
  deviceName: string;
  status: 'active' | 'inactive' | 'maintenance';
  screenResolution: string;
  screenSize: number;
  pricePerHour: number;
  maxDuration: number;
  minDuration: number;
  availability: {
    monday: string[];
    tuesday: string[];
    wednesday: string[];
    thursday: string[];
    friday: string[];
    saturday: string[];
    sunday: string[];
  };
  tags: string[];
  description: string;
  currentBooking?: {
    id: string;
    advertiserName: string;
    contentTitle: string;
    startTime: Date;
    endTime: Date;
    status: 'scheduled' | 'playing' | 'completed';
  };
  performance: {
    totalImpressions: number;
    avgViewTime: number;
    revenue: number;
    occupancyRate: number;
  };
  createdAt: Date;
  updatedAt: Date;
}

interface Location {
  id: string;
  name: string;
  address: string;
  category: string;
  footTraffic: number;
  demographics: {
    ageGroups: Record<string, number>;
    interests: string[];
  };
}

export default function AdSlotsPage() {
  const { user, isHostCompany, isAdvertiserCompany } = useAuth();
  const [activeTab, setActiveTab] = useState('slots');
  const [adSlots, setAdSlots] = useState<AdSlot[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [locationFilter, setLocationFilter] = useState('all');
  const [showCreateSlot, setShowCreateSlot] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState<AdSlot | null>(null);

  // Form state for creating/editing slots
  const [formData, setFormData] = useState({
    name: '',
    locationId: '',
    deviceId: '',
    pricePerHour: 0,
    maxDuration: 60,
    minDuration: 5,
    description: '',
    tags: '',
    availability: {
      monday: ['09:00-18:00'],
      tuesday: ['09:00-18:00'],
      wednesday: ['09:00-18:00'],
      thursday: ['09:00-18:00'],
      friday: ['09:00-18:00'],
      saturday: ['10:00-16:00'],
      sunday: ['12:00-16:00']
    }
  });

  useEffect(() => {
    fetchAdSlots();
    fetchLocations();
  }, []);

  const fetchAdSlots = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/ad-slots', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAdSlots(data.ad_slots || []);
      } else {
        // Mock data for demo
        setAdSlots([
          {
            id: '1',
            name: 'Mall Entrance - Main Display',
            locationId: 'loc1',
            locationName: 'Downtown Mall',
            deviceId: 'dev1',
            deviceName: 'Entrance Display 1',
            status: 'active',
            screenResolution: '1920x1080',
            screenSize: 55,
            pricePerHour: 25,
            maxDuration: 120,
            minDuration: 15,
            availability: {
              monday: ['08:00-22:00'],
              tuesday: ['08:00-22:00'],
              wednesday: ['08:00-22:00'],
              thursday: ['08:00-22:00'],
              friday: ['08:00-23:00'],
              saturday: ['09:00-23:00'],
              sunday: ['10:00-21:00']
            },
            tags: ['high-traffic', 'premium', 'entrance'],
            description: 'Prime location at mall entrance with high foot traffic',
            currentBooking: {
              id: 'book1',
              advertiserName: 'TechCorp Solutions',
              contentTitle: 'Summer Sale Campaign',
              startTime: new Date(),
              endTime: new Date(Date.now() + 2 * 60 * 60 * 1000),
              status: 'playing'
            },
            performance: {
              totalImpressions: 15420,
              avgViewTime: 12.5,
              revenue: 1850,
              occupancyRate: 78
            },
            createdAt: new Date('2024-01-15'),
            updatedAt: new Date()
          },
          {
            id: '2',
            name: 'Food Court - Digital Menu Board',
            locationId: 'loc2',
            locationName: 'Food Court',
            deviceId: 'dev2',
            deviceName: 'Menu Board 1',
            status: 'active',
            screenResolution: '3840x2160',
            screenSize: 75,
            pricePerHour: 35,
            maxDuration: 180,
            minDuration: 30,
            availability: {
              monday: ['11:00-21:00'],
              tuesday: ['11:00-21:00'],
              wednesday: ['11:00-21:00'],
              thursday: ['11:00-21:00'],
              friday: ['11:00-22:00'],
              saturday: ['10:00-22:00'],
              sunday: ['11:00-20:00']
            },
            tags: ['food-court', '4k', 'large-screen'],
            description: '4K display in busy food court area',
            performance: {
              totalImpressions: 22100,
              avgViewTime: 18.2,
              revenue: 2650,
              occupancyRate: 85
            },
            createdAt: new Date('2024-02-01'),
            updatedAt: new Date()
          }
        ]);
      }
    } catch (error) {
      console.error('Failed to fetch ad slots:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchLocations = async () => {
    try {
      const response = await fetch('/api/locations', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setLocations(data.locations || []);
      } else {
        // Mock data
        setLocations([
          {
            id: 'loc1',
            name: 'Downtown Mall',
            address: '123 Main St, Downtown',
            category: 'Shopping Center',
            footTraffic: 45000,
            demographics: {
              ageGroups: { '18-25': 25, '26-35': 35, '36-45': 20, '46-60': 15, '60+': 5 },
              interests: ['shopping', 'dining', 'entertainment']
            }
          },
          {
            id: 'loc2',
            name: 'Food Court',
            address: '123 Main St, Level 2',
            category: 'Food & Dining',
            footTraffic: 28000,
            demographics: {
              ageGroups: { '18-25': 30, '26-35': 30, '36-45': 25, '46-60': 12, '60+': 3 },
              interests: ['food', 'dining', 'quick-service']
            }
          }
        ]);
      }
    } catch (error) {
      console.error('Failed to fetch locations:', error);
    }
  };

  const filteredSlots = adSlots.filter(slot => {
    const matchesSearch = slot.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         slot.locationName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         slot.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesStatus = statusFilter === 'all' || slot.status === statusFilter;
    const matchesLocation = locationFilter === 'all' || slot.locationId === locationFilter;

    return matchesSearch && matchesStatus && matchesLocation;
  });

  const handleCreateSlot = async () => {
    try {
      const response = await fetch('/api/ad-slots', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...formData,
          tags: formData.tags.split(',').map(tag => tag.trim()).filter(Boolean)
        })
      });

      if (response.ok) {
        await fetchAdSlots();
        setShowCreateSlot(false);
        resetForm();
      }
    } catch (error) {
      console.error('Failed to create ad slot:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      locationId: '',
      deviceId: '',
      pricePerHour: 0,
      maxDuration: 60,
      minDuration: 5,
      description: '',
      tags: '',
      availability: {
        monday: ['09:00-18:00'],
        tuesday: ['09:00-18:00'],
        wednesday: ['09:00-18:00'],
        thursday: ['09:00-18:00'],
        friday: ['09:00-18:00'],
        saturday: ['10:00-16:00'],
        sunday: ['12:00-16:00']
      }
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'inactive': return 'bg-gray-100 text-gray-800';
      case 'maintenance': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getBookingStatusColor = (status: string) => {
    switch (status) {
      case 'scheduled': return 'bg-blue-100 text-blue-800';
      case 'playing': return 'bg-green-100 text-green-800';
      case 'completed': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const renderSlotsTab = () => (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold">
            {isHostCompany() ? 'Manage Ad Slots' : 'Available Ad Slots'}
          </h2>
          <p className="text-muted-foreground">
            {isHostCompany()
              ? 'Configure and manage your advertising slots'
              : 'Browse and book advertising slots for your campaigns'
            }
          </p>
        </div>
        {isHostCompany() && (
          <PermissionGate permission={{ resource: "ad_slot", action: "create" }}>
            <Dialog open={showCreateSlot} onOpenChange={setShowCreateSlot}>
              <DialogTrigger asChild>
                <Button className="gap-2">
                  <Plus className="h-4 w-4" />
                  Create Ad Slot
                </Button>
              </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create New Ad Slot</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 max-h-96 overflow-y-auto">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Slot Name</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({...formData, name: e.target.value})}
                      placeholder="e.g., Mall Entrance Display"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="location">Location</Label>
                    <Select value={formData.locationId} onValueChange={(value) => setFormData({...formData, locationId: value})}>
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
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="price">Price per Hour ($)</Label>
                    <Input
                      id="price"
                      type="number"
                      value={formData.pricePerHour}
                      onChange={(e) => setFormData({...formData, pricePerHour: Number(e.target.value)})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="minDuration">Min Duration (min)</Label>
                    <Input
                      id="minDuration"
                      type="number"
                      value={formData.minDuration}
                      onChange={(e) => setFormData({...formData, minDuration: Number(e.target.value)})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="maxDuration">Max Duration (min)</Label>
                    <Input
                      id="maxDuration"
                      type="number"
                      value={formData.maxDuration}
                      onChange={(e) => setFormData({...formData, maxDuration: Number(e.target.value)})}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    placeholder="Describe the ad slot location and audience"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="tags">Tags (comma separated)</Label>
                  <Input
                    id="tags"
                    value={formData.tags}
                    onChange={(e) => setFormData({...formData, tags: e.target.value})}
                    placeholder="high-traffic, premium, entrance"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-4">
                  <Button variant="outline" onClick={() => setShowCreateSlot(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreateSlot}>
                    Create Slot
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
          </PermissionGate>
        )}
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search slots by name, location, or tags..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
                <SelectItem value="maintenance">Maintenance</SelectItem>
              </SelectContent>
            </Select>
            <Select value={locationFilter} onValueChange={setLocationFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Location" />
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
          </div>
        </CardContent>
      </Card>

      {/* Ad Slots Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredSlots.map(slot => (
          <Card key={slot.id} className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-lg">{slot.name}</CardTitle>
                  <div className="flex items-center gap-1 text-sm text-muted-foreground mt-1">
                    <MapPin className="h-3 w-3" />
                    {slot.locationName}
                  </div>
                </div>
                <Badge className={getStatusColor(slot.status)}>
                  {slot.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Device Info */}
              <div className="flex items-center gap-2 text-sm">
                <Monitor className="h-4 w-4 text-muted-foreground" />
                <span>{slot.screenResolution} • {slot.screenSize}"</span>
              </div>

              {/* Pricing */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1">
                  <DollarSign className="h-4 w-4 text-green-600" />
                  <span className="font-semibold text-green-600">${slot.pricePerHour}/hour</span>
                </div>
                <div className="text-sm text-muted-foreground">
                  {slot.minDuration}-{slot.maxDuration} min
                </div>
              </div>

              {/* Current Booking */}
              {slot.currentBooking ? (
                <div className="bg-blue-50 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-sm font-medium">Current Booking</div>
                    <Badge className={getBookingStatusColor(slot.currentBooking.status)}>
                      {slot.currentBooking.status}
                    </Badge>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    <div>{slot.currentBooking.advertiserName}</div>
                    <div className="truncate">{slot.currentBooking.contentTitle}</div>
                  </div>
                </div>
              ) : (
                <div className="bg-green-50 rounded-lg p-3 text-center">
                  <div className="text-sm font-medium text-green-800">Available</div>
                  <div className="text-xs text-green-600">Ready for booking</div>
                </div>
              )}

              {/* Performance Stats */}
              <div className="grid grid-cols-2 gap-4 pt-2 border-t">
                <div className="text-center">
                  <div className="text-lg font-bold">{slot.performance.totalImpressions.toLocaleString()}</div>
                  <div className="text-xs text-muted-foreground">Impressions</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold">{slot.performance.occupancyRate}%</div>
                  <div className="text-xs text-muted-foreground">Occupancy</div>
                </div>
              </div>

              {/* Tags */}
              <div className="flex flex-wrap gap-1">
                {slot.tags.slice(0, 3).map(tag => (
                  <Badge key={tag} variant="secondary" className="text-xs">
                    {tag}
                  </Badge>
                ))}
                {slot.tags.length > 3 && (
                  <Badge variant="secondary" className="text-xs">
                    +{slot.tags.length - 3} more
                  </Badge>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-2 pt-2">
                <PermissionGate permission={{ resource: "ad_slot", action: "view" }}>
                  <Button variant="outline" size="sm" className="flex-1 gap-1">
                    <Eye className="h-3 w-3" />
                    View Details
                  </Button>
                </PermissionGate>
                {isHostCompany() ? (
                  <PermissionGate permission={{ resource: "ad_slot", action: "edit" }}>
                    <Button variant="outline" size="sm" className="gap-1">
                      <Settings className="h-3 w-3" />
                      Manage
                    </Button>
                  </PermissionGate>
                ) : (
                  <PermissionGate permission={{ resource: "booking", action: "create" }}>
                    <Button size="sm" className="gap-1" disabled={!!slot.currentBooking}>
                      <Calendar className="h-3 w-3" />
                      Book
                    </Button>
                  </PermissionGate>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredSlots.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <Monitor className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No ad slots found</h3>
            <p className="text-muted-foreground mb-4">
              {isHostCompany()
                ? 'Create your first ad slot to start monetizing your screens'
                : 'Try adjusting your search filters or check back later for new opportunities'
              }
            </p>
            {isHostCompany() && (
              <PermissionGate permission={{ resource: "ad_slot", action: "create" }}>
                <Button onClick={() => setShowCreateSlot(true)} className="gap-2">
                  <Plus className="h-4 w-4" />
                  Create Ad Slot
                </Button>
              </PermissionGate>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderAnalyticsTab = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Ad Slot Analytics</h2>
        <p className="text-muted-foreground">
          Performance insights and revenue analytics for your ad slots
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$4,500</div>
            <p className="text-xs text-muted-foreground">+12% from last month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Impressions</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">37.5K</div>
            <p className="text-xs text-muted-foreground">+8% from last month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Occupancy</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">82%</div>
            <p className="text-xs text-muted-foreground">+5% from last month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Slots</CardTitle>
            <Monitor className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2</div>
            <p className="text-xs text-muted-foreground">All online</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  return (
    <PermissionGate 
      permission={{ resource: "ad_slot", action: "read" }}
      fallback={
        <div className="container mx-auto py-6">
          <Card>
            <CardContent className="text-center py-12">
              <h3 className="text-lg font-semibold mb-2">Access Denied</h3>
              <p className="text-muted-foreground">
                You don't have permission to access ad slots management.
              </p>
            </CardContent>
          </Card>
        </div>
      }
    >
      <div className="container mx-auto py-6">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="slots">
            {isHostCompany() ? 'Manage Slots' : 'Browse Slots'}
          </TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="slots" className="mt-6">
          {renderSlotsTab()}
        </TabsContent>

        <TabsContent value="analytics" className="mt-6">
          {renderAnalyticsTab()}
        </TabsContent>
      </Tabs>
    </div>
    </PermissionGate>
  );
}