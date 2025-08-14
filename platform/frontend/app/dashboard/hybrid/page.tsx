'use client';

import React from 'react';
import { UnifiedDashboard } from '../../../hybrid_interface/components/unified_dashboard/UnifiedDashboard';

export default function HybridDashboard() {
  return (
    <div className="hybrid-dashboard-wrapper">
      <UnifiedDashboard userRole="hybrid_admin" />
    </div>
  );
}