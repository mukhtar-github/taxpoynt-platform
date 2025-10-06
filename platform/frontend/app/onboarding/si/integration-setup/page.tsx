'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ERPOnboarding } from '../../../../si_interface/workflows/erp_onboarding';
import { getPostOnboardingUrl } from '../../../../shared_components/utils/dashboardRouting';

export default function SIIntegrationSetupPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const handleOnboardingComplete = async (onboardingData: Record<string, unknown>) => {
    setIsLoading(true);
    
    try {
      // Save onboarding data to user profile
      // This would typically call an API to update the onboarding status for the user
      console.log('SI Onboarding completed:', onboardingData);
      
      // Redirect to SI dashboard after successful onboarding
      const currentUser = { role: 'system_integrator' }; // Get from auth service in real implementation
      router.push(getPostOnboardingUrl(currentUser));
      
    } catch (error) {
      console.error('Onboarding failed:', error);
      // Handle error - maybe show a notification
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkipForNow = () => {
    // Allow user to skip onboarding and go directly to dashboard
    // They can complete it later from the dashboard
    const currentUser = { role: 'system_integrator' }; // Get from auth service in real implementation
    router.push(getPostOnboardingUrl(currentUser));
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            System Integrator Setup
          </h1>
          <p className="mt-2 text-lg text-gray-600">
            Configure your ERP integration and compliance settings
          </p>
        </div>
        
        <ERPOnboarding 
          onComplete={handleOnboardingComplete}
          onSkip={handleSkipForNow}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
