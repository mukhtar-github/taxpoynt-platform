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
            state = await onboardingApi.updateOnboardingState({
              current_step: 'service_introduction',
              completed_steps: [],
              metadata: { 
                service_package: userServicePackage,
                initialization_source: 'frontend'
              }
            });
            console.log('🚀 Started new onboarding:', state);
          } catch (updateError) {
            console.warn('⚠️ Failed to create backend state, using local fallback');
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
        ? [...onboardingState.completed_steps, step]
        : onboardingState.completed_steps;

      const updatedState = await onboardingApi.updateOnboardingState({
        current_step: step,
        completed_steps: completedSteps,
        metadata: {
          ...onboardingState.metadata,
          step_updated_at: new Date().toISOString()
        }
      });

      setOnboardingState(updatedState);
      console.log('✅ Onboarding state updated:', updatedState);
    } catch (error) {
      console.error('❌ Failed to update onboarding state:', error);
      
      // Fallback to localStorage update
      const updatedState: OnboardingState = {
        ...onboardingState,
        current_step: step,
        completed_steps: completed 
          ? [...onboardingState.completed_steps, step]
          : onboardingState.completed_steps,
        last_active_date: new Date().toISOString(),
        updated_at: new Date().toISOString()
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

// Legacy utility functions for backward compatibility
// New code should use onboardingApi and OnboardingStateManager from services/onboardingApi.ts
export const OnboardingStateManager = {
  /**
   * Get current onboarding state for user (with backend sync)
   * @deprecated Use onboardingApi.getOnboardingState() instead
   */
  getOnboardingState: async (userId: string): Promise<OnboardingState | null> => {
    try {
      return await onboardingApi.getOnboardingState();
    } catch (error) {
      console.error('Failed to get onboarding state:', error);
      // Fallback to localStorage
      try {
        const saved = localStorage.getItem(`onboarding_${userId}`);
        if (!saved) return null;
        
        const legacy = JSON.parse(saved);
        // Convert legacy format to new format
        return {
          user_id: userId,
          current_step: legacy.currentStep || 'service_introduction',
          completed_steps: legacy.completedSteps || [],
          has_started: legacy.hasStarted ?? true,
          is_complete: legacy.completedSteps?.includes('onboarding_complete') ?? false,
          last_active_date: legacy.lastActiveDate || new Date().toISOString(),
          metadata: legacy.metadata || {},
          created_at: legacy.lastActiveDate || new Date().toISOString(),
          updated_at: legacy.lastActiveDate || new Date().toISOString()
        };
      } catch (legacyError) {
        console.error('Failed to get legacy onboarding state:', legacyError);
        return null;
      }
    }
  },

  /**
   * Update onboarding step (with backend sync)
   * @deprecated Use onboardingApi.updateOnboardingState() instead
   */
  updateStep: async (userId: string, step: string, completed: boolean = false): Promise<void> => {
    try {
      const current = await onboardingApi.getOnboardingState();
      const completedSteps = completed && current
        ? [...current.completed_steps, step]
        : current?.completed_steps || [];

      await onboardingApi.updateOnboardingState({
        current_step: step,
        completed_steps: completedSteps,
        metadata: { step_updated_at: new Date().toISOString() }
      });
    } catch (error) {
      console.error('Failed to update onboarding step:', error);
      // Fallback to localStorage
      try {
        const saved = localStorage.getItem(`onboarding_${userId}`);
        const current = saved ? JSON.parse(saved) : null;
        
        if (current) {
          const updated = {
            ...current,
            currentStep: step,
            completedSteps: completed 
              ? [...(current.completedSteps || []), step]
              : current.completedSteps || [],
            lastActiveDate: new Date().toISOString()
          };
          localStorage.setItem(`onboarding_${userId}`, JSON.stringify(updated));
        }
      } catch (legacyError) {
        console.error('Failed to update legacy onboarding state:', legacyError);
      }
    }
  },

  /**
   * Mark onboarding as complete (with backend sync)
   * @deprecated Use onboardingApi.completeOnboarding() instead
   */
  completeOnboarding: async (userId: string): Promise<void> => {
    try {
      await onboardingApi.completeOnboarding({
        completion_source: 'legacy_manager',
        completed_at: new Date().toISOString()
      });
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
      // Fallback to updateStep
      await OnboardingStateManager.updateStep(userId, 'onboarding_complete', true);
    }
  },

  /**
   * Check if onboarding is complete (with backend sync)
   * @deprecated Use onboardingApi.getOnboardingState() instead
   */
  isOnboardingComplete: async (userId: string): Promise<boolean> => {
    try {
      const state = await onboardingApi.getOnboardingState();
      return state?.is_complete || false;
    } catch (error) {
      console.error('Failed to check onboarding completion:', error);
      // Fallback to localStorage
      try {
        const saved = localStorage.getItem(`onboarding_${userId}`);
        const state = saved ? JSON.parse(saved) : null;
        return state?.completedSteps?.includes('onboarding_complete') || false;
      } catch (legacyError) {
        console.error('Failed to check legacy onboarding completion:', legacyError);
        return false;
      }
    }
  },

  /**
   * Reset onboarding state (with backend sync)
   * @deprecated Use onboardingApi.resetOnboardingState() instead
   */
  resetOnboarding: async (userId: string): Promise<void> => {
    try {
      await onboardingApi.resetOnboardingState();
    } catch (error) {
      console.error('Failed to reset onboarding state:', error);
      // Fallback to localStorage
      localStorage.removeItem(`onboarding_${userId}`);
    }
  }
};
