import React from 'react';

/**
 * Onboarding Analytics Service
 * ===========================
 * 
 * Comprehensive analytics tracking for onboarding flows across all user roles.
 * Provides detailed insights into completion rates, drop-off points, user behavior,
 * and performance metrics.
 * 
 * Features:
 * - Step-by-step completion tracking
 * - Drop-off point identification
 * - Time-based performance metrics
 * - User behavior analytics
 * - A/B testing support
 * - Real-time event tracking
 */

interface OnboardingEvent {
  eventType: 'step_start' | 'step_complete' | 'step_skip' | 'step_error' | 'session_start' | 'session_complete' | 'session_abandon';
  stepId: string;
  userId: string;
  userRole: 'si' | 'app' | 'hybrid';
  timestamp: string;
  sessionId: string;
  metadata: Record<string, any>;
}

interface OnboardingMetrics {
  completionRate: number;
  averageCompletionTime: number;
  dropOffPoints: Array<{
    stepId: string;
    dropOffRate: number;
    userCount: number;
  }>;
  stepPerformance: Array<{
    stepId: string;
    completionRate: number;
    averageTime: number;
    errorRate: number;
    skipRate: number;
  }>;
  userSegments: Array<{
    role: string;
    completionRate: number;
    averageTime: number;
    commonDropOff: string;
  }>;
  timeBasedMetrics: {
    hourlyDistribution: Record<number, number>;
    dailyDistribution: Record<string, number>;
    weeklyTrends: Record<string, number>;
  };
}

interface AnalyticsConfig {
  enableTracking: boolean;
  sampleRate: number;
  batchSize: number;
  flushInterval: number;
  enableDebugMode: boolean;
  apiEndpoint: string;
}

class OnboardingAnalyticsService {
  private config: AnalyticsConfig;
  private eventQueue: OnboardingEvent[] = [];
  private sessionStartTime: Date | null = null;
  private currentSessionId: string | null = null;
  private flushTimer: NodeJS.Timeout | null = null;
  private isInitialized = false;

  constructor(config: Partial<AnalyticsConfig> = {}) {
    this.config = {
      enableTracking: true,
      sampleRate: 1.0,
      batchSize: 10,
      flushInterval: 30000, // 30 seconds
      enableDebugMode: false,
      apiEndpoint: '/api/v1/analytics/onboarding',
      ...config
    };

    if (typeof window !== 'undefined') {
      this.initialize();
    }
  }

