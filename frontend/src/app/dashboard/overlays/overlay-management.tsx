import UnifiedOverlayManager from '@/components/overlay/UnifiedOverlayManager';

export default function OverlayManagement() {
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
