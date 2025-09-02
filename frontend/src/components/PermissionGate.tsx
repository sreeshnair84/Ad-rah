import React from 'react';
import { useAuth } from '@/hooks/useAuth';

interface PermissionGateProps {
  children: React.ReactNode;
  // Permission-based access
  permission?: {
    resource: string;
    action: string;
  };
  // Role-based access
  role?: 'ADMIN' | 'REVIEWER' | 'EDITOR' | 'VIEWER';
  roles?: Array<'ADMIN' | 'REVIEWER' | 'EDITOR' | 'VIEWER'>;
  // User type access
  userType?: 'SUPER_USER' | 'COMPANY_USER' | 'DEVICE_USER';
  userTypes?: Array<'SUPER_USER' | 'COMPANY_USER' | 'DEVICE_USER'>;
  // Component-based access
  component?: string;
  // Fallback content when access denied
  fallback?: React.ReactNode;
  // Show loading state
  showLoading?: boolean;
}

export function PermissionGate({
  children,
  permission,
  role,
  roles,
  userType,
  userTypes,
  component,
  fallback = null,
  showLoading = false
}: PermissionGateProps) {
  const { user, loading, hasPermission, hasRole, hasAnyRole, canAccess } = useAuth();

  // Show loading state if requested and auth is loading
  if (loading && showLoading) {
    return <div className="flex items-center justify-center p-4">Loading...</div>;
  }

  // If no user, deny access
  if (!user) {
    return <>{fallback}</>;
  }

  // Check permission-based access
  if (permission) {
    if (!hasPermission(permission.resource, permission.action)) {
      return <>{fallback}</>;
    }
  }

  // Check single role access
  if (role) {
    if (!hasRole(role)) {
      return <>{fallback}</>;
    }
  }

  // Check multiple roles access
  if (roles) {
    if (!hasAnyRole(roles)) {
      return <>{fallback}</>;
    }
  }

  // Check single user type access
  if (userType) {
    if (user.user_type !== userType) {
      return <>{fallback}</>;
    }
  }

  // Check multiple user types access
  if (userTypes) {
    if (!userTypes.includes(user.user_type)) {
      return <>{fallback}</>;
    }
  }

  // Check component-based access
  if (component) {
    if (!canAccess(component)) {
      return <>{fallback}</>;
    }
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
    <PermissionGate permission={{ resource: 'device', action: 'view' }} fallback={fallback}>
      {children}
    </PermissionGate>
  );
}
