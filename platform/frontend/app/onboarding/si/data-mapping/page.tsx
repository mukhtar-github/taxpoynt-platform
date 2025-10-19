'use client';

import React, { useEffect } from 'react';
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

    if (user) {
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

  return <DataMapping systemId={systemId} organizationId={organizationId ?? undefined} />;
}
