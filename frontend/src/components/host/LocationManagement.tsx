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
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  MapPin,
  Plus,
  Edit2,
  Trash2,
  Eye,
  Monitor,
  Users,
  Clock,
  Search,
  Filter,
  Download,
  Upload,
  CheckCircle,
  AlertTriangle,
  Info
} from 'lucide-react';

interface Location {
  id: string;
  name: string;
  address: string;
  city: string;
  state: string;
  zipCode: string;
  category: string;
  description: string;
  contactPerson: string;
  contactEmail: string;
  contactPhone: string;
  operatingHours: {
    monday: { open: string; close: string; closed: boolean };
    tuesday: { open: string; close: string; closed: boolean };
    wednesday: { open: string; close: string; closed: boolean };
    thursday: { open: string; close: string; closed: boolean };
    friday: { open: string; close: string; closed: boolean };
    saturday: { open: string; close: string; closed: boolean };
    sunday: { open: string; close: string; closed: boolean };
  };
  footTraffic: number;
  demographics: {
    primaryAgeGroup: string;
    genderDistribution: string;
    incomeLevel: string;
  };
  devices: number;
  activeSlots: number;
  monthlyRevenue: number;
  status: 'active' | 'inactive' | 'pending';
  createdAt: string;
  updatedAt: string;
}

const defaultOperatingHours = {
  monday: { open: '09:00', close: '21:00', closed: false },
  tuesday: { open: '09:00', close: '21:00', closed: false },
  wednesday: { open: '09:00', close: '21:00', closed: false },
  thursday: { open: '09:00', close: '21:00', closed: false },
  friday: { open: '09:00', close: '22:00', closed: false },
  saturday: { open: '10:00', close: '22:00', closed: false },
  sunday: { open: '11:00', close: '20:00', closed: false }
};

