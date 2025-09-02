/**
 * Onboarding Progress Hook
 * =======================
 * 
 * Custom hook for managing onboarding progress state and visual indicators.
 * Provides real-time progress tracking, time estimation, and completion analytics.
 * 
 * Features:
 * - Real-time progress calculation
 * - Step completion tracking
 * - Time estimation and analytics
 * - Progress persistence across sessions
 * - Loading state management
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useUserContext } from './useUserContext';
import { useOnboardingAnalytics } from '../analytics/OnboardingAnalytics';

interface OnboardingProgressState {
  currentStep: string;
  completedSteps: string[];
  hasStarted: boolean;
  isComplete: boolean;
  lastActiveDate: string;
  metadata: Record<string, any>;
}

// Type for backend API (snake_case)
interface BackendOnboardingState {
  user_id: string;
  current_step: string;
  completed_steps: string[];
  has_started: boolean;
  is_complete: boolean;
  last_active_date: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

interface ProgressAnalytics {
  completionPercentage: number;
  estimatedTimeRemaining: number;
  totalEstimatedTime: number;
  timeSpent: number;
  stepsRemaining: number;
  totalSteps: number;
  averageStepTime: number;
  isOnTrack: boolean;
  expectedCompletionTime?: Date;
}

interface UseOnboardingProgressReturn {
  // Progress state
  progressState: OnboardingProgressState | null;
  analytics: ProgressAnalytics;
  isLoading: boolean;
  error: string | null;
  
  // Progress actions
  updateProgress: (step: string, completed?: boolean) => Promise<void>;
  completeStep: (stepId: string, metadata?: Record<string, any>) => Promise<void>;
  markComplete: () => Promise<void>;
  resetProgress: () => Promise<void>;
  
  // Utility functions
  getStepStatus: (stepId: string) => 'completed' | 'current' | 'upcoming' | 'blocked';
  getNextStep: () => string | null;
  canProgressToStep: (stepId: string) => boolean;
  
  // Loading states
  isUpdating: boolean;
  lastUpdate: Date | null;
}

// Step configurations with dependencies and time estimates
const STEP_CONFIGURATIONS = {
  si: [
    { id: 'service_introduction', estimatedMinutes: 2, dependencies: [] },
    { id: 'integration_choice', estimatedMinutes: 3, dependencies: ['service_introduction'] },
    { id: 'business_systems_setup', estimatedMinutes: 8, dependencies: ['integration_choice'] },
    { id: 'financial_systems_setup', estimatedMinutes: 5, dependencies: ['business_systems_setup'] },
    { id: 'banking_connected', estimatedMinutes: 7, dependencies: ['financial_systems_setup'] },
    { id: 'reconciliation_setup', estimatedMinutes: 6, dependencies: ['banking_connected'] },
    { id: 'integration_setup', estimatedMinutes: 4, dependencies: ['banking_connected'] },
    { id: 'onboarding_complete', estimatedMinutes: 1, dependencies: ['integration_setup'] }
  ],
  app: [
    { id: 'service_introduction', estimatedMinutes: 2, dependencies: [] },
    { id: 'business_verification', estimatedMinutes: 10, dependencies: ['service_introduction'] },
    { id: 'firs_integration_setup', estimatedMinutes: 12, dependencies: ['business_verification'] },
    { id: 'compliance_settings', estimatedMinutes: 8, dependencies: ['firs_integration_setup'] },
    { id: 'taxpayer_setup', estimatedMinutes: 6, dependencies: ['compliance_settings'] },
    { id: 'onboarding_complete', estimatedMinutes: 1, dependencies: ['compliance_settings'] }
  ],
  hybrid: [
    { id: 'service_introduction', estimatedMinutes: 3, dependencies: [] },
    { id: 'service_selection', estimatedMinutes: 5, dependencies: ['service_introduction'] },
    { id: 'business_verification', estimatedMinutes: 12, dependencies: ['service_selection'] },
    { id: 'integration_setup', estimatedMinutes: 15, dependencies: ['business_verification'] },
    { id: 'compliance_setup', estimatedMinutes: 10, dependencies: ['integration_setup'] },
    { id: 'onboarding_complete', estimatedMinutes: 1, dependencies: ['compliance_setup'] }
  ]
};

// Utility functions for type conversion
const convertBackendToLocal = (backendState: BackendOnboardingState): OnboardingProgressState => {
  return {
    currentStep: backendState.current_step,
    completedSteps: backendState.completed_steps,
    hasStarted: backendState.has_started,
    isComplete: backendState.is_complete,
    lastActiveDate: backendState.last_active_date,
    metadata: backendState.metadata
  };
};

const convertLocalToBackend = (localState: OnboardingProgressState, userId: string): BackendOnboardingState => {
  const now = new Date().toISOString();
  return {
    user_id: userId,
    current_step: localState.currentStep,
    completed_steps: localState.completedSteps,
    has_started: localState.hasStarted,
    is_complete: localState.isComplete,
    last_active_date: localState.lastActiveDate,
    metadata: localState.metadata,
    created_at: localState.metadata.created_at || now,
    updated_at: now
  };
};

export const useOnboardingProgress = (): UseOnboardingProgressReturn => {
  const { user, isLoading: userLoading } = useUserContext();
  const analyticsService = useOnboardingAnalytics();
  const [progressState, setProgressState] = useState<OnboardingProgressState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [sessionStarted, setSessionStarted] = useState(false);

  // Get step configuration for user role
  const stepConfig = useMemo(() => {
    if (!user?.role) return [];
    
    const roleMap: Record<string, keyof typeof STEP_CONFIGURATIONS> = {
      'system_integrator': 'si',
      'access_point_provider': 'app',
      'hybrid_user': 'hybrid'
    };
    
    const configKey = roleMap[user.role] || 'si';
    return STEP_CONFIGURATIONS[configKey] || [];
  }, [user?.role]);

  // Calculate progress analytics
  const analytics = useMemo((): ProgressAnalytics => {
    if (!progressState || !stepConfig.length) {
      return {
        completionPercentage: 0,
        estimatedTimeRemaining: 0,
        totalEstimatedTime: 0,
        timeSpent: 0,
        stepsRemaining: 0,
        totalSteps: 0,
        averageStepTime: 0,
        isOnTrack: true
      };
    }

    const totalSteps = stepConfig.length;
    const completedCount = progressState.completedSteps.length;
    const completionPercentage = Math.round((completedCount / totalSteps) * 100);
    
    const totalEstimatedTime = stepConfig.reduce((sum, step) => sum + step.estimatedMinutes, 0);
    const completedTime = stepConfig
      .filter(step => progressState.completedSteps.includes(step.id))
      .reduce((sum, step) => sum + step.estimatedMinutes, 0);
    const estimatedTimeRemaining = totalEstimatedTime - completedTime;
    
    const startTime = new Date(progressState.metadata?.startTime || progressState.lastActiveDate);
    const now = new Date();
    const timeSpentMinutes = Math.max(0, (now.getTime() - startTime.getTime()) / (1000 * 60));
    
    const averageStepTime = completedCount > 0 ? timeSpentMinutes / completedCount : 0;
    const expectedTimeForCompleted = stepConfig
      .filter(step => progressState.completedSteps.includes(step.id))
      .reduce((sum, step) => sum + step.estimatedMinutes, 0);
    const isOnTrack = timeSpentMinutes <= expectedTimeForCompleted * 1.5; // 50% buffer

    const expectedCompletionTime = isOnTrack && averageStepTime > 0 
      ? new Date(now.getTime() + (estimatedTimeRemaining / averageStepTime) * averageStepTime * 60 * 1000)
      : undefined;

    return {
      completionPercentage,
      estimatedTimeRemaining,
      totalEstimatedTime,
      timeSpent: Math.round(timeSpentMinutes),
      stepsRemaining: totalSteps - completedCount,
      totalSteps,
      averageStepTime: Math.round(averageStepTime),
      isOnTrack,
      expectedCompletionTime
    };
  }, [progressState, stepConfig]);

  // Load progress state from backend
  const loadProgressState = useCallback(async () => {
    if (!user?.id) return;

    try {
      setIsLoading(true);
      setError(null);

      // Try to load from backend first
      const { onboardingApi } = await import('../services/onboardingApi');
      const backendState = await onboardingApi.getOnboardingState();
      
      if (backendState) {
        const localState = convertBackendToLocal(backendState);
        setProgressState(localState);
      } else {
        // Fallback to localStorage
        const localKey = `onboarding_progress_${user.id}`;
        const localState = localStorage.getItem(localKey);
        
        if (localState) {
          const parsed = JSON.parse(localState);
          setProgressState(parsed);
        } else {
          // Initialize new progress state
          const newState: OnboardingProgressState = {
            currentStep: stepConfig[0]?.id || 'service_introduction',
            completedSteps: [],
            hasStarted: true,
            isComplete: false,
            lastActiveDate: new Date().toISOString(),
            metadata: {
              startTime: new Date().toISOString(),
              userRole: user.role
            }
          };
          setProgressState(newState);
          
          // Save to backend
          const backendState = convertLocalToBackend(newState, user.id);
          await onboardingApi.updateOnboardingState(backendState);
          
          // Start analytics session
          if (analyticsService.isInitialized && user.role) {
            const userRoleMap: Record<string, 'si' | 'app' | 'hybrid'> = {
              'system_integrator': 'si',
              'access_point_provider': 'app',
              'hybrid_user': 'hybrid'
            };
            const mappedRole = userRoleMap[user.role] || 'si';
            
            analyticsService.startSession(user.id, mappedRole, {
              initialStep: newState.currentStep,
              userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : '',
              referrer: typeof document !== 'undefined' ? document.referrer : ''
            });
            setSessionStarted(true);
          }
        }
      }
    } catch (err) {
      console.error('Failed to load onboarding progress:', err);
      setError('Failed to load progress. Please refresh the page.');
    } finally {
      setIsLoading(false);
    }
  }, [user?.id, stepConfig]);

  // Update progress state
  const updateProgress = useCallback(async (step: string, completed = false) => {
    if (!user?.id || !progressState) return;

    try {
      setIsUpdating(true);
      setError(null);

      const updatedState: OnboardingProgressState = {
        ...progressState,
        currentStep: step,
        completedSteps: completed 
          ? Array.from(new Set([...progressState.completedSteps, step]))
          : progressState.completedSteps,
        lastActiveDate: new Date().toISOString(),
        metadata: {
          ...progressState.metadata,
          lastUpdate: new Date().toISOString()
        }
      };

      setProgressState(updatedState);
      setLastUpdate(new Date());

      // Update backend
      const { onboardingApi } = await import('../services/onboardingApi');
      const backendState = convertLocalToBackend(updatedState, user.id);
      await onboardingApi.updateOnboardingState(backendState);

      // Update localStorage as backup
      const localKey = `onboarding_progress_${user.id}`;
      localStorage.setItem(localKey, JSON.stringify(updatedState));

    } catch (err) {
      console.error('Failed to update onboarding progress:', err);
      setError('Failed to save progress. Changes may be lost.');
    } finally {
      setIsUpdating(false);
    }
  }, [user?.id, progressState]);

  // Complete a specific step
  const completeStep = useCallback(async (stepId: string, metadata: Record<string, any> = {}) => {
    if (!user?.id || !progressState) return;

    try {
      setIsUpdating(true);
      
      const stepMetadata = {
        ...progressState.metadata,
        stepCompletions: {
          ...progressState.metadata.stepCompletions,
          [stepId]: {
            completedAt: new Date().toISOString(),
            ...metadata
          }
        }
      };

      const updatedState: OnboardingProgressState = {
        ...progressState,
        completedSteps: Array.from(new Set([...progressState.completedSteps, stepId])),
        lastActiveDate: new Date().toISOString(),
        metadata: stepMetadata
      };

      setProgressState(updatedState);
      setLastUpdate(new Date());

      // Update backend
      const { onboardingApi } = await import('../services/onboardingApi');
      const backendState = convertLocalToBackend(updatedState, user.id);
      await onboardingApi.updateOnboardingState(backendState);

      // Track step completion in analytics
      if (analyticsService.isInitialized && user.role) {
        const userRoleMap: Record<string, 'si' | 'app' | 'hybrid'> = {
          'system_integrator': 'si',
          'access_point_provider': 'app',
          'hybrid_user': 'hybrid'
        };
        const mappedRole = userRoleMap[user.role] || 'si';
        
        // Calculate step duration if we have start time
        const stepStartTime = progressState.metadata.stepStartTimes?.[stepId];
        const duration = stepStartTime ? Date.now() - stepStartTime : 0;
        
        analyticsService.trackStepComplete(stepId, user.id, mappedRole, duration, metadata);
      }

      // Also call step completion endpoint for analytics
      try {
        const apiConfig = user.role === 'system_integrator' ? 'si' : 
                         user.role === 'access_point_provider' ? 'app' : 'si';
        
        const response = await fetch(`/api/v1/${apiConfig}/onboarding/state/step/${stepId}/complete`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ metadata })
        });
        
        if (!response.ok) {
          console.warn('Step completion tracking failed:', response.statusText);
        }
      } catch (trackingError) {
        console.warn('Step completion tracking failed:', trackingError);
        // Don't fail the main operation for tracking issues
      }

    } catch (err) {
      console.error('Failed to complete step:', err);
      setError('Failed to save step completion.');
    } finally {
      setIsUpdating(false);
    }
  }, [user?.id, user?.role, progressState]);

  // Mark entire onboarding as complete
  const markComplete = useCallback(async () => {
    if (!user?.id || !progressState) return;

    try {
      setIsUpdating(true);
      
      const completedState: OnboardingProgressState = {
        ...progressState,
        currentStep: 'onboarding_complete',
        completedSteps: Array.from(new Set([...progressState.completedSteps, 'onboarding_complete'])),
        isComplete: true,
        lastActiveDate: new Date().toISOString(),
        metadata: {
          ...progressState.metadata,
          completedAt: new Date().toISOString(),
          finalCompletionTime: analytics.timeSpent
        }
      };

      setProgressState(completedState);
      setLastUpdate(new Date());

      // Update backend  
      const { OnboardingStateManager } = await import('../services/onboardingApi');
      await OnboardingStateManager.completeOnboarding(user.id);

    } catch (err) {
      console.error('Failed to mark onboarding complete:', err);
      setError('Failed to complete onboarding.');
    } finally {
      setIsUpdating(false);
    }
  }, [user?.id, progressState, analytics.timeSpent]);

  // Reset progress
  const resetProgress = useCallback(async () => {
    if (!user?.id) return;

    try {
      setIsUpdating(true);
      
      const { onboardingApi } = await import('../services/onboardingApi');
      await onboardingApi.resetOnboardingState();
      
      const localKey = `onboarding_progress_${user.id}`;
      localStorage.removeItem(localKey);
      
      setProgressState(null);
      await loadProgressState();
      
    } catch (err) {
      console.error('Failed to reset progress:', err);
      setError('Failed to reset progress.');
    } finally {
      setIsUpdating(false);
    }
  }, [user?.id, loadProgressState]);

  // Utility functions
  const getStepStatus = useCallback((stepId: string): 'completed' | 'current' | 'upcoming' | 'blocked' => {
    if (!progressState || !stepConfig.length) return 'upcoming';
    
    if (progressState.completedSteps.includes(stepId)) return 'completed';
    if (progressState.currentStep === stepId) return 'current';
    
    const step = stepConfig.find(s => s.id === stepId);
    if (step?.dependencies) {
      const dependenciesMet = step.dependencies.every(dep => 
        progressState.completedSteps.includes(dep)
      );
      if (!dependenciesMet) return 'blocked';
    }
    
    return 'upcoming';
  }, [progressState, stepConfig]);

  const getNextStep = useCallback((): string | null => {
    if (!progressState || !stepConfig.length) return null;
    
    const nextStep = stepConfig.find(step => 
      !progressState.completedSteps.includes(step.id) &&
      (step.dependencies?.every(dep => progressState.completedSteps.includes(dep)) ?? true)
    );
    
    return nextStep?.id || null;
  }, [progressState, stepConfig]);

  const canProgressToStep = useCallback((stepId: string): boolean => {
    const status = getStepStatus(stepId);
    return status !== 'blocked';
  }, [getStepStatus]);

  // Load progress on mount and user change
  useEffect(() => {
    if (!userLoading && user?.id) {
      loadProgressState();
    }
  }, [userLoading, user?.id, loadProgressState]);

  return {
    // Progress state
    progressState,
    analytics,
    isLoading: isLoading || userLoading,
    error,
    
    // Progress actions
    updateProgress,
    completeStep,
    markComplete,
    resetProgress,
    
    // Utility functions
    getStepStatus,
    getNextStep,
    canProgressToStep,
    
    // Loading states
    isUpdating,
    lastUpdate
  };
};

export default useOnboardingProgress;
