'use client';

/**
 * Onboarding Resume Middleware
 * ===========================
 * 
 * Middleware component that automatically detects interrupted onboarding sessions
 * and handles resume logic across the application. Should be placed in the app layout
 * or root component to monitor all route changes.
 * 
 * Features:
 * - Automatic session interruption detection
 * - Cross-page resume state management
 * - Smart redirect logic based on user intent
 * - Session persistence across browser restarts
 * - Graceful handling of stale sessions
 */

import React, { useEffect, useState, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useUserContext } from '../hooks/useUserContext';
import { useOnboardingProgress } from '../hooks/useOnboardingProgress';
import { OnboardingResumeManager } from './OnboardingResumeManager';

interface ResumeMiddlewareProps {
  children: React.ReactNode;
  enableAutoResume?: boolean;
  excludePaths?: string[];
  resumePromptDelay?: number;
}

interface SessionState {
  hasShownResumePrompt: boolean;
  lastPromptTime: string;
  userDismissedResume: boolean;
  resumeAttempts: number;
}

const STORAGE_KEY = 'taxpoynt_resume_session_state';
const MAX_RESUME_ATTEMPTS = 3;
const PROMPT_COOLDOWN_HOURS = 24;

export const OnboardingResumeMiddleware: React.FC<ResumeMiddlewareProps> = ({
  children,
  enableAutoResume = true,
  excludePaths = ['/dashboard', '/auth', '/api'],
  resumePromptDelay = 2000
}) => {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading } = useUserContext();
  const { progressState, analytics, isLoading: progressLoading } = useOnboardingProgress();
  
  const [sessionState, setSessionState] = useState<SessionState>({
    hasShownResumePrompt: false,
    lastPromptTime: '',
    userDismissedResume: false,
    resumeAttempts: 0
  });
  
  const [shouldShowResumePrompt, setShouldShowResumePrompt] = useState(false);
  const [isProcessingResume, setIsProcessingResume] = useState(false);

  // Load session state from localStorage
  const loadSessionState = useCallback((): SessionState => {
    if (typeof window === 'undefined') {
      return {
        hasShownResumePrompt: false,
        lastPromptTime: '',
        userDismissedResume: false,
        resumeAttempts: 0
      };
    }

    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        
        // Check if session state is stale (older than 7 days)
        if (parsed.lastPromptTime) {
          const lastPrompt = new Date(parsed.lastPromptTime);
          const daysSinceLastPrompt = (new Date().getTime() - lastPrompt.getTime()) / (1000 * 60 * 60 * 24);
          
          if (daysSinceLastPrompt > 7) {
            // Reset stale session state
            return {
              hasShownResumePrompt: false,
              lastPromptTime: '',
              userDismissedResume: false,
              resumeAttempts: 0
            };
          }
        }
        
        return { ...sessionState, ...parsed };
      }
    } catch (error) {
      console.warn('Failed to load resume session state:', error);
    }
    
    return sessionState;
  }, [sessionState]);

  // Save session state to localStorage
  const saveSessionState = useCallback((state: SessionState) => {
    if (typeof window === 'undefined') return;
    
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      setSessionState(state);
    } catch (error) {
      console.warn('Failed to save resume session state:', error);
    }
  }, []);

  // Check if current path should be excluded from resume prompts
  const isExcludedPath = useCallback((path: string): boolean => {
    return excludePaths.some(excluded => path.startsWith(excluded));
  }, [excludePaths]);

  // Check if user is currently in an onboarding flow
  const isInOnboardingFlow = useCallback((path: string): boolean => {
    return path.includes('/onboarding/');
  }, []);

  // Determine if we should show resume prompt
  const shouldShowResume = useCallback((): boolean => {
    // Don't show if loading or not authenticated
    if (isLoading || progressLoading || !isAuthenticated || !user || !progressState) {
      return false;
    }

    // Don't show if onboarding is complete
    if (progressState.isComplete) {
      return false;
    }

    // Don't show on excluded paths
    if (isExcludedPath(pathname)) {
      return false;
    }

    // Don't show if user is already in onboarding flow
    if (isInOnboardingFlow(pathname)) {
      return false;
    }

    // Don't show if user dismissed resume recently
    if (sessionState.userDismissedResume) {
      const lastPrompt = new Date(sessionState.lastPromptTime);
      const hoursSinceLastPrompt = (new Date().getTime() - lastPrompt.getTime()) / (1000 * 60 * 60);
      
      if (hoursSinceLastPrompt < PROMPT_COOLDOWN_HOURS) {
        return false;
      }
    }

    // Don't show if max resume attempts reached
    if (sessionState.resumeAttempts >= MAX_RESUME_ATTEMPTS) {
      return false;
    }

    // Check if session appears interrupted
    const lastActiveTime = new Date(progressState.lastActiveDate);
    const minutesSinceLastActive = Math.floor(
      (new Date().getTime() - lastActiveTime.getTime()) / (1000 * 60)
    );

    const isInterrupted = 
      progressState.hasStarted && 
      !progressState.isComplete && 
      minutesSinceLastActive > 10 && // More than 10 minutes
      minutesSinceLastActive < 7 * 24 * 60; // Less than 7 days

    return isInterrupted;
  }, [
    isLoading, 
    progressLoading, 
    isAuthenticated, 
    user, 
    progressState, 
    pathname, 
    sessionState,
    isExcludedPath,
    isInOnboardingFlow
  ]);

  // Handle resume action
  const handleResume = useCallback((step: string) => {
    setIsProcessingResume(true);
    setShouldShowResumePrompt(false);
    
    // Update session state
    const newState: SessionState = {
      ...sessionState,
      hasShownResumePrompt: true,
      lastPromptTime: new Date().toISOString(),
      resumeAttempts: sessionState.resumeAttempts + 1,
      userDismissedResume: false
    };
    saveSessionState(newState);
    
    // Navigate to resume step
    setTimeout(() => {
      setIsProcessingResume(false);
    }, 1000);
  }, [sessionState, saveSessionState]);

  // Handle skip resume
  const handleSkipResume = useCallback(() => {
    setShouldShowResumePrompt(false);
    
    // Update session state
    const newState: SessionState = {
      ...sessionState,
      hasShownResumePrompt: true,
      lastPromptTime: new Date().toISOString(),
      userDismissedResume: true
    };
    saveSessionState(newState);
  }, [sessionState, saveSessionState]);

  // Monitor route changes and user authentication
  useEffect(() => {
    if (!enableAutoResume) return;

    // Load session state on mount
    const loadedState = loadSessionState();
    setSessionState(loadedState);
  }, [enableAutoResume, loadSessionState]);

  // Check for resume conditions when dependencies change
  useEffect(() => {
    if (!enableAutoResume || isProcessingResume) return;

    const checkResumeConditions = async () => {
      const shouldShow = shouldShowResume();
      
      if (shouldShow && !shouldShowResumePrompt) {
        // Delay showing the prompt to avoid interrupting user flow
        setTimeout(() => {
          if (shouldShowResume()) {
            setShouldShowResumePrompt(true);
          }
        }, resumePromptDelay);
      }
    };

    checkResumeConditions();
  }, [
    enableAutoResume,
    shouldShowResume,
    shouldShowResumePrompt,
    isProcessingResume,
    resumePromptDelay,
    pathname,
    user,
    progressState
  ]);

  // Handle browser/tab visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && enableAutoResume) {
        // User returned to tab, check if we should show resume prompt
        setTimeout(() => {
          if (shouldShowResume() && !shouldShowResumePrompt) {
            setShouldShowResumePrompt(true);
          }
        }, 1000);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [enableAutoResume, shouldShowResume, shouldShowResumePrompt]);

  // Handle before unload to track session interruptions
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (progressState && !progressState.isComplete && isInOnboardingFlow(pathname)) {
        // User is leaving during onboarding, mark as potentially interrupted
        const interruptionState = {
          ...sessionState,
          lastPromptTime: new Date().toISOString()
        };
        saveSessionState(interruptionState);
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [progressState, pathname, sessionState, saveSessionState, isInOnboardingFlow]);

  // Reset resume prompt when onboarding is completed
  useEffect(() => {
    if (progressState?.isComplete && shouldShowResumePrompt) {
      setShouldShowResumePrompt(false);
      
      // Clear session state
      const clearedState: SessionState = {
        hasShownResumePrompt: false,
        lastPromptTime: '',
        userDismissedResume: false,
        resumeAttempts: 0
      };
      saveSessionState(clearedState);
    }
  }, [progressState?.isComplete, shouldShowResumePrompt, saveSessionState]);

  return (
    <>
      {children}
      
      {/* Resume Prompt Modal */}
      {shouldShowResumePrompt && enableAutoResume && (
        <OnboardingResumeManager
          showInModal={true}
          onResume={handleResume}
          onSkip={handleSkipResume}
        />
      )}
      
      {/* Processing Overlay */}
      {isProcessingResume && (
        <div className="fixed inset-0 bg-black bg-opacity-25 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 shadow-lg">
            <div className="flex items-center space-x-3">
              <div className="animate-spin rounded-full h-6 w-6 border-2 border-blue-500 border-t-transparent" />
              <span className="text-gray-700">Resuming your setup...</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// Hook for programmatically triggering resume checks
export const useResumeCheck = () => {
  const { progressState } = useOnboardingProgress();
  
  const triggerResumeCheck = useCallback(() => {
    // Force a resume check by updating localStorage
    if (typeof window !== 'undefined') {
      const event = new StorageEvent('storage', {
        key: STORAGE_KEY,
        newValue: JSON.stringify({
          hasShownResumePrompt: false,
          lastPromptTime: '',
          userDismissedResume: false,
          resumeAttempts: 0
        })
      });
      window.dispatchEvent(event);
    }
  }, []);

  const clearResumeState = useCallback(() => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  return {
    triggerResumeCheck,
    clearResumeState,
    hasResumableSession: progressState && !progressState.isComplete && progressState.hasStarted
  };
};

export default OnboardingResumeMiddleware;
