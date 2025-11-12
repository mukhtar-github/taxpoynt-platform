'use client';

import React from 'react';
import { CombinedRoleProvider } from '../../role_management/combined_provider';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <CombinedRoleProvider>
      {children}
    </CombinedRoleProvider>
  );
}
