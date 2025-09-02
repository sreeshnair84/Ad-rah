// Enhanced Role Management Component
// Clean page-level permissions interface replacing dropdown complexity

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Users, Shield, Settings, Eye, Edit, Trash2, Check, Plus, Building } from 'lucide-react';

// Types for the enhanced RBAC system
export interface PagePermission {
  page: string;
  permissions: string[];
}

export interface RoleTemplate {
  role: string;
  name: string;
  description: string;
  userType: string;
  pagePermissions: PagePermission[];
  isSystem: boolean;
}

export interface UserRole {
  id: string;
  userId: string;
  companyId: string | null;
  role: string;
  permissions: PagePermission[];
  isPrimary: boolean;
  status: string;
  companyName?: string;
  companyType?: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  userType: string;
  status: string;
  roles: UserRole[];
}

// Page definitions with user-friendly labels
const PAGES = {
  dashboard: { label: 'Dashboard', icon: '📊', category: 'Core' },
  analytics: { label: 'Analytics', icon: '📈', category: 'Core' },
  users: { label: 'User Management', icon: '👥', category: 'Administration' },
  companies: { label: 'Companies', icon: '🏢', category: 'Administration' },
  roles: { label: 'Roles & Permissions', icon: '🔐', category: 'Administration' },
  content: { label: 'Content Library', icon: '📁', category: 'Content' },
  content_upload: { label: 'Content Upload', icon: '📤', category: 'Content' },
  content_review: { label: 'Content Review', icon: '👀', category: 'Content' },
  content_approval: { label: 'Content Approval', icon: '✅', category: 'Content' },
  devices: { label: 'Devices', icon: '📺', category: 'Devices' },
  device_registration: { label: 'Device Registration', icon: '🆔', category: 'Devices' },
  device_monitoring: { label: 'Device Monitoring', icon: '📡', category: 'Devices' },
  schedules: { label: 'Content Schedules', icon: '📅', category: 'Advanced' },
  overlays: { label: 'Content Overlays', icon: '🖼️', category: 'Advanced' },
  digital_twin: { label: 'Digital Twin', icon: '🎭', category: 'Advanced' },
  system_settings: { label: 'System Settings', icon: '⚙️', category: 'System' },
  audit_logs: { label: 'Audit Logs', icon: '📋', category: 'System' },
  api_keys: { label: 'API Keys', icon: '🔑', category: 'System' }
} as const;

// Permission definitions with user-friendly labels
const PERMISSIONS = {
  view: { label: 'View', icon: <Eye className="h-4 w-4" />, color: 'bg-blue-100 text-blue-800' },
  create: { label: 'Create', icon: <Plus className="h-4 w-4" />, color: 'bg-green-100 text-green-800' },
  edit: { label: 'Edit', icon: <Edit className="h-4 w-4" />, color: 'bg-yellow-100 text-yellow-800' },
  delete: { label: 'Delete', icon: <Trash2 className="h-4 w-4" />, color: 'bg-red-100 text-red-800' },
  approve: { label: 'Approve', icon: <Check className="h-4 w-4" />, color: 'bg-emerald-100 text-emerald-800' },
  reject: { label: 'Reject', icon: '❌', color: 'bg-orange-100 text-orange-800' },
  manage: { label: 'Manage', icon: <Settings className="h-4 w-4" />, color: 'bg-purple-100 text-purple-800' },
  export: { label: 'Export', icon: '📤', color: 'bg-indigo-100 text-indigo-800' },
  import: { label: 'Import', icon: '📥', color: 'bg-cyan-100 text-cyan-800' }
} as const;

// Role templates with clean definitions
const ROLE_TEMPLATES = {
  SUPER_ADMIN: { 
    name: 'Super Administrator', 
    description: 'Full system access and management',
    color: 'bg-red-100 text-red-800 border-red-200',
    icon: <Shield className="h-4 w-4" />
  },
  COMPANY_ADMIN: { 
    name: 'Company Administrator', 
    description: 'Full management within company scope',
    color: 'bg-purple-100 text-purple-800 border-purple-200',
    icon: <Building className="h-4 w-4" />
  },
  CONTENT_MANAGER: { 
    name: 'Content Manager', 
    description: 'Content and device management',
    color: 'bg-blue-100 text-blue-800 border-blue-200',
    icon: <Users className="h-4 w-4" />
  },
  REVIEWER: { 
    name: 'Content Reviewer', 
    description: 'Content review and approval',
    color: 'bg-green-100 text-green-800 border-green-200',
    icon: <Eye className="h-4 w-4" />
  },
  EDITOR: { 
    name: 'Content Editor', 
    description: 'Content creation and editing',
    color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    icon: <Edit className="h-4 w-4" />
  },
  VIEWER: { 
    name: 'Viewer', 
    description: 'Read-only access to company data',
    color: 'bg-gray-100 text-gray-800 border-gray-200',
    icon: <Eye className="h-4 w-4" />
  }
} as const;

