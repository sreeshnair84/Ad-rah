import { useState, useCallback, useEffect } from 'react';
import { User, LoginCredentials } from '@/types';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  const getCurrentUser = useCallback(async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      console.log('No token found, user not authenticated');
      setUser(null);
      setLoading(false);
      setIsInitialized(true);
      return null;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        const userData = data.user || data;
        setUser(userData);
        setIsInitialized(true);
        // Log detailed user info for debugging
        console.log('🔍 User authenticated:', {
          userType: userData?.user_type,
          companyRole: userData?.company_role,
          companyType: userData?.company?.company_type,
          companyName: userData?.company?.name,
          permissionsCount: userData?.permissions?.length || 0,
          permissions: userData?.permissions
        });
        return userData;
      } else if (response.status === 401) {
        console.log('Token expired or invalid, clearing token');
        localStorage.removeItem('token');
        setUser(null);
        setError('Authentication token expired');
        setIsInitialized(true);
        return null;
      } else {
        console.error(`Failed to get user: ${response.status}`);
        setUser(null);
        setError(`Failed to authenticate: ${response.status}`);
        setIsInitialized(true);
        return null;
      }
    } catch (err) {
      console.error('Failed to get user:', err);
      setError(err instanceof Error ? err.message : 'Failed to get user');
      setUser(null);
      localStorage.removeItem('token');
      setIsInitialized(true);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Initialize authentication state on mount
  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        console.log('Found existing token, validating user session');
        await getCurrentUser();
      } else {
        console.log('No token found, user not authenticated');
        setIsInitialized(true);
      }
    };

    initializeAuth();
  }, [getCurrentUser]);

  const login = useCallback(async (credentials: LoginCredentials): Promise<User | null> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      }

      const data = await response.json();
      localStorage.setItem('token', data.access_token);

      // Set user data from login response
      if (data.user) {
        setUser(data.user);
        return data.user;
      }

      // Fetch user info if not included in login response
      const userResponse = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${data.access_token}`,
        },
      });

      if (userResponse.ok) {
        const userData = await userResponse.json();
        setUser(userData.user || userData);
        return userData.user || userData;
      }
      return null;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (token) {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      }
    } catch (err) {
      console.error('Error during logout:', err);
    } finally {
      localStorage.removeItem('token');
      setUser(null);
      setIsInitialized(true);
    }
  }, []);

  // Check if user has a specific permission
  const hasPermission = useCallback((resource: string, action: string): boolean => {
    if (!user) return false;
    if (user.user_type === 'SUPER_USER') return true;
    
    // Check if user has the permission
    const permissionKey = `${resource}_${action}`;
    return user.permissions && user.permissions.includes(permissionKey);
  }, [user]);

  // Check if user has any of the specified permissions
  const hasAnyPermission = useCallback((permissions: Array<{resource: string, action: string}>): boolean => {
    if (!user) return false;
    if (user.user_type === 'SUPER_USER') return true;
    return permissions.some(({resource, action}) => user.permissions.includes(`${resource}_${action}`));
  }, [user]);

  // Check if user has a specific company role
  const hasRole = useCallback((role: 'ADMIN' | 'REVIEWER' | 'EDITOR' | 'VIEWER'): boolean => {
    if (!user) return false;
    if (user.user_type === 'SUPER_USER') return true;
    return user.company_role === role;
  }, [user]);

  // Check if user has any of the specified roles
  const hasAnyRole = useCallback((roles: Array<'ADMIN' | 'REVIEWER' | 'EDITOR' | 'VIEWER'>): boolean => {
    if (!user) return false;
    if (user.user_type === 'SUPER_USER') return true;
    return user.company_role ? roles.includes(user.company_role) : false;
  }, [user]);

  // Check if user is super user
  const isSuperUser = useCallback((): boolean => {
    return user?.user_type === 'SUPER_USER';
  }, [user]);

  // Check if user is company user
  const isCompanyUser = useCallback((): boolean => {
    return user?.user_type === 'COMPANY_USER';
  }, [user]);

  // Check if user belongs to HOST company
  const isHostCompany = useCallback((): boolean => {
    return user?.company?.company_type === 'HOST';
  }, [user]);

  // Check if user belongs to ADVERTISER company
  const isAdvertiserCompany = useCallback((): boolean => {
    return user?.company?.company_type === 'ADVERTISER';
  }, [user]);

  // Check if user can access component
  const canAccess = useCallback((component: string): boolean => {
    if (!user) return false;
    if (user.user_type === 'SUPER_USER') return true;

    switch (component) {
      case 'user_management':
        return hasPermission('user', 'view');
      case 'device_management':
        return hasPermission('device', 'view');
      case 'content_creation':
        return hasPermission('content', 'create');
      case 'content_approval':
        return hasPermission('content', 'approve');
      case 'content_sharing':
        return hasPermission('content', 'share');
      case 'analytics':
        return hasPermission('analytics', 'view');
      case 'platform_admin':
        return hasPermission('platform', 'admin');
      case 'company_admin':
        return hasRole('ADMIN');
      default:
        return false;
    }
  }, [user, hasPermission, hasRole]);

  // Get user's display name
  const getDisplayName = useCallback((): string => {
    if (!user) return 'Guest';
    return `${user.first_name} ${user.last_name}`.trim() || user.email;
  }, [user]);

  // Get user's role display
  const getRoleDisplay = useCallback((): string => {
    if (!user) return 'No Role';
    if (user.user_type === 'SUPER_USER') return 'Super User';
    if (user.company_role) {
      const roleLabels = {
        'ADMIN': 'Administrator',
        'REVIEWER': 'Reviewer',
        'EDITOR': 'Editor',
        'VIEWER': 'Viewer'
      };
      return roleLabels[user.company_role];
    }
    return 'Company User';
  }, [user]);

  // Get user's default role (for backwards compatibility)
  const getDefaultRole = useCallback(() => {
    if (!user) return null;
    
    // For super users
    if (user.user_type === 'SUPER_USER') {
      return {
        role_name: 'Super Administrator',
        role: 'SUPER_USER',
        company_name: 'Platform'
      };
    }
    
    // For company users
    if (user.company_role) {
      const roleLabels = {
        'ADMIN': 'Administrator',
        'REVIEWER': 'Reviewer', 
        'EDITOR': 'Editor',
        'VIEWER': 'Viewer'
      };
      
      return {
        role_name: roleLabels[user.company_role] || user.company_role,
        role: user.company_role,
        company_name: user.company?.name || 'Unknown Company'
      };
    }
    
    return {
      role_name: 'Company User',
      role: 'USER',
      company_name: user.company?.name || 'Unknown Company'
    };
  }, [user]);

  return {
    user,
    loading,
    error,
    isInitialized,
    login,
    logout,
    getCurrentUser,
    hasPermission,
    hasAnyPermission,
    hasRole,
    hasAnyRole,
    isSuperUser,
    isCompanyUser,
    isHostCompany,
    isAdvertiserCompany,
    canAccess,
    getDisplayName,
    getRoleDisplay,
    getDefaultRole,
  };
}
