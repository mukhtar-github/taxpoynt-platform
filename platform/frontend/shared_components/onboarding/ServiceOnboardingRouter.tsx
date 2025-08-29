/**
 * Service Onboarding Router
 * =========================
 * Routes users to appropriate onboarding flows based on their service selection
 * and handles post-registration onboarding state management
 */

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '../services/auth';
import { Logo } from '../../design_system/components/Logo';

interface ServiceOnboardingRouterProps {
  userServicePackage: 'si' | 'app' | 'hybrid';
  userId: string;
  onboardingStep?: string;
}

interface OnboardingState {
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
        // Check if user has existing onboarding state
        const savedState = localStorage.getItem(`onboarding_${userId}`);
        let state: OnboardingState;

        if (savedState) {
          state = JSON.parse(savedState);
          console.log('📋 Resuming onboarding:', state);
        } else {
          // Initialize new onboarding
          state = {
            hasStarted: true,
            currentStep: 'service_introduction',
            completedSteps: [],
            lastActiveDate: new Date().toISOString()
          };
          localStorage.setItem(`onboarding_${userId}`, JSON.stringify(state));
          console.log('🚀 Starting new onboarding for service:', userServicePackage);
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
    const baseRoutes = {
      si: '/onboarding/si',
      app: '/onboarding/app',
      hybrid: '/onboarding/hybrid'
    };

    // Determine specific onboarding step based on service and current state
    switch (servicePackage) {
      case 'si':
        if (state.currentStep === 'service_introduction' || !state.hasStarted) {
          router.push(`${baseRoutes.si}/integration-choice`);
        } else if (state.currentStep === 'integration_choice') {
          router.push(`${baseRoutes.si}/integration-choice`);
        } else if (state.currentStep === 'business_systems_setup') {
          router.push(`${baseRoutes.si}/business-systems-setup`);
        } else if (state.currentStep === 'financial_systems_setup') {
          router.push(`${baseRoutes.si}/financial-systems-setup`);
        } else if (state.currentStep === 'reconciliation_setup') {
          router.push(`${baseRoutes.si}/reconciliation-setup`);
        } else if (state.completedSteps.includes('onboarding_complete')) {
          router.push('/dashboard/si');
        } else {
          // Default to integration choice
          router.push(`${baseRoutes.si}/integration-choice`);
        }
        break;

      case 'app':
        if (state.currentStep === 'service_introduction' || !state.hasStarted) {
          router.push(`${baseRoutes.app}/business-verification`);
        } else if (state.currentStep === 'invoice_processing_setup') {
          router.push(`${baseRoutes.app}/invoice-processing-setup`);
        } else if (state.completedSteps.includes('onboarding_complete')) {
          router.push('/dashboard/app');
        } else {
          // Default to business verification
          router.push(`${baseRoutes.app}/business-verification`);
        }
        break;

      case 'hybrid':
        if (state.currentStep === 'service_introduction' || !state.hasStarted) {
          router.push(`${baseRoutes.hybrid}/service-selection`);
        } else if (state.currentStep === 'combined_setup') {
          router.push(`${baseRoutes.hybrid}/combined-setup`);
        } else if (state.completedSteps.includes('onboarding_complete')) {
          router.push('/dashboard/hybrid');
        } else {
          // Default to service selection
          router.push(`${baseRoutes.hybrid}/service-selection`);
        }
        break;

      default:
        console.warn('⚠️ Unknown service package, redirecting to dashboard');
        router.push('/dashboard');
    }
  };

  const updateOnboardingState = (step: string, completed: boolean = false) => {
    if (!onboardingState || !userId) return;

    const updatedState: OnboardingState = {
      ...onboardingState,
      currentStep: step,
      completedSteps: completed 
        ? [...onboardingState.completedSteps, step]
        : onboardingState.completedSteps,
      lastActiveDate: new Date().toISOString()
    };

    setOnboardingState(updatedState);
    localStorage.setItem(`onboarding_${userId}`, JSON.stringify(updatedState));
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

// Utility functions for onboarding state management
export const OnboardingStateManager = {
  /**
   * Get current onboarding state for user
   */
  getOnboardingState: (userId: string): OnboardingState | null => {
    try {
      const saved = localStorage.getItem(`onboarding_${userId}`);
      return saved ? JSON.parse(saved) : null;
    } catch (error) {
      console.error('Failed to get onboarding state:', error);
      return null;
    }
  },

  /**
   * Update onboarding step
   */
  updateStep: (userId: string, step: string, completed: boolean = false): void => {
    try {
      const current = OnboardingStateManager.getOnboardingState(userId);
      if (!current) return;

      const updated: OnboardingState = {
        ...current,
        currentStep: step,
        completedSteps: completed 
          ? [...current.completedSteps, step]
          : current.completedSteps,
        lastActiveDate: new Date().toISOString()
      };

      localStorage.setItem(`onboarding_${userId}`, JSON.stringify(updated));
    } catch (error) {
      console.error('Failed to update onboarding state:', error);
    }
  },

  /**
   * Mark onboarding as complete
   */
  completeOnboarding: (userId: string): void => {
    OnboardingStateManager.updateStep(userId, 'onboarding_complete', true);
  },

  /**
   * Check if onboarding is complete
   */
  isOnboardingComplete: (userId: string): boolean => {
    const state = OnboardingStateManager.getOnboardingState(userId);
    return state?.completedSteps.includes('onboarding_complete') || false;
  },

  /**
   * Reset onboarding state (for testing or re-onboarding)
   */
  resetOnboarding: (userId: string): void => {
    localStorage.removeItem(`onboarding_${userId}`);
  }
};
