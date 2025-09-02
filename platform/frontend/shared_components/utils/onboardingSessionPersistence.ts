import React from 'react';

/**
 * Onboarding Session Persistence
 * ==============================
 * 
 * Utilities for persisting onboarding session data across browser restarts,
 * tab closures, and network interruptions. Ensures users can always resume
 * their onboarding progress.
 * 
 * Features:
 * - Cross-tab synchronization
 * - Automatic session recovery
 * - Data integrity validation
 * - Session expiry management
 * - Conflict resolution
 */

interface OnboardingSessionData {
  userId: string;
  currentStep: string;
  completedSteps: string[];
  userRole: string;
  sessionId: string;
  startTime: string;
  lastActiveTime: string;
  metadata: Record<string, any>;
  version: number;
}

interface SessionSyncEvent {
  type: 'session_update' | 'session_resume' | 'session_complete' | 'session_conflict';
  data: OnboardingSessionData;
  timestamp: string;
  tabId: string;
}

class OnboardingSessionPersistence {
  private readonly STORAGE_KEY = 'taxpoynt_onboarding_session';
  private readonly SYNC_EVENT_KEY = 'taxpoynt_onboarding_sync';
  private readonly SESSION_VERSION = 1;
  private readonly MAX_SESSION_AGE_DAYS = 30;
  
  private tabId: string;
  private syncListeners: ((event: SessionSyncEvent) => void)[] = [];
  private currentSession: OnboardingSessionData | null = null;

  constructor() {
    this.tabId = this.generateTabId();
    this.setupStorageListener();
  }

