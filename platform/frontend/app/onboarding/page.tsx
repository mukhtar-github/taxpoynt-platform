'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import UnifiedOnboardingWizardComponent, {
  ServicePackage,
} from '../../shared_components/onboarding/UnifiedOnboardingWizard';
import { authService } from '../../shared_components/services/auth';

const OnboardingPage: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [initialService, setInitialService] = useState<ServicePackage | null>(null);
  const [defaultStep, setDefaultStep] = useState<string | undefined>(undefined);

  const normalizeServicePackage = (value?: string | null): ServicePackage | null => {
    if (!value) return null;
    if (value === 'si' || value === 'app' || value === 'hybrid') {
      return value;
    }
    return null;
  };

  useEffect(() => {
    const user = authService.getStoredUser();
    if (!authService.isAuthenticated() || !user) {
      router.push('/auth/signin');
      return;
    }

    const serviceParam = searchParams.get('service');
    const normalizedParam = normalizeServicePackage(serviceParam);
    const userService = normalizeServicePackage(user.service_package);
    setInitialService(normalizedParam ?? userService ?? null);

    const stepParam = searchParams.get('step');
    if (stepParam) {
      setDefaultStep(stepParam);
    }

    setIsLoading(false);
  }, [router, searchParams]);

  const handleComplete = (service: ServicePackage) => {
    switch (service) {
      case 'si':
        router.push('/dashboard/si');
        break;
      case 'app':
        router.push('/dashboard/app');
        break;
      case 'hybrid':
      default:
        router.push('/dashboard/hybrid');
        break;
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
          <p className="text-sm text-gray-600">Preparing your onboarding experience…</p>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-100 p-6">
      <div className="mx-auto max-w-4xl">
        <UnifiedOnboardingWizardComponent
          initialService={initialService}
          defaultStep={defaultStep}
          onComplete={handleComplete}
        />
      </div>
    </main>
  );
};

export default OnboardingPage;
