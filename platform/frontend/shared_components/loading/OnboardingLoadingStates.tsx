/**
 * Onboarding Loading States
 * ========================
 * 
 * Comprehensive loading states and skeleton screens for onboarding flows.
 * Provides contextual loading indicators with progress feedback and error states.
 * 
 * Features:
 * - Step-specific loading indicators
 * - Skeleton screens for content loading
 * - Progress animations and transitions
 * - Error and retry states
 * - Accessibility support
 */

import React from 'react';
import { Loader2, CheckCircle, AlertCircle, RefreshCw, ArrowRight, Clock } from 'lucide-react';

interface LoadingStateProps {
  type: 'page' | 'component' | 'action' | 'form' | 'data';
  message?: string;
  progress?: number;
  showProgress?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

interface SkeletonProps {
  type: 'form' | 'card' | 'list' | 'progress' | 'navigation';
  count?: number;
  animated?: boolean;
  className?: string;
}

interface StepLoadingProps {
  currentStep: string;
  isLoading: boolean;
  hasError: boolean;
  errorMessage?: string;
  onRetry?: () => void;
  estimated?: number;
  className?: string;
}

// Generic loading spinner component
export const LoadingSpinner: React.FC<LoadingStateProps> = ({
  type,
  message,
  progress,
  showProgress = false,
  size = 'md',
  className = ''
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8'
  };

  const containerClasses = {
    page: 'flex flex-col items-center justify-center min-h-[400px] space-y-4',
    component: 'flex items-center justify-center p-8 space-x-3',
    action: 'flex items-center space-x-2',
    form: 'flex items-center justify-center p-4',
    data: 'flex items-center space-x-2 text-sm text-gray-600'
  };

  return (
    <div className={`${containerClasses[type]} ${className}`}>
      <div className="flex items-center space-x-3">
        <Loader2 className={`animate-spin text-blue-500 ${sizeClasses[size]}`} />
        {message && (
          <span className={`text-gray-600 ${
            size === 'sm' ? 'text-sm' : size === 'lg' ? 'text-lg' : 'text-base'
          }`}>
            {message}
          </span>
        )}
      </div>
      
      {showProgress && typeof progress === 'number' && (
        <div className="w-full max-w-xs">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Progress</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

// Skeleton loading screens
export const OnboardingSkeleton: React.FC<SkeletonProps> = ({
  type,
  count = 1,
  animated = true,
  className = ''
}) => {
  const baseClasses = `bg-gray-200 rounded ${animated ? 'animate-pulse' : ''}`;

  const renderSkeleton = () => {
    switch (type) {
      case 'form':
        return (
          <div className="space-y-4">
            <div className={`${baseClasses} h-6 w-3/4`} />
            <div className={`${baseClasses} h-10 w-full`} />
            <div className={`${baseClasses} h-10 w-full`} />
            <div className={`${baseClasses} h-4 w-1/2`} />
            <div className={`${baseClasses} h-10 w-32`} />
          </div>
        );
      
      case 'card':
        return (
          <div className="border border-gray-200 rounded-lg p-6 space-y-4">
            <div className={`${baseClasses} h-6 w-2/3`} />
            <div className={`${baseClasses} h-4 w-full`} />
            <div className={`${baseClasses} h-4 w-3/4`} />
            <div className="flex space-x-3">
              <div className={`${baseClasses} h-8 w-20`} />
              <div className={`${baseClasses} h-8 w-24`} />
            </div>
          </div>
        );
      
      case 'list':
        return (
          <div className="space-y-3">
            {Array.from({ length: count }).map((_, i) => (
              <div key={i} className="flex items-center space-x-3">
                <div className={`${baseClasses} h-10 w-10 rounded-full`} />
                <div className="flex-1 space-y-2">
                  <div className={`${baseClasses} h-4 w-3/4`} />
                  <div className={`${baseClasses} h-3 w-1/2`} />
                </div>
              </div>
            ))}
          </div>
        );
      
      case 'progress':
        return (
          <div className="space-y-4">
            <div className="flex justify-between">
              <div className={`${baseClasses} h-6 w-40`} />
              <div className={`${baseClasses} h-6 w-16`} />
            </div>
            <div className={`${baseClasses} h-3 w-full rounded-full`} />
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center space-x-3">
                  <div className={`${baseClasses} h-5 w-5 rounded-full`} />
                  <div className="flex-1">
                    <div className={`${baseClasses} h-4 w-2/3 mb-1`} />
                    <div className={`${baseClasses} h-3 w-1/2`} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      
      case 'navigation':
        return (
          <div className="flex space-x-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className={`${baseClasses} h-10 w-24`} />
            ))}
          </div>
        );
      
      default:
        return <div className={`${baseClasses} h-20 w-full`} />;
    }
  };

  return (
    <div className={className}>
      {renderSkeleton()}
    </div>
  );
};

// Step-specific loading component
export const OnboardingStepLoader: React.FC<StepLoadingProps> = ({
  currentStep,
  isLoading,
  hasError,
  errorMessage,
  onRetry,
  estimated,
  className = ''
}) => {
  const getStepMessage = (step: string): string => {
    const messages: Record<string, string> = {
      'service_introduction': 'Loading introduction...',
      'integration_choice': 'Preparing integration options...',
      'business_systems_setup': 'Configuring business systems...',
      'financial_systems_setup': 'Setting up financial connections...',
      'banking_connected': 'Connecting to your bank...',
      'reconciliation_setup': 'Configuring reconciliation...',
      'business_verification': 'Verifying business details...',
      'firs_integration_setup': 'Setting up FIRS integration...',
      'compliance_settings': 'Configuring compliance rules...',
      'onboarding_complete': 'Finalizing setup...'
    };
    
    return messages[step] || 'Processing...';
  };

  if (hasError) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-start space-x-3">
          <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-sm font-medium text-red-900">
              Setup Error
            </h3>
            <p className="text-sm text-red-700 mt-1">
              {errorMessage || 'An error occurred during setup. Please try again.'}
            </p>
            {onRetry && (
              <button
                onClick={onRetry}
                className="mt-3 inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm leading-4 font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (!isLoading) {
    return null;
  }

  return (
    <div className={`bg-blue-50 border border-blue-200 rounded-lg p-6 ${className}`}>
      <div className="flex items-center space-x-3">
        <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
        <div className="flex-1">
          <h3 className="text-sm font-medium text-blue-900">
            {getStepMessage(currentStep)}
          </h3>
          {estimated && (
            <p className="text-sm text-blue-700 mt-1 flex items-center">
              <Clock className="h-4 w-4 mr-1" />
              Estimated time: {estimated < 60 ? `${estimated}s` : `${Math.ceil(estimated / 60)}m`}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

// Banking connection specific loader
export const BankingConnectionLoader: React.FC<{
  stage: 'initializing' | 'connecting' | 'authenticating' | 'verifying' | 'complete';
  providerName?: string;
  className?: string;
}> = ({ stage, providerName = 'your bank', className = '' }) => {
  const stages = [
    { id: 'initializing', label: 'Initializing connection', duration: 2 },
    { id: 'connecting', label: `Connecting to ${providerName}`, duration: 3 },
    { id: 'authenticating', label: 'Authenticating account', duration: 5 },
    { id: 'verifying', label: 'Verifying account details', duration: 4 },
    { id: 'complete', label: 'Connection established', duration: 1 }
  ];

  const currentStageIndex = stages.findIndex(s => s.id === stage);
  const currentStage = stages[currentStageIndex];

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
      <div className="text-center">
        <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
          {stage === 'complete' ? (
            <CheckCircle className="h-8 w-8 text-green-500" />
          ) : (
            <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
          )}
        </div>
        
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Banking Connection
        </h3>
        
        <p className="text-sm text-gray-600 mb-4">
          {currentStage?.label || 'Processing...'}
        </p>
        
        {/* Progress indicators */}
        <div className="flex justify-center space-x-2 mb-4">
          {stages.slice(0, -1).map((stageItem, index) => (
            <div
              key={stageItem.id}
              className={`h-2 w-8 rounded-full ${
                index <= currentStageIndex 
                  ? 'bg-blue-500' 
                  : 'bg-gray-200'
              }`}
            />
          ))}
        </div>
        
        <p className="text-xs text-gray-500">
          Step {currentStageIndex + 1} of {stages.length - 1}
          {currentStage && stage !== 'complete' && (
            ` • ~${currentStage.duration}s remaining`
          )}
        </p>
      </div>
    </div>
  );
};

// Form submission loader
export const FormSubmissionLoader: React.FC<{
  isSubmitting: boolean;
  submitText?: string;
  submittingText?: string;
  className?: string;
}> = ({ 
  isSubmitting, 
  submitText = 'Submit', 
  submittingText = 'Processing...', 
  className = '' 
}) => {
  return (
    <button
      type="submit"
      disabled={isSubmitting}
      className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
    >
      {isSubmitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
      {isSubmitting ? submittingText : submitText}
    </button>
  );
};

// Data loading indicator
export const DataLoadingIndicator: React.FC<{
  isLoading: boolean;
  error?: string;
  onRetry?: () => void;
  emptyMessage?: string;
  children: React.ReactNode;
}> = ({ isLoading, error, onRetry, emptyMessage, children }) => {
  if (error) {
    return (
      <div className="text-center py-8">
        <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
        <p className="text-sm text-gray-600 mb-4">{error}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </button>
        )}
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-blue-500 mr-3" />
        <span className="text-sm text-gray-600">Loading...</span>
      </div>
    );
  }

  return <>{children}</>;
};

export default {
  LoadingSpinner,
  OnboardingSkeleton,
  OnboardingStepLoader,
  BankingConnectionLoader,
  FormSubmissionLoader,
  DataLoadingIndicator
};
