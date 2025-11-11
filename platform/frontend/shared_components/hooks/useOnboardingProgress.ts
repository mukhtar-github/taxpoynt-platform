'use client';

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
import apiClient from '../api/client';
import { onboardingApi } from '../services/onboardingApi';
import type { OnboardingState as BackendUnifiedState } from '../services/onboardingApi';

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

const isRecord = (value: unknown): value is Record<string, any> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const roleToServicePackage = (role?: string): keyof typeof STEP_CONFIGURATIONS => {
  if (!role) return 'si';
  const normalized = role.toLowerCase();
  if (normalized.includes('access_point')) return 'app';
  if (normalized.includes('hybrid')) return 'hybrid';
  return 'si';
};

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
    { id: 'registration', estimatedMinutes: 2, dependencies: [] },
    { id: 'email_verification', estimatedMinutes: 2, dependencies: ['registration'] },
    { id: 'terms_acceptance', estimatedMinutes: 1, dependencies: ['email_verification'] },
    { id: 'service_introduction', estimatedMinutes: 2, dependencies: ['terms_acceptance'] },
    { id: 'integration_choice', estimatedMinutes: 3, dependencies: ['service_introduction'] },
    { id: 'business_systems_setup', estimatedMinutes: 8, dependencies: ['integration_choice'] },
    { id: 'financial_systems_setup', estimatedMinutes: 5, dependencies: ['business_systems_setup'] },
    { id: 'banking_connected', estimatedMinutes: 7, dependencies: ['financial_systems_setup'] },
    { id: 'reconciliation_setup', estimatedMinutes: 6, dependencies: ['banking_connected'] },
    { id: 'integration_setup', estimatedMinutes: 4, dependencies: ['banking_connected'] },
    { id: 'onboarding_complete', estimatedMinutes: 1, dependencies: ['integration_setup'] }
  ],
  app: [
    { id: 'registration', estimatedMinutes: 2, dependencies: [] },
    { id: 'email_verification', estimatedMinutes: 2, dependencies: ['registration'] },
    { id: 'terms_acceptance', estimatedMinutes: 1, dependencies: ['email_verification'] },
    { id: 'service_introduction', estimatedMinutes: 2, dependencies: ['terms_acceptance'] },
    { id: 'business_verification', estimatedMinutes: 10, dependencies: ['service_introduction'] },
    { id: 'firs_integration_setup', estimatedMinutes: 12, dependencies: ['business_verification'] },
    { id: 'compliance_settings', estimatedMinutes: 8, dependencies: ['firs_integration_setup'] },
    { id: 'taxpayer_setup', estimatedMinutes: 6, dependencies: ['compliance_settings'] },
    { id: 'onboarding_complete', estimatedMinutes: 1, dependencies: ['compliance_settings'] }
  ],
  hybrid: [
    { id: 'registration', estimatedMinutes: 2, dependencies: [] },
    { id: 'email_verification', estimatedMinutes: 2, dependencies: ['registration'] },
    { id: 'terms_acceptance', estimatedMinutes: 1, dependencies: ['email_verification'] },
    { id: 'service_introduction', estimatedMinutes: 3, dependencies: ['terms_acceptance'] },
    { id: 'service_selection', estimatedMinutes: 5, dependencies: ['service_introduction'] },
    { id: 'business_verification', estimatedMinutes: 12, dependencies: ['service_selection'] },
    { id: 'integration_setup', estimatedMinutes: 15, dependencies: ['business_verification'] },
    { id: 'compliance_setup', estimatedMinutes: 10, dependencies: ['integration_setup'] },
    { id: 'onboarding_complete', estimatedMinutes: 1, dependencies: ['compliance_setup'] }
  ]
};

