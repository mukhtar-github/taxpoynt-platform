'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { usePathname } from 'next/navigation';
import CombinedRoleProvider from '../role_management/combined_provider';
import { authService } from '../shared_components/services/auth';

interface RoleProviderGateProps {
  children: React.ReactNode;
}

const SESSION_POLL_INTERVAL_MS = 2000;
const ROLE_REQUIRED_PREFIXES = ['/dashboard'];

/**
 * Ensures the role management stack is only mounted when needed.
 * Dashboard routes always require it; public/auth/onboarding pages always skip it
 * even if a stale token exists to avoid false-positive initialization errors.
 */
export function RoleProviderGate({ children }: RoleProviderGateProps) {
  const pathname = usePathname() || '';
  const [hasSession, setHasSession] = useState(false);

  useEffect(() => {
    const checkSession = () => {
      try {
        setHasSession(Boolean(authService.getToken()));
      } catch {
        setHasSession(false);
      }
    };

    checkSession();

    const intervalId = window.setInterval(checkSession, SESSION_POLL_INTERVAL_MS);
    const handleStorage = (event: StorageEvent) => {
      if (!event.key) {
        return;
      }
      if (event.key.includes('taxpoynt')) {
        checkSession();
      }
    };

    window.addEventListener('storage', handleStorage);

    return () => {
      window.clearInterval(intervalId);
      window.removeEventListener('storage', handleStorage);
    };
  }, []);

  const requiresRoleProvider = useMemo(
    () => ROLE_REQUIRED_PREFIXES.some((prefix) => pathname.startsWith(prefix)),
    [pathname]
  );

  if (!requiresRoleProvider) {
    return <>{children}</>;
  }

  if (!hasSession) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
          <p className="text-sm text-slate-600">Preparing your dashboard…</p>
        </div>
      </div>
    );
  }

  return <CombinedRoleProvider>{children}</CombinedRoleProvider>;
}

export default RoleProviderGate;
