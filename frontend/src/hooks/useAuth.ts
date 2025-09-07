// Clean useAuth Hook
import { useState, useCallback, useEffect } from 'react';
import { UserProfile, LoginCredentials, LoginResponse, UserType, CompanyType, CompanyRole } from '@/types/auth';

const API_BASE_URL = '/api/auth';

export function useAuth() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  const apiCall = async <T>(endpoint: string, options: RequestInit = {}): Promise<T> => {
    const token = localStorage.getItem('access_token');
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      
      if (response.status === 401) {
        localStorage.removeItem('access_token');
        setUser(null);
        throw new Error('Unauthorized');
      }
      
      throw new Error(errorData.detail || `Request failed: ${response.status}`);
    }

    return response.json();
  };

  const getCurrentUser = useCallback(async (): Promise<UserProfile | null> => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setUser(null);
      setIsInitialized(true);
      return null;
    }

    setLoading(true);
    setError(null);

    try {
      const userData = await apiCall<UserProfile>('/me');
      setUser(userData);
      setIsInitialized(true);
      return userData;
    } catch (err) {
      console.error('Failed to get user:', err);
      localStorage.removeItem('access_token');
      setUser(null);
      setError(err instanceof Error ? err.message : 'Failed to get user');
      setIsInitialized(true);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    getCurrentUser();
  }, [getCurrentUser]);

  const login = useCallback(async (credentials: LoginCredentials): Promise<UserProfile | null> => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiCall<LoginResponse>('/login', {
        method: 'POST',
        body: JSON.stringify(credentials),
      });

      localStorage.setItem('access_token', response.access_token);
      setUser(response.user);
      return response.user;
    } catch (err) {
      console.error('Login failed:', err);
      setError(err instanceof Error ? err.message : 'Login failed');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async (): Promise<void> => {
    try {
      await apiCall('/logout', { method: 'POST' });
    } catch (err) {
      console.error('Error during logout:', err);
    } finally {
      localStorage.removeItem('access_token');
      setUser(null);
      setError(null);
    }
  }, []);

  // Permission checking functions
  const hasPermission = useCallback((resource: string, action: string): boolean => {
    if (!user) return false;
    if (user.user_type === UserType.SUPER_USER) return true;
    const permissionKey = `${resource}_${action}`;
    return user.permissions.includes(permissionKey);
  }, [user]);

  const hasRole = useCallback((role: CompanyRole): boolean => {
    if (!user) return false;
    if (user.user_type === UserType.SUPER_USER) return true;
    return user.company_role === role;
  }, [user]);

  const isSuperUser = useCallback((): boolean => {
    return user?.user_type === UserType.SUPER_USER;
  }, [user]);

  const isCompanyUser = useCallback((): boolean => {
    return user?.user_type === UserType.COMPANY_USER;
  }, [user]);

  const isHostCompany = useCallback((): boolean => {
    return user?.company?.company_type === CompanyType.HOST;
  }, [user]);

  const isAdvertiserCompany = useCallback((): boolean => {
    return user?.company?.company_type === CompanyType.ADVERTISER;
  }, [user]);

  const canAccessNavigation = useCallback((navigationKey: string): boolean => {
    if (!user) return false;
    return user.accessible_navigation.includes(navigationKey);
  }, [user]);

  const canAccess = useCallback((component: string): boolean => {
    if (!user) return false;
    if (user.user_type === UserType.SUPER_USER) return true;

    const componentPermissionMap: Record<string, {resource: string, action: string}> = {
      'user_management': { resource: 'user', action: 'read' },
      'device_management': { resource: 'device', action: 'read' },
      'content_creation': { resource: 'content', action: 'create' },
      'content_approval': { resource: 'content', action: 'approve' },
      'analytics': { resource: 'analytics', action: 'read' }
    };

    const permission = componentPermissionMap[component];
    if (permission) {
      return hasPermission(permission.resource, permission.action);
    }

    return canAccessNavigation(component);
  }, [user, hasPermission, canAccessNavigation]);

  const getDisplayName = useCallback((): string => {
    if (!user) return 'Guest';
    const fullName = `${user.first_name || ''} ${user.last_name || ''}`.trim();
    return fullName || user.email;
  }, [user]);

  const getRoleDisplay = useCallback((): string => {
    if (!user) return 'No Role';
    if (user.user_type === UserType.SUPER_USER) return 'Super User';
    
    if (user.company_role) {
      const roleLabels = {
        [CompanyRole.ADMIN]: 'Administrator',
        [CompanyRole.REVIEWER]: 'Reviewer',
        [CompanyRole.EDITOR]: 'Editor',
        [CompanyRole.VIEWER]: 'Viewer'
      };
      return roleLabels[user.company_role];
    }
    
    return 'Company User';
  }, [user]);

  const getDefaultRole = useCallback(() => {
    if (!user) return null;
    
    if (user.user_type === UserType.SUPER_USER) {
      return { role_name: 'Super Administrator', role: 'SUPER_USER', company_name: 'Platform' };
    }
    
    if (user.company_role) {
      const roleLabels = {
        [CompanyRole.ADMIN]: 'Administrator',
        [CompanyRole.REVIEWER]: 'Reviewer', 
        [CompanyRole.EDITOR]: 'Editor',
        [CompanyRole.VIEWER]: 'Viewer'
      };
      
      return {
        role_name: roleLabels[user.company_role] || user.company_role,
        role: user.company_role,
        company_name: user.company?.name || 'Unknown Company'
      };
    }
    
    return { role_name: 'Company User', role: 'USER', company_name: user.company?.name || 'Unknown Company' };
  }, [user]);

  return {
    user, loading, error, isInitialized,
    login, logout, getCurrentUser,
    hasPermission, hasRole, isSuperUser, isCompanyUser, 
    isHostCompany, isAdvertiserCompany, canAccess, canAccessNavigation,
    getDisplayName, getRoleDisplay, getDefaultRole,
  };
}
