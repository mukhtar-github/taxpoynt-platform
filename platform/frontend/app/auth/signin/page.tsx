'use client';

import React, { Suspense, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { EnhancedSignInPage } from '../../../business_interface/auth/EnhancedSignInPage';
import { authService } from '../../../shared_components/services/auth';
import { onboardingApi } from '../../../shared_components/services/onboardingApi';
import type { OnboardingState } from '../../../shared_components/services/onboardingApi';

type ServicePackage = 'si' | 'app' | 'hybrid';

const isValidService = (value: string | null | undefined): value is ServicePackage =>
  value === 'si' || value === 'app' || value === 'hybrid';

const SignInPageContent: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const handleSignIn = async (credentials: { email: string; password: string; rememberMe?: boolean }) => {
    setIsLoading(true);
    setError('');

    try {
      const rememberPreference = Boolean(credentials.rememberMe);
      const response = await authService.login({
        email: credentials.email,
        password: credentials.password,
        remember_me: rememberPreference
      });

      // Get user role and redirect to appropriate dashboard
      const userRole = response.user.role;
      const userService = response.user.service_package;
      const requestedService = searchParams.get('service');
      const resolvedService: ServicePackage = isValidService(requestedService)
        ? requestedService
        : isValidService(userService)
        ? userService
        : 'si';

      const nextParam = searchParams.get('next');
      let shouldRedirectToOnboarding = !nextParam;

      if (shouldRedirectToOnboarding) {
        try {
          const onboardingState: OnboardingState | null = await onboardingApi.getOnboardingState();

          if (onboardingState) {
            const completedSteps = Array.isArray(onboardingState.completed_steps)
              ? onboardingState.completed_steps
              : [];
            const hasCompletedFlag = completedSteps.includes('onboarding_complete');
            const isComplete =
              typeof onboardingState.is_complete === 'boolean'
                ? onboardingState.is_complete
                : hasCompletedFlag;

            shouldRedirectToOnboarding = !isComplete;
          } else {
            // No state yet; treat as not onboarded
            shouldRedirectToOnboarding = true;
          }
        } catch (error) {
          console.warn('Failed to load onboarding state during sign-in:', error);
          // API not available or forbidden for this role; default to onboarding flow for first-run experience
          shouldRedirectToOnboarding = true;
        }
      }

      if (nextParam) {
        router.push(nextParam);
        return;
      }

      if (shouldRedirectToOnboarding) {
        router.push(`/onboarding?service=${resolvedService}`);
        return;
      }

      switch (userRole) {
        case 'system_integrator':
          router.push('/dashboard/si');
          break;
        case 'access_point_provider':
          router.push('/dashboard/app');
          break;
        case 'hybrid_user':
          router.push('/dashboard/hybrid');
          break;
        default:
          router.push('/dashboard');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign in failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <EnhancedSignInPage 
      onSignIn={handleSignIn}
      isLoading={isLoading}
      error={error}
    />
  );
};

const SignInPageFallback: React.FC = () => (
  <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
  </div>
);

export default function SignInPageWrapper() {
  return (
    <Suspense fallback={<SignInPageFallback />}>
      <SignInPageContent />
    </Suspense>
  );
}
