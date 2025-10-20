/**
 * Onboarding API Client
 * =====================
 * 
 * API client for onboarding state management and synchronization.
 * Provides centralized onboarding progress tracking across devices and sessions.
 * 
 * Features:
 * - Get/update onboarding state
 * - Complete steps and entire onboarding
 * - Onboarding analytics and insights  
 * - Automatic retry and error handling
 * - Local storage fallback for offline scenarios
 */

import axios, { AxiosResponse, AxiosError } from 'axios';
import { authService } from './auth';

export interface OnboardingState {
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

export interface OnboardingStateRequest {
  current_step: string;
  completed_steps?: string[];
  metadata?: Record<string, any>;
}

export interface OnboardingAnalytics {
  user_id: string;
  status: 'not_started' | 'in_progress' | 'complete';
  analytics: {
    completion_percentage: number;
    completed_steps: number;
    total_steps: number;
    remaining_steps: number;
    current_step: string;
    days_since_start: number;
    days_since_last_active: number;
    is_stale: boolean;
    expected_completion: {
      next_steps: string[];
      estimated_remaining_time: string;
    };
  };
  timeline: {
    started_at: string;
    last_active: string;
    completed_at?: string;
  };
}

export interface ApiResponse<T = any> {
  success: boolean;
  action: string;
  api_version: string;
  timestamp: string;
  data: T;
  meta?: Record<string, any>;
}

class OnboardingApiClient {
  private baseUrl: string;
  private retryAttempts: number = 4;
  private baseRetryDelay: number = 1500; // start at 1.5s
  private maxRetryDelay: number = 12000; // 12 seconds cap

  constructor() {
    const primaryApiUrl = process.env.NEXT_PUBLIC_API_URL;
    const legacyApiBase = process.env.NEXT_PUBLIC_API_BASE_URL;

    let resolvedBase = primaryApiUrl?.trim() || '';

    if (!resolvedBase && legacyApiBase) {
      resolvedBase = `${legacyApiBase.replace(/\/+$/, '')}/api/v1`;
    }

    if (!resolvedBase) {
      resolvedBase = 'http://localhost:8000/api/v1';
    }

    this.baseUrl = resolvedBase.replace(/\/+$/, '');
  }

  /**
   * Get the authorization headers for API requests
   */
  private async getAuthHeaders(): Promise<Record<string, string>> {
    try {
      const token = authService.getToken();
      if (!token) {
        throw new Error('No authentication token available');
      }

      const headers: Record<string, string> = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };

      const storedUser = authService.getStoredUser();
      if (storedUser?.id) {
        headers['X-User-Id'] = storedUser.id;
      }
      const orgId = storedUser?.organization?.id;
      if (orgId) {
        headers['X-Organization-Id'] = orgId;
      }

      const servicePackage = storedUser?.service_package;
      if (servicePackage) {
        headers['X-Service-Package'] = servicePackage;
      }

      return headers;
    } catch (error) {
      console.error('Failed to get auth headers:', error);
      throw new Error('Authentication required');
    }
  }

