/**
 * Main Sign Up Page - Now Using Streamlined Registration
 * =====================================================
 * Updated to use the new streamlined registration flow as single source of truth
 * This replaces the old complex registration with our improved 4-step process
 */

'use client';

import React, { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { StreamlinedRegistration } from '../../../business_interface/auth/StreamlinedRegistration';
import { authService } from '../../../shared_components/services/auth';
import { ServiceOnboardingRouter } from '../../../shared_components/onboarding/ServiceOnboardingRouter';
import { secureLogger } from '../../../shared_components/utils/secureLogger';

interface StreamlinedRegistrationData {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  business_name: string;
  service_package: 'si' | 'app' | 'hybrid';
  terms_accepted: boolean;
  privacy_accepted: boolean;
  trial_started: boolean;
  trial_start_date: string;
}

function SignUpPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [registrationComplete, setRegistrationComplete] = useState(false);
  const [userData, setUserData] = useState<any>(null);

  const handleCompleteRegistration = async (registrationData: StreamlinedRegistrationData) => {
    setIsLoading(true);
    setError('');

    try {
      secureLogger.userAction('Starting streamlined registration', { 
        service_package: registrationData.service_package,
        terms_accepted: registrationData.terms_accepted,
        privacy_accepted: registrationData.privacy_accepted,
        trial_started: registrationData.trial_started
      });

      // Transform streamlined data to full registration format expected by backend
      const fullRegistrationData = {
        // Required fields only - optional fields omitted to avoid validation issues
        email: registrationData.email,
        password: registrationData.password,
        first_name: registrationData.first_name,
        last_name: registrationData.last_name,
        service_package: registrationData.service_package,
        business_name: registrationData.business_name,
        terms_accepted: registrationData.terms_accepted,
        privacy_accepted: registrationData.privacy_accepted,
        marketing_consent: false, // Default to false, can be updated later
        // Note: Optional fields like business_type, phone, tin, etc. are omitted
        // to avoid backend validation issues and will be collected during onboarding
      };

      secureLogger.formData('Registration data prepared for backend', {
        service_package: fullRegistrationData.service_package,
        terms_accepted: fullRegistrationData.terms_accepted,
        privacy_accepted: fullRegistrationData.privacy_accepted
      });

      // Register with complete data using auth service
      const authResponse = await authService.register(fullRegistrationData);
      
      secureLogger.success('Registration successful', {
        service_package: authResponse.user.service_package,
        trial_active: registrationData.trial_started
      });

      // Set completion state to trigger onboarding routing
      setUserData(authResponse.user);
      setRegistrationComplete(true);
      
    } catch (err) {
      secureLogger.error('Registration failed', err);
      const errorMessage = authService.handleAuthError(err);
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // If registration is complete, show onboarding router
  if (registrationComplete && userData) {
    return (
      <ServiceOnboardingRouter
        userServicePackage={userData.service_package}
        userId={userData.id}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <StreamlinedRegistration 
        onCompleteRegistration={handleCompleteRegistration}
        isLoading={isLoading}
        error={error}
      />
    </div>
  );
}

export default function SignUpPageWrapper() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    }>
      <SignUpPageContent />
    </Suspense>
  );
}