'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { SignInPage } from '../../../business_interface/auth/SignInPage';
import { authService } from '../../../shared_components/services/auth';

export default function SignInPageWrapper() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const handleSignIn = async (credentials: { email: string; password: string }) => {
    setIsLoading(true);
    setError('');

    try {
      const response = await authService.login({
        email: credentials.email,
        password: credentials.password,
        remember_me: false
      });

      // Get user role and redirect to appropriate dashboard
      const userRole = response.user.role;
      
      switch (userRole) {
        case 'system_integrator':
          router.push('/dashboard/si');
          break;
        case 'access_point_provider':
          router.push('/dashboard/app');
          break;
        case 'hybrid_user':
          router.push('/dashboard/hybrid');
          break;
        default:
          router.push('/dashboard');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign in failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SignInPage 
      onSignIn={handleSignIn}
      isLoading={isLoading}
      error={error}
    />
  );
}