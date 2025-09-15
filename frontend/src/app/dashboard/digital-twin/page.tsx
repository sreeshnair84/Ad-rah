'use client';

import { DigitalTwinDashboard } from '@/components/digital-twin/DigitalTwinDashboard';
import { PermissionGate } from '@/components/PermissionGate';
import { PageLayout } from '@/components/shared/PageLayout';

export default function DigitalTwinPage() {
  return (
    <PermissionGate requiredPermissions={['device_read', 'analytics_read']}>
      <PageLayout
        title="Digital Twin Dashboard"
        description="Monitor and control your digital signage devices in real-time"
      >
        <DigitalTwinDashboard />
      </PageLayout>
    </PermissionGate>
  );
}