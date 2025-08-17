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
      // Use enhanced auth service with Axios
      const registrationData = {
        email: basicInfo.email,
        password: basicInfo.password,
        first_name: 'User', // Will be collected in onboarding flow
        last_name: 'Name',   // Will be collected in onboarding flow
        service_package: basicInfo.selectedRole,
        business_name: 'TBD', // Will be collected in onboarding flow
        business_type: 'TBD', // Will be collected in onboarding flow
        terms_accepted: true,
        privacy_accepted: true
      };

      const authResponse = await authService.register(registrationData);
      
      // Redirect to role-based dashboard using auth service helper
      const redirectUrl = authService.getDashboardRedirectUrl(authResponse.user.role);
      router.push(redirectUrl);
      
    } catch (err) {
      // Use auth service error handling for consistent user-friendly messages
      const errorMessage = authService.handleAuthError(err);
      setError(errorMessage);
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