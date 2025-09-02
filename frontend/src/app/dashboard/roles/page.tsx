'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/hooks/useAuth';
import { Shield, Plus, Edit, Trash2, Users, Settings, AlertCircle, Building2, Key, Save, Search } from 'lucide-react';

interface Role {
  id: string;
  name: string;
  role_group: 'ADMIN' | 'HOST' | 'ADVERTISER';
  company_id: string;
  company_name?: string;
  is_default: boolean;
  status: 'active' | 'inactive';
  user_count?: number;
  permissions?: Permission[];
  created_at: string;
  updated_at: string;
}

interface Permission {
  screen: string;
  permissions: string[];
}

interface Company {
  id: string;
  name: string;
  type: string;
  status: string;
}

const SCREENS = [
  { id: 'dashboard', name: 'Dashboard', icon: '📊' },
  { id: 'users', name: 'User Management', icon: '👥' },
  { id: 'companies', name: 'Company Management', icon: '🏢' },
  { id: 'content', name: 'Content Management', icon: '📱' },
  { id: 'moderation', name: 'Content Moderation', icon: '🔍' },
  { id: 'analytics', name: 'Analytics & Reports', icon: '📈' },
  { id: 'billing', name: 'Billing & Payments', icon: '💳' },
  { id: 'settings', name: 'System Settings', icon: '⚙️' }
];

const PERMISSIONS = [
  { id: 'view', name: 'View', description: 'Can view the screen' },
  { id: 'edit', name: 'Edit', description: 'Can modify content' },
  { id: 'delete', name: 'Delete', description: 'Can delete items' },
  { id: 'access', name: 'Full Access', description: 'Complete control' }
];

const ROLE_GROUPS = [
  { id: 'ADMIN', name: 'Administrator', color: 'destructive', description: 'Full system access' },
  { id: 'HOST', name: 'Host Company', color: 'default', description: 'Venue management' },
  { id: 'ADVERTISER', name: 'Advertiser', color: 'secondary', description: 'Content creation' }
];