  /**
   * Make an authenticated API request with retry logic
   */
  private async makeRequest<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    endpoint: string,
    data?: any,
    attempt: number = 1
  ): Promise<T> {
    try {
      const headers = await this.getAuthHeaders();
      const url = `${this.baseUrl}/si/onboarding${endpoint}`;

      let response: AxiosResponse<ApiResponse<T>>;

      switch (method) {
        case 'GET':
          response = await axios.get(url, { headers });
          break;
        case 'POST':
          response = await axios.post(url, data, { headers });
          break;
        case 'PUT':
          response = await axios.put(url, data, { headers });
          break;
        case 'DELETE':
          response = await axios.delete(url, { headers });
          break;
        default:
          throw new Error(`Unsupported HTTP method: ${method}`);
      }

      if (response.data.success) {
        return response.data.data;
      }

      const metaMessage = typeof response.data.meta?.message === 'string'
        ? response.data.meta.message
        : undefined;
      const metaError = typeof response.data.meta?.error === 'string'
        ? response.data.meta.error
        : undefined;
      const fallbackMessage = metaMessage || metaError || response.data.action || 'API request failed';
      throw new Error(fallbackMessage);

    } catch (error) {
      console.error(`❌ ${method} ${endpoint} failed (attempt ${attempt}):`, error);

      // Retry logic for network errors
      if (attempt < this.retryAttempts && this.isRetryableError(error)) {
        const delay = this.getBackoffDelay(attempt);
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.makeRequest<T>(method, endpoint, data, attempt + 1);
      }

      throw this.handleApiError(error);
    }
  }

  /**
   * Check if an error is retryable
   */
  private isRetryableError(error: any): boolean {
    if (axios.isAxiosError(error)) {
      // Retry on network errors or 5xx server errors
      return !error.response || (error.response.status >= 500 && error.response.status < 600);
    }
    return false;
  }

  /**
   * Exponential backoff with jitter so we avoid retry stampedes
   */
  private getBackoffDelay(attempt: number): number {
    const exponentialDelay = Math.min(
      this.baseRetryDelay * Math.pow(2, attempt - 1),
      this.maxRetryDelay
    );
    const jitterFactor = 0.8 + Math.random() * 0.4; // 0.8x – 1.2x jitter
    return Math.floor(exponentialDelay * jitterFactor);
  }

  /**
   * Handle and transform API errors
   */
  private handleApiError(error: any): Error {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<ApiResponse>;
      
      if (axiosError.response?.status === 401) {
        // Authentication error - clear stored auth data
        authService.logout();
        return new Error('Authentication expired. Please log in again.');
      }
      
      if (axiosError.response?.status === 403) {
        return new Error('Access denied. Insufficient permissions.');
      }
      
      const payload = axiosError.response?.data;
      const metaError = typeof payload?.meta?.error === 'string' ? payload.meta.error : undefined;
      const metaMessage = typeof payload?.meta?.message === 'string' ? payload.meta.message : undefined;

      if (metaError || metaMessage) {
        return new Error(metaError || metaMessage!);
      }

      if (typeof payload?.action === 'string') {
        return new Error(payload.action);
      }
      
      return new Error(`API request failed: ${axiosError.message}`);
    }
    
    return error instanceof Error ? error : new Error('Unknown API error');
  }

  // Core onboarding API methods

  /**
   * Get current onboarding state for the authenticated user
   */
  async getOnboardingState(): Promise<OnboardingState | null> {
    try {
      const state = await this.makeRequest<OnboardingState>('GET', '/state');
      const localState = this.getLocalOnboardingState();

      if (localState) {
        const remoteSteps = Array.isArray(state?.completed_steps) ? state.completed_steps.length : 0;
        const localSteps = Array.isArray(localState.completed_steps) ? localState.completed_steps.length : 0;

        if (localSteps > remoteSteps || (!state?.has_started && localState.has_started)) {
          return localState;
        }
      }

      return state;
    } catch (error) {
      console.error('Failed to get onboarding state:', error);
      
      // Fallback to localStorage for offline scenarios
      return this.getLocalOnboardingState();
    }
  }

  /**
   * Update onboarding state with new progress
   */
  async updateOnboardingState(request: OnboardingStateRequest): Promise<OnboardingState> {
    try {
      const state = await this.makeRequest<OnboardingState>('PUT', '/state', request);
      
      // Also update local storage for offline scenarios
      await this.updateLocalOnboardingState(state);
      
      return state;
    } catch (error) {
      console.error('Failed to update onboarding state:', error);
      
      // Fallback to localStorage update
      const localState = await this.updateLocalOnboardingStateFallback(request);
      if (localState) {
        return localState;
      }
      throw error; // Still throw error so caller knows sync failed
    }
  }

  /**
   * Complete a specific onboarding step
   */
  async completeOnboardingStep(stepName: string, metadata?: Record<string, any>): Promise<OnboardingState> {
    try {
      const state = await this.makeRequest<OnboardingState>(
        'POST', 
        `/state/step/${encodeURIComponent(stepName)}/complete`,
        { metadata }
      );
      
      // Update local storage
      await this.updateLocalOnboardingState(state);
      
      return state;
    } catch (error) {
      console.error(`Failed to complete onboarding step ${stepName}:`, error);
      throw error;
    }
  }

  /**
   * Mark entire onboarding as complete
   */
  async completeOnboarding(metadata?: Record<string, any>): Promise<OnboardingState> {
    try {
      const state = await this.makeRequest<OnboardingState>(
        'POST', 
        '/complete',
        { metadata }
      );
      
      // Update local storage
      await this.updateLocalOnboardingState(state);
      
      return state;
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
      throw error;
    }
  }

  /**
   * Reset onboarding state (admin/testing only)
   */
  async resetOnboardingState(): Promise<void> {
    try {
      await this.makeRequest<void>('DELETE', '/state/reset');
      
      // Clear local storage
      await this.clearLocalOnboardingState();
    } catch (error) {
      console.error('Failed to reset onboarding state:', error);
      throw error;
    }
  }

  /**
   * Get onboarding analytics and insights
   */
  async getOnboardingAnalytics(): Promise<OnboardingAnalytics> {
    try {
      return await this.makeRequest<OnboardingAnalytics>('GET', '/analytics');
    } catch (error) {
      console.error('Failed to get onboarding analytics:', error);
      throw error;
    }
  }

  // Local storage fallback methods

  /**
   * Get onboarding state from localStorage
   */
  private getLocalOnboardingState(): OnboardingState | null {
    try {
      const user = authService.getStoredUser();
      if (!user?.id) return null;

      const stored = localStorage.getItem(`onboarding_${user.id}`);
      if (!stored) return null;

      const parsed = JSON.parse(stored);
      
      // Convert old format to new format if needed
      if (parsed && !parsed.user_id) {
        return {
          user_id: user.id,
          current_step: parsed.currentStep || 'service_introduction',
          completed_steps: parsed.completedSteps || [],
          has_started: parsed.hasStarted ?? true,
          is_complete: parsed.completedSteps?.includes('onboarding_complete') ?? false,
          last_active_date: parsed.lastActiveDate || new Date().toISOString(),
          metadata: parsed.metadata || {},
          created_at: parsed.lastActiveDate || new Date().toISOString(),
          updated_at: parsed.lastActiveDate || new Date().toISOString()
        };
      }

      return parsed;
    } catch (error) {
      console.error('Failed to get local onboarding state:', error);
      return null;
    }
  }

  /**
   * Update localStorage with onboarding state
   */
  private async updateLocalOnboardingState(state: OnboardingState): Promise<void> {
    try {
      const user = authService.getStoredUser();
      if (!user?.id) return;

      localStorage.setItem(`onboarding_${user.id}`, JSON.stringify(state));
    } catch (error) {
      console.error('Failed to update local onboarding state:', error);
    }
  }

  /**
   * Fallback update for local storage when API fails
   */
  private async updateLocalOnboardingStateFallback(request: OnboardingStateRequest): Promise<OnboardingState | null> {
    try {
      const user = authService.getStoredUser();
      if (!user?.id) return null;

      const current = this.getLocalOnboardingState();
      const now = new Date().toISOString();

      const updated: OnboardingState = {
        user_id: user.id,
        current_step: request.current_step,
        completed_steps: request.completed_steps || current?.completed_steps || [],
        has_started: true,
        is_complete: request.completed_steps?.includes('onboarding_complete') ?? current?.is_complete ?? false,
        last_active_date: now,
        metadata: { ...current?.metadata, ...request.metadata },
        created_at: current?.created_at || now,
        updated_at: now
      };

      await this.updateLocalOnboardingState(updated);
      return updated;
    } catch (error) {
      console.error('Failed to update local onboarding state fallback:', error);
      return null;
    }
  }

  /**
   * Clear localStorage onboarding state
   */
  private async clearLocalOnboardingState(): Promise<void> {
    try {
      const user = authService.getStoredUser();
      if (!user?.id) return;

      localStorage.removeItem(`onboarding_${user.id}`);
    } catch (error) {
      console.error('Failed to clear local onboarding state:', error);
    }
  }

  /**
   * Sync local state with backend (useful after coming back online)
   */
  async syncLocalStateWithBackend(): Promise<OnboardingState | null> {
    try {
      // Get current backend state
      const backendState = await this.makeRequest<OnboardingState>('GET', '/state');
      
      // Get local state
      const localState = this.getLocalOnboardingState();
      
      if (!localState) {
        // No local state, use backend state
        if (backendState) {
          await this.updateLocalOnboardingState(backendState);
        }
        return backendState;
      }
      
      if (!backendState) {
        // No backend state, push local state to backend
        return await this.updateOnboardingState({
          current_step: localState.current_step,
          completed_steps: localState.completed_steps,
          metadata: localState.metadata
        });
      }
      
      // Both exist, use the most recent one
      const localUpdated = new Date(localState.updated_at);
      const backendUpdated = new Date(backendState.updated_at);
      
      if (localUpdated > backendUpdated) {
        // Local is more recent, push to backend
        return await this.updateOnboardingState({
          current_step: localState.current_step,
          completed_steps: localState.completed_steps,
          metadata: localState.metadata
        });
      } else {
        // Backend is more recent, update local
        await this.updateLocalOnboardingState(backendState);
        return backendState;
      }
      
    } catch (error) {
      console.error('Failed to sync local state with backend:', error);
      return this.getLocalOnboardingState();
    }
  }
}

