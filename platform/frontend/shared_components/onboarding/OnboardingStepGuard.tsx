/**
 * Onboarding Step Guard
 * ====================
 * 
 * Component that guards onboarding steps and ensures users can only access
 * steps they're eligible for based on their progress. Provides automatic
 * redirects and resume functionality.
 * 
 * Features:
 * - Step eligibility validation
 * - Automatic redirect to correct step
 * - Resume interrupted sessions
 * - Prevent step skipping
 * - Handle step dependencies
 */

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AlertTriangle, ArrowLeft, ArrowRight, Clock } from 'lucide-react';
import { useUserContext } from '../hooks/useUserContext';
import { useOnboardingProgress } from '../hooks/useOnboardingProgress';
import { OnboardingResumeManager } from './OnboardingResumeManager';
import { LoadingSpinner } from '../loading/OnboardingLoadingStates';
import { UrlBuilder } from '../config/urlConfig';

interface StepGuardProps {
  currentStep: string;
  requiredRole?: 'si' | 'app' | 'hybrid';
  dependencies?: string[];
  allowSkip?: boolean;
  children: React.ReactNode;
  onStepValidated?: (isValid: boolean) => void;
}

interface StepValidationResult {
  isValid: boolean;
  canAccess: boolean;
  redirectTo?: string;
  reason?: string;
  showResume?: boolean;
  missingDependencies?: string[];
}

const STEP_HIERARCHY: Record<string, Record<string, number>> = {
  si: {
    'service_introduction': 0,
    'integration_choice': 1,
    'business_systems_setup': 2,
    'financial_systems_setup': 3,
    'banking_connected': 4,
    'reconciliation_setup': 5,
    'integration_setup': 6,
    'onboarding_complete': 7
  },
  app: {
    'service_introduction': 0,
    'business_verification': 1,
    'firs_integration_setup': 2,
    'compliance_settings': 3,
    'taxpayer_setup': 4,
    'onboarding_complete': 5
  },
  hybrid: {
    'service_introduction': 0,
    'service_selection': 1,
    'business_verification': 2,
    'integration_setup': 3,
    'compliance_setup': 4,
    'onboarding_complete': 5
  }
};