export default function RolesManagementPage() {
  const { user } = useAuth();
  const [roles, setRoles] = useState<Role[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredRoles, setFilteredRoles] = useState<Role[]>([]);
  
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showPermissionDialog, setShowPermissionDialog] = useState(false);
  const [newRole, setNewRole] = useState({
    name: '',
    role_group: 'HOST' as 'ADMIN' | 'HOST' | 'ADVERTISER',
    company_id: '',
    is_default: false
  });
  const [rolePermissions, setRolePermissions] = useState<Record<string, string[]>>({});

  // Fetch roles from API
  const fetchRoles = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch('/api/roles', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch roles');
      }

      const data = await response.json();
      setRoles(data);
      setFilteredRoles(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch roles');
    } finally {
      setLoading(false);
    }
  };

  // Fetch companies from API
  const fetchCompanies = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/users/companies/dropdown', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch companies');
      }

      const data = await response.json();
      setCompanies(data);
    } catch (err) {
      console.error('Failed to fetch companies:', err);
    }
  };

  // Filter roles based on search
  useEffect(() => {
    let filtered = roles;

    if (searchTerm) {
      filtered = filtered.filter(role =>
        role.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        role.role_group.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (role.company_name && role.company_name.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    setFilteredRoles(filtered);
  }, [roles, searchTerm]);

  useEffect(() => {
    fetchRoles();
    fetchCompanies();
  }, []);

  // Check if user has admin access to role management
  const canManageRoles = user?.roles?.some(role => role.role === 'ADMIN') || false;

  if (!canManageRoles) {
    return (
      <div className="flex items-center justify-center h-full">
        <Alert className="max-w-md">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            You don&apos;t have permission to access role management. Contact your administrator.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const handleCreateRole = async () => {
    if (!newRole.name || !newRole.company_id) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/roles', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(newRole),
      });

      if (!response.ok) {
        throw new Error('Failed to create role');
      }

      await fetchRoles();
      setNewRole({ name: '', role_group: 'HOST', company_id: '', is_default: false });
      setShowCreateDialog(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create role');
    }
  };

  const handleDeleteRole = async (roleId: string) => {
    if (!confirm('Are you sure you want to delete this role? This action cannot be undone.')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/roles/${roleId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete role');
      }

      await fetchRoles();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete role');
    }
  };

  const handleSavePermissions = async () => {
    if (!selectedRole) return;

    try {
      const permissions: Permission[] = Object.entries(rolePermissions).map(([screen, perms]) => ({
        screen,
        permissions: perms
      }));

      const token = localStorage.getItem('token');
      const response = await fetch(`/api/roles/${selectedRole.id}/permissions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(permissions),
      });

      if (!response.ok) {
        throw new Error('Failed to save permissions');
      }

      await fetchRoles();
      setShowPermissionDialog(false);
      setSelectedRole(null);
      setRolePermissions({});
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save permissions');
    }
  };

  const openPermissionDialog = (role: Role) => {
    setSelectedRole(role);
    const currentPermissions: Record<string, string[]> = {};
    
    if (role.permissions) {
      role.permissions.forEach(perm => {
        currentPermissions[perm.screen] = perm.permissions;
      });
    }
    
    setRolePermissions(currentPermissions);
    setShowPermissionDialog(true);
  };

  const togglePermission = (screen: string, permission: string) => {
    setRolePermissions(prev => {
      const current = prev[screen] || [];
      const updated = current.includes(permission)
        ? current.filter(p => p !== permission)
        : [...current, permission];
      
      return {
        ...prev,
        [screen]: updated
      };
    });
  };

  const getRoleGroupBadge = (group: string) => {
    const roleGroup = ROLE_GROUPS.find(rg => rg.id === group);
    return roleGroup ? (
      <Badge variant={roleGroup.color as any} className="gap-1">
        <Shield className="w-3 h-3" />
        {roleGroup.name}
      </Badge>
    ) : null;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading roles...</span>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Shield className="h-8 w-8 text-blue-600" />
            Role Management
          </h1>
          <p className="text-muted-foreground">
            Manage user roles and permissions across your organization
          </p>
        </div>
        
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Create Role
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Role</DialogTitle>
              <DialogDescription>
                Create a custom role with specific permissions for your organization.
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div>
                <Label htmlFor="role-name">Role Name</Label>
                <Input
                  id="role-name"
                  placeholder="Enter role name"
                  value={newRole.name}
                  onChange={(e) => setNewRole({...newRole, name: e.target.value})}
                />
              </div>
              
              <div>
                <Label htmlFor="role-group">Role Group</Label>
                <Select value={newRole.role_group} onValueChange={(value) => 
                  setNewRole({...newRole, role_group: value as any})
                }>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ROLE_GROUPS.map(group => (
                      <SelectItem key={group.id} value={group.id}>
                        <div className="flex items-center gap-2">
                          <Shield className="w-4 h-4" />
                          <span>{group.name}</span>
                          <span className="text-xs text-muted-foreground">
                            {group.description}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label htmlFor="company">Company</Label>
                <Select value={newRole.company_id} onValueChange={(value) => 
                  setNewRole({...newRole, company_id: value})
                }>
                  <SelectTrigger>
                    <SelectValue placeholder="Select company" />
                  </SelectTrigger>
                  <SelectContent>
                    {companies.map(company => (
                      <SelectItem key={company.id} value={company.id}>
                        <div className="flex items-center gap-2">
                          <Building2 className="w-4 h-4" />
                          <span>{company.name}</span>
                          <Badge variant="outline" className="text-xs">
                            {company.type}
                          </Badge>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is-default"
                  checked={newRole.is_default}
                  onCheckedChange={(checked) => 
                    setNewRole({...newRole, is_default: checked as boolean})
                  }
                />
                <Label htmlFor="is-default">Set as default role for new users</Label>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateRole} disabled={!newRole.name || !newRole.company_id}>
                Create Role
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search by role name, group, or company..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="text-sm text-gray-600">
          {filteredRoles.length} of {roles.length} roles
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Roles</p>
              <p className="text-2xl font-bold text-gray-900">{roles.length}</p>
            </div>
            <Shield className="h-8 w-8 text-blue-600" />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Admin Roles</p>
              <p className="text-2xl font-bold text-red-600">
                {roles.filter(r => r.role_group === 'ADMIN').length}
              </p>
            </div>
            <Shield className="h-8 w-8 text-red-600" />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Host Roles</p>
              <p className="text-2xl font-bold text-blue-600">
                {roles.filter(r => r.role_group === 'HOST').length}
              </p>
            </div>
            <Shield className="h-8 w-8 text-blue-600" />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Advertiser Roles</p>
              <p className="text-2xl font-bold text-purple-600">
                {roles.filter(r => r.role_group === 'ADVERTISER').length}
              </p>
            </div>
            <Shield className="h-8 w-8 text-purple-600" />
          </div>
        </div>
      </div>

      <Tabs defaultValue="roles" className="space-y-4">
        <TabsList>
          <TabsTrigger value="roles" className="flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Roles
          </TabsTrigger>
          <TabsTrigger value="permissions" className="flex items-center gap-2">
            <Key className="w-4 h-4" />
            Permission Templates
          </TabsTrigger>
        </TabsList>

        <TabsContent value="roles">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                System Roles
              </CardTitle>
              <CardDescription>
                Manage roles and their assignments across companies
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Role</TableHead>
                    <TableHead>Company</TableHead>
                    <TableHead>Group</TableHead>
                    <TableHead>Users</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRoles.map((role) => (
                    <TableRow key={role.id}>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium">{role.name}</span>
                          {role.is_default && (
                            <Badge variant="outline" className="w-fit text-xs">
                              Default
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Building2 className="w-4 h-4 text-muted-foreground" />
                          {role.company_name}
                        </div>
                      </TableCell>
                      <TableCell>
                        {getRoleGroupBadge(role.role_group)}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Users className="w-4 h-4 text-muted-foreground" />
                          {role.user_count || 0}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={role.status === 'active' ? 'default' : 'secondary'}>
                          {role.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openPermissionDialog(role)}
                          >
                            <Settings className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {}}
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          {!role.is_default && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteRole(role.id)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              {filteredRoles.length === 0 && (
                <div className="text-center py-12">
                  <Shield className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No roles found</h3>
                  <p className="text-gray-500 mb-6">
                    {searchTerm
                      ? 'Try adjusting your search criteria'
                      : 'Get started by creating your first role'
                    }
                  </p>
                  {!searchTerm && (
                    <Button onClick={() => setShowCreateDialog(true)}>
                      <Plus className="h-4 w-4 mr-2" />
                      Create First Role
                    </Button>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="permissions">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="w-5 h-5" />
                Permission Templates
              </CardTitle>
              <CardDescription>
                Pre-defined permission sets for common role types
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {ROLE_GROUPS.map(group => (
                  <Card key={group.id} className="p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <Shield className="w-4 h-4" />
                      <h3 className="font-semibold">{group.name}</h3>
                    </div>
                    <p className="text-sm text-muted-foreground mb-3">
                      {group.description}
                    </p>
                    <div className="space-y-1">
                      {SCREENS.slice(0, 4).map(screen => (
                        <div key={screen.id} className="flex items-center text-xs">
                          <span className="mr-2">{screen.icon}</span>
                          <span>{screen.name}</span>
                        </div>
                      ))}
                      {SCREENS.length > 4 && (
                        <div className="text-xs text-muted-foreground">
                          +{SCREENS.length - 4} more...
                        </div>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Permission Management Dialog */}
      <Dialog open={showPermissionDialog} onOpenChange={setShowPermissionDialog}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Manage Permissions - {selectedRole?.name}</DialogTitle>
            <DialogDescription>
              Configure screen-level permissions for this role
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="grid gap-4">
              {SCREENS.map(screen => (
                <Card key={screen.id} className="p-4">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-lg">{screen.icon}</span>
                    <div>
                      <h4 className="font-semibold">{screen.name}</h4>
                      <p className="text-sm text-muted-foreground">Screen ID: {screen.id}</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {PERMISSIONS.map(permission => (
                      <div key={permission.id} className="flex items-center space-x-2">
                        <Checkbox
                          id={`${screen.id}-${permission.id}`}
                          checked={(rolePermissions[screen.id] || []).includes(permission.id)}
                          onCheckedChange={() => togglePermission(screen.id, permission.id)}
                        />
                        <Label 
                          htmlFor={`${screen.id}-${permission.id}`}
                          className="text-sm font-normal"
                        >
                          {permission.name}
                        </Label>
                      </div>
                    ))}
                  </div>
                </Card>
              ))}
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPermissionDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSavePermissions}>
              <Save className="w-4 h-4 mr-2" />
              Save Permissions
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}