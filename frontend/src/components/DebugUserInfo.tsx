import React from 'react';
import { useAuth } from '@/hooks/useAuth';

export function DebugUserInfo() {
  const { user, hasAnyRole, hasRole } = useAuth();

  if (!user) {
    return (
      <div className="p-4 bg-red-100 border border-red-300 rounded">
        <h3 className="font-bold text-red-800">🚨 No User Data</h3>
        <p>User is not authenticated or user data is missing</p>
      </div>
    );
  }

  return (
    <div className="p-4 bg-blue-100 border border-blue-300 rounded mb-4">
      <h3 className="font-bold text-blue-800">🔍 Debug User Info</h3>
      <div className="mt-2 text-sm">
        <p><strong>Email:</strong> {user.email}</p>
        <p><strong>ID:</strong> {user.id}</p>
        <p><strong>Active Company:</strong> {user.active_company || 'None'}</p>
        <p><strong>Active Role:</strong> {user.active_role || 'None'}</p>
        
        <div className="mt-2">
          <strong>Roles ({user.roles?.length || 0}):</strong>
          {user.roles?.length > 0 ? (
            <ul className="list-disc list-inside ml-2">
              {user.roles.map((role, index) => (
                <li key={index}>
                  <strong>Role:</strong> {role.role} | 
                  <strong> Name:</strong> {role.role_name} | 
                  <strong> Company:</strong> {role.company_id} |
                  <strong> Default:</strong> {role.is_default ? 'Yes' : 'No'}
                </li>
              ))}
            </ul>
          ) : (
            <span className="text-red-600"> No roles found!</span>
          )}
        </div>

        <div className="mt-2">
          <strong>Role Checks:</strong>
          <ul className="list-disc list-inside ml-2">
            <li>hasRole('ADMIN'): {hasRole('ADMIN') ? '✅ Yes' : '❌ No'}</li>
            <li>hasRole('HOST'): {hasRole('HOST') ? '✅ Yes' : '❌ No'}</li>
            <li>hasRole('ADVERTISER'): {hasRole('ADVERTISER') ? '✅ Yes' : '❌ No'}</li>
            <li>hasAnyRole(['ADMIN']): {hasAnyRole(['ADMIN']) ? '✅ Yes' : '❌ No'}</li>
            <li>hasAnyRole(['ADMIN', 'HOST']): {hasAnyRole(['ADMIN', 'HOST']) ? '✅ Yes' : '❌ No'}</li>
          </ul>
        </div>

        <div className="mt-2">
          <strong>Raw User Object:</strong>
          <pre className="text-xs bg-gray-100 p-2 mt-1 rounded overflow-auto max-h-40">
            {JSON.stringify(user, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}