export const OnboardingStepGuard: React.FC<StepGuardProps> = ({
  currentStep,
  requiredRole,
  dependencies = [],
  allowSkip = false,
  children,
  onStepValidated
}) => {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: userLoading } = useUserContext();
  const { 
    progressState, 
    getStepStatus, 
    getNextStep, 
    canProgressToStep,
    updateProgress,
    isLoading: progressLoading 
  } = useOnboardingProgress();
  
  const [validationResult, setValidationResult] = useState<StepValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(true);
  const [showResumePrompt, setShowResumePrompt] = useState(false);
  const [hasRedirected, setHasRedirected] = useState(false);

  // Get user role for validation
  const getUserRole = (): 'si' | 'app' | 'hybrid' => {
    if (!user) return 'si';
    
    const roleMap: Record<string, 'si' | 'app' | 'hybrid'> = {
      'system_integrator': 'si',
      'access_point_provider': 'app',
      'hybrid_user': 'hybrid'
    };
    
    return roleMap[user.role] || 'si';
  };

  // Validate step access
  const validateStepAccess = React.useCallback((): StepValidationResult => {
    // Basic checks
    if (!user || !progressState) {
      return {
        isValid: false,
        canAccess: false,
        reason: 'User authentication or progress state not available'
      };
    }

    const userRole = getUserRole();
    
    // Check role requirement
    if (requiredRole && userRole !== requiredRole) {
      return {
        isValid: false,
        canAccess: false,
        redirectTo: UrlBuilder.dashboardUrl(userRole),
        reason: `This step is not available for ${userRole} users`
      };
    }

    // Check if onboarding is already complete
    if (progressState.isComplete && currentStep !== 'onboarding_complete') {
      return {
        isValid: false,
        canAccess: false,
        redirectTo: UrlBuilder.dashboardUrl(userRole),
        reason: 'Onboarding is already complete'
      };
    }

    // Check step dependencies
    const missingDependencies = dependencies.filter(dep => 
      !progressState.completedSteps.includes(dep)
    );
    
    if (missingDependencies.length > 0 && !allowSkip) {
      // Find the first missing dependency to redirect to
      const stepHierarchy = STEP_HIERARCHY[userRole] || {};
      const nextRequiredStep = missingDependencies
        .sort((a, b) => (stepHierarchy[a] || 0) - (stepHierarchy[b] || 0))[0];
      
      return {
        isValid: false,
        canAccess: false,
        redirectTo: UrlBuilder.onboardingStepUrl(userRole, nextRequiredStep),
        reason: `Missing required dependencies: ${missingDependencies.join(', ')}`,
        missingDependencies
      };
    }

    // Check if user is trying to access a step too far ahead
    const stepHierarchy = STEP_HIERARCHY[userRole] || {};
    const currentStepOrder = stepHierarchy[currentStep];
    const completedSteps = progressState.completedSteps;
    
    if (typeof currentStepOrder === 'number' && !allowSkip) {
      const maxCompletedOrder = Math.max(
        ...completedSteps
          .map(step => stepHierarchy[step])
          .filter(order => typeof order === 'number'),
        -1
      );
      
      // Allow access to next step or current step
      if (currentStepOrder > maxCompletedOrder + 1) {
        const nextStep = getNextStep();
        const redirectStep = nextStep || completedSteps[completedSteps.length - 1] || 'service_introduction';
        
        return {
          isValid: false,
          canAccess: false,
          redirectTo: UrlBuilder.onboardingStepUrl(userRole, redirectStep),
          reason: 'Cannot skip ahead in onboarding flow',
          showResume: true
        };
      }
    }

    // Check if user should be redirected to resume
    const stepStatus = getStepStatus(currentStep);
    if (stepStatus === 'completed' && currentStep !== progressState.currentStep) {
      const nextStep = getNextStep();
      if (nextStep && nextStep !== currentStep) {
        return {
          isValid: true,
          canAccess: true,
          redirectTo: UrlBuilder.onboardingStepUrl(userRole, nextStep),
          reason: 'Step already completed, redirecting to next step',
          showResume: true
        };
      }
    }

    // All validations passed
    return {
      isValid: true,
      canAccess: true
    };
  }, [user, progressState, currentStep, requiredRole, dependencies, allowSkip, getNextStep, getStepStatus]);

  // Run validation when dependencies change
  useEffect(() => {
    if (userLoading || progressLoading) {
      setIsValidating(true);
      return;
    }

    const result = validateStepAccess();
    setValidationResult(result);
    setIsValidating(false);

    // Notify parent component
    if (onStepValidated) {
      onStepValidated(result.isValid);
    }

    // Handle redirects
    if (result.redirectTo && !hasRedirected) {
      if (result.showResume) {
        setShowResumePrompt(true);
      } else {
        setHasRedirected(true);
        router.push(result.redirectTo);
      }
    }

    // Update progress if user is accessing a valid step
    if (result.isValid && result.canAccess && progressState && currentStep !== progressState.currentStep) {
      updateProgress(currentStep, false);
    }
  }, [
    userLoading,
    progressLoading,
    validateStepAccess,
    onStepValidated,
    hasRedirected,
    router,
    progressState,
    currentStep,
    updateProgress
  ]);

  // Handle resume from prompt
  const handleResumeFromPrompt = (step: string) => {
    setShowResumePrompt(false);
    setHasRedirected(true);
    router.push(UrlBuilder.onboardingStepUrl(getUserRole(), step));
  };

  // Handle skip resume
  const handleSkipResume = () => {
    setShowResumePrompt(false);
    if (validationResult?.redirectTo) {
      setHasRedirected(true);
      router.push(validationResult.redirectTo);
    }
  };

  // Show loading state
  if (isValidating || userLoading || progressLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <LoadingSpinner 
          type="page"
          message="Validating step access..."
          size="lg"
        />
      </div>
    );
  }

  // Show resume prompt
  if (showResumePrompt) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <OnboardingResumeManager
          onResume={handleResumeFromPrompt}
          onSkip={handleSkipResume}
          className="max-w-md w-full"
        />
      </div>
    );
  }

  // Show access denied
  if (!validationResult?.canAccess) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white border border-red-200 rounded-lg p-6 text-center">
          <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="h-6 w-6 text-red-600" />
          </div>
          
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            Access Restricted
          </h2>
          
          <p className="text-sm text-gray-600 mb-6">
            {validationResult?.reason || 'You cannot access this step at this time.'}
          </p>

          {validationResult?.missingDependencies && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6 text-left">
              <h3 className="text-sm font-medium text-yellow-900 mb-2">
                Complete these steps first:
              </h3>
              <ul className="text-sm text-yellow-800 space-y-1">
                {validationResult.missingDependencies.map((dep, index) => (
                  <li key={index} className="flex items-center">
                    <Clock className="h-4 w-4 mr-2" />
                    {dep.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          <div className="flex space-x-3">
            <button
              onClick={() => router.back()}
              className="flex-1 bg-gray-100 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-200 transition-colors flex items-center justify-center space-x-2"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Go Back</span>
            </button>
            
            {validationResult?.redirectTo && (
              <button
                onClick={() => router.push(validationResult.redirectTo!)}
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2"
              >
                <span>Continue</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Render children if access is granted
  return <>{children}</>;
};

export default OnboardingStepGuard;
