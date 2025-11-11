'use client';

import React, { useEffect, useState } from 'react';
import CombinedRoleProvider from '../role_management/combined_provider';
import { authService } from '../shared_components/services/auth';

interface ClientRoleProviderProps {
  children: React.ReactNode;
}

const TOKEN_CHECK_INTERVAL_MS = 2000;

/**
 * Delays initialization of the heavy role management stack until
 * we actually have an authenticated session. This keeps unauthenticated
 * flows (signup/verify email) lightweight and avoids hydration errors
 * from loading provider dependencies before the browser session exists.
 */
export function ClientRoleProvider({ children }: ClientRoleProviderProps) {
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
    const interval = window.setInterval(checkSession, TOKEN_CHECK_INTERVAL_MS);

    const handleStorage = (event: StorageEvent) => {
      if (event.key === 'taxpoynt_secure_tokens' || event.key === 'taxpoynt_token') {
        checkSession();
      }
    };

    window.addEventListener('storage', handleStorage);

    return () => {
      window.clearInterval(interval);
      window.removeEventListener('storage', handleStorage);
    };
  }, []);

  if (!hasSession) {
    return <>{children}</>;
  }

  return <CombinedRoleProvider>{children}</CombinedRoleProvider>;
}

export default ClientRoleProvider;
