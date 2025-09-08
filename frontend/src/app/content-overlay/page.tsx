import { Metadata } from 'next';
import UnifiedOverlayManager from '@/components/overlay/UnifiedOverlayManager';

export const metadata: Metadata = {
  title: 'Content Overlay Management | Digital Signage',
  description: 'Design and manage content overlays on your digital screens',
};

export default function ContentOverlayPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <UnifiedOverlayManager
        mode="advanced"
        showCanvas={true}
        showList={true}
      />
    </div>
  );
}
