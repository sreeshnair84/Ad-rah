// Clean PermissionGate Component
import React from 'react';
import { useAuth } from '@/hooks/useAuth';
import { UserType, CompanyType, CompanyRole } from '@/types/auth';

interface PermissionGateProps {
  children: React.ReactNode;
  permission?: { resource: string; action: string; };
  roles?: CompanyRole[];
  userTypes?: UserType[];
  companyTypes?: CompanyType[];
  navigationKey?: string;
  component?: string;
  fallback?: React.ReactNode;
  showLoading?: boolean;
}

export function PermissionGate({
  children,
  permission,
  roles,
  userTypes,
  companyTypes,
  navigationKey,
  component,
  fallback = null,
  showLoading = false
}: PermissionGateProps) {
  const {
    user, loading, isInitialized, hasPermission, hasRole,
    isSuperUser, canAccessNavigation, canAccess
  } = useAuth();

  if (showLoading && (loading || !isInitialized)) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
        <span className="ml-2 text-sm text-gray-500">Loading...</span>
      </div>
    );
  }

  if (!isInitialized || !user) {
    return <>{fallback}</>;
  }

  if (isSuperUser()) {
    return <>{children}</>;
  }

  // Check user type requirements
  if (userTypes && userTypes.length > 0) {
    if (!userTypes.includes(user.user_type)) {
      return <>{fallback}</>;
    }
  }

  // Check company type requirements
  if (companyTypes && companyTypes.length > 0) {
    const userCompanyType = user.company?.company_type as CompanyType;
    if (!userCompanyType || !companyTypes.includes(userCompanyType)) {
      return <>{fallback}</>;
    }
  }

  // Check role requirements
  if (roles && roles.length > 0) {
    if (!user.company_role || !roles.some(role => hasRole(role))) {
      return <>{fallback}</>;
    }
  }

  // Check single permission
  if (permission) {
    if (!hasPermission(permission.resource, permission.action)) {
      return <>{fallback}</>;
    }
  }

  // Check navigation access
  if (navigationKey) {
    if (!canAccessNavigation(navigationKey)) {
      return <>{fallback}</>;
    }
  }

  // Check component access (legacy)
  if (component) {
    if (!canAccess(component)) {
      return <>{fallback}</>;
    }
  }

  return <>{children}</>;
}

// Convenience components
export function SuperUserOnly({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return <PermissionGate userTypes={[UserType.SUPER_USER]} fallback={fallback}>{children}</PermissionGate>;
}

export function HostCompanyOnly({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return <PermissionGate companyTypes={[CompanyType.HOST]} fallback={fallback}>{children}</PermissionGate>;
}

export function AdminOnly({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return <PermissionGate roles={[CompanyRole.ADMIN]} fallback={fallback}>{children}</PermissionGate>;
}

export function RequirePermission({ children, resource, action, fallback }: {
  children: React.ReactNode; resource: string; action: string; fallback?: React.ReactNode;
}) {
  return <PermissionGate permission={{ resource, action }} fallback={fallback}>{children}</PermissionGate>;
}
