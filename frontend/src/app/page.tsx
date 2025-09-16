// Copyright (c) 2025 Adara Screen by Hebron
// Owner: Sujesh M S
// All Rights Reserved
//
// This software is proprietary to Adara Screen by Hebron.
// Unauthorized use, reproduction, or distribution is strictly prohibited.

'use client';

import { useEffect } from 'react';
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Check if user is logged in
    const user = localStorage.getItem('user');
    if (user) {
      router.push('/dashboard');
    } else {
      router.push('/login');
    }
  }, [router]);

  return <div>Redirecting...</div>;
}
