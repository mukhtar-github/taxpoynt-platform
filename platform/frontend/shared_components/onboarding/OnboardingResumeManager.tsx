/**
 * Onboarding Resume Manager
 * ========================
 * 
 * Manages onboarding resumption functionality across all user roles.
 * Detects interrupted onboarding sessions and provides smart resume options.
 * 
 * Features:
 * - Automatic session detection and recovery
 * - Cross-tab/window state synchronization
 * - Smart step recommendation based on progress
 * - Time-based session expiry handling
 * - Graceful degradation for corrupted state
 */

import React, { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, Clock, RefreshCw, ChevronRight, AlertTriangle, CheckCircle } from 'lucide-react';
import { useUserContext } from '../hooks/useUserContext';
import { useOnboardingProgress } from '../hooks/useOnboardingProgress';
import { urlConfig, UrlBuilder } from '../config/urlConfig';

interface OnboardingResumeProps {
  autoRedirect?: boolean;
  showInModal?: boolean;
  onResume?: (step: string) => void;
  onSkip?: () => void;
  className?: string;
}

interface ResumeSession {
  userId: string;
  currentStep: string;
  completedSteps: string[];
  lastActiveTime: string;
  userRole: string;
  sessionStartTime: string;
  interruptedAt: string;
  estimatedProgress: number;
  canResume: boolean;
  resumeRecommendation: {
    step: string;
    reason: string;
    estimatedTime: number;
  };
}

const STEP_NAMES: Record<string, Record<string, string>> = {
  si: {
    'service_introduction': 'Service Introduction',
    'integration_choice': 'Integration Choice',
    'business_systems_setup': 'Business Systems Setup',
    'financial_systems_setup': 'Financial Systems Setup',
    'banking_connected': 'Banking Connection',
    'reconciliation_setup': 'Reconciliation Setup',
    'integration_setup': 'Complete Integration',
    'onboarding_complete': 'Setup Complete'
  },
  app: {
    'service_introduction': 'Service Introduction',
    'business_verification': 'Business Verification',
    'firs_integration_setup': 'FIRS Integration',
    'compliance_settings': 'Compliance Settings',
    'taxpayer_setup': 'Taxpayer Setup',
    'onboarding_complete': 'Setup Complete'
  },
  hybrid: {
    'service_introduction': 'Service Introduction',
    'service_selection': 'Service Selection',
    'business_verification': 'Business Verification',
    'integration_setup': 'Integration Setup',
    'compliance_setup': 'Compliance Setup',
    'onboarding_complete': 'Setup Complete'
  }
};

