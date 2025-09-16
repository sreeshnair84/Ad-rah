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
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import {
  Plus,
  MapPin,
  Building2,
  Users,
  TrendingUp,
  Eye,
  Edit,
  Settings,
  Search,
  Filter
} from 'lucide-react';

interface Location {
  id: string;
  name: string;
  address: string;
  category: string;
  footTraffic: number;
  deviceCount: number;
  activeDevices: number;
  totalRevenue: number;
  demographics: {
    ageGroups: Record<string, number>;
    interests: string[];
  };
  status: 'active' | 'inactive' | 'maintenance';
  createdAt: Date;
  updatedAt: Date;
}

export default function LocationsPage() {
  const { user, isHostCompany } = useAuth();
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    address: '',
    category: '',
    description: ''
  });

  useEffect(() => {
    fetchLocations();
  }, []);

  const fetchLocations = async () => {
    try {
      setLoading(true);
      // Mock data for demo
      setLocations([
        {
          id: '1',
          name: 'Downtown Mall',
          address: '123 Main St, Downtown',
          category: 'Shopping Center',
          footTraffic: 45000,
          deviceCount: 8,
          activeDevices: 7,
          totalRevenue: 12500,
          demographics: {
            ageGroups: { '18-25': 25, '26-35': 35, '36-45': 20, '46-60': 15, '60+': 5 },
            interests: ['shopping', 'dining', 'entertainment']
          },
          status: 'active',
          createdAt: new Date('2024-01-15'),
          updatedAt: new Date()
        },
        {
          id: '2',
          name: 'Business District Plaza',
          address: '456 Corporate Ave, Business District',
          category: 'Office Complex',
          footTraffic: 28000,
          deviceCount: 5,
          activeDevices: 5,
          totalRevenue: 8200,
          demographics: {
            ageGroups: { '18-25': 15, '26-35': 45, '36-45': 30, '46-60': 8, '60+': 2 },
            interests: ['business', 'dining', 'services']
          },
          status: 'active',
          createdAt: new Date('2024-02-01'),
          updatedAt: new Date()
        }
      ]);
    } catch (error) {
      console.error('Failed to fetch locations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateLocation = async () => {
    try {
      // API call would go here
      console.log('Creating location:', formData);
      setShowCreateDialog(false);
      setFormData({ name: '', address: '', category: '', description: '' });
      await fetchLocations();
    } catch (error) {
      console.error('Failed to create location:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'inactive': return 'bg-gray-100 text-gray-800';
      case 'maintenance': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredLocations = locations.filter(location =>
    location.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    location.address.toLowerCase().includes(searchTerm.toLowerCase()) ||
    location.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <PermissionGate 
      permission={{ resource: "location", action: "read" }}
      fallback={
        <div className="container mx-auto py-6">
          <Card>
            <CardContent className="p-6">
              <div className="text-center text-muted-foreground">
                You don't have permission to view locations.
              </div>
            </CardContent>
          </Card>
        </div>
      }
    >
      <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold">Locations</h2>
          <p className="text-muted-foreground">
            Manage your physical locations and their performance
          </p>
        </div>
        {isHostCompany() && (
          <PermissionGate permission={{ resource: "location", action: "create" }}>
            <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
              <DialogTrigger asChild>
                <Button className="gap-2">
                  <Plus className="h-4 w-4" />
                  Add Location
                </Button>
              </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add New Location</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Location Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    placeholder="e.g., Downtown Mall"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="address">Address</Label>
                  <Input
                    id="address"
                    value={formData.address}
                    onChange={(e) => setFormData({...formData, address: e.target.value})}
                    placeholder="Full address"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="category">Category</Label>
                  <Input
                    id="category"
                    value={formData.category}
                    onChange={(e) => setFormData({...formData, category: e.target.value})}
                    placeholder="e.g., Shopping Center"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-4">
                  <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreateLocation}>
                    Create Location
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
          </PermissionGate>
        )}
      </div>

      {/* Search */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search locations..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Locations</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{locations.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Devices</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {locations.reduce((sum, loc) => sum + loc.deviceCount, 0)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monthly Revenue</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              ${locations.reduce((sum, loc) => sum + loc.totalRevenue, 0).toLocaleString()}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Foot Traffic</CardTitle>
            <Users className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Math.round(locations.reduce((sum, loc) => sum + loc.footTraffic, 0) / Math.max(locations.length, 1)).toLocaleString()}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Locations Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredLocations.map(location => (
          <Card key={location.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-lg">{location.name}</CardTitle>
                  <div className="flex items-center gap-1 text-sm text-muted-foreground mt-1">
                    <MapPin className="h-3 w-3" />
                    {location.address}
                  </div>
                </div>
                <Badge className={getStatusColor(location.status)}>
                  {location.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-sm">
                <div className="font-medium text-blue-600">{location.category}</div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-muted-foreground">Devices</div>
                  <div className="font-medium">
                    {location.activeDevices}/{location.deviceCount} active
                  </div>
                </div>
                <div>
                  <div className="text-muted-foreground">Revenue</div>
                  <div className="font-medium text-green-600">
                    ${location.totalRevenue.toLocaleString()}
                  </div>
                </div>
              </div>

              <div className="text-sm">
                <div className="text-muted-foreground">Monthly Foot Traffic</div>
                <div className="font-medium">{location.footTraffic.toLocaleString()}</div>
              </div>

              <div className="flex gap-2">
                <PermissionGate permission={{ resource: "location", action: "view" }}>
                  <Button variant="outline" size="sm" className="flex-1 gap-1">
                    <Eye className="h-3 w-3" />
                    View Details
                  </Button>
                </PermissionGate>
                {isHostCompany() && (
                  <PermissionGate permission={{ resource: "location", action: "edit" }}>
                    <Button variant="outline" size="sm" className="gap-1">
                      <Edit className="h-3 w-3" />
                      Edit
                    </Button>
                  </PermissionGate>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredLocations.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <Building2 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No locations found</h3>
            <p className="text-muted-foreground mb-4">
              {isHostCompany()
                ? 'Add your first location to start managing ad slots'
                : 'No locations available'}
            </p>
            {isHostCompany() && (
              <PermissionGate permission={{ resource: "location", action: "create" }}>
                <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
                  <Plus className="h-4 w-4" />
                  Add Location
                </Button>
              </PermissionGate>
            )}
          </CardContent>
        </Card>
      )}
    </div>
    </PermissionGate>
  );
}