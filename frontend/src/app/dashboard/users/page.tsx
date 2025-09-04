'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/hooks/useAuth';
import { PermissionGate } from '@/components/PermissionGate';
import {
  UserPlus,
  Edit2,
  Trash2,
  Users,
  Building2,
  Shield,
  Mail,
  Phone,
  AlertCircle,
  CheckCircle2,
  Clock,
  Search,
  Filter
} from 'lucide-react';

interface User {
  id: string;
  name: string;
  email: string;
  phone?: string;
  status: string;
  roles: UserRole[];
  companies: Company[];
  active_company?: string;
  active_role?: string;
  email_verified: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
}

interface UserRole {
  id: string;
  user_id: string;
  company_id: string;
  role_id: string;
  role: string;
  role_name: string;
  company_name: string;
  is_default: boolean;
  status: string;
  created_at: string;
  updated_at: string;
}

interface Company {
  id: string;
  name: string;
  type: string;
  status: string;
}

interface Role {
  id: string;
  name: string;
  role_group: string;
  company_id: string;
  company_name: string;
  is_default: boolean;
}

interface UserFormData {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  password: string;
  user_type: string;
  company_id: string;
  company_role: string;
}

export default function UsersPage() {
  const { user, isSuperUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  const [formData, setFormData] = useState<UserFormData>({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    password: '',
    user_type: 'COMPANY_USER',
    company_id: '',
    company_role: 'VIEWER'
  });

  // Fetch users from API
  const fetchUsers = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch('/api/auth/users', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch users');
      }

      const data = await response.json();
      // Transform the RBAC user data to match the expected format
      const transformedUsers = data.map((user: any) => ({
        id: user.id,
        name: user.display_name || `${user.first_name} ${user.last_name}`.trim(),
        email: user.email,
        phone: user.phone || '',
        status: user.is_active ? 'active' : 'inactive',
        roles: [{
          id: user.company_role || 'USER',
          user_id: user.id,
          company_id: user.company_id || 'global',
          role_id: user.company_role || 'USER',
          role: user.company_role || 'USER',
          role_name: user.role_display || user.company_role || 'User',
          company_name: user.company?.name || 'Platform',
          is_default: true,
          status: 'active',
          created_at: user.created_at,
          updated_at: user.updated_at
        }],
        companies: user.company ? [{
          id: user.company.id,
          name: user.company.name,
          type: user.company.company_type,
          status: user.company.status
        }] : [],
        active_company: user.company_id,
        active_role: user.company_role,
        email_verified: user.email_verified,
        last_login: user.last_login,
        created_at: user.created_at,
        updated_at: user.updated_at
      }));
      setUsers(transformedUsers);
      setFilteredUsers(transformedUsers);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  // Fetch roles for dropdown - using hardcoded RBAC roles
  const fetchRoles = async () => {
    try {
      // For now, use the hardcoded RBAC roles from the system
      const roleData = [
        { id: 'ADMIN', name: 'Administrator', role_group: 'ADMIN', company_id: 'global', company_name: 'Global', is_default: false },
        { id: 'REVIEWER', name: 'Reviewer', role_group: 'REVIEWER', company_id: 'global', company_name: 'Global', is_default: false },
        { id: 'EDITOR', name: 'Editor', role_group: 'EDITOR', company_id: 'global', company_name: 'Global', is_default: false },
        { id: 'VIEWER', name: 'Viewer', role_group: 'VIEWER', company_id: 'global', company_name: 'Global', is_default: false }
      ];
      setRoles(roleData);
    } catch (err) {
      console.error('Failed to fetch roles:', err);
    }
  };

  // Fetch companies for dropdown
  const fetchCompanies = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/auth/companies', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch companies');
      }

      const data = await response.json();
      // Transform the data to match expected format
      const transformedData = data.map((company: any) => ({
        id: company.id,
        name: company.name,
        type: company.company_type,
        status: company.status
      }));
      setCompanies(transformedData);
    } catch (err) {
      console.error('Failed to fetch companies:', err);
    }
  };

  // Filter users based on search and filters
  useEffect(() => {
    let filtered = users;

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(user =>
        user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.roles.some(role => 
          role.role_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          role.company_name.toLowerCase().includes(searchTerm.toLowerCase())
        )
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(user => user.status === statusFilter);
    }

    // Apply role filter
    if (roleFilter !== 'all') {
      filtered = filtered.filter(user => 
        user.roles.some(role => role.role === roleFilter)
      );
    }

    setFilteredUsers(filtered);
  }, [users, searchTerm, statusFilter, roleFilter]);

  useEffect(() => {
    fetchUsers();
    fetchRoles();
    fetchCompanies();
  }, []);

  // Create new user
  const handleCreateUser = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/auth/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create user');
      }

      await fetchUsers();
      setIsCreateDialogOpen(false);
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create user');
    }
  };

  // Update user
  const handleEditUser = async () => {
    if (!selectedUser) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/users/${selectedUser.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('Failed to update user');
      }

      await fetchUsers();
      setIsEditDialogOpen(false);
      setSelectedUser(null);
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update user');
    }
  };

  // Delete user
  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Are you sure you want to delete this user?')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete user');
      }

      await fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete user');
    }
  };

  const resetForm = () => {
    setFormData({
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      password: '',
      user_type: 'COMPANY_USER',
      company_id: user?.company_id || '',
      company_role: 'VIEWER'
    });
  };

  const openEditDialog = (user: User) => {
    setSelectedUser(user);
    const nameParts = user.name.split(' ');
    setFormData({
      first_name: nameParts[0] || '',
      last_name: nameParts.slice(1).join(' ') || '',
      email: user.email,
      phone: user.phone || '',
      password: '',
      user_type: 'COMPANY_USER',
      company_id: user.active_company || '',
      company_role: user.active_role || user.roles[0]?.role || 'VIEWER'
    });
    setIsEditDialogOpen(true);
  };


  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'inactive':
        return <Clock className="h-4 w-4 text-gray-600" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-700 bg-green-50 border-green-200';
      case 'inactive':
        return 'text-gray-700 bg-gray-50 border-gray-200';
      default:
        return 'text-gray-700 bg-gray-50 border-gray-200';
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'ADMIN':
        return 'text-red-700 bg-red-50 border-red-200';
      case 'HOST':
        return 'text-blue-700 bg-blue-50 border-blue-200';
      case 'ADVERTISER':
        return 'text-purple-700 bg-purple-50 border-purple-200';
      default:
        return 'text-gray-700 bg-gray-50 border-gray-200';
    }
  };

  // Legacy permission check (keeping for backwards compatibility)
  const canEditUsers = isSuperUser() || user?.company_role === 'ADMIN' || false;

  // Check if user has permission to access user management
  if (!user || (user.user_type !== 'SUPER_USER' && user.company_role !== 'ADMIN')) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-6xl mb-4">🔒</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Access Restricted</h3>
          <p className="text-gray-600">Only administrators can manage users.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading users...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <Users className="h-8 w-8 text-blue-600" />
            User Management
          </h1>
          <p className="text-gray-600 mt-1">
            Manage system users, roles, and permissions
          </p>
        </div>
        <PermissionGate permission={{ resource: "users", action: "create" }}>
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700">
                <UserPlus className="h-4 w-4 mr-2" />
                Add User
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create New User</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="first_name">First Name *</Label>
                    <Input
                      id="first_name"
                      value={formData.first_name}
                      onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                      placeholder="John"
                    />
                  </div>
                  <div>
                    <Label htmlFor="last_name">Last Name *</Label>
                    <Input
                      id="last_name"
                      value={formData.last_name}
                      onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                      placeholder="Doe"
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="john@company.com"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="phone">Phone</Label>
                    <Input
                      id="phone"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      placeholder="+1-555-0123"
                    />
                  </div>
                  <div>
                    <Label htmlFor="password">Password *</Label>
                    <Input
                      id="password"
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      placeholder="Enter password"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="company_id">Company *</Label>
                    <select
                      id="company_id"
                      className="w-full p-2 border border-gray-300 rounded-md"
                      value={formData.company_id}
                      onChange={(e) => setFormData({ ...formData, company_id: e.target.value })}
                    >
                      <option value="">Select Company</option>
                      {companies
                        .filter(company => {
                          // Super admin can select any company
                          if (user?.user_type === 'SUPER_USER') return true;
                          // Company admin can only select their own company
                          return company.id === user?.company_id;
                        })
                        .map(company => (
                        <option key={company.id} value={company.id}>
                          {company.name} ({company.type})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label htmlFor="company_role">Role *</Label>
                    <select
                      id="company_role"
                      className="w-full p-2 border border-gray-300 rounded-md"
                      value={formData.company_role}
                      onChange={(e) => setFormData({ ...formData, company_role: e.target.value })}
                    >
                      <option value="VIEWER">Viewer</option>
                      <option value="EDITOR">Editor</option>
                      <option value="REVIEWER">Reviewer</option>
                      <option value="ADMIN">Administrator</option>
                    </select>
                  </div>
                </div>


                <div className="flex justify-end space-x-2 pt-4">
                  <Button variant="outline" onClick={() => {
                    setIsCreateDialogOpen(false);
                    resetForm();
                  }}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreateUser} disabled={!formData.first_name || !formData.last_name || !formData.email || !formData.password || !formData.company_id}>
                    Create User
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </PermissionGate>
      </div>

      {/* Edit User Dialog */}
      <PermissionGate permission={{ resource: "users", action: "edit" }}>
        <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Edit User</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="edit-first-name">First Name *</Label>
                  <Input
                    id="edit-first-name"
                    value={formData.first_name}
                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                    placeholder="John"
                  />
                </div>
                <div>
                  <Label htmlFor="edit-last-name">Last Name *</Label>
                  <Input
                    id="edit-last-name"
                    value={formData.last_name}
                    onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                    placeholder="Doe"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="edit-phone">Phone</Label>
                  <Input
                    id="edit-phone"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    placeholder="+1-555-0123"
                  />
                </div>
                <div>
                  <Label htmlFor="edit-email">Email *</Label>
                  <Input
                    id="edit-email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="john@company.com"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="edit-company-role">Company Role</Label>
                <select
                  id="edit-company-role"
                  className="w-full p-2 border border-gray-300 rounded-md"
                  value={formData.company_role}
                  onChange={(e) => setFormData({ ...formData, company_role: e.target.value })}
                >
                  <option value="">Select Role</option>
                  <option value="ADMIN">Administrator - Full company access</option>
                  <option value="REVIEWER">Reviewer - Content approval and user management</option>
                  <option value="EDITOR">Editor - Content creation and editing</option>
                  <option value="VIEWER">Viewer - Read access with upload capability</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Role determines what permissions and navigation items this user can access
                </p>
              </div>

              {/* Show company for super users (read-only) */}
              {user?.user_type === 'SUPER_USER' && selectedUser && (
                <div>
                  <Label htmlFor="edit-company">Company (Read-only)</Label>
                  <Input
                    id="edit-company"
                    value={selectedUser.companies.length > 0 ? selectedUser.companies[0].name : 'No company assigned'}
                    readOnly
                    className="bg-gray-50 cursor-not-allowed"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Company assignment cannot be changed for existing users
                  </p>
                </div>
              )}

              <div className="flex justify-end space-x-2 pt-4">
                <Button variant="outline" onClick={() => {
                  setIsEditDialogOpen(false);
                  setSelectedUser(null);
                  resetForm();
                }}>
                  Cancel
                </Button>
                <Button onClick={handleEditUser} disabled={!formData.first_name || !formData.last_name || !formData.email || !formData.company_role}>
                  Update User
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </PermissionGate>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Search and Filters */}
      <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search by name, email, role, or company..."
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
            <option value="inactive">Inactive</option>
          </select>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="p-2 border border-gray-300 rounded-md bg-white"
          >
            <option value="all">All Roles</option>
            <option value="ADMIN">Admin</option>
            <option value="HOST">Host</option>
            <option value="ADVERTISER">Advertiser</option>
          </select>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Users</p>
              <p className="text-2xl font-bold text-gray-900">{users.length}</p>
            </div>
            <Users className="h-8 w-8 text-blue-600" />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active</p>
              <p className="text-2xl font-bold text-green-600">
                {users.filter(u => u.status === 'active').length}
              </p>
            </div>
            <CheckCircle2 className="h-8 w-8 text-green-600" />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Admins</p>
              <p className="text-2xl font-bold text-red-600">
                {users.filter(u => u.roles.some(r => r.role === 'ADMIN')).length}
              </p>
            </div>
            <Shield className="h-8 w-8 text-red-600" />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Companies</p>
              <p className="text-2xl font-bold text-purple-600">{companies.length}</p>
            </div>
            <Building2 className="h-8 w-8 text-purple-600" />
          </div>
        </div>
      </div>

      {/* Users Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredUsers.map((user) => (
          <div key={user.id} className="bg-white rounded-lg border border-gray-200 hover:shadow-lg transition-shadow">
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white font-semibold">
                    {user.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{user.name}</h3>
                    <p className="text-sm text-gray-500 flex items-center gap-1">
                      <Mail className="h-3 w-3" />
                      {user.email}
                    </p>
                    {user.phone && (
                      <p className="text-sm text-gray-500 flex items-center gap-1">
                        <Phone className="h-3 w-3" />
                        {user.phone}
                      </p>
                    )}
                  </div>
                </div>
                <div className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(user.status)}`}>
                  <div className="flex items-center space-x-1">
                    {getStatusIcon(user.status)}
                    <span className="capitalize">{user.status}</span>
                  </div>
                </div>
              </div>

              {/* User Roles */}
              <div className="space-y-2 mb-4">
                <Label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Roles</Label>
                <div className="flex flex-wrap gap-2">
                  {user.roles.map((role) => (
                    <Badge
                      key={role.id}
                      className={`text-xs px-2 py-1 border ${getRoleColor(role.role)}`}
                    >
                      {role.is_default && <Shield className="h-3 w-3 mr-1" />}
                      {role.role_name}
                      <span className="ml-1 opacity-75">@ {role.company_name}</span>
                    </Badge>
                  ))}
                </div>
              </div>

              {/* User Info */}
              <div className="space-y-1 text-xs text-gray-600 mb-4">
                <div className="flex items-center justify-between">
                  <span>Email Verified:</span>
                  <span className={user.email_verified ? 'text-green-600' : 'text-red-600'}>
                    {user.email_verified ? 'Yes' : 'No'}
                  </span>
                </div>
                {user.last_login && (
                  <div className="flex items-center justify-between">
                    <span>Last Login:</span>
                    <span>{new Date(user.last_login).toLocaleDateString()}</span>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <span>Created:</span>
                  <span>{new Date(user.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="flex space-x-2 pt-4 border-t border-gray-100">
                <PermissionGate permission={{ resource: "users", action: "edit" }}>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openEditDialog(user)}
                    className="flex-1"
                  >
                    <Edit2 className="h-3 w-3 mr-1" />
                    Edit
                  </Button>
                </PermissionGate>
                <PermissionGate permission={{ resource: "users", action: "delete" }}>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDeleteUser(user.id)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="h-3 w-3 mr-1" />
                    Delete
                  </Button>
                </PermissionGate>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredUsers.length === 0 && (
        <div className="text-center py-12">
          <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No users found</h3>
          <p className="text-gray-500 mb-6">
            {searchTerm || statusFilter !== 'all' || roleFilter !== 'all'
              ? 'Try adjusting your search or filter criteria'
              : 'Get started by creating your first user'
            }
          </p>
          <PermissionGate permission={{ resource: "users", action: "create" }}>
            {!searchTerm && statusFilter === 'all' && roleFilter === 'all' && (
              <Button onClick={() => setIsCreateDialogOpen(true)}>
                <UserPlus className="h-4 w-4 mr-2" />
                Add First User
              </Button>
            )}
          </PermissionGate>
        </div>
      )}
    </div>
  );
}