export const OnboardingResumeManager: React.FC<OnboardingResumeProps> = ({
  autoRedirect = false,
  showInModal = false,
  onResume,
  onSkip,
  className = ''
}) => {
  const router = useRouter();
  const { user, isAuthenticated } = useUserContext();
  const { progressState, analytics, getNextStep, canProgressToStep } = useOnboardingProgress();
  const [resumeSession, setResumeSession] = useState<ResumeSession | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(true);
  const [showResumePrompt, setShowResumePrompt] = useState(false);
  const [hasUserInteracted, setHasUserInteracted] = useState(false);

  // Analyze current session for resume opportunities
  const analyzeResumeSession = useCallback(async (): Promise<ResumeSession | null> => {
    if (!user || !progressState || progressState.isComplete) {
      return null;
    }

    const now = new Date();
    const lastActiveTime = new Date(progressState.lastActiveDate);
    const timeSinceLastActive = now.getTime() - lastActiveTime.getTime();
    const minutesSinceLastActive = Math.floor(timeSinceLastActive / (1000 * 60));

    // Don't show resume for very recent activity (< 5 minutes)
    if (minutesSinceLastActive < 5) {
      return null;
    }

    // Don't show resume for very old sessions (> 7 days)
    if (minutesSinceLastActive > 7 * 24 * 60) {
      return null;
    }

    // Check if session appears to be interrupted
    const isInterrupted = 
      !progressState.isComplete && 
      progressState.hasStarted && 
      minutesSinceLastActive > 5;

    if (!isInterrupted) {
      return null;
    }

    // Determine best resume step
    const nextStep = getNextStep();
    const currentStep = progressState.currentStep;
    const bestResumeStep = nextStep || currentStep;

    // Calculate resume recommendation
    let resumeRecommendation = {
      step: bestResumeStep,
      reason: 'Continue where you left off',
      estimatedTime: 5
    };

    // Smart recommendations based on step and time elapsed
    if (minutesSinceLastActive > 24 * 60) { // More than 1 day
      if (currentStep === 'banking_connected' && !progressState.completedSteps.includes('banking_connected')) {
        resumeRecommendation = {
          step: 'financial_systems_setup',
          reason: 'Banking connection may have expired, restart from financial setup',
          estimatedTime: 10
        };
      } else if (progressState.completedSteps.length === 0) {
        resumeRecommendation = {
          step: 'service_introduction',
          reason: 'Start fresh with a quick overview',
          estimatedTime: 3
        };
      }
    }

    const roleMap: Record<string, 'si' | 'app' | 'hybrid'> = {
      'system_integrator': 'si',
      'access_point_provider': 'app',
      'hybrid_user': 'hybrid'
    };

    return {
      userId: user.id,
      currentStep: progressState.currentStep,
      completedSteps: progressState.completedSteps,
      lastActiveTime: progressState.lastActiveDate,
      userRole: roleMap[user.role] || 'si',
      sessionStartTime: progressState.metadata?.startTime || progressState.lastActiveDate,
      interruptedAt: lastActiveTime.toISOString(),
      estimatedProgress: analytics.completionPercentage,
      canResume: canProgressToStep(bestResumeStep),
      resumeRecommendation
    };
  }, [user, progressState, analytics, getNextStep, canProgressToStep]);

  // Load and analyze session on mount
  useEffect(() => {
    if (!isAuthenticated || !user) {
      setIsAnalyzing(false);
      return;
    }

    const loadSession = async () => {
      try {
        setIsAnalyzing(true);
        const session = await analyzeResumeSession();
        setResumeSession(session);
        
        if (session && autoRedirect && !hasUserInteracted) {
          // Auto-redirect after a short delay
          setTimeout(() => {
            if (!hasUserInteracted) {
              handleResumeStep(session.resumeRecommendation.step);
            }
          }, 3000);
        } else if (session) {
          setShowResumePrompt(true);
        }
      } catch (error) {
        console.error('Failed to analyze resume session:', error);
      } finally {
        setIsAnalyzing(false);
      }
    };

    loadSession();
  }, [isAuthenticated, user, autoRedirect, hasUserInteracted, analyzeResumeSession]);

  // Handle resuming from a specific step
  const handleResumeStep = useCallback((stepId: string) => {
    setHasUserInteracted(true);
    
    if (onResume) {
      onResume(stepId);
      return;
    }

    // Navigate to appropriate step URL
    if (!user || !resumeSession) return;

    const role = resumeSession.userRole;
    const stepUrl = UrlBuilder.onboardingStepUrl(role, stepId);
    router.push(stepUrl);
  }, [user, resumeSession, router, onResume]);

  // Handle skipping resume
  const handleSkipResume = useCallback(() => {
    setHasUserInteracted(true);
    setShowResumePrompt(false);
    
    if (onSkip) {
      onSkip();
      return;
    }

    // Navigate to dashboard or continue normal flow
    if (user) {
      const dashboardUrl = UrlBuilder.dashboardUrl(resumeSession?.userRole as any);
      router.push(dashboardUrl);
    }
  }, [user, resumeSession, router, onSkip]);

  // Handle starting fresh
  const handleStartFresh = useCallback(() => {
    setHasUserInteracted(true);
    
    if (!user || !resumeSession) return;

    // Navigate to the beginning of onboarding
    const role = resumeSession.userRole;
    const startUrl = role === 'si' ? '/onboarding/si/integration-choice' :
                    role === 'app' ? '/onboarding/app/service-introduction' :
                    '/onboarding/hybrid/service-introduction';
    
    router.push(startUrl);
  }, [user, resumeSession, router]);

  // Format time ago
  const formatTimeAgo = (timestamp: string): string => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60));
    
    if (diffMinutes < 60) {
      return `${diffMinutes} minutes ago`;
    } else if (diffMinutes < 24 * 60) {
      const hours = Math.floor(diffMinutes / 60);
      return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    } else {
      const days = Math.floor(diffMinutes / (24 * 60));
      return `${days} day${days !== 1 ? 's' : ''} ago`;
    }
  };

  // Get step display name
  const getStepDisplayName = (stepId: string, role: string): string => {
    return STEP_NAMES[role]?.[stepId] || stepId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  // Don't render anything if no resume session or still analyzing
  if (isAnalyzing || !resumeSession || !showResumePrompt) {
    return null;
  }

  const ResumeContent = () => (
    <div className={`bg-white border border-blue-200 rounded-lg shadow-lg p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-start space-x-3 mb-4">
        <div className="flex-shrink-0">
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
            <Clock className="h-5 w-5 text-blue-600" />
          </div>
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">
            Resume Your Setup?
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            We found an incomplete onboarding session from {formatTimeAgo(resumeSession.interruptedAt)}
          </p>
        </div>
      </div>

      {/* Progress Summary */}
      <div className="bg-gray-50 rounded-lg p-4 mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Progress</span>
          <span className="text-sm text-gray-600">{resumeSession.estimatedProgress}% complete</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
          <div 
            className="bg-blue-500 h-2 rounded-full"
            style={{ width: `${resumeSession.estimatedProgress}%` }}
          />
        </div>
        <div className="flex items-center text-sm text-gray-600">
          <CheckCircle className="h-4 w-4 text-green-500 mr-1" />
          {resumeSession.completedSteps.length} steps completed
        </div>
      </div>

      {/* Resume Recommendation */}
      <div className="border border-green-200 bg-green-50 rounded-lg p-4 mb-6">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center">
              <ArrowRight className="h-4 w-4 text-green-600" />
            </div>
          </div>
          <div className="flex-1">
            <h4 className="text-sm font-medium text-green-900 mb-1">
              Recommended: {getStepDisplayName(resumeSession.resumeRecommendation.step, resumeSession.userRole)}
            </h4>
            <p className="text-sm text-green-700 mb-2">
              {resumeSession.resumeRecommendation.reason}
            </p>
            <p className="text-xs text-green-600 flex items-center">
              <Clock className="h-3 w-3 mr-1" />
              ~{resumeSession.resumeRecommendation.estimatedTime} minutes to complete
            </p>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button
          onClick={() => handleResumeStep(resumeSession.resumeRecommendation.step)}
          className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2"
        >
          <ArrowRight className="h-4 w-4" />
          <span>Resume Setup</span>
        </button>
        
        <button
          onClick={handleStartFresh}
          className="flex-1 bg-gray-100 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-200 transition-colors flex items-center justify-center space-x-2"
        >
          <RefreshCw className="h-4 w-4" />
          <span>Start Fresh</span>
        </button>
        
        <button
          onClick={handleSkipResume}
          className="flex-1 text-gray-500 px-4 py-2 rounded-lg font-medium hover:text-gray-700 transition-colors"
        >
          Skip for Now
        </button>
      </div>

      {/* Additional Help */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <details className="text-sm text-gray-600">
          <summary className="cursor-pointer hover:text-gray-800 flex items-center">
            <ChevronRight className="h-4 w-4 mr-1" />
            What happens if I start fresh?
          </summary>
          <div className="mt-2 ml-5 text-xs">
            <p>Starting fresh will:</p>
            <ul className="list-disc list-inside mt-1 space-y-1">
              <li>Reset your onboarding progress</li>
              <li>Clear any saved configuration data</li>
              <li>Take you through the complete setup process again</li>
              <li>Ensure you don't miss any important steps</li>
            </ul>
          </div>
        </details>
      </div>
    </div>
  );

  if (showInModal) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="max-w-md w-full">
          <ResumeContent />
        </div>
      </div>
    );
  }

  return <ResumeContent />;
};

// Hook for checking if user has resumable onboarding
export const useOnboardingResume = () => {
  const { user } = useUserContext();
  const { progressState, analytics } = useOnboardingProgress();
  
  const hasResumableSession = React.useMemo(() => {
    if (!user || !progressState || progressState.isComplete) {
      return false;
    }
    
    const lastActiveTime = new Date(progressState.lastActiveDate);
    const minutesSinceLastActive = Math.floor(
      (new Date().getTime() - lastActiveTime.getTime()) / (1000 * 60)
    );
    
    return progressState.hasStarted && 
           !progressState.isComplete && 
           minutesSinceLastActive > 5 && 
           minutesSinceLastActive < 7 * 24 * 60;
  }, [user, progressState]);
  
  return {
    hasResumableSession,
    progressState,
    analytics
  };
};

export default OnboardingResumeManager;