// Export singleton instance
export const onboardingApi = new OnboardingApiClient();

// Export utility functions
export const OnboardingStateManager = {
  /**
   * Get current onboarding state (with backend sync)
   */
  getOnboardingState: async (userId: string): Promise<OnboardingState | null> => {
    try {
      return await onboardingApi.getOnboardingState();
    } catch (error) {
      console.error('Failed to get onboarding state:', error);
      return null;
    }
  },

  /**
   * Update onboarding step (with backend sync)
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
      // Fallback to old localStorage method
      const user = authService.getStoredUser();
      if (!user?.id) return;

      const saved = localStorage.getItem(`onboarding_${user.id}`);
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
        localStorage.setItem(`onboarding_${user.id}`, JSON.stringify(updated));
      }
    }
  },

  /**
   * Mark onboarding as complete (with backend sync)
   */
  completeOnboarding: async (userId: string): Promise<void> => {
    try {
      await onboardingApi.completeOnboarding({
        completion_source: 'frontend',
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
   */
  isOnboardingComplete: async (userId: string): Promise<boolean> => {
    try {
      const state = await onboardingApi.getOnboardingState();
      return state?.is_complete || false;
    } catch (error) {
      console.error('Failed to check onboarding completion:', error);
      // Fallback to localStorage
      const saved = localStorage.getItem(`onboarding_${userId}`);
      const state = saved ? JSON.parse(saved) : null;
      return state?.completedSteps?.includes('onboarding_complete') || false;
    }
  },

  /**
   * Reset onboarding state (with backend sync)
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