  /**
   * Initialize analytics service
   */
  private initialize(): void {
    if (this.isInitialized) return;

    // Start flush timer
    this.startFlushTimer();

    // Handle page unload
    window.addEventListener('beforeunload', () => {
      this.flush(true);
    });

    // Handle visibility changes
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        this.flush();
      }
    });

    this.isInitialized = true;
    this.debug('Analytics service initialized');
  }

  /**
   * Start session tracking
   */
  public startSession(userId: string, userRole: 'si' | 'app' | 'hybrid', metadata: Record<string, any> = {}): void {
    if (!this.shouldTrack()) return;

    this.currentSessionId = this.generateSessionId();
    this.sessionStartTime = new Date();

    this.trackEvent({
      eventType: 'session_start',
      stepId: 'session_start',
      userId,
      userRole,
      timestamp: new Date().toISOString(),
      sessionId: this.currentSessionId,
      metadata: {
        ...metadata,
        userAgent: navigator.userAgent,
        referrer: document.referrer,
        screenResolution: `${screen.width}x${screen.height}`,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        language: navigator.language
      }
    });

    this.debug('Session started', { sessionId: this.currentSessionId, userId, userRole });
  }

  /**
   * Track step start
   */
  public trackStepStart(stepId: string, userId: string, userRole: 'si' | 'app' | 'hybrid', metadata: Record<string, any> = {}): void {
    if (!this.shouldTrack()) return;

    this.trackEvent({
      eventType: 'step_start',
      stepId,
      userId,
      userRole,
      timestamp: new Date().toISOString(),
      sessionId: this.currentSessionId || this.generateSessionId(),
      metadata: {
        ...metadata,
        stepStartTime: Date.now()
      }
    });

    this.debug('Step started', { stepId, userId });
  }

  /**
   * Track step completion
   */
  public trackStepComplete(
    stepId: string, 
    userId: string, 
    userRole: 'si' | 'app' | 'hybrid', 
    duration: number,
    metadata: Record<string, any> = {}
  ): void {
    if (!this.shouldTrack()) return;

    this.trackEvent({
      eventType: 'step_complete',
      stepId,
      userId,
      userRole,
      timestamp: new Date().toISOString(),
      sessionId: this.currentSessionId || this.generateSessionId(),
      metadata: {
        ...metadata,
        duration,
        completedAt: Date.now()
      }
    });

    this.debug('Step completed', { stepId, userId, duration });
  }

  /**
   * Track step skip
   */
  public trackStepSkip(stepId: string, userId: string, userRole: 'si' | 'app' | 'hybrid', reason: string, metadata: Record<string, any> = {}): void {
    if (!this.shouldTrack()) return;

    this.trackEvent({
      eventType: 'step_skip',
      stepId,
      userId,
      userRole,
      timestamp: new Date().toISOString(),
      sessionId: this.currentSessionId || this.generateSessionId(),
      metadata: {
        ...metadata,
        skipReason: reason,
        skippedAt: Date.now()
      }
    });

    this.debug('Step skipped', { stepId, userId, reason });
  }

  /**
   * Track step error
   */
  public trackStepError(
    stepId: string, 
    userId: string, 
    userRole: 'si' | 'app' | 'hybrid', 
    error: Error | string,
    metadata: Record<string, any> = {}
  ): void {
    if (!this.shouldTrack()) return;

    const errorMessage = error instanceof Error ? error.message : error;
    const errorStack = error instanceof Error ? error.stack : undefined;

    this.trackEvent({
      eventType: 'step_error',
      stepId,
      userId,
      userRole,
      timestamp: new Date().toISOString(),
      sessionId: this.currentSessionId || this.generateSessionId(),
      metadata: {
        ...metadata,
        errorMessage,
        errorStack,
        errorType: error instanceof Error ? error.constructor.name : 'String',
        errorAt: Date.now()
      }
    });

    this.debug('Step error', { stepId, userId, error: errorMessage });
  }

  /**
   * Track session completion
   */
  public trackSessionComplete(userId: string, userRole: 'si' | 'app' | 'hybrid', metadata: Record<string, any> = {}): void {
    if (!this.shouldTrack()) return;

    const sessionDuration = this.sessionStartTime 
      ? Date.now() - this.sessionStartTime.getTime()
      : 0;

    this.trackEvent({
      eventType: 'session_complete',
      stepId: 'session_complete',
      userId,
      userRole,
      timestamp: new Date().toISOString(),
      sessionId: this.currentSessionId || this.generateSessionId(),
      metadata: {
        ...metadata,
        sessionDuration,
        completedAt: Date.now()
      }
    });

    this.debug('Session completed', { userId, duration: sessionDuration });
    
    // Reset session
    this.currentSessionId = null;
    this.sessionStartTime = null;
  }

  /**
   * Track session abandonment
   */
  public trackSessionAbandon(userId: string, userRole: 'si' | 'app' | 'hybrid', currentStep: string, metadata: Record<string, any> = {}): void {
    if (!this.shouldTrack()) return;

    const sessionDuration = this.sessionStartTime 
      ? Date.now() - this.sessionStartTime.getTime()
      : 0;

    this.trackEvent({
      eventType: 'session_abandon',
      stepId: currentStep,
      userId,
      userRole,
      timestamp: new Date().toISOString(),
      sessionId: this.currentSessionId || this.generateSessionId(),
      metadata: {
        ...metadata,
        sessionDuration,
        abandonedAt: Date.now(),
        lastCompletedStep: currentStep
      }
    });

    this.debug('Session abandoned', { userId, currentStep, duration: sessionDuration });
  }

  /**
   * Track custom event
   */
  public trackCustomEvent(
    eventName: string,
    stepId: string,
    userId: string,
    userRole: 'si' | 'app' | 'hybrid',
    metadata: Record<string, any> = {}
  ): void {
    if (!this.shouldTrack()) return;

    this.trackEvent({
      eventType: 'step_complete', // Use existing type for custom events
      stepId: `custom_${eventName}`,
      userId,
      userRole,
      timestamp: new Date().toISOString(),
      sessionId: this.currentSessionId || this.generateSessionId(),
      metadata: {
        ...metadata,
        customEvent: eventName,
        customEventAt: Date.now()
      }
    });

    this.debug('Custom event tracked', { eventName, stepId, userId });
  }

  /**
   * Get analytics metrics
   */
  public async getMetrics(
    timeRange: { start: Date; end: Date },
    userRole?: 'si' | 'app' | 'hybrid'
  ): Promise<OnboardingMetrics> {
    try {
      const params = new URLSearchParams({
        start: timeRange.start.toISOString(),
        end: timeRange.end.toISOString(),
        ...(userRole && { role: userRole })
      });

      const response = await fetch(`${this.config.apiEndpoint}/metrics?${params}`);
      
      if (!response.ok) {
        throw new Error(`Analytics API error: ${response.status}`);
      }

      const metrics: OnboardingMetrics = await response.json();
      return metrics;
    } catch (error) {
      console.error('Failed to fetch analytics metrics:', error);
      throw error;
    }
  }

  /**
   * Get real-time dashboard data
   */
  public async getDashboardData(): Promise<{
    activeUsers: number;
    completionRateToday: number;
    topDropOffStep: string;
    averageSessionTime: number;
  }> {
    try {
      const response = await fetch(`${this.config.apiEndpoint}/dashboard`);
      
      if (!response.ok) {
        throw new Error(`Dashboard API error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      throw error;
    }
  }

  /**
   * Track event internally
   */
  private trackEvent(event: OnboardingEvent): void {
    this.eventQueue.push(event);
    
    if (this.eventQueue.length >= this.config.batchSize) {
      this.flush();
    }
  }

  /**
   * Flush events to server
   */
  private async flush(force = false): Promise<void> {
    if (this.eventQueue.length === 0) return;
    if (!force && !this.shouldFlush()) return;

    const eventsToSend = [...this.eventQueue];
    this.eventQueue = [];

    try {
      const response = await fetch(this.config.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          events: eventsToSend,
          timestamp: new Date().toISOString()
        })
      });

      if (!response.ok) {
        // Re-queue events on failure
        this.eventQueue.unshift(...eventsToSend);
        throw new Error(`Analytics flush failed: ${response.status}`);
      }

      this.debug(`Flushed ${eventsToSend.length} events`);
    } catch (error) {
      console.error('Failed to flush analytics events:', error);
      
      // Re-queue events on network error
      this.eventQueue.unshift(...eventsToSend);
    }
  }

  /**
   * Start flush timer
   */
  private startFlushTimer(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }

    this.flushTimer = setInterval(() => {
      this.flush();
    }, this.config.flushInterval);
  }

  /**
   * Generate unique session ID
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Check if tracking should be enabled
   */
  private shouldTrack(): boolean {
    if (!this.config.enableTracking) return false;
    if (Math.random() > this.config.sampleRate) return false;
    return true;
  }

  /**
   * Check if events should be flushed
   */
  private shouldFlush(): boolean {
    return this.eventQueue.length > 0;
  }

  /**
   * Debug logging
   */
  private debug(message: string, data?: any): void {
    if (this.config.enableDebugMode) {
      console.log(`[OnboardingAnalytics] ${message}`, data || '');
    }
  }

  /**
   * Cleanup resources
   */
  public destroy(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
    
    this.flush(true);
    this.isInitialized = false;
  }
}

// Export singleton instance
export const onboardingAnalytics = new OnboardingAnalyticsService({
  enableTracking: process.env.NODE_ENV === 'production',
  enableDebugMode: process.env.NODE_ENV === 'development',
  apiEndpoint: process.env.NEXT_PUBLIC_API_BASE_URL + '/api/v1/analytics/onboarding'
});

// Export hook for React components
export const useOnboardingAnalytics = () => {
  const [isInitialized, setIsInitialized] = React.useState(false);
  
  React.useEffect(() => {
    setIsInitialized(true);
    
    return () => {
      onboardingAnalytics.destroy();
    };
  }, []);
  
  return {
    isInitialized,
    startSession: onboardingAnalytics.startSession.bind(onboardingAnalytics),
    trackStepStart: onboardingAnalytics.trackStepStart.bind(onboardingAnalytics),
    trackStepComplete: onboardingAnalytics.trackStepComplete.bind(onboardingAnalytics),
    trackStepSkip: onboardingAnalytics.trackStepSkip.bind(onboardingAnalytics),
    trackStepError: onboardingAnalytics.trackStepError.bind(onboardingAnalytics),
    trackSessionComplete: onboardingAnalytics.trackSessionComplete.bind(onboardingAnalytics),
    trackSessionAbandon: onboardingAnalytics.trackSessionAbandon.bind(onboardingAnalytics),
    trackCustomEvent: onboardingAnalytics.trackCustomEvent.bind(onboardingAnalytics),
    getMetrics: onboardingAnalytics.getMetrics.bind(onboardingAnalytics),
    getDashboardData: onboardingAnalytics.getDashboardData.bind(onboardingAnalytics)
  };
};

export default onboardingAnalytics;
