import React from 'react';
import { useAuth } from '@/hooks/useAuth';

interface PermissionGateProps {
  children: React.ReactNode;
  // Permission-based access
  permission?: {
    resource: string;
    action: string;
  };
  permissions?: Array<{
    resource: string;
    action: string;
  }>;
  // Role-based access
  role?: 'ADMIN' | 'REVIEWER' | 'EDITOR' | 'VIEWER';
  roles?: Array<'ADMIN' | 'REVIEWER' | 'EDITOR' | 'VIEWER'>;
  // User type access
  userType?: 'SUPER_USER' | 'COMPANY_USER' | 'DEVICE_USER';
  userTypes?: Array<'SUPER_USER' | 'COMPANY_USER' | 'DEVICE_USER'>;
  // Company type restrictions
  companyTypes?: Array<'HOST' | 'ADVERTISER'>;
  // Component-based access
  component?: string;
  // Require ALL conditions vs ANY (default: ANY)
  requireAll?: boolean;
  // Fallback content when access denied
  fallback?: React.ReactNode;
  // Show loading state
  showLoading?: boolean;
}

export function PermissionGate({
  children,
  permission,
  permissions = [],
  role,
  roles,
  userType,
  userTypes,
  companyTypes = [],
  component,
  requireAll = false,
  fallback = null,
  showLoading = false
}: PermissionGateProps) {
  const { 
    user, 
    loading, 
    hasPermission, 
    hasRole, 
    hasAnyRole, 
    canAccess, 
    isSuperUser,
    isCompanyUser 
  } = useAuth();

  // Show loading state if requested and auth is loading
  if (loading && showLoading) {
    return <div className="flex items-center justify-center p-4">Loading...</div>;
  }

  // If no user, deny access
  if (!user) {
    return <>{fallback}</>;
  }

  // Super users bypass all checks except explicit user type restrictions
  if (isSuperUser() && !userType) {
    return <>{children}</>;
  }

  // Check user type access first
  if (userType && user.user_type !== userType) {
    return <>{fallback}</>;
  }

  if (userTypes && !userTypes.includes(user.user_type)) {
    return <>{fallback}</>;
  }

  // Check company type restrictions (only for company users)
  if (companyTypes.length > 0 && isCompanyUser()) {
    const userCompanyType = user.company?.company_type;
    if (!userCompanyType || !companyTypes.includes(userCompanyType)) {
      return <>{fallback}</>;
    }
  }

  // Collect all permissions to check
  const allPermissions = [];
  if (permission) allPermissions.push(permission);
  if (permissions.length > 0) allPermissions.push(...permissions);

  // Check permissions
  if (allPermissions.length > 0) {
    const permissionResults = allPermissions.map(perm => 
      hasPermission(perm.resource, perm.action)
    );

    const hasRequiredPermissions = requireAll 
      ? permissionResults.every(result => result)
      : permissionResults.some(result => result);

    if (!hasRequiredPermissions) {
      return <>{fallback}</>;
    }
  }

  // Collect all roles to check
  const allRoles = [];
  if (role) allRoles.push(role);
  if (roles && roles.length > 0) allRoles.push(...roles);

  // Check roles
  if (allRoles.length > 0) {
    const roleResults = allRoles.map(r => hasRole(r));
    
    const hasRequiredRoles = requireAll 
      ? roleResults.every(result => result)
      : roleResults.some(result => result);

    if (!hasRequiredRoles) {
      return <>{fallback}</>;
    }
  }

  // Check component-based access
  if (component && !canAccess(component)) {
    return <>{fallback}</>;
  }

  // All checks passed, render children
  return <>{children}</>;
}

// Convenience components for common use cases
export function SuperUserOnly({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return (
    <PermissionGate userType="SUPER_USER" fallback={fallback}>
      {children}
    </PermissionGate>
  );
}

export function CompanyAdminOnly({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return (
    <PermissionGate role="ADMIN" fallback={fallback}>
      {children}
    </PermissionGate>
  );
}

export function ContentManagerOnly({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return (
    <PermissionGate roles={['ADMIN', 'REVIEWER', 'EDITOR']} fallback={fallback}>
      {children}
    </PermissionGate>
  );
}

export function ContentCreatorOnly({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return (
    <PermissionGate permission={{ resource: 'content', action: 'create' }} fallback={fallback}>
      {children}
    </PermissionGate>
  );
}

export function ContentApproverOnly({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return (
    <PermissionGate permission={{ resource: 'content', action: 'approve' }} fallback={fallback}>
      {children}
    </PermissionGate>
  );
}

export function DeviceManagerOnly({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return (
    <PermissionGate permission={{ resource: 'devices', action: 'view' }} companyTypes={['HOST']} fallback={fallback}>
      {children}
    </PermissionGate>
  );
}

// New convenience components for enhanced permissions
export function UserManagerOnly({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return (
    <PermissionGate permission={{ resource: 'users', action: 'view' }} fallback={fallback}>
      {children}
    </PermissionGate>
  );
}

export function HostCompanyOnly({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return (
    <PermissionGate companyTypes={['HOST']} fallback={fallback}>
      {children}
    </PermissionGate>
  );
}

export function AdvertiserCompanyOnly({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return (
    <PermissionGate companyTypes={['ADVERTISER']} fallback={fallback}>
      {children}
    </PermissionGate>
  );
}

export function AnalyticsViewerOnly({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return (
    <PermissionGate permission={{ resource: 'analytics', action: 'view' }} fallback={fallback}>
      {children}
    </PermissionGate>
  );
}
