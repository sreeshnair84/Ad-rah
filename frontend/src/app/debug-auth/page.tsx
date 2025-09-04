// Test page to check user context
'use client';

import { useAuth } from '@/hooks/useAuth';
import { useEffect } from 'react';

export default function DebugAuth() {
  const { user, loading, isSuperUser } = useAuth();

  useEffect(() => {
    console.log('Debug Auth - User:', user);
    console.log('Debug Auth - Loading:', loading);
    console.log('Debug Auth - isSuperUser():', isSuperUser());
    console.log('Debug Auth - user?.user_type:', user?.user_type);
    console.log('Debug Auth - user?.roles:', user?.roles);
  }, [user, loading, isSuperUser]);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="p-6">
      <h1>Auth Debug Page</h1>
      <div className="space-y-4">
        <div>
          <strong>User Type:</strong> {user?.user_type || 'N/A'}
        </div>
        <div>
          <strong>Is Super User:</strong> {isSuperUser() ? 'Yes' : 'No'}
        </div>
        <div>
          <strong>User Email:</strong> {user?.email || 'N/A'}
        </div>
        <div>
          <strong>User Roles:</strong> {JSON.stringify(user?.roles, null, 2)}
        </div>
        <div>
          <strong>User Permissions Count:</strong> {user?.permissions?.length || 0}
        </div>
        <pre className="bg-gray-100 p-4 rounded text-sm">
          {JSON.stringify(user, null, 2)}
        </pre>
      </div>
    </div>
  );
}