interface RoleManagementProps {
  selectedUser: User | null;
  onUserRoleUpdate: (userId: string, roles: UserRole[]) => void;
  companies: any[];
  currentUser: User;
}

export const RoleManagement: React.FC<RoleManagementProps> = ({ 
  selectedUser, 
  onUserRoleUpdate,
  companies,
  currentUser 
}) => {
  const [userRoles, setUserRoles] = useState<UserRole[]>([]);
  const [editingRole, setEditingRole] = useState<string | null>(null);
  const [selectedCompany, setSelectedCompany] = useState<string>('');
  const [selectedRoleTemplate, setSelectedRoleTemplate] = useState<string>('VIEWER');
  const [customPermissions, setCustomPermissions] = useState<Record<string, string[]>>({});
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Load user roles when selectedUser changes
  useEffect(() => {
    if (selectedUser) {
      setUserRoles(selectedUser.roles || []);
      setEditingRole(null);
      setCustomPermissions({});
    }
  }, [selectedUser]);

  // Group pages by category
  const pagesByCategory = Object.entries(PAGES).reduce((acc, [pageKey, pageInfo]) => {
    if (!acc[pageInfo.category]) {
      acc[pageInfo.category] = [];
    }
    acc[pageInfo.category].push({ key: pageKey, ...pageInfo });
    return acc;
  }, {} as Record<string, Array<{ key: string; label: string; icon: string; category: string }>>);

  // Handle role assignment
  const handleAssignRole = async () => {
    if (!selectedUser || !selectedRoleTemplate) return;

    const newRole: UserRole = {
      id: `temp-${Date.now()}`,
      userId: selectedUser.id,
      companyId: selectedCompany || null,
      role: selectedRoleTemplate,
      permissions: [], // Will be populated by backend based on role template
      isPrimary: userRoles.length === 0, // First role is primary
      status: 'active',
      companyName: selectedCompany ? companies.find(c => c.id === selectedCompany)?.name : 'System',
      companyType: selectedCompany ? companies.find(c => c.id === selectedCompany)?.company_type : null
    };

    const updatedRoles = [...userRoles, newRole];
    setUserRoles(updatedRoles);
    onUserRoleUpdate(selectedUser.id, updatedRoles);

    // Reset form
    setSelectedCompany('');
    setSelectedRoleTemplate('VIEWER');
  };

  // Handle role removal
  const handleRemoveRole = (roleId: string) => {
    const updatedRoles = userRoles.filter(role => role.id !== roleId);
    setUserRoles(updatedRoles);
    
    if (selectedUser) {
      onUserRoleUpdate(selectedUser.id, updatedRoles);
    }
  };

  // Handle permission toggle
  const handlePermissionToggle = (roleId: string, page: string, permission: string) => {
    if (!showAdvanced) return;

    const rolePermissions = customPermissions[roleId] || {};
    const pagePermissions = rolePermissions[page] || [];
    
    const updatedPagePermissions = pagePermissions.includes(permission)
      ? pagePermissions.filter(p => p !== permission)
      : [...pagePermissions, permission];

    const updatedRolePermissions = {
      ...rolePermissions,
      [page]: updatedPagePermissions
    };

    setCustomPermissions({
      ...customPermissions,
      [roleId]: updatedRolePermissions
    });
  };

  // Check if permission is enabled for a role
  const isPermissionEnabled = (role: UserRole, page: string, permission: string): boolean => {
    // Check custom permissions first
    const customPerms = customPermissions[role.id];
    if (customPerms && customPerms[page]) {
      return customPerms[page].includes(permission);
    }

    // Fall back to role's current permissions
    const pagePermission = role.permissions?.find(p => p.page === page);
    return pagePermission?.permissions.includes(permission) || false;
  };

  if (!selectedUser) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <Users className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No User Selected</h3>
          <p className="text-gray-500">Select a user to manage their roles and permissions</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* User Info Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Role Management for {selectedUser.name}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div>
              <p className="text-sm text-gray-500">Email</p>
              <p className="font-medium">{selectedUser.email}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">User Type</p>
              <Badge variant="secondary">{selectedUser.userType}</Badge>
            </div>
            <div>
              <p className="text-sm text-gray-500">Status</p>
              <Badge variant={selectedUser.status === 'active' ? 'default' : 'destructive'}>
                {selectedUser.status}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Role Assignment */}
      <Card>
        <CardHeader>
          <CardTitle>Assign New Role</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Company Selection */}
            <div>
              <label className="text-sm font-medium mb-2 block">Company</label>
              <select 
                value={selectedCompany} 
                onChange={(e) => setSelectedCompany(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">System Level</option>
                {companies.map(company => (
                  <option key={company.id} value={company.id}>
                    {company.name} ({company.company_type})
                  </option>
                ))}
              </select>
            </div>

            {/* Role Template Selection */}
            <div>
              <label className="text-sm font-medium mb-2 block">Role</label>
              <select 
                value={selectedRoleTemplate} 
                onChange={(e) => setSelectedRoleTemplate(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {Object.entries(ROLE_TEMPLATES).map(([key, template]) => (
                  <option key={key} value={key}>
                    {template.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Assign Button */}
            <div className="flex items-end">
              <Button onClick={handleAssignRole} className="w-full">
                <Plus className="h-4 w-4 mr-2" />
                Assign Role
              </Button>
            </div>
          </div>

          {/* Role Template Description */}
          {selectedRoleTemplate && ROLE_TEMPLATES[selectedRoleTemplate as keyof typeof ROLE_TEMPLATES] && (
            <Alert>
              <AlertDescription>
                {ROLE_TEMPLATES[selectedRoleTemplate as keyof typeof ROLE_TEMPLATES].description}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Current Roles */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Current Roles ({userRoles.length})</CardTitle>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Advanced Mode</span>
            <Switch 
              checked={showAdvanced} 
              onCheckedChange={setShowAdvanced}
            />
          </div>
        </CardHeader>
        <CardContent>
          {userRoles.length === 0 ? (
            <div className="text-center py-8">
              <Shield className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Roles Assigned</h3>
              <p className="text-gray-500">This user has no roles assigned yet</p>
            </div>
          ) : (
            <div className="space-y-4">
              {userRoles.map((role) => (
                <div key={role.id} className="border border-gray-200 rounded-lg p-4">
                  {/* Role Header */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <Badge 
                        className={ROLE_TEMPLATES[role.role as keyof typeof ROLE_TEMPLATES]?.color || 'bg-gray-100'}
                      >
                        {ROLE_TEMPLATES[role.role as keyof typeof ROLE_TEMPLATES]?.icon}
                        <span className="ml-2">
                          {ROLE_TEMPLATES[role.role as keyof typeof ROLE_TEMPLATES]?.name || role.role}
                        </span>
                      </Badge>
                      
                      {role.isPrimary && (
                        <Badge variant="outline" className="text-xs">
                          Primary
                        </Badge>
                      )}
                      
                      <div className="text-sm text-gray-500">
                        {role.companyName || 'System Level'}
                        {role.companyType && (
                          <span className="ml-1">({role.companyType})</span>
                        )}
                      </div>
                    </div>
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveRole(role.id)}
                      className="text-red-600 hover:text-red-800 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>

                  {/* Page-Level Permissions */}
                  {showAdvanced && (
                    <div className="space-y-4">
                      <h4 className="text-sm font-medium text-gray-900">Page Permissions</h4>
                      
                      {Object.entries(pagesByCategory).map(([category, pages]) => (
                        <div key={category} className="space-y-2">
                          <h5 className="text-xs font-medium text-gray-700 uppercase tracking-wide">
                            {category}
                          </h5>
                          
                          <div className="grid grid-cols-1 gap-2">
                            {pages.map((page) => (
                              <div key={page.key} className="bg-gray-50 rounded-md p-3">
                                <div className="flex items-center justify-between mb-2">
                                  <div className="flex items-center gap-2">
                                    <span className="text-lg">{page.icon}</span>
                                    <span className="text-sm font-medium">{page.label}</span>
                                  </div>
                                </div>
                                
                                <div className="flex flex-wrap gap-2">
                                  {Object.entries(PERMISSIONS).map(([permKey, permission]) => (
                                    <label key={permKey} className="flex items-center gap-2 cursor-pointer">
                                      <input
                                        type="checkbox"
                                        checked={isPermissionEnabled(role, page.key, permKey)}
                                        onChange={() => handlePermissionToggle(role.id, page.key, permKey)}
                                        className="h-3 w-3 text-blue-600 rounded focus:ring-blue-500"
                                      />
                                      <span className={`text-xs px-2 py-1 rounded-full flex items-center gap-1 ${permission.color}`}>
                                        {permission.icon}
                                        {permission.label}
                                      </span>
                                    </label>
                                  ))}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Simple Permissions View */}
                  {!showAdvanced && role.permissions && role.permissions.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium text-gray-900">Permissions Summary</h4>
                      <div className="flex flex-wrap gap-1">
                        {role.permissions.slice(0, 5).map((pagePermission, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {PAGES[pagePermission.page as keyof typeof PAGES]?.label || pagePermission.page}
                          </Badge>
                        ))}
                        {role.permissions.length > 5 && (
                          <Badge variant="outline" className="text-xs">
                            +{role.permissions.length - 5} more
                          </Badge>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default RoleManagement;