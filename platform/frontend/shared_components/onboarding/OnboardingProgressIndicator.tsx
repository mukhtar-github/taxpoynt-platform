/**
 * Onboarding Progress Indicator
 * =============================
 * 
 * Visual progress indicator for onboarding flows across all user roles.
 * Provides step-by-step progress tracking with completion status and time estimates.
 * 
 * Features:
 * - Role-specific step configurations (SI, APP, Hybrid)
 * - Visual progress bar with step indicators
 * - Time estimation and completion tracking
 * - Responsive design with accessibility support
 * - Loading states and transitions
 */

import React, { useMemo } from 'react';
import { CheckCircle, Circle, Clock, ArrowRight, AlertCircle } from 'lucide-react';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  estimatedMinutes: number;
  isRequired: boolean;
  dependencies?: string[];
}

interface OnboardingProgressProps {
  currentStep: string | number;
  completedSteps: string[];
  userRole: 'si' | 'app' | 'hybrid';
  isLoading?: boolean;
  showTimeEstimate?: boolean;
  showRemainingTime?: boolean;
  compact?: boolean;
  mobileOptimized?: boolean;
  className?: string;
}

// Role-specific onboarding step configurations
const ONBOARDING_STEPS: Record<string, OnboardingStep[]> = {
  si: [
    {
      id: 'service_introduction',
      title: 'Welcome to TaxPoynt SI',
      description: 'Introduction to System Integrator services',
      estimatedMinutes: 2,
      isRequired: true
    },
    {
      id: 'integration_choice',
      title: 'Choose Integration Type',
      description: 'Select your preferred integration approach',
      estimatedMinutes: 3,
      isRequired: true
    },
    {
      id: 'business_systems_setup',
      title: 'Business Systems Setup',
      description: 'Configure your business management systems',
      estimatedMinutes: 8,
      isRequired: true,
      dependencies: ['integration_choice']
    },
    {
      id: 'financial_systems_setup',
      title: 'Financial Systems Setup',
      description: 'Connect your financial and banking systems',
      estimatedMinutes: 5,
      isRequired: true,
      dependencies: ['business_systems_setup']
    },
    {
      id: 'banking_connected',
      title: 'Banking Connection',
      description: 'Secure connection to your bank accounts',
      estimatedMinutes: 7,
      isRequired: true,
      dependencies: ['financial_systems_setup']
    },
    {
      id: 'reconciliation_setup',
      title: 'Reconciliation Setup',
      description: 'Configure automatic transaction reconciliation',
      estimatedMinutes: 6,
      isRequired: false,
      dependencies: ['banking_connected']
    },
    {
      id: 'integration_setup',
      title: 'Complete Integration',
      description: 'Finalize your system integration setup',
      estimatedMinutes: 4,
      isRequired: true,
      dependencies: ['banking_connected']
    },
    {
      id: 'onboarding_complete',
      title: 'Setup Complete',
      description: 'Your SI dashboard is ready to use',
      estimatedMinutes: 1,
      isRequired: true,
      dependencies: ['integration_setup']
    }
  ],
  app: [
    {
      id: 'service_introduction',
      title: 'Welcome to TaxPoynt APP',
      description: 'Introduction to Access Point Provider services',
      estimatedMinutes: 2,
      isRequired: true
    },
    {
      id: 'business_verification',
      title: 'Business Verification',
      description: 'Verify your business details and credentials',
      estimatedMinutes: 10,
      isRequired: true
    },
    {
      id: 'firs_integration_setup',
      title: 'FIRS Integration',
      description: 'Configure FIRS e-invoicing integration',
      estimatedMinutes: 12,
      isRequired: true,
      dependencies: ['business_verification']
    },
    {
      id: 'compliance_settings',
      title: 'Compliance Configuration',
      description: 'Set up compliance rules and validation',
      estimatedMinutes: 8,
      isRequired: true,
      dependencies: ['firs_integration_setup']
    },
    {
      id: 'taxpayer_setup',
      title: 'Taxpayer Management',
      description: 'Configure taxpayer onboarding settings',
      estimatedMinutes: 6,
      isRequired: false,
      dependencies: ['compliance_settings']
    },
    {
      id: 'onboarding_complete',
      title: 'Setup Complete',
      description: 'Your APP dashboard is ready to use',
      estimatedMinutes: 1,
      isRequired: true,
      dependencies: ['compliance_settings']
    }
  ],
  hybrid: [
    {
      id: 'service_introduction',
      title: 'Welcome to TaxPoynt Hybrid',
      description: 'Introduction to combined SI and APP services',
      estimatedMinutes: 3,
      isRequired: true
    },
    {
      id: 'service_selection',
      title: 'Service Configuration',
      description: 'Choose which services to enable',
      estimatedMinutes: 5,
      isRequired: true
    },
    {
      id: 'business_verification',
      title: 'Business Verification',
      description: 'Verify business details for both services',
      estimatedMinutes: 12,
      isRequired: true,
      dependencies: ['service_selection']
    },
    {
      id: 'integration_setup',
      title: 'System Integration',
      description: 'Configure business and financial systems',
      estimatedMinutes: 15,
      isRequired: true,
      dependencies: ['business_verification']
    },
    {
      id: 'compliance_setup',
      title: 'Compliance Configuration',
      description: 'Set up FIRS compliance and validation',
      estimatedMinutes: 10,
      isRequired: true,
      dependencies: ['integration_setup']
    },
    {
      id: 'onboarding_complete',
      title: 'Setup Complete',
      description: 'Your hybrid dashboard is ready to use',
      estimatedMinutes: 1,
      isRequired: true,
      dependencies: ['compliance_setup']
    }
  ]
};

