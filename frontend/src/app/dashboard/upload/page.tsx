'use client';

import UnifiedUploadManager from '@/components/upload/UnifiedUploadManager';

export default function UploadPage() {
  return (
    <UnifiedUploadManager
      mode="simple"
      title="Upload Your First Content"
      description="Upload your advertisement content for review and approval"
      showAI={false}
      redirectPath="/dashboard/my-ads"
    />
  );
}
