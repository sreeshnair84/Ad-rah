'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (user) {
      // Redirect to unified dashboard
      router.replace('/dashboard/unified');
    }
  }, [user, router]);

  if (!user) {
    return <div>Loading...</div>;
  }

  return <div>Redirecting to dashboard...</div>;
}
