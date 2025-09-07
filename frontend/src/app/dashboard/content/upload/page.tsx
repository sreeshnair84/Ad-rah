'use client';

import UnifiedUploadPage from '@/components/upload/UnifiedUploadPage';

export default function ContentUploadPage() {
  return (
    <UnifiedUploadPage
      mode="advanced"
      title="Upload Content"
      description="Upload images, videos, and documents for AI review and approval"
      showAI={true}
      redirectPath="/dashboard/content"
    />
  );
}
