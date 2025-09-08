'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Company } from '@/types';
import { Building2, MapPin, Phone, Mail, Globe, Plus, Edit, Trash2, Save, X } from 'lucide-react';
import { useCompanies } from '@/hooks/useCompanies';

export default function MasterDataPage() {
  const { companies, loading, error, addCompany, updateCompany, deleteCompany } = useCompanies();
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingCompany, setEditingCompany] = useState<Company | null>(null);
  const [newCompany, setNewCompany] = useState({
    name: '',
    type: 'HOST' as 'HOST' | 'ADVERTISER',
    address: '',
    city: '',
    country: 'UAE',
    phone: '',
    email: '',
    website: '',
    status: 'active' as 'active' | 'inactive'
  });

  const handleAddCompany = async () => {
    if (newCompany.name && newCompany.address && newCompany.city) {
      try {
        await addCompany(newCompany);
        setNewCompany({
          name: '',
          type: 'HOST',
          address: '',
          city: '',
          country: 'UAE',
          phone: '',
          email: '',
          website: '',
          status: 'active'
        });
        setShowAddForm(false);
        alert('Company added successfully!');
      } catch (error) {
        alert('Failed to add company: ' + (error instanceof Error ? error.message : 'Unknown error'));
      }
    }
  };

  const handleEditCompany = (company: Company) => {
    setEditingCompany(company);
    setNewCompany({
      name: company.name,
      type: company.type,
      address: company.address,
      city: company.city,
      country: company.country,
      phone: company.phone || '',
      email: company.email || '',
      website: company.website || '',
      status: company.status
    });
    setShowAddForm(true);
  };

  const handleUpdateCompany = async () => {
    if (!editingCompany) return;

    try {
      await updateCompany(editingCompany.id, newCompany);
      setEditingCompany(null);
      setNewCompany({
        name: '',
        type: 'HOST',
        address: '',
        city: '',
        country: 'UAE',
        phone: '',
        email: '',
        website: '',
        status: 'active'
      });
      setShowAddForm(false);
      alert('Company updated successfully!');
    } catch (error) {
      alert('Failed to update company: ' + (error instanceof Error ? error.message : 'Unknown error'));
    }
  };

  const handleCancelForm = () => {
    setEditingCompany(null);
    setNewCompany({
      name: '',
      type: 'HOST',
      address: '',
      city: '',
      country: 'UAE',
      phone: '',
      email: '',
      website: '',
      status: 'active'
    });
    setShowAddForm(false);
  };

  const handleDeleteCompany = async (companyId: string) => {
    if (confirm('Are you sure you want to delete this company?')) {
      try {
        await deleteCompany(companyId);
        alert('Company deleted successfully!');
      } catch (error) {
        alert('Failed to delete company: ' + (error instanceof Error ? error.message : 'Unknown error'));
      }
    }
  };

  const getCompanyTypeBadge = (type: string) => {
    return type === 'HOST' ? 'default' : 'secondary';
  };

  const getStatusBadge = (status: string) => {
    return status === 'active' ? 'default' : 'destructive';
  };

  if (loading) return <div className="flex justify-center items-center h-64">Loading...</div>;
  if (error) return <div className="text-red-500 text-center">Error: {error}</div>;

  return (
    <div className="grid gap-3 p-3 lg:grid-cols-4">
      <Card className="lg:col-span-3">
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>Master Data Management</CardTitle>
              <CardDescription>
                Manage companies and organizations in the system
              </CardDescription>
            </div>
            <Button onClick={() => {
              setEditingCompany(null);
              setNewCompany({
                name: '',
                type: 'HOST',
                address: '',
                city: '',
                country: 'UAE',
                phone: '',
                email: '',
                website: '',
                status: 'active'
              });
              setShowAddForm(true);
            }}>
              <Plus className="mr-2 h-4 w-4" />
              Add Company
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {showAddForm && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="text-lg">
                  {editingCompany ? 'Edit Company' : 'Add New Company'}
                </CardTitle>
                <CardDescription>
                  {editingCompany ? 'Update company information' : 'Create a new company in the system'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="name">Company Name</Label>
                      <Input
                        id="name"
                        value={newCompany.name}
                        onChange={(e) => setNewCompany({ ...newCompany, name: e.target.value })}
                        placeholder="Enter company name"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="type">Type</Label>
                      <Select value={newCompany.type} onValueChange={(value: 'HOST' | 'ADVERTISER') =>
                        setNewCompany({ ...newCompany, type: value })
                      } name="type">
                        <SelectTrigger id="type">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="HOST">Host Company</SelectItem>
                          <SelectItem value="ADVERTISER">Advertiser Company</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="address">Address</Label>
                    <Input
                      id="address"
                      value={newCompany.address}
                      onChange={(e) => setNewCompany({ ...newCompany, address: e.target.value })}
                      placeholder="Street address"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="city">City</Label>
                      <Input
                        id="city"
                        value={newCompany.city}
                        onChange={(e) => setNewCompany({ ...newCompany, city: e.target.value })}
                        placeholder="City"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="country">Country</Label>
                      <Input
                        id="country"
                        value={newCompany.country}
                        onChange={(e) => setNewCompany({ ...newCompany, country: e.target.value })}
                        placeholder="Country"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="phone">Phone</Label>
                      <Input
                        id="phone"
                        value={newCompany.phone}
                        onChange={(e) => setNewCompany({ ...newCompany, phone: e.target.value })}
                        placeholder="+971-XX-XXXXXXX"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Email</Label>
                      <Input
                        id="email"
                        type="email"
                        value={newCompany.email}
                        onChange={(e) => setNewCompany({ ...newCompany, email: e.target.value })}
                        placeholder="contact@company.com"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="website">Website</Label>
                    <Input
                      id="website"
                      value={newCompany.website}
                      onChange={(e) => setNewCompany({ ...newCompany, website: e.target.value })}
                      placeholder="https://www.company.com"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="status">Status</Label>
                    <Select value={newCompany.status} onValueChange={(value: 'active' | 'inactive') =>
                      setNewCompany({ ...newCompany, status: value })
                    } name="status">
                      <SelectTrigger id="status">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="active">Active</SelectItem>
                        <SelectItem value="inactive">Inactive</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex gap-2 pt-4">
                    <Button variant="outline" onClick={handleCancelForm}>
                      <X className="mr-2 h-4 w-4" />
                      Cancel
                    </Button>
                    <Button onClick={editingCompany ? handleUpdateCompany : handleAddCompany}>
                      <Save className="mr-2 h-4 w-4" />
                      {editingCompany ? 'Update Company' : 'Add Company'}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Company</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {companies.map((company) => (
                <TableRow key={company.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Building2 className="h-4 w-4" />
                      <div>
                        <p className="font-medium">{company.name}</p>
                        {company.website && (
                          <p className="text-xs text-muted-foreground flex items-center gap-1">
                            <Globe className="h-3 w-3" />
                            {company.website}
                          </p>
                        )}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={getCompanyTypeBadge(company.type)}>
                      {company.type}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1 text-sm">
                      <MapPin className="h-3 w-3" />
                      {company.address}, {company.city}, {company.country}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      {company.phone && (
                        <div className="flex items-center gap-1 text-xs">
                          <Phone className="h-3 w-3" />
                          {company.phone}
                        </div>
                      )}
                      {company.email && (
                        <div className="flex items-center gap-1 text-xs">
                          <Mail className="h-3 w-3" />
                          {company.email}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={getStatusBadge(company.status)}>
                      {company.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEditCompany(company)}
                      >
                        <Edit className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeleteCompany(company.id)}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-xl border p-3">
            <p className="text-sm font-medium">Total Companies</p>
            <p className="text-2xl font-bold">{companies.length}</p>
          </div>
          <div className="rounded-xl border p-3">
            <p className="text-sm font-medium">Host Companies</p>
            <p className="text-2xl font-bold">
              {companies.filter(c => c.type === 'HOST').length}
            </p>
          </div>
          <div className="rounded-xl border p-3">
            <p className="text-sm font-medium">Advertiser Companies</p>
            <p className="text-2xl font-bold">
              {companies.filter(c => c.type === 'ADVERTISER').length}
            </p>
          </div>
          <div className="rounded-xl border p-3">
            <p className="text-sm font-medium">Active Companies</p>
            <p className="text-2xl font-bold">
              {companies.filter(c => c.status === 'active').length}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
