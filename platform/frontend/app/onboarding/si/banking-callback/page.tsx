'use client';

import React, { Suspense, useEffect, useState, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useUserContext } from '../../../../shared_components/hooks/useUserContext';
import { OnboardingStateManager } from '../../../../shared_components/services/onboardingApi';
import { useBankingErrorRecovery, BankingError } from '../../../../shared_components/services/bankingErrorRecovery';
import { getPostBankingUrl } from '../../../../shared_components/utils/dashboardRouting';
import { TaxPoyntButton } from '../../../../design_system';
import { OnboardingProgressIndicator } from '../../../../shared_components/onboarding/OnboardingProgressIndicator';
import { BankingConnectionLoader, OnboardingStepLoader } from '../../../../shared_components/loading/OnboardingLoadingStates';
import { useOnboardingProgress } from '../../../../shared_components/hooks/useOnboardingProgress';
import apiClient from '../../../../shared_components/api/client';

interface BankingAccount {
  id?: string;
  name?: string;
  accountNumber?: string;
  [key: string]: unknown;
}

interface BankingCallbackResponse {
  success: boolean;
  message?: string;
  data?: { accounts?: BankingAccount[] };
  token?: string;
}

const BankingCallbackContent: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isAuthenticated, isLoading } = useUserContext({ requireAuth: true });
  const { handleError } = useBankingErrorRecovery();
  const { progressState, completeStep, updateProgress, isUpdating } = useOnboardingProgress();
  const [status, setStatus] = useState<'processing' | 'success' | 'error' | 'retrying'>('processing');
  const [message, setMessage] = useState('Processing your bank connection...');
  const [currentError, setCurrentError] = useState<BankingError | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [connectionStage, setConnectionStage] = useState<'initializing' | 'connecting' | 'authenticating' | 'verifying' | 'complete'>('initializing');

  const processBankingCallback = useCallback(async () => {
    try {
      // Set initial stage
      setConnectionStage('initializing');
      await updateProgress('banking_connected', false);
      
      // Get parameters from URL
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const error = searchParams.get('error');
      const error_description = searchParams.get('error_description');

      console.log('🏦 Banking callback received:', {
        code: code ? 'present' : 'missing',
        state,
        error,
        error_description
      });

      // Handle error case
      if (error) {
        setStatus('error');
        setMessage(error_description || 'Bank connection failed. Please try again.');
        return;
      }

      // Handle missing code
      if (!code) {
        setStatus('error');
        setMessage('Invalid callback: missing authorization code.');
        return;
      }

      // Progress to connecting stage
      setConnectionStage('connecting');
      setMessage('Connecting to your bank...');

      // Progress to authenticating stage
      setConnectionStage('authenticating');
      setMessage('Authenticating with your bank...');
      
      // Exchange code for access token and account information
      const data = await apiClient.post<BankingCallbackResponse>('/si/banking/open-banking/mono/callback', {
        code,
        state,
        redirect_url: window.location.origin + '/onboarding/si/banking-callback'
      });

      // Progress to verifying stage
      setConnectionStage('verifying');
      setMessage('Verifying account details...');
      
      if (data.success) {
        // Progress to complete stage
        setConnectionStage('complete');
        setStatus('success');
        setMessage(`Successfully connected ${data.data?.accounts?.length || 1} bank account(s)!`);
        
        // Update onboarding state with progress tracking
        if (user) {
          await completeStep('banking_connected', {
            provider: 'mono',
            accountCount: data.data?.accounts?.length || 1,
            connectionTimestamp: new Date().toISOString()
          });
        }
        
        // Auto-redirect to next step after 3 seconds
        setTimeout(() => {
          if (user) {
            router.push(getPostBankingUrl(user));
          }
        }, 3000);
        
      } else {
        throw new Error(data.message || 'Failed to process bank connection');
      }

    } catch (error) {
      console.error('Banking callback processing failed:', error);
      
      // Use error recovery service to classify and handle the error
      const bankingError = handleError(error, { 
        provider: 'mono',
        context: 'callback_processing',
        retryCount
      });
      
      setStatus('error');
      setCurrentError(bankingError);
      setMessage(bankingError.userMessage);
      
      // Log detailed error information
      console.error('Banking Error Details:', {
        error: bankingError,
        originalError: error,
        retryCount,
        canRetry: bankingError.retryable && retryCount < 3
      });
    }
  }, [completeStep, handleError, retryCount, router, searchParams, updateProgress, user]);

  useEffect(() => {
    if (isLoading) return;
    
    if (!isAuthenticated) {
      router.push('/auth/signin');
      return;
    }
    
    if (user) {
      // Process the Mono callback
      processBankingCallback();
    }
  }, [isLoading, isAuthenticated, user, processBankingCallback, router]);

  const handleAutoRetry = async () => {
    setIsRetrying(true);
    setRetryCount(prev => prev + 1);
    setStatus('processing');
    setMessage('Retrying connection...');
    setCurrentError(null);
    
    setTimeout(() => {
      processBankingCallback();
      setIsRetrying(false);
    }, 1000);
  };



  const handleContinue = () => {
    if (user) {
      OnboardingStateManager.updateStep(user.id, 'reconciliation_setup');
      router.push(getPostBankingUrl(user));
    }
  };

  const handleRetry = () => {
    router.push('/onboarding/si/financial-systems-setup');
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'processing':
        return (
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-200 border-t-blue-600 mx-auto"></div>
        );
      case 'success':
        return (
          <div className="text-6xl text-green-500 mx-auto">✅</div>
        );
      case 'error':
        return (
          <div className="text-6xl text-red-500 mx-auto">❌</div>
        );
      default:
        return null;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'processing':
        return 'text-blue-600';
      case 'success':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getBackgroundColor = () => {
    switch (status) {
      case 'processing':
        return 'bg-blue-50';
      case 'success':
        return 'bg-green-50';
      case 'error':
        return 'bg-red-50';
      default:
        return 'bg-gray-50';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Progress Indicator - Compact version in top section */}
        {progressState && (
          <div className="mb-8">
            <OnboardingProgressIndicator
              currentStep={progressState.currentStep}
              completedSteps={progressState.completedSteps}
              userRole="si"
              isLoading={isUpdating || status === 'processing'}
              showTimeEstimate={true}
              compact={true}
              className="max-w-md mx-auto"
            />
          </div>
        )}

        {/* Step Loading Indicator for Errors */}
        {status === 'error' && currentError && (
          <div className="mb-8">
            <OnboardingStepLoader
              currentStep="banking_connected"
              isLoading={false}
              hasError={true}
              errorMessage={currentError.userMessage}
              onRetry={currentError.retryable ? handleAutoRetry : undefined}
              className="max-w-md mx-auto"
            />
          </div>
        )}

        {/* Main Banking Connection Status */}
        <div className="flex items-center justify-center">
          <div className="max-w-md w-full mx-4">
        <div className={`${getBackgroundColor()} border-2 ${
          status === 'processing' ? 'border-blue-200' :
          status === 'success' ? 'border-green-200' :
          'border-red-200'
        } rounded-2xl p-8 text-center`}>
          
          {/* Banking Connection Loader or Status Icon */}
          <div className="mb-6">
            {status === 'processing' ? (
              <BankingConnectionLoader 
                stage={connectionStage}
                providerName="Mono"
                className="bg-transparent border-0 p-0"
              />
            ) : (
              getStatusIcon()
            )}
          </div>

          {/* Title */}
          <h1 className={`text-2xl font-bold mb-4 ${getStatusColor()}`}>
            {status === 'processing' && 'Processing Bank Connection'}
            {status === 'success' && 'Bank Connected Successfully!'}
            {status === 'error' && 'Connection Failed'}
          </h1>

          {/* Message */}
          <p className="text-gray-700 mb-6 leading-relaxed">
            {message}
          </p>

          {/* Additional Info for Success */}
          {status === 'success' && (
                          <div className="bg-white border border-green-200 rounded-lg p-4 mb-6 text-left">
            <h3 className="font-semibold text-gray-900 mb-2">🎉 What&apos;s Next?</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Your bank account is now connected via Mono</li>
                <li>• Transaction monitoring is active</li>
                <li>• Next: Configure auto-reconciliation rules</li>
                <li>• Then: Access your SI dashboard for full control</li>
              </ul>
            </div>
          )}

          {/* Action Buttons */}
          <div className="space-y-3">
            {status === 'processing' && (
              <p className="text-sm text-gray-600">
                Please wait while we process your bank connection...
              </p>
            )}
            
            {status === 'success' && (
              <div className="space-y-3">
                <TaxPoyntButton
                  variant="primary"
                  onClick={handleContinue}
                  className="w-full"
                >
                  Continue to Reconciliation Setup
                </TaxPoyntButton>
                <p className="text-sm text-gray-600">
                  Auto-redirecting to setup reconciliation...
                </p>
              </div>
            )}
            
            {status === 'error' && (
              <div className="space-y-3">
                {/* Show retry option if error is retryable and under retry limit */}
                {currentError?.retryable && retryCount < 3 && (
                  <TaxPoyntButton
                    onClick={handleAutoRetry}
                    className="w-full"
                    variant="primary"
                    disabled={isRetrying}
                  >
                    {isRetrying ? 'Retrying...' : `Retry Connection (${retryCount + 1}/3)`}
                  </TaxPoyntButton>
                )}
                
                <TaxPoyntButton
                  variant={currentError?.retryable && retryCount < 3 ? "secondary" : "primary"}
                  onClick={handleRetry}
                  className="w-full"
                >
                  Restart Banking Setup
                </TaxPoyntButton>
                
                <TaxPoyntButton
                  variant="secondary"
                  onClick={() => router.push('/dashboard/si')}
                  className="w-full"
                >
                  Skip for Now
                </TaxPoyntButton>
                
                {/* Show error suggestions if available */}
                {currentError && (
                  <div className="mt-4 text-left">
                    <details className="bg-white border border-red-200 rounded-lg p-4">
                      <summary className="font-semibold text-red-800 cursor-pointer">
                        Troubleshooting Tips
                      </summary>
                      <div className="mt-2 text-sm text-gray-600">
                        <ul className="list-disc list-inside space-y-1">
                          {currentError.suggestedActions.map((action, index) => (
                            <li key={index}>{action}</li>
                          ))}
                        </ul>
                      </div>
                    </details>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Help Link */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              Having trouble? 
              <button className="ml-1 text-green-600 hover:text-green-800 font-medium">
                Contact Support
              </button>
            </p>
          </div>
        </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const BankingCallbackFallback: React.FC = () => (
  <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-blue-50 flex items-center justify-center">
    <div className="text-center">
      <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-b-2 border-indigo-600" />
      <p className="text-sm text-gray-600">Processing Mono callback…</p>
    </div>
  </div>
);

export default function BankingCallbackPage() {
  return (
    <Suspense fallback={<BankingCallbackFallback />}>
      <BankingCallbackContent />
    </Suspense>
  );
}
