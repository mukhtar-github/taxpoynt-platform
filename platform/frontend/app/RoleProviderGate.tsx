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
 * - Always wraps dashboard routes so `useRoleDetector` consumers stay wired.
 * - Skips mounting for public/auth pages unless a valid session exists,
 *   preventing unauthenticated flows from crashing the role provider.
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

  const requiresRoleProvider = useMemo(() => {
    return ROLE_REQUIRED_PREFIXES.some((prefix) =>
      pathname.startsWith(prefix)
    );
  }, [pathname]);

  if (!hasSession && !requiresRoleProvider) {
    return <>{children}</>;
  }

  return <CombinedRoleProvider>{children}</CombinedRoleProvider>;
}

export default RoleProviderGate;
