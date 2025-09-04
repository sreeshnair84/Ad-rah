'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

export default function ContentRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to my-content page
    router.replace('/dashboard/my-content');
  }, [router]);

  return (
    <div className="flex justify-center items-center h-64">
      <div className="text-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
        <p className="text-sm text-muted-foreground">Redirecting to content management...</p>
      </div>
    </div>
  );
}