export const OnboardingProgressIndicator: React.FC<OnboardingProgressProps> = ({
  currentStep,
  completedSteps,
  userRole,
  isLoading = false,
  showTimeEstimate = true,
  showRemainingTime = false,
  compact = false,
  mobileOptimized = true,
  className = ''
}) => {
  const steps = ONBOARDING_STEPS[userRole] || [];
  
  const progressData = useMemo(() => {
    // Handle both string and number currentStep
    const currentStepStr = typeof currentStep === 'number' ? steps[currentStep - 1]?.id || '' : currentStep;
    const currentStepIndex = steps.findIndex(step => step.id === currentStepStr);
    const completedCount = completedSteps.length;
    const totalSteps = steps.length;
    const progressPercentage = Math.round((completedCount / totalSteps) * 100);
    
    // Calculate time estimates
    const completedTime = steps
      .filter(step => completedSteps.includes(step.id))
      .reduce((sum, step) => sum + step.estimatedMinutes, 0);
    
    const remainingTime = steps
      .filter(step => !completedSteps.includes(step.id))
      .reduce((sum, step) => sum + step.estimatedMinutes, 0);
    
    const totalTime = completedTime + remainingTime;
    
    return {
      currentStepIndex,
      completedCount,
      totalSteps,
      progressPercentage,
      completedTime,
      remainingTime,
      totalTime,
      isComplete: completedSteps.includes('onboarding_complete')
    };
  }, [currentStep, completedSteps, steps]);

  const getStepStatus = (step: OnboardingStep, index: number): 'completed' | 'current' | 'upcoming' | 'blocked' => {
    if (completedSteps.includes(step.id)) return 'completed';
    const currentStepStr = typeof currentStep === 'number' ? steps[currentStep - 1]?.id || '' : currentStep;
    if (step.id === currentStepStr) return 'current';
    
    // Check if dependencies are met
    if (step.dependencies) {
      const dependenciesMet = step.dependencies.every(dep => completedSteps.includes(dep));
      if (!dependenciesMet) return 'blocked';
    }
    
    return 'upcoming';
  };

  const getStepIcon = (step: OnboardingStep, status: string) => {
    const currentStepStr = typeof currentStep === 'number' ? steps[currentStep - 1]?.id || '' : currentStep;
    if (isLoading && step.id === currentStepStr) {
      return (
        <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-500 border-t-transparent" />
      );
    }
    
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'current':
        return <Circle className="h-5 w-5 text-blue-500 fill-current" />;
      case 'blocked':
        return <AlertCircle className="h-5 w-5 text-gray-400" />;
      default:
        return <Circle className="h-5 w-5 text-gray-300" />;
    }
  };

  const formatTime = (minutes: number): string => {
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  };

  if (compact) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-gray-900">
            Setup Progress
          </h3>
          <span className="text-sm text-gray-500">
            {progressData.completedCount} of {progressData.totalSteps}
          </span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
          <div 
            className="bg-blue-500 h-2 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${progressData.progressPercentage}%` }}
          />
        </div>
        
        {showTimeEstimate && (
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center">
              <Clock className="h-3 w-3 mr-1" />
              {progressData.remainingTime > 0 ? (
                `${formatTime(progressData.remainingTime)} remaining`
              ) : (
                'Complete!'
              )}
            </div>
            {showRemainingTime && progressData.totalTime > 0 && (
              <span className="text-gray-400">
                Total: {formatTime(progressData.totalTime)}
              </span>
            )}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            {userRole.toUpperCase()} Setup Progress
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            Step {Math.max(1, progressData.currentStepIndex + 1)} of {progressData.totalSteps}
            {showTimeEstimate && progressData.remainingTime > 0 && (
              ` • ${formatTime(progressData.remainingTime)} remaining`
            )}
          </p>
        </div>
        
        <div className="text-right">
          <div className="text-2xl font-bold text-gray-900">
            {progressData.progressPercentage}%
          </div>
          <div className="text-xs text-gray-500">Complete</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-3 mb-6">
        <div 
          className={`h-3 rounded-full transition-all duration-500 ease-out ${
            progressData.isComplete ? 'bg-green-500' : 'bg-blue-500'
          }`}
          style={{ width: `${progressData.progressPercentage}%` }}
        />
      </div>

      {/* Steps List */}
      <div className="space-y-4">
        {steps.map((step, index) => {
          const status = getStepStatus(step, index);
          
          return (
            <div
              key={step.id}
              className={`flex items-start space-x-3 p-3 rounded-lg transition-colors ${
                status === 'current' ? 'bg-blue-50 border border-blue-200' :
                status === 'completed' ? 'bg-green-50' :
                status === 'blocked' ? 'bg-gray-50' : 'bg-gray-50'
              }`}
            >
              <div className="flex-shrink-0 mt-0.5">
                {getStepIcon(step, status)}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className={`text-sm font-medium ${
                    status === 'completed' ? 'text-green-900' :
                    status === 'current' ? 'text-blue-900' :
                    status === 'blocked' ? 'text-gray-500' : 'text-gray-700'
                  }`}>
                    {step.title}
                    {!step.isRequired && (
                      <span className="ml-2 text-xs text-gray-500">(Optional)</span>
                    )}
                  </h4>
                  
                  {showTimeEstimate && status !== 'completed' && (
                    <span className="text-xs text-gray-500 flex items-center">
                      <Clock className="h-3 w-3 mr-1" />
                      {formatTime(step.estimatedMinutes)}
                    </span>
                  )}
                </div>
                
                <p className={`text-xs mt-1 ${
                  status === 'completed' ? 'text-green-700' :
                  status === 'current' ? 'text-blue-700' :
                  status === 'blocked' ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  {step.description}
                </p>
                
                {status === 'blocked' && step.dependencies && (
                  <p className="text-xs text-amber-600 mt-1">
                    Requires: {step.dependencies.map(dep => 
                      steps.find(s => s.id === dep)?.title
                    ).join(', ')}
                  </p>
                )}
              </div>
              
              {status === 'current' && (
                <ArrowRight className="h-4 w-4 text-blue-500 mt-1" />
              )}
            </div>
          );
        })}
      </div>

      {/* Time Summary */}
      {showTimeEstimate && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="flex justify-between text-xs text-gray-500">
            <span>Time completed: {formatTime(progressData.completedTime)}</span>
            <span>Total estimated: {formatTime(progressData.totalTime)}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default OnboardingProgressIndicator;
