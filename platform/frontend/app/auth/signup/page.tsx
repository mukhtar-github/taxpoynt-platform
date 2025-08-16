'use client';

import React, { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { SignUpPage } from '../../../business_interface/auth/SignUpPage';
import { authService } from '../../../shared_components/services/auth';

function SignUpPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const handleContinueToRegistration = async (basicInfo: {
    email: string;
    password: string;
    selectedRole: 'si' | 'app' | 'hybrid';
  }) => {
    setIsLoading(true);
    setError('');

    try {
      // Map frontend roles to backend roles
      const roleMapping = {
        'si': 'system_integrator',
        'app': 'access_point_provider', 
        'hybrid': 'hybrid_user'
      };

      const response = await fetch('https://taxpoynt-platform-production.up.railway.app/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: basicInfo.email,
          password: basicInfo.password,
          first_name: 'User', // Will be collected in onboarding flow
          last_name: 'Name',   // Will be collected in onboarding flow
          role: roleMapping[basicInfo.selectedRole]
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Registration failed');
      }

      const data = await response.json();
      
      // Store auth data
      localStorage.setItem('taxpoynt_token', data.access_token);
      localStorage.setItem('taxpoynt_user', JSON.stringify(data.user));
      
      // Redirect to role-based dashboard
      switch (basicInfo.selectedRole) {
        case 'si':
          router.push('/dashboard/si');
          break;
        case 'app':
          router.push('/dashboard/app');
          break;
        case 'hybrid':
          router.push('/dashboard/hybrid');
          break;
        default:
          router.push('/dashboard');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SignUpPage 
      onContinueToRegistration={handleContinueToRegistration}
      isLoading={isLoading}
      error={error}
    />
  );
}

export default function SignUpPageWrapper() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <SignUpPageContent />
    </Suspense>
  );
}