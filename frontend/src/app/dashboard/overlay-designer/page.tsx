'use client';

import { OverlayDesigner } from '@/components/overlay/OverlayDesigner';
import { useSearchParams } from 'next/navigation';

export default function OverlayDesignerPage() {
  const searchParams = useSearchParams();
  const screenId = searchParams.get('screen_id');
  const templateId = searchParams.get('template_id');

  const handleSave = (overlayData: any) => {
    console.log('Overlay saved:', overlayData);
    // You could redirect or show a success message here
  };

  const handlePreview = (overlayData: any) => {
    console.log('Overlay preview:', overlayData);
    // You could open a preview modal or new window
  };

  return (
    <OverlayDesigner
      screenId={screenId || undefined}
      templateId={templateId || undefined}
      onSave={handleSave}
      onPreview={handlePreview}
    />
  );
}