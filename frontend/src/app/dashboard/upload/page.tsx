'use client';

import UnifiedUploadPage from '@/components/upload/UnifiedUploadPage';

export default function UploadPage() {
  return (
    <UnifiedUploadPage
      mode="simple"
      title="Upload Your First Content"
      description="Upload your advertisement content for review and approval"
      showAI={false}
      redirectPath="/dashboard/my-ads"
    />
  );
}
