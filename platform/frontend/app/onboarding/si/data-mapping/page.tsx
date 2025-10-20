'use client';

import React, { useCallback, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import DataMapping from '../../../../si_interface/pages/data_mapping';
import { useUserContext } from '../../../../shared_components/hooks/useUserContext';
import { OnboardingStateManager } from '../../../../shared_components/onboarding/ServiceOnboardingRouter';

export default function SIDataMappingPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isAuthenticated, isSystemIntegrator, isLoading, organizationId } = useUserContext({
    requireAuth: true,
  });
  const hasMarkedInitialStep = useRef(false);

  useEffect(() => {
    if (isLoading) {
      return;
    }

    if (!isAuthenticated) {
      router.push('/auth/signin');
      return;
    }

    if (!isSystemIntegrator()) {
      router.push('/dashboard');
      return;
    }

    if (user && !hasMarkedInitialStep.current) {
      hasMarkedInitialStep.current = true;
      void OnboardingStateManager.updateStep(user.id, 'data_mapping');
    }
  }, [isAuthenticated, isLoading, isSystemIntegrator, router, user]);

  if (isLoading || !user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-indigo-600" />
      </div>
    );
  }

  const systemId = searchParams?.get('system') || undefined;

  const handleResetSelection = useCallback(() => {
    router.replace('/onboarding/si/data-mapping');
  }, [router]);

  const handleMappingComplete = useCallback(() => {
    if (!user?.id) {
      return;
    }

    void (async () => {
      try {
        await OnboardingStateManager.updateStep(user.id, 'data_mapping', true);
        await OnboardingStateManager.updateStep(user.id, 'testing_validation');
      } catch (error) {
        console.warn('Failed to sync onboarding step after data mapping:', error);
      } finally {
        if (typeof window !== 'undefined') {
          const payload = {
            step: 'data_mapping',
            nextStep: 'testing_validation',
            timestamp: Date.now()
          };
          sessionStorage.setItem('taxpoynt_erp_onboarding_step_completed', JSON.stringify(payload));
          window.dispatchEvent(new CustomEvent('taxpoynt:onboarding-step-completed', { detail: payload }));
        }
      }
    })();
  }, [user]);

  return (
    <DataMapping
      systemId={systemId}
      organizationId={organizationId ?? undefined}
      onResetSelection={handleResetSelection}
      onMappingComplete={handleMappingComplete}
    />
  );
}