  /**
   * Generate unique tab identifier
   */
  private generateTabId(): string {
    return `tab_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Setup storage listener for cross-tab synchronization
   */
  private setupStorageListener(): void {
    if (typeof window === 'undefined') return;

    window.addEventListener('storage', (event) => {
      if (event.key === this.SYNC_EVENT_KEY && event.newValue) {
        try {
          const syncEvent: SessionSyncEvent = JSON.parse(event.newValue);
          
          // Don't process events from same tab
          if (syncEvent.tabId === this.tabId) return;
          
          this.handleSyncEvent(syncEvent);
        } catch (error) {
          console.warn('Failed to parse session sync event:', error);
        }
      }
    });

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
      this.updateLastActiveTime();
    });

    // Handle visibility changes
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        this.handleTabFocus();
      } else {
        this.updateLastActiveTime();
      }
    });
  }

  /**
   * Handle cross-tab sync events
   */
  private handleSyncEvent(event: SessionSyncEvent): void {
    // Notify listeners
    this.syncListeners.forEach(listener => {
      try {
        listener(event);
      } catch (error) {
        console.error('Session sync listener error:', error);
      }
    });

    // Handle specific event types
    switch (event.type) {
      case 'session_update':
        this.handleSessionUpdate(event.data);
        break;
      case 'session_complete':
        this.handleSessionComplete(event.data);
        break;
      case 'session_conflict':
        this.handleSessionConflict(event.data);
        break;
    }
  }

  /**
   * Handle session update from another tab
   */
  private handleSessionUpdate(sessionData: OnboardingSessionData): void {
    const currentSession = this.getSession();
    
    if (!currentSession || sessionData.version > currentSession.version) {
      // Accept newer version
      this.currentSession = sessionData;
    } else if (sessionData.version === currentSession.version) {
      // Merge sessions with same version
      this.currentSession = this.mergeSessions(currentSession, sessionData);
    }
  }

  /**
   * Handle session completion from another tab
   */
  private handleSessionComplete(sessionData: OnboardingSessionData): void {
    this.currentSession = sessionData;
    this.saveSession(sessionData);
  }

  /**
   * Handle session conflict resolution
   */
  private handleSessionConflict(sessionData: OnboardingSessionData): void {
    const currentSession = this.getSession();
    
    if (!currentSession) {
      this.currentSession = sessionData;
      return;
    }

    // Resolve conflict by choosing session with more progress
    const currentProgress = currentSession.completedSteps.length;
    const incomingProgress = sessionData.completedSteps.length;
    
    if (incomingProgress > currentProgress) {
      this.currentSession = sessionData;
      this.saveSession(sessionData);
    }
  }

  /**
   * Handle tab focus (user switched back to this tab)
   */
  private handleTabFocus(): void {
    // Check if session was updated in another tab
    const storedSession = this.getStoredSession();
    
    if (storedSession && this.currentSession) {
      if (storedSession.version > this.currentSession.version) {
        this.currentSession = storedSession;
        
        // Notify that session was updated
        this.broadcastSyncEvent({
          type: 'session_resume',
          data: storedSession,
          timestamp: new Date().toISOString(),
          tabId: this.tabId
        });
      }
    }
  }

  /**
   * Merge two session objects, preferring newer data
   */
  private mergeSessions(
    session1: OnboardingSessionData, 
    session2: OnboardingSessionData
  ): OnboardingSessionData {
    const lastActive1 = new Date(session1.lastActiveTime);
    const lastActive2 = new Date(session2.lastActiveTime);
    
    // Use the session with more recent activity as base
    const baseSession = lastActive1 > lastActive2 ? session1 : session2;
    const otherSession = lastActive1 > lastActive2 ? session2 : session1;
    
    // Merge completed steps (union)
    const mergedCompletedSteps = Array.from(new Set([
      ...baseSession.completedSteps,
      ...otherSession.completedSteps
    ]));
    
    // Use the most advanced current step
    const steps = ['service_introduction', 'integration_choice', 'business_systems_setup', 
                  'financial_systems_setup', 'banking_connected', 'reconciliation_setup', 
                  'integration_setup', 'onboarding_complete'];
    
    const step1Index = steps.indexOf(session1.currentStep);
    const step2Index = steps.indexOf(session2.currentStep);
    const currentStep = step1Index > step2Index ? session1.currentStep : session2.currentStep;
    
    return {
      ...baseSession,
      currentStep,
      completedSteps: mergedCompletedSteps,
      lastActiveTime: new Date().toISOString(),
      version: Math.max(session1.version, session2.version) + 1,
      metadata: {
        ...baseSession.metadata,
        ...otherSession.metadata,
        mergedAt: new Date().toISOString(),
        mergedFrom: [session1.sessionId, session2.sessionId]
      }
    };
  }

  /**
   * Broadcast sync event to other tabs
   */
  private broadcastSyncEvent(event: SessionSyncEvent): void {
    if (typeof window === 'undefined') return;

    try {
      // Use localStorage to communicate with other tabs
      localStorage.setItem(this.SYNC_EVENT_KEY, JSON.stringify(event));
      
      // Clear the event after a short delay to avoid accumulation
      setTimeout(() => {
        localStorage.removeItem(this.SYNC_EVENT_KEY);
      }, 100);
    } catch (error) {
      console.warn('Failed to broadcast sync event:', error);
    }
  }

  /**
   * Get session from localStorage
   */
  private getStoredSession(): OnboardingSessionData | null {
    if (typeof window === 'undefined') return null;

    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      if (!stored) return null;

      const session: OnboardingSessionData = JSON.parse(stored);
      
      // Validate session age
      const sessionAge = Date.now() - new Date(session.startTime).getTime();
      const maxAge = this.MAX_SESSION_AGE_DAYS * 24 * 60 * 60 * 1000;
      
      if (sessionAge > maxAge) {
        this.clearSession();
        return null;
      }

      return session;
    } catch (error) {
      console.warn('Failed to load stored session:', error);
      return null;
    }
  }

  /**
   * Save session to localStorage
   */
  private saveSession(session: OnboardingSessionData): void {
    if (typeof window === 'undefined') return;

    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(session));
    } catch (error) {
      console.error('Failed to save session:', error);
    }
  }

  /**
   * Initialize new session
   */
  public initializeSession(userId: string, userRole: string): OnboardingSessionData {
    const session: OnboardingSessionData = {
      userId,
      currentStep: 'service_introduction',
      completedSteps: [],
      userRole,
      sessionId: `session_${Date.now()}_${userId}`,
      startTime: new Date().toISOString(),
      lastActiveTime: new Date().toISOString(),
      metadata: {
        tabId: this.tabId,
        createdBy: 'OnboardingSessionPersistence',
        version: this.SESSION_VERSION
      },
      version: 1
    };

    this.currentSession = session;
    this.saveSession(session);
    
    this.broadcastSyncEvent({
      type: 'session_update',
      data: session,
      timestamp: new Date().toISOString(),
      tabId: this.tabId
    });

    return session;
  }

  /**
   * Get current session
   */
  public getSession(): OnboardingSessionData | null {
    if (this.currentSession) {
      return this.currentSession;
    }

    this.currentSession = this.getStoredSession();
    return this.currentSession;
  }

  /**
   * Update session data
   */
  public updateSession(updates: Partial<OnboardingSessionData>): OnboardingSessionData | null {
    const currentSession = this.getSession();
    if (!currentSession) return null;

    const updatedSession: OnboardingSessionData = {
      ...currentSession,
      ...updates,
      lastActiveTime: new Date().toISOString(),
      version: currentSession.version + 1
    };

    this.currentSession = updatedSession;
    this.saveSession(updatedSession);

    this.broadcastSyncEvent({
      type: 'session_update',
      data: updatedSession,
      timestamp: new Date().toISOString(),
      tabId: this.tabId
    });

    return updatedSession;
  }

  /**
   * Complete session
   */
  public completeSession(): void {
    const session = this.getSession();
    if (!session) return;

    const completedSession: OnboardingSessionData = {
      ...session,
      currentStep: 'onboarding_complete',
      completedSteps: [...session.completedSteps, 'onboarding_complete'],
      lastActiveTime: new Date().toISOString(),
      version: session.version + 1,
      metadata: {
        ...session.metadata,
        completedAt: new Date().toISOString()
      }
    };

    this.currentSession = completedSession;
    this.saveSession(completedSession);

    this.broadcastSyncEvent({
      type: 'session_complete',
      data: completedSession,
      timestamp: new Date().toISOString(),
      tabId: this.tabId
    });
  }

  /**
   * Update last active time
   */
  public updateLastActiveTime(): void {
    if (this.currentSession) {
      this.updateSession({
        lastActiveTime: new Date().toISOString()
      });
    }
  }

  /**
   * Clear session data
   */
  public clearSession(): void {
    if (typeof window === 'undefined') return;

    this.currentSession = null;
    localStorage.removeItem(this.STORAGE_KEY);
  }

  /**
   * Add sync listener
   */
  public addSyncListener(listener: (event: SessionSyncEvent) => void): () => void {
    this.syncListeners.push(listener);
    
    return () => {
      const index = this.syncListeners.indexOf(listener);
      if (index > -1) {
        this.syncListeners.splice(index, 1);
      }
    };
  }

  /**
   * Check if session exists and is valid
   */
  public hasValidSession(userId: string): boolean {
    const session = this.getSession();
    return session !== null && session.userId === userId;
  }

  /**
   * Get session analytics
   */
  public getSessionAnalytics(): {
    duration: number;
    stepsCompleted: number;
    lastActive: string;
    isStale: boolean;
  } | null {
    const session = this.getSession();
    if (!session) return null;

    const now = new Date();
    const startTime = new Date(session.startTime);
    const lastActive = new Date(session.lastActiveTime);
    
    const duration = now.getTime() - startTime.getTime();
    const timeSinceLastActive = now.getTime() - lastActive.getTime();
    const isStale = timeSinceLastActive > (24 * 60 * 60 * 1000); // 24 hours

    return {
      duration,
      stepsCompleted: session.completedSteps.length,
      lastActive: session.lastActiveTime,
      isStale
    };
  }
}

// Export singleton instance
export const sessionPersistence = new OnboardingSessionPersistence();

// Export hook for React components
export const useSessionPersistence = () => {
  const [session, setSession] = React.useState<OnboardingSessionData | null>(null);
  
  React.useEffect(() => {
    const currentSession = sessionPersistence.getSession();
    setSession(currentSession);
    
    const unsubscribe = sessionPersistence.addSyncListener((event) => {
      setSession(event.data);
    });
    
    return unsubscribe;
  }, []);
  
  return {
    session,
    initializeSession: sessionPersistence.initializeSession.bind(sessionPersistence),
    updateSession: sessionPersistence.updateSession.bind(sessionPersistence),
    completeSession: sessionPersistence.completeSession.bind(sessionPersistence),
    clearSession: sessionPersistence.clearSession.bind(sessionPersistence),
    hasValidSession: sessionPersistence.hasValidSession.bind(sessionPersistence),
    getSessionAnalytics: sessionPersistence.getSessionAnalytics.bind(sessionPersistence)
  };
};

export default sessionPersistence;
