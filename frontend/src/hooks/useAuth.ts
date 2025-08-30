import { useState, useCallback, useEffect } from 'react';

interface AuthUser {
  id: string;
  name?: string;
  email: string;
  phone?: string;
  status: string;
  roles: Array<{
    id: string;
    user_id: string;
    company_id: string;
    role_id: string;
    role: string;  // role_group like "ADMIN", "HOST", "ADVERTISER"
    role_name: string;  // full role name like "System Administrator"
    is_default: boolean;
    status: string;
    created_at: string;
    role_details?: {
      id: string;
      name: string;
      role_group: string;
      company_id: string;
      is_default: boolean;
      status: string;
      created_at: string;
      updated_at: string;
    };
  }>;
  companies?: Array<{
    id: string;
    name: string;
    type: string;
    address: string;
    city: string;
    country: string;
    phone?: string;
    email?: string;
    website?: string;
    status: string;
    created_at: string;
    updated_at: string;
  }>;
  active_company?: string;
  active_role?: string;
}

interface LoginCredentials {
  username: string;
  password: string;
}

export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null);
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
      const response = await fetch('/api/auth/me/with-roles', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
        setIsInitialized(true);
        console.log('User data loaded successfully:', data.user);
        return data.user;
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

  const login = useCallback(async (credentials: LoginCredentials): Promise<AuthUser | null> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/auth/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username: credentials.username,
          password: credentials.password,
        }),
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data = await response.json();
      localStorage.setItem('token', data.access_token);

      // Fetch user info with roles and companies
      const userResponse = await fetch('/api/auth/me/with-roles', {
        headers: {
          'Authorization': `Bearer ${data.access_token}`,
        },
      });

      if (userResponse.ok) {
        const userData = await userResponse.json();
        setUser(userData.user);
        return userData.user;
      }
      return null;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    setUser(null);
    setIsInitialized(true);
  }, []);

  const switchRole = useCallback(async (companyId: string, roleId: string) => {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    try {
      const response = await fetch('/api/auth/switch-role', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          company_id: companyId,
          role_id: roleId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        let errorMessage = 'Failed to switch role';
        if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail;
        } else if (errorData.detail && typeof errorData.detail === 'object') {
          errorMessage = JSON.stringify(errorData.detail);
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      setUser(data.user);
    } catch (err) {
      throw err;
    }
  }, []);

  const hasRole = useCallback((role: string, companyId?: string) => {
    if (!user) return false;

    return user.roles.some(userRole => {
      if (companyId) {
        return userRole.role === role && userRole.company_id === companyId;
      }
      return userRole.role === role;
    });
  }, [user]);

  const hasAnyRole = useCallback((roles: string[]) => {
    if (!user) return false;

    return user.roles.some(userRole => roles.includes(userRole.role));
  }, [user]);

  const getDefaultRole = useCallback(() => {
    if (!user) return null;

    const defaultRole = user.roles.find(role => role.is_default);
    return defaultRole || user.roles[0];
  }, [user]);

  return {
    user,
    loading,
    error,
    isInitialized,
    login,
    logout,
    getCurrentUser,
    switchRole,
    hasRole,
    hasAnyRole,
    getDefaultRole,
  };
}