// Utility functions for type conversion
const mapServicePackageFromMetadata = (metadata: Record<string, any>): keyof typeof STEP_CONFIGURATIONS | null => {
  const raw = metadata?.service_package ?? metadata?.servicePackage;
  if (typeof raw !== 'string') return null;
  const normalized = raw.toLowerCase();
  if (['si', 'system_integrator', 'system-integrator'].includes(normalized)) return 'si';
  if (['app', 'access_point_provider', 'access-point-provider'].includes(normalized)) return 'app';
  if (['hybrid', 'hybrid_user', 'hybrid-user'].includes(normalized)) return 'hybrid';
  return null;
};

const convertBackendToLocal = (
  backendState: BackendOnboardingState | BackendUnifiedState
): OnboardingProgressState => {
  const metadata = isRecord(backendState.metadata) ? backendState.metadata : {};
  const servicePackage = mapServicePackageFromMetadata(metadata);

  return {
    currentStep: typeof backendState.current_step === 'string'
      ? backendState.current_step
      : 'service_introduction',
    completedSteps: Array.isArray(backendState.completed_steps)
      ? backendState.completed_steps.filter((step): step is string => typeof step === 'string')
      : [],
    hasStarted: Boolean(backendState.has_started),
    isComplete: Boolean(backendState.is_complete),
    lastActiveDate:
      typeof backendState.last_active_date === 'string'
        ? backendState.last_active_date
        : new Date().toISOString(),
    metadata: {
      ...metadata,
      service_package: servicePackage ?? metadata.service_package ?? metadata.servicePackage,
    },
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

    const configKey = roleMap[user.role] || mapServicePackageFromMetadata(progressState?.metadata || {}) || 'si';
    return STEP_CONFIGURATIONS[configKey] || [];
  }, [user?.role, progressState?.metadata]);

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

    const localStorageKey = `onboarding_progress_${user.id}`;

    try {
      setIsLoading(true);
      setError(null);

      let backendState: BackendOnboardingState | BackendUnifiedState | null = null;

      try {
        backendState = await onboardingApi.getOnboardingState();
      } catch (unifiedError) {
        console.warn('Unified onboarding state fetch failed; falling back to legacy endpoint.', unifiedError);
      }

      if (!backendState) {
        try {
          backendState = await apiClient.get<BackendOnboardingState>('/onboarding/state');
        } catch (legacyError) {
          console.warn('Legacy onboarding state fetch failed.', legacyError);
        }
      }

      if (backendState) {
        const hydrated = convertBackendToLocal(backendState);
        hydrated.metadata.service_package =
          hydrated.metadata.service_package || roleToServicePackage(user.role);
        setProgressState(hydrated);
        localStorage.setItem(localStorageKey, JSON.stringify(hydrated));

        if (analyticsService.isInitialized && user.role && !sessionStarted) {
          const mappedRole = roleToServicePackage(user.role);
          analyticsService.startSession(user.id, mappedRole, {
            initialStep: hydrated.currentStep,
            userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : '',
            referrer: typeof document !== 'undefined' ? document.referrer : '',
          });
          setSessionStarted(true);
        }

        return;
      }

      const cachedProgress = localStorage.getItem(localStorageKey);
      if (cachedProgress) {
        const parsed = JSON.parse(cachedProgress) as OnboardingProgressState;
        setProgressState(parsed);
        if (analyticsService.isInitialized && user.role && !sessionStarted) {
          const mappedRole = roleToServicePackage(user.role);
          analyticsService.startSession(user.id, mappedRole, {
            initialStep: parsed.currentStep,
            userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : '',
            referrer: typeof document !== 'undefined' ? document.referrer : '',
          });
          setSessionStarted(true);
        }
        return;
      }

      const servicePackage = roleToServicePackage(user.role);
      const initialStep = stepConfig[0]?.id || 'service_introduction';
      const newState: OnboardingProgressState = {
        currentStep: initialStep,
        completedSteps: [],
        hasStarted: true,
        isComplete: false,
        lastActiveDate: new Date().toISOString(),
        metadata: {
          startTime: new Date().toISOString(),
          userRole: user.role,
          service_package: servicePackage,
        },
      };

      setProgressState(newState);
      localStorage.setItem(localStorageKey, JSON.stringify(newState));

      try {
        await onboardingApi.updateOnboardingState({
          current_step: newState.currentStep,
          completed_steps: newState.completedSteps,
          metadata: newState.metadata,
        });
      } catch (syncError) {
        console.warn('Failed to synchronise initial onboarding state.', syncError);
      }

      if (analyticsService.isInitialized && user.role && !sessionStarted) {
        const mappedRole = roleToServicePackage(user.role);
        analyticsService.startSession(user.id, mappedRole, {
          initialStep: newState.currentStep,
          userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : '',
          referrer: typeof document !== 'undefined' ? document.referrer : '',
        });
        setSessionStarted(true);
      }
    } catch (err) {
      console.error('Failed to load onboarding progress:', err);
      setError('Failed to load progress. Please refresh the page.');
    } finally {
      setIsLoading(false);
    }
  }, [user?.id, user?.role, analyticsService, sessionStarted, stepConfig]);

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

      // Update backend (with legacy fallback)
      try {
        await onboardingApi.updateOnboardingState({
          current_step: updatedState.currentStep,
          completed_steps: updatedState.completedSteps,
          metadata: updatedState.metadata,
        });
      } catch (syncError) {
        console.warn('Primary onboarding update failed, attempting legacy endpoint.', syncError);
        const fallbackNamespace = user.role === 'access_point_provider' ? 'app' : 'si';
        await apiClient.put(`/${fallbackNamespace}/onboarding/state`, {
          current_step: updatedState.currentStep,
          completed_steps: updatedState.completedSteps,
          metadata: updatedState.metadata,
        });
      }

      // Update localStorage as backup
      const localKey = `onboarding_progress_${user.id}`;
      localStorage.setItem(localKey, JSON.stringify(updatedState));

    } catch (err) {
      console.error('Failed to update onboarding progress:', err);
      setError('Failed to save progress. Changes may be lost.');
    } finally {
      setIsUpdating(false);
    }
  }, [user?.id, user?.role, progressState]);

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

      // Update backend using unified endpoint with legacy fallback
      try {
        await onboardingApi.completeOnboardingStep(stepId, metadata);
      } catch (syncError) {
        console.warn('Primary step completion failed, attempting legacy endpoint.', syncError);
        await apiClient.post(
          `/${user.role === 'access_point_provider' ? 'app' : 'si'}/onboarding/state/step/${stepId}/complete`,
          { metadata }
        );
      }

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

      // Legacy analytics endpoint already invoked above when fallback occurs

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

      try {
        await onboardingApi.completeOnboarding(completedState.metadata);
      } catch (syncError) {
        console.warn('Primary onboarding completion failed, attempting legacy endpoint.', syncError);
        const fallbackNamespace = user.role === 'access_point_provider' ? 'app' : 'si';
        await apiClient.post(`/${fallbackNamespace}/onboarding/complete`, { metadata: completedState.metadata });
      }

    } catch (err) {
      console.error('Failed to mark onboarding complete:', err);
      setError('Failed to complete onboarding.');
    } finally {
      setIsUpdating(false);
    }
  }, [user?.id, user?.role, progressState, analytics.timeSpent]);

  // Reset progress
  const resetProgress = useCallback(async () => {
    if (!user?.id) return;

    try {
      setIsUpdating(true);
      
      try {
        await onboardingApi.resetOnboardingState();
      } catch (syncError) {
        console.warn('Primary onboarding reset failed, attempting legacy endpoint.', syncError);
        const fallbackNamespace = user.role === 'access_point_provider' ? 'app' : 'si';
        await apiClient.delete(`/${fallbackNamespace}/onboarding/state/reset`);
      }
      
      const localKey = `onboarding_progress_${user.id}`;
      localStorage.removeItem(localKey);
      
      setProgressState(null);
      setSessionStarted(false);
      await loadProgressState();
      
    } catch (err) {
      console.error('Failed to reset progress:', err);
      setError('Failed to reset progress.');
    } finally {
      setIsUpdating(false);
    }
  }, [user?.id, user?.role, loadProgressState]);

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
