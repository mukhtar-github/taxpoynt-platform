'use client';

/**
 * Service Onboarding Router
 * =========================
 * Routes users to appropriate onboarding flows based on their service selection
 * and handles post-registration onboarding state management
 */

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '../services/auth';
import { onboardingApi, OnboardingState } from '../services/onboardingApi';
import { onboardingStateQueue } from '../services/onboardingStateQueue';
import { Logo } from '../../design_system/components/Logo';

interface ServiceOnboardingRouterProps {
  userServicePackage: 'si' | 'app' | 'hybrid';
  userId: string;
  onboardingStep?: string;
}

interface LegacyOnboardingState {
  hasStarted: boolean;
  currentStep: string;
  completedSteps: string[];
  lastActiveDate: string;
}

export const ServiceOnboardingRouter: React.FC<ServiceOnboardingRouterProps> = ({
  userServicePackage,
  userId,
  onboardingStep
}) => {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [onboardingState, setOnboardingState] = useState<OnboardingState | null>(null);

  useEffect(() => {
    const initializeOnboarding = async () => {
      try {
        console.log('🚀 Initializing onboarding with backend sync...');

        if (!authService.isAuthenticated()) {
          console.warn('⚠️ Skipping onboarding init because user is not authenticated.');
          setIsLoading(false);
          router.push('/auth/signin');
          return;
        }
        
        // Try to get onboarding state from backend first, fallback to localStorage
        let state: OnboardingState | null = null;
        
        try {
          state = await onboardingApi.getOnboardingState();
          console.log('✅ Got onboarding state from backend:', state);
        } catch (backendError) {
          console.warn('⚠️ Backend unavailable, using localStorage fallback:', backendError);
          
          // Fallback to localStorage
          const savedState = localStorage.getItem(`onboarding_${userId}`);
          if (savedState) {
            const legacyState = JSON.parse(savedState) as LegacyOnboardingState;
            // Convert legacy format to new format
            state = {
              user_id: userId,
              current_step: legacyState.currentStep || 'service_introduction',
              completed_steps: legacyState.completedSteps || [],
              has_started: legacyState.hasStarted ?? true,
              is_complete: legacyState.completedSteps?.includes('onboarding_complete') ?? false,
              last_active_date: legacyState.lastActiveDate || new Date().toISOString(),
              metadata: { service_package: userServicePackage },
              created_at: legacyState.lastActiveDate || new Date().toISOString(),
              updated_at: legacyState.lastActiveDate || new Date().toISOString()
            };
            console.log('📋 Resuming onboarding from localStorage:', state);
          }
        }

        // If no state exists, initialize new onboarding
        if (!state) {
          try {
            await onboardingStateQueue.enqueue({
              step: 'service_introduction',
              completed: false,
              completedSteps: [],
              metadata: {
                service_package: userServicePackage,
                initialization_source: 'frontend'
              },
              userId,
              source: 'ServiceOnboardingRouter.initialize',
            });
            state = await onboardingApi.getOnboardingState();
            console.log('🚀 Started new onboarding:', state);
          } catch (updateError) {
            console.warn('⚠️ Failed to create backend state, using local fallback', updateError);
            // Complete fallback - create local state
            state = {
              user_id: userId,
              current_step: 'service_introduction',
              completed_steps: [],
              has_started: true,
              is_complete: false,
              last_active_date: new Date().toISOString(),
              metadata: { service_package: userServicePackage },
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            };
          }
        }

        setOnboardingState(state);

        // Route to appropriate onboarding flow
        await routeToOnboardingFlow(userServicePackage, state);

      } catch (error) {
        console.error('❌ Onboarding initialization failed:', error);
        // Fallback to dashboard
        router.push('/dashboard');
      } finally {
        setIsLoading(false);
      }
    };

    initializeOnboarding();
  }, [userServicePackage, userId, router]);

  const routeToOnboardingFlow = async (
    servicePackage: 'si' | 'app' | 'hybrid',
    state: OnboardingState
  ) => {
    const preCheckSteps = new Set(['registration', 'email_verification', 'terms_acceptance']);

    if (preCheckSteps.has(state.current_step)) {
      const storedUser = authService.getStoredUser();
      const email = storedUser?.email || (state.metadata?.email as string | undefined);
      const onboardingToken = state.metadata?.onboarding_token;
      const params = new URLSearchParams({ service: servicePackage });
      if (email) {
        params.set('email', email);
      }
      if (typeof onboardingToken === 'string') {
        params.set('onboarding_token', onboardingToken);
      }

      const nextByRole: Record<'si' | 'app' | 'hybrid', string> = {
        si: '/onboarding/si/integration-choice',
        app: '/onboarding/app/business-verification',
        hybrid: '/onboarding/hybrid/service-selection',
      };
      params.set('next', nextByRole[servicePackage]);

      if (state.current_step === 'registration') {
        router.push(`/auth/signup?${params.toString()}`);
        return;
      }

      router.push(`/auth/verify-email?${params.toString()}`);
      return;
    }

    if (state.completed_steps.includes('onboarding_complete')) {
      switch (servicePackage) {
        case 'si':
          router.push('/dashboard/si');
          return;
        case 'app':
          router.push('/dashboard/app');
          return;
        case 'hybrid':
        default:
          router.push('/dashboard/hybrid');
          return;
      }
    }

    const unifiedStep = mapLegacyStepToUnified(state.current_step, servicePackage);
    const query = new URLSearchParams({
      service: servicePackage,
      step: unifiedStep,
    });

    router.push(`/onboarding?${query.toString()}`);
  };

  const mapLegacyStepToUnified = (
    legacyStep: string,
    servicePackage: 'si' | 'app' | 'hybrid'
  ): string => {
    if (!legacyStep) {
      return servicePackage === 'si' && !onboardingState?.has_started
        ? 'service-selection'
        : 'company-profile';
    }

    switch (legacyStep) {
      case 'registration':
        return 'registration';
      case 'email_verification':
        return 'email_verification';
      case 'terms_acceptance':
        return 'terms_acceptance';
      case 'service_introduction':
      case 'integration_choice':
      case 'business_verification':
      case 'service_selection':
        return 'service-selection';
      case 'business_systems_setup':
      case 'financial_systems_setup':
      case 'invoice_processing_setup':
      case 'combined_setup':
        return 'service-configuration';
      case 'reconciliation_setup':
      case 'onboarding_review':
        return 'review';
      default:
        return 'company-profile';
    }
  };

  const updateOnboardingState = async (step: string, completed: boolean = false) => {
    if (!onboardingState || !userId) return;

    try {
      const completedSteps = completed
        ? Array.from(new Set([...onboardingState.completed_steps, step]))
        : onboardingState.completed_steps;

      await onboardingStateQueue.enqueue({
        step,
        completed,
        completedSteps,
        metadata: {
          ...onboardingState.metadata,
          step_updated_at: new Date().toISOString(),
        },
        userId,
        source: 'ServiceOnboardingRouter.update',
      });

      setOnboardingState((prev) =>
        prev
          ? {
              ...prev,
              current_step: step,
              completed_steps: completedSteps,
              last_active_date: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            }
          : prev,
      );
    } catch (error) {
      console.error('❌ Failed to queue onboarding state update:', error);
      const updatedState: OnboardingState = {
        ...onboardingState,
        current_step: step,
        completed_steps: completed
          ? Array.from(new Set([...onboardingState.completed_steps, step]))
          : onboardingState.completed_steps,
        last_active_date: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setOnboardingState(updatedState);
      localStorage.setItem(`onboarding_${userId}`, JSON.stringify(updatedState));
    }
  };

  const getServiceDisplayName = (servicePackage: string): string => {
    const names = {
      si: 'System Integration',
      app: 'Access Point Provider',
      hybrid: 'Hybrid Premium'
    };
    return names[servicePackage as keyof typeof names] || servicePackage.toUpperCase();
  };

  const getOnboardingMessage = (servicePackage: string): string => {
    const messages = {
      si: 'Setting up your system integration workspace...',
      app: 'Preparing your invoice processing environment...',
      hybrid: 'Configuring your premium hybrid solution...'
    };
    return messages[servicePackage as keyof typeof messages] || 'Setting up your workspace...';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto">
          <div className="mb-8">
            <Logo size="xl" variant="full" showTagline={true} />
          </div>
          
          <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8">
            <div className="mb-6">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">
                Welcome to {getServiceDisplayName(userServicePackage)}! 🎉
              </h2>
              <p className="text-gray-600 text-sm">
                {getOnboardingMessage(userServicePackage)}
              </p>
            </div>

            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center justify-center text-blue-800 text-sm">
                <span className="mr-2">⏱️</span>
                <span>Typical setup time: 5-15 minutes</span>
              </div>
            </div>
          </div>

          <div className="mt-6 text-xs text-gray-500">
            Your 7-day free trial is active
          </div>
        </div>
      </div>
    );
  }

  // This component handles routing, so it typically doesn't render content
  // Content is shown only during the loading state
  return null;
};

export default ServiceOnboardingRouter;

// Maintain legacy export for compatibility while delegating to the primary implementation.
export { OnboardingStateManager } from '../services/onboardingApi';
