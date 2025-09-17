'use client';

import React from 'react';
import { UnifiedContentManager } from '@/components/content/UnifiedContentManager';

export default function ContentPage() {
  return (
    <UnifiedContentManager
      mode="all"
      showUpload={true}
      showFilters={true}
      showActions={true}
      compactView={false}
    />
  );
}