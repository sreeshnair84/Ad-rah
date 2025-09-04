'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAuth } from '@/hooks/useAuth';
import { PermissionGate } from '@/components/PermissionGate';
import {
  Building2,
  Plus,
  Search,
  Filter,
  Users,
  Monitor,
  Eye,
  Edit,
  Trash2,
  ExternalLink,
  Key,
  Activity
} from 'lucide-react';

interface Company {
  id: string;
  name: string;
  company_type: 'HOST' | 'ADVERTISER';
  organization_code: string;
  registration_key: string;
  status: string;
  address?: string;
  city?: string;
  country?: string;
  phone?: string;
  email?: string;
  website?: string;
  created_at: string;
  updated_at: string;
}

interface CompanyCreate {
  name: string;
  company_type: 'HOST' | 'ADVERTISER';
  address: string;
  city: string;
  country: string;
  phone: string;
  email: string;
  website: string;
}

export default function CompaniesPage() {
  const { user, hasPermission } = useAuth();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState<CompanyCreate>({
    name: '',
    company_type: 'HOST',
    address: '',
    city: '',
    country: 'UAE',
    phone: '',
    email: '',
    website: ''
  });

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/auth/companies', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch companies');
      }

      const data = await response.json();
      setCompanies(data.companies || data || []);
    } catch (error) {
      console.error('Error fetching companies:', error);
      setCompanies([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCompany = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/auth/companies', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('Failed to create company');
      }

      await fetchCompanies();
      setShowCreateForm(false);
      setFormData({
        name: '',
        company_type: 'HOST',
        address: '',
        city: '',
        country: 'UAE',
        phone: '',
        email: '',
        website: ''
      });
    } catch (error) {
      console.error('Error creating company:', error);
      alert('Failed to create company. Please try again.');
    }
  };

  const filteredCompanies = companies.filter(company => {
    const matchesSearch = company.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         company.organization_code.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = typeFilter === 'all' || company.company_type === typeFilter;
    return matchesSearch && matchesType;
  });

  const getCompanyTypeColor = (type: string) => {
    switch (type) {
      case 'HOST': return 'bg-green-100 text-green-800';
      case 'ADVERTISER': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'inactive': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Building2 className="h-8 w-8 text-blue-600" />
            Company Management
          </h1>
          <p className="text-gray-600 mt-1">
            Manage companies and their configurations
          </p>
        </div>
        
        <PermissionGate permission={{ resource: "company", action: "create" }}>
          <Button onClick={() => setShowCreateForm(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add Company
          </Button>
        </PermissionGate>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600">Total Companies</p>
                <p className="text-2xl font-bold text-blue-900">{companies.length}</p>
              </div>
              <Building2 className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600">HOST Companies</p>
                <p className="text-2xl font-bold text-green-900">
                  {companies.filter(c => c.company_type === 'HOST').length}
                </p>
              </div>
              <Monitor className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-600">ADVERTISER Companies</p>
                <p className="text-2xl font-bold text-orange-900">
                  {companies.filter(c => c.company_type === 'ADVERTISER').length}
                </p>
              </div>
              <Users className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-600">Active Companies</p>
                <p className="text-2xl font-bold text-purple-900">
                  {companies.filter(c => c.status === 'active').length}
                </p>
              </div>
              <Activity className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search companies..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-48">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="HOST">HOST Companies</SelectItem>
            <SelectItem value="ADVERTISER">ADVERTISER Companies</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Create Company Form */}
      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create New Company</CardTitle>
            <CardDescription>Add a new company to the platform</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateCompany} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Company Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="company_type">Company Type *</Label>
                  <Select 
                    value={formData.company_type} 
                    onValueChange={(value: 'HOST' | 'ADVERTISER') => 
                      setFormData({...formData, company_type: value})
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="HOST">HOST - Physical Screen Owner</SelectItem>
                      <SelectItem value="ADVERTISER">ADVERTISER - Content Creator</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone</Label>
                  <Input
                    id="phone"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="city">City</Label>
                  <Input
                    id="city"
                    value={formData.city}
                    onChange={(e) => setFormData({...formData, city: e.target.value})}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="country">Country</Label>
                  <Input
                    id="country"
                    value={formData.country}
                    onChange={(e) => setFormData({...formData, country: e.target.value})}
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="address">Address</Label>
                <Input
                  id="address"
                  value={formData.address}
                  onChange={(e) => setFormData({...formData, address: e.target.value})}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="website">Website</Label>
                <Input
                  id="website"
                  type="url"
                  value={formData.website}
                  onChange={(e) => setFormData({...formData, website: e.target.value})}
                />
              </div>
              
              <div className="flex gap-2 pt-4">
                <Button type="submit">Create Company</Button>
                <Button type="button" variant="outline" onClick={() => setShowCreateForm(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Companies List */}
      <Card>
        <CardHeader>
          <CardTitle>Companies ({filteredCompanies.length})</CardTitle>
          <CardDescription>
            Manage existing companies and their settings
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-muted-foreground">Loading companies...</div>
            </div>
          ) : filteredCompanies.length === 0 ? (
            <div className="text-center py-8">
              <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Companies Found</h3>
              <p className="text-gray-600">
                {searchTerm || typeFilter !== 'all' 
                  ? 'Try adjusting your search or filters.'
                  : 'Get started by creating your first company.'}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredCompanies.map((company) => (
                <div key={company.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">{company.name}</h3>
                        <Badge className={getCompanyTypeColor(company.company_type)}>
                          {company.company_type}
                        </Badge>
                        <Badge className={getStatusColor(company.status)}>
                          {company.status}
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
                        <div className="flex items-center gap-2">
                          <Key className="h-4 w-4" />
                          <span>Code: {company.organization_code}</span>
                        </div>
                        {company.city && (
                          <div className="flex items-center gap-2">
                            <Building2 className="h-4 w-4" />
                            <span>{company.city}, {company.country}</span>
                          </div>
                        )}
                        {company.email && (
                          <div className="flex items-center gap-2">
                            <ExternalLink className="h-4 w-4" />
                            <span>{company.email}</span>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <PermissionGate permission={{ resource: "company", action: "update" }}>
                        <Button variant="outline" size="sm">
                          <Eye className="h-4 w-4 mr-2" />
                          View
                        </Button>
                        <Button variant="outline" size="sm">
                          <Edit className="h-4 w-4 mr-2" />
                          Edit
                        </Button>
                      </PermissionGate>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}