export default function LocationManagement() {
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [formData, setFormData] = useState<Partial<Location>>({
    operatingHours: defaultOperatingHours
  });

  useEffect(() => {
    fetchLocations();
  }, []);

  const fetchLocations = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/host/locations', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setLocations(data.locations || []);
      } else {
        // Mock data for development
        setLocations([
          {
            id: '1',
            name: 'Downtown Shopping Mall',
            address: '123 Main Street',
            city: 'New York',
            state: 'NY',
            zipCode: '10001',
            category: 'shopping',
            description: 'High-traffic shopping mall in downtown Manhattan',
            contactPerson: 'John Manager',
            contactEmail: 'john@mall.com',
            contactPhone: '+1-555-0123',
            operatingHours: defaultOperatingHours,
            footTraffic: 50000,
            demographics: {
              primaryAgeGroup: '25-45',
              genderDistribution: '55% Female, 45% Male',
              incomeLevel: 'Upper Middle'
            },
            devices: 8,
            activeSlots: 12,
            monthlyRevenue: 8450.00,
            status: 'active',
            createdAt: '2024-01-15',
            updatedAt: '2024-12-10'
          },
          {
            id: '2',
            name: 'Airport Terminal A',
            address: '100 Airport Blvd',
            city: 'New York',
            state: 'NY',
            zipCode: '11430',
            category: 'transportation',
            description: 'Main terminal of international airport',
            contactPerson: 'Sarah Admin',
            contactEmail: 'sarah@airport.com',
            contactPhone: '+1-555-0456',
            operatingHours: {
              ...defaultOperatingHours,
              monday: { open: '05:00', close: '23:00', closed: false },
              tuesday: { open: '05:00', close: '23:00', closed: false },
              wednesday: { open: '05:00', close: '23:00', closed: false },
              thursday: { open: '05:00', close: '23:00', closed: false },
              friday: { open: '05:00', close: '23:00', closed: false },
              saturday: { open: '05:00', close: '23:00', closed: false },
              sunday: { open: '05:00', close: '23:00', closed: false }
            },
            footTraffic: 75000,
            demographics: {
              primaryAgeGroup: '25-55',
              genderDistribution: '50% Female, 50% Male',
              incomeLevel: 'Mixed'
            },
            devices: 15,
            activeSlots: 24,
            monthlyRevenue: 15600.00,
            status: 'active',
            createdAt: '2024-02-20',
            updatedAt: '2024-12-08'
          },
          {
            id: '3',
            name: 'University Campus Center',
            address: '456 College Ave',
            city: 'Boston',
            state: 'MA',
            zipCode: '02115',
            category: 'education',
            description: 'Student center at major university',
            contactPerson: 'Mike Director',
            contactEmail: 'mike@university.edu',
            contactPhone: '+1-555-0789',
            operatingHours: defaultOperatingHours,
            footTraffic: 25000,
            demographics: {
              primaryAgeGroup: '18-25',
              genderDistribution: '52% Female, 48% Male',
              incomeLevel: 'Student'
            },
            devices: 6,
            activeSlots: 8,
            monthlyRevenue: 3200.00,
            status: 'active',
            createdAt: '2024-03-10',
            updatedAt: '2024-12-05'
          }
        ]);
      }
    } catch (error) {
      console.error('Failed to fetch locations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddLocation = async () => {
    try {
      const response = await fetch('/api/host/locations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        await fetchLocations();
        setIsAddDialogOpen(false);
        setFormData({ operatingHours: defaultOperatingHours });
      } else {
        console.error('Failed to add location');
      }
    } catch (error) {
      console.error('Error adding location:', error);
    }
  };

  const handleEditLocation = async () => {
    if (!selectedLocation) return;

    try {
      const response = await fetch(`/api/host/locations/${selectedLocation.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        await fetchLocations();
        setIsEditDialogOpen(false);
        setSelectedLocation(null);
        setFormData({ operatingHours: defaultOperatingHours });
      } else {
        console.error('Failed to update location');
      }
    } catch (error) {
      console.error('Error updating location:', error);
    }
  };

  const handleDeleteLocation = async (locationId: string) => {
    if (!confirm('Are you sure you want to delete this location?')) return;

    try {
      const response = await fetch(`/api/host/locations/${locationId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        await fetchLocations();
      } else {
        console.error('Failed to delete location');
      }
    } catch (error) {
      console.error('Error deleting location:', error);
    }
  };

  const filteredLocations = locations.filter(location => {
    const matchesSearch = location.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         location.city.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         location.address.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = filterCategory === 'all' || location.category === filterCategory;
    return matchesSearch && matchesCategory;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'inactive':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'shopping':
        return '🛍️';
      case 'transportation':
        return '✈️';
      case 'education':
        return '🎓';
      case 'healthcare':
        return '🏥';
      case 'entertainment':
        return '🎭';
      default:
        return '📍';
    }
  };

  const renderLocationForm = () => (
    <div className="grid gap-6">
      {/* Basic Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Basic Information</h3>
        
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <Label htmlFor="name">Location Name *</Label>
            <Input
              id="name"
              value={formData.name || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="e.g., Downtown Shopping Mall"
            />
          </div>
          
          <div>
            <Label htmlFor="category">Category *</Label>
            <Select 
              value={formData.category || ''} 
              onValueChange={(value) => setFormData(prev => ({ ...prev, category: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="shopping">Shopping Center</SelectItem>
                <SelectItem value="transportation">Transportation Hub</SelectItem>
                <SelectItem value="education">Educational Institution</SelectItem>
                <SelectItem value="healthcare">Healthcare Facility</SelectItem>
                <SelectItem value="entertainment">Entertainment Venue</SelectItem>
                <SelectItem value="office">Office Building</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div>
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            value={formData.description || ''}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            placeholder="Describe the location and its characteristics"
            rows={3}
          />
        </div>
      </div>

      {/* Address Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Address</h3>
        
        <div>
          <Label htmlFor="address">Street Address *</Label>
          <Input
            id="address"
            value={formData.address || ''}
            onChange={(e) => setFormData(prev => ({ ...prev, address: e.target.value }))}
            placeholder="123 Main Street"
          />
        </div>
        
        <div className="grid gap-4 md:grid-cols-3">
          <div>
            <Label htmlFor="city">City *</Label>
            <Input
              id="city"
              value={formData.city || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, city: e.target.value }))}
              placeholder="New York"
            />
          </div>
          
          <div>
            <Label htmlFor="state">State *</Label>
            <Input
              id="state"
              value={formData.state || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, state: e.target.value }))}
              placeholder="NY"
            />
          </div>
          
          <div>
            <Label htmlFor="zipCode">ZIP Code *</Label>
            <Input
              id="zipCode"
              value={formData.zipCode || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, zipCode: e.target.value }))}
              placeholder="10001"
            />
          </div>
        </div>
      </div>

      {/* Contact Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Contact Information</h3>
        
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <Label htmlFor="contactPerson">Contact Person</Label>
            <Input
              id="contactPerson"
              value={formData.contactPerson || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, contactPerson: e.target.value }))}
              placeholder="John Manager"
            />
          </div>
          
          <div>
            <Label htmlFor="contactEmail">Contact Email</Label>
            <Input
              id="contactEmail"
              type="email"
              value={formData.contactEmail || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, contactEmail: e.target.value }))}
              placeholder="john@example.com"
            />
          </div>
        </div>
        
        <div>
          <Label htmlFor="contactPhone">Contact Phone</Label>
          <Input
            id="contactPhone"
            value={formData.contactPhone || ''}
            onChange={(e) => setFormData(prev => ({ ...prev, contactPhone: e.target.value }))}
            placeholder="+1-555-0123"
          />
        </div>
      </div>

      {/* Demographics & Traffic */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Demographics & Traffic</h3>
        
        <div>
          <Label htmlFor="footTraffic">Daily Foot Traffic (approximate)</Label>
          <Input
            id="footTraffic"
            type="number"
            value={formData.footTraffic || ''}
            onChange={(e) => setFormData(prev => ({ ...prev, footTraffic: parseInt(e.target.value) || 0 }))}
            placeholder="10000"
          />
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading locations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Location Management</h2>
          <p className="text-gray-600 mt-1">
            Manage your digital signage locations and their properties
          </p>
        </div>
        
        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              Add Location
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Add New Location</DialogTitle>
            </DialogHeader>
            {renderLocationForm()}
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleAddLocation}>
                Add Location
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters and Search */}
      <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search locations..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        
        <Select value={filterCategory} onValueChange={setFilterCategory}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="All Categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            <SelectItem value="shopping">Shopping Centers</SelectItem>
            <SelectItem value="transportation">Transportation</SelectItem>
            <SelectItem value="education">Education</SelectItem>
            <SelectItem value="healthcare">Healthcare</SelectItem>
            <SelectItem value="entertainment">Entertainment</SelectItem>
            <SelectItem value="office">Office Buildings</SelectItem>
          </SelectContent>
        </Select>
        
        <Button variant="outline" size="sm" className="gap-2">
          <Download className="h-4 w-4" />
          Export
        </Button>
      </div>

      {/* Locations Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredLocations.map((location) => (
          <Card key={location.id} className="border-0 shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{getCategoryIcon(location.category)}</span>
                  <div>
                    <CardTitle className="text-lg">{location.name}</CardTitle>
                    <p className="text-sm text-gray-600">{location.city}, {location.state}</p>
                  </div>
                </div>
                <Badge className={getStatusColor(location.status)}>
                  {location.status}
                </Badge>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-4">
              <div className="text-sm text-gray-600">
                <p className="flex items-center gap-1">
                  <MapPin className="h-3 w-3" />
                  {location.address}
                </p>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Devices</p>
                  <p className="font-semibold flex items-center gap-1">
                    <Monitor className="h-3 w-3" />
                    {location.devices}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Active Slots</p>
                  <p className="font-semibold">{location.activeSlots}</p>
                </div>
                <div>
                  <p className="text-gray-500">Monthly Revenue</p>
                  <p className="font-semibold text-green-600">
                    ${location.monthlyRevenue.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Daily Traffic</p>
                  <p className="font-semibold flex items-center gap-1">
                    <Users className="h-3 w-3" />
                    {location.footTraffic.toLocaleString()}
                  </p>
                </div>
              </div>
              
              <div className="flex justify-between pt-2 border-t border-gray-100">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSelectedLocation(location);
                    setFormData(location);
                    setIsEditDialogOpen(true);
                  }}
                  className="gap-1"
                >
                  <Edit2 className="h-3 w-3" />
                  Edit
                </Button>
                
                <div className="flex gap-1">
                  <Button variant="outline" size="sm" className="gap-1">
                    <Eye className="h-3 w-3" />
                    View
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDeleteLocation(location.id)}
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

      {filteredLocations.length === 0 && (
        <Card className="border-0 shadow-lg">
          <CardContent className="text-center py-12">
            <MapPin className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No locations found</h3>
            <p className="text-gray-600 mb-4">
              {searchTerm || filterCategory !== 'all' 
                ? 'Try adjusting your search or filter criteria.'
                : 'Get started by adding your first location.'}
            </p>
            {!searchTerm && filterCategory === 'all' && (
              <Button onClick={() => setIsAddDialogOpen(true)} className="gap-2">
                <Plus className="h-4 w-4" />
                Add Your First Location
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Edit Location Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Location</DialogTitle>
          </DialogHeader>
          {renderLocationForm()}
          <div className="flex justify-end gap-3 pt-4">
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleEditLocation}>
              Save Changes
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}