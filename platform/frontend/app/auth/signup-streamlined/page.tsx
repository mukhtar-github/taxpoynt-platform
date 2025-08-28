/**
 * Streamlined Sign Up Page
 * ========================
 * New improved registration flow with simplified steps and better UX
 * Uses the streamlined registration component for faster onboarding
 */

'use client';

import React, { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { StreamlinedRegistration } from '../../../business_interface/auth/StreamlinedRegistration';
import { authService } from '../../../shared_components/services/auth';
import { ServiceOnboardingRouter } from '../../../shared_components/onboarding/ServiceOnboardingRouter';

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

function StreamlinedSignUpPageContent() {
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
      console.log('🚀 Processing streamlined registration:', {
        ...registrationData,
        password: '***hidden***'
      });

      // Transform streamlined data to full registration format expected by backend
      const fullRegistrationData = {
        email: registrationData.email,
        password: registrationData.password,
        first_name: registrationData.first_name,
        last_name: registrationData.last_name,
        phone: '', // Will be collected during onboarding
        service_package: registrationData.service_package,
        business_name: registrationData.business_name,
        business_type: '', // Will be collected during onboarding
        tin: '', // Will be collected during onboarding
        rc_number: '', // Will be collected during onboarding
        address: '', // Will be collected during onboarding
        state: '', // Will be collected during onboarding
        lga: '', // Will be collected during onboarding
        terms_accepted: registrationData.terms_accepted,
        privacy_accepted: registrationData.privacy_accepted,
        marketing_consent: false, // Default to false, can be updated later
        trial_started: registrationData.trial_started,
        trial_start_date: registrationData.trial_start_date
      };

      // Register with complete data using auth service
      const authResponse = await authService.register(fullRegistrationData);
      
      console.log('✅ Streamlined registration successful:', {
        user: authResponse.user.email,
        service_package: authResponse.user.service_package,
        trial_active: registrationData.trial_started
      });

      // Set completion state to trigger onboarding routing
      setUserData(authResponse.user);
      setRegistrationComplete(true);
      
    } catch (err) {
      console.error('❌ Streamlined registration failed:', err);
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

export default function StreamlinedSignUpPageWrapper() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    }>
      <StreamlinedSignUpPageContent />
    </Suspense>
  );
}
