import { useState, useEffect } from 'react';
import { User } from '@/types';

interface UserMetrics {
  totalUsers: number;
  hostCount: number;
  advertiserCount: number;
}

export function useUsers() {
  const [users, setUsers] = useState<User[]>([]);
  const [metrics, setMetrics] = useState<UserMetrics>({
    totalUsers: 0,
    hostCount: 0,
    advertiserCount: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch('/api/users/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch users');
      }

      const usersData = await response.json();
      setUsers(usersData);

      // Calculate metrics
      const hostCount = usersData.filter((u: User) =>
        u.roles.some(r => r.role === 'HOST')
      ).length;
      const advertiserCount = usersData.filter((u: User) =>
        u.roles.some(r => r.role === 'ADVERTISER')
      ).length;

      setMetrics({
        totalUsers: usersData.length,
        hostCount,
        advertiserCount,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const addUser = async (userData: Omit<User, 'id' | 'roles' | 'created_at' | 'updated_at'> & {
    password: string;
    roles: Array<{ company_id: string; role: string; is_default: boolean }>;
  }) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch('/api/users/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create user');
      }

      const newUser = await response.json();
      setUsers(prev => [...prev, newUser]);

      // Update metrics
      setMetrics(prev => ({
        ...prev,
        totalUsers: prev.totalUsers + 1,
        hostCount: userData.roles.some(r => r.role === 'HOST') ? prev.hostCount + 1 : prev.hostCount,
        advertiserCount: userData.roles.some(r => r.role === 'ADVERTISER') ? prev.advertiserCount + 1 : prev.advertiserCount,
      }));
    } catch (err) {
      throw err;
    }
  };

  const deleteUser = async (userId: string) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch(`/api/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete user');
      }

      const userToDelete = users.find(u => u.id === userId);
      setUsers(prev => prev.filter(u => u.id !== userId));

      if (userToDelete) {
        setMetrics(prev => ({
          ...prev,
          totalUsers: prev.totalUsers - 1,
          hostCount: userToDelete.roles.some(r => r.role === 'HOST') ? prev.hostCount - 1 : prev.hostCount,
          advertiserCount: userToDelete.roles.some(r => r.role === 'ADVERTISER') ? prev.advertiserCount - 1 : prev.advertiserCount,
        }));
      }
    } catch (err) {
      throw err;
    }
  };

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'ADMIN':
        return 'default';
      case 'HOST':
        return 'secondary';
      case 'ADVERTISER':
        return 'outline';
      default:
        return 'outline';
    }
  };

  return {
    users,
    metrics,
    loading,
    error,
    addUser,
    deleteUser,
    getRoleBadge,
    refetch: fetchUsers,
  };
}
