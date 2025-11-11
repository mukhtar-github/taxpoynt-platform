'use client';

import React, { Suspense, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ERPOnboarding } from '../../../../si_interface/workflows/erp_onboarding';
import { getPostOnboardingUrl } from '../../../../shared_components/utils/dashboardRouting';

const VALID_STEP_IDS = new Set([
  'organization_setup',
  'compliance_verification',
  'erp_selection',
  'erp_configuration',
  'data_mapping',
  'testing_validation',
  'compliance_setup',
  'production_deployment',
  'training_handover',
]);

const STEP_ALIAS_MAP: Record<string, string> = {
  organization: 'organization_setup',
  compliance: 'compliance_verification',
  erp: 'erp_selection',
  configuration: 'erp_configuration',
  mapping: 'data_mapping',
  testing: 'testing_validation',
  validation: 'testing_validation',
  deployment: 'production_deployment',
  production: 'production_deployment',
  training: 'training_handover',
  handover: 'training_handover',
};

const resolveStepId = (value?: string | null): string | undefined => {
  if (!value) {
    return undefined;
  }

  const normalized = value.toLowerCase().replace(/[\s-]+/g, '_');
  const resolved = STEP_ALIAS_MAP[normalized] ?? normalized;
  return VALID_STEP_IDS.has(resolved) ? resolved : undefined;
};

const SIIntegrationSetupContent: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const initialStepId = useMemo(
    () => resolveStepId(searchParams?.get('step')),
    [searchParams]
  );

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
          initialStepId={initialStepId}
        />
      </div>
    </div>
  );
};

const SIIntegrationSetupFallback: React.FC = () => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-indigo-600" />
  </div>
);

export default function SIIntegrationSetupPage() {
  return (
    <Suspense fallback={<SIIntegrationSetupFallback />}>
      <SIIntegrationSetupContent />
    </Suspense>
  );
}
