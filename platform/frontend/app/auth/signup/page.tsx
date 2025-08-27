'use client';

import React, { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { EnhancedConsentIntegratedRegistration } from '../../../business_interface/auth/EnhancedConsentIntegratedRegistration';
import { authService } from '../../../shared_components/services/auth';

function SignUpPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const handleCompleteRegistration = async (registrationData: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    phone?: string;
    service_package: string;
    business_name: string;
    business_type: string;
    tin?: string;
    rc_number?: string;
    address?: string;
    state?: string;
    lga?: string;
    terms_accepted: boolean;
    privacy_accepted: boolean;
    marketing_consent?: boolean;
    consents?: Record<string, any>;
  }) => {
    setIsLoading(true);
    setError('');

    try {
      // Validate required consent
      if (!registrationData.terms_accepted) {
        throw new Error('Terms and conditions must be accepted');
      }
      if (!registrationData.privacy_accepted) {
        throw new Error('Privacy policy must be accepted');
      }

      // Register with complete data using sophisticated auth system
      const authResponse = await authService.register(registrationData);
      
      // Redirect to appropriate onboarding based on service selection
      if (registrationData.service_package === 'si') {
        router.push('/onboarding/si/service-selection');
      } else if (registrationData.service_package === 'app') {
        router.push('/onboarding/app/invoice-processing-setup');
      } else if (registrationData.service_package === 'hybrid') {
        router.push('/onboarding/hybrid/service-selection');
      } else {
        // Default to dashboard if no specific onboarding needed
        const redirectUrl = authService.getDashboardRedirectUrl(authResponse.user.role);
        router.push(redirectUrl);
      }
      
    } catch (err) {
      // Use auth service error handling for consistent user-friendly messages
      const errorMessage = authService.handleAuthError(err);
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <EnhancedConsentIntegratedRegistration 
      onCompleteRegistration={handleCompleteRegistration}
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