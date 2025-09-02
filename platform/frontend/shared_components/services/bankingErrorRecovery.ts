/**
 * Banking Error Recovery Service
 * ==============================
 * 
 * Comprehensive error recovery and retry mechanisms for banking integration failures.
 * Provides user-friendly error handling, automatic retries, and fallback strategies.
 * 
 * Features:
 * - Smart retry logic with exponential backoff
 * - User-friendly error classification
 * - Recovery suggestions and actions
 * - Persistent retry state management
 * - Error analytics and reporting
 */

export interface BankingError {
  code: string;
  message: string;
  type: 'network' | 'authentication' | 'provider' | 'validation' | 'server' | 'unknown';
  severity: 'low' | 'medium' | 'high' | 'critical';
  retryable: boolean;
  userMessage: string;
  suggestedActions: string[];
  metadata?: Record<string, any>;
  timestamp: string;
  provider?: 'mono' | 'generic';
}

export interface RetryConfig {
  maxAttempts: number;
  baseDelay: number; // milliseconds
  maxDelay: number; // milliseconds
  backoffMultiplier: number;
  jitter: boolean;
}

export interface RecoveryState {
  attemptCount: number;
  lastAttemptAt: string;
  nextRetryAt: string;
  isRecovering: boolean;
  errors: BankingError[];
  recoveryStrategy: 'retry' | 'fallback' | 'manual' | 'abort';
}

export interface RecoveryResult {
  success: boolean;
  error?: BankingError;
  shouldRetry: boolean;
  nextAction: 'retry' | 'fallback' | 'manual' | 'abort';
  userMessage: string;
  retryAfter?: number; // milliseconds
}

class BankingErrorRecoveryService {
  private defaultRetryConfig: RetryConfig = {
    maxAttempts: 3,
    baseDelay: 1000, // 1 second
    maxDelay: 30000, // 30 seconds
    backoffMultiplier: 2,
    jitter: true
  };

  private recoveryStates: Map<string, RecoveryState> = new Map();

  /**
   * Classify and handle a banking error
   */
  handleBankingError(error: any, context?: Record<string, any>): BankingError {
    const bankingError = this.classifyError(error, context);
    
    console.error('🚨 Banking error classified:', bankingError);
    
    // Store error for analytics
    this.logError(bankingError, context);
    
    return bankingError;
  }

  /**
   * Classify an error into a structured banking error
   */
  private classifyError(error: any, context?: Record<string, any>): BankingError {
    const timestamp = new Date().toISOString();
    const provider = context?.provider || 'generic';

    // Network errors
    if (this.isNetworkError(error)) {
      return {
        code: 'NETWORK_ERROR',
        message: error.message || 'Network connection failed',
        type: 'network',
        severity: 'medium',
        retryable: true,
        userMessage: 'Connection issue detected. We\'ll try again automatically.',
        suggestedActions: [
          'Check your internet connection',
          'Try again in a few moments',
          'Contact support if the issue persists'
        ],
        timestamp,
        provider: provider as any,
        metadata: { originalError: error.toString() }
      };
    }

    // Authentication errors
    if (this.isAuthenticationError(error)) {
      return {
        code: 'AUTH_ERROR',
        message: error.message || 'Authentication failed',
        type: 'authentication',
        severity: 'high',
        retryable: false,
        userMessage: 'Authentication issue. Please reconnect your account.',
        suggestedActions: [
          'Sign out and sign back in',
          'Clear browser cache and cookies',
          'Try connecting from a different device'
        ],
        timestamp,
        provider: provider as any,
        metadata: { status: error.status, originalError: error.toString() }
      };
    }

    // Provider-specific errors (Mono, etc.)
    if (this.isProviderError(error)) {
      return {
        code: 'PROVIDER_ERROR',
        message: error.message || 'Banking provider error',
        type: 'provider',
        severity: 'high',
        retryable: true,
        userMessage: 'Banking service temporarily unavailable. We\'ll keep trying.',
        suggestedActions: [
          'Wait a few minutes and try again',
          'Check if your bank is experiencing outages',
          'Try connecting during off-peak hours'
        ],
        timestamp,
        provider: provider as any,
        metadata: { 
          providerCode: error.code,
          providerMessage: error.message,
          originalError: error.toString()
        }
      };
    }

    // Validation errors
    if (this.isValidationError(error)) {
      return {
        code: 'VALIDATION_ERROR',
        message: error.message || 'Invalid data provided',
        type: 'validation',
        severity: 'medium',
        retryable: false,
        userMessage: 'Invalid information provided. Please check your details.',
        suggestedActions: [
          'Verify your account details',
          'Check for typos in your information',
          'Contact support for assistance'
        ],
        timestamp,
        provider: provider as any,
        metadata: { validationErrors: error.details, originalError: error.toString() }
      };
    }

    // Server errors
    if (this.isServerError(error)) {
      return {
        code: 'SERVER_ERROR',
        message: error.message || 'Server error occurred',
        type: 'server',
        severity: 'high',
        retryable: true,
        userMessage: 'Server issue detected. We\'re working to resolve this.',
        suggestedActions: [
          'Try again in a few minutes',
          'Check our status page for updates',
          'Contact support if the problem continues'
        ],
        timestamp,
        provider: provider as any,
        metadata: { status: error.status, originalError: error.toString() }
      };
    }

    // Unknown/generic errors
    return {
      code: 'UNKNOWN_ERROR',
      message: error.message || 'An unexpected error occurred',
      type: 'unknown',
      severity: 'medium',
      retryable: true,
      userMessage: 'Something went wrong. We\'ll try to resolve this automatically.',
      suggestedActions: [
        'Refresh the page and try again',
        'Clear your browser cache',
        'Contact support with error details'
      ],
      timestamp,
      provider: provider as any,
      metadata: { originalError: error.toString() }
    };
  }

  /**
   * Attempt recovery for a banking operation
   */
  async attemptRecovery(
    operationId: string,
    operation: () => Promise<any>,
    config?: Partial<RetryConfig>
  ): Promise<RecoveryResult> {
    const retryConfig = { ...this.defaultRetryConfig, ...config };
    const state = this.getRecoveryState(operationId);

    // Check if we've exceeded max attempts
    if (state.attemptCount >= retryConfig.maxAttempts) {
      return {
        success: false,
        shouldRetry: false,
        nextAction: 'abort',
        userMessage: 'Maximum retry attempts reached. Please try again later or contact support.',
        error: {
          code: 'MAX_RETRIES_EXCEEDED',
          message: 'Maximum retry attempts exceeded',
          type: 'unknown',
          severity: 'high',
          retryable: false,
          userMessage: 'Unable to complete after multiple attempts',
          suggestedActions: ['Contact support for assistance'],
          timestamp: new Date().toISOString()
        }
      };
    }

    // Check if we need to wait before next retry
    const now = new Date().getTime();
    const nextRetry = new Date(state.nextRetryAt).getTime();
    if (now < nextRetry) {
      return {
        success: false,
        shouldRetry: true,
        nextAction: 'retry',
        userMessage: `Please wait ${Math.ceil((nextRetry - now) / 1000)} seconds before retrying.`,
        retryAfter: nextRetry - now
      };
    }

    // Update state for this attempt
    state.attemptCount++;
    state.lastAttemptAt = new Date().toISOString();
    state.isRecovering = true;
    
    try {
      console.log(`🔄 Banking recovery attempt ${state.attemptCount}/${retryConfig.maxAttempts} for operation: ${operationId}`);
      
      const result = await operation();
      
      // Success - clear recovery state
      this.clearRecoveryState(operationId);
      
      return {
        success: true,
        shouldRetry: false,
        nextAction: 'retry',
        userMessage: 'Connection restored successfully!'
      };
      
    } catch (error) {
      const bankingError = this.handleBankingError(error, { operationId, attempt: state.attemptCount });
      
      state.errors.push(bankingError);
      state.isRecovering = false;
      
      // Calculate next retry time if retryable
      if (bankingError.retryable && state.attemptCount < retryConfig.maxAttempts) {
        const delay = this.calculateRetryDelay(state.attemptCount, retryConfig);
        state.nextRetryAt = new Date(Date.now() + delay).toISOString();
        state.recoveryStrategy = 'retry';
        
        this.setRecoveryState(operationId, state);
        
        return {
          success: false,
          error: bankingError,
          shouldRetry: true,
          nextAction: 'retry',
          userMessage: `${bankingError.userMessage} Retrying in ${Math.ceil(delay / 1000)} seconds...`,
          retryAfter: delay
        };
      } else {
        state.recoveryStrategy = bankingError.retryable ? 'abort' : 'manual';
        this.setRecoveryState(operationId, state);
        
        return {
          success: false,
          error: bankingError,
          shouldRetry: false,
          nextAction: bankingError.retryable ? 'abort' : 'manual',
          userMessage: bankingError.userMessage
        };
      }
    }
  }

  /**
   * Get recovery suggestions for a specific error
   */
  getRecoverySuggestions(error: BankingError): {
    immediate: string[];
    alternative: string[];
    support: string[];
  } {
    const suggestions = {
      immediate: [...error.suggestedActions],
      alternative: [] as string[],
      support: [] as string[]
    };

    switch (error.type) {
      case 'network':
        suggestions.alternative = [
          'Try using mobile data instead of WiFi',
          'Use a different browser or device',
          'Disable VPN if active'
        ];
        suggestions.support = [
          'Check our status page',
          'Report connectivity issues'
        ];
        break;

      case 'authentication':
        suggestions.alternative = [
          'Use incognito/private browsing mode',
          'Try connecting from a different device',
          'Reset your account password'
        ];
        suggestions.support = [
          'Contact account support',
          'Request account verification'
        ];
        break;

      case 'provider':
        suggestions.alternative = [
          'Try connecting to a different bank',
          'Use manual account linking',
          'Check bank maintenance schedules'
        ];
        suggestions.support = [
          'Report banking provider issues',
          'Request manual account linking'
        ];
        break;

      case 'validation':
        suggestions.alternative = [
          'Double-check account numbers',
          'Verify spelling of bank names',
          'Ensure account is active'
        ];
        suggestions.support = [
          'Provide account verification documents',
          'Request manual verification'
        ];
        break;

      default:
        suggestions.alternative = [
          'Refresh the page and try again',
          'Try from a different device',
          'Clear browser cache and cookies'
        ];
        suggestions.support = [
          'Report this issue',
          'Request technical assistance'
        ];
    }

    return suggestions;
  }

  /**
   * Check if an error should trigger automatic retry
   */
  shouldAutoRetry(error: BankingError, attemptCount: number): boolean {
    if (!error.retryable) return false;
    if (attemptCount >= this.defaultRetryConfig.maxAttempts) return false;
    
    // Don't auto-retry authentication or validation errors
    if (error.type === 'authentication' || error.type === 'validation') return false;
    
    return true;
  }

  /**
   * Create a user-friendly error message with recovery options
   */
  createUserFriendlyMessage(error: BankingError, recoveryResult?: RecoveryResult): {
    title: string;
    message: string;
    actions: Array<{
      label: string;
      action: 'retry' | 'fallback' | 'manual' | 'support';
      primary?: boolean;
    }>;
  } {
    let title = 'Banking Connection Issue';
    let message = error.userMessage;
    const actions: Array<{ label: string; action: 'retry' | 'fallback' | 'manual' | 'support'; primary?: boolean }> = [];

    switch (error.severity) {
      case 'low':
        title = 'Minor Connection Issue';
        break;
      case 'medium':
        title = 'Banking Connection Problem';
        break;
      case 'high':
        title = 'Banking Service Unavailable';
        break;
      case 'critical':
        title = 'Critical Banking Error';
        break;
    }

    // Add appropriate actions based on error type and recovery status
    if (recoveryResult?.shouldRetry) {
      actions.push({
        label: recoveryResult.retryAfter ? 'Retry Automatically' : 'Retry Now',
        action: 'retry',
        primary: true
      });
    }

    if (error.type !== 'authentication') {
      actions.push({
        label: 'Try Alternative Method',
        action: 'fallback'
      });
    }

    if (error.type === 'authentication' || error.type === 'validation') {
      actions.push({
        label: 'Fix Account Details',
        action: 'manual',
        primary: true
      });
    }

    actions.push({
      label: 'Contact Support',
      action: 'support'
    });

    return { title, message, actions };
  }

  // Helper methods for error classification
  private isNetworkError(error: any): boolean {
    return (
      error.code === 'NETWORK_ERROR' ||
      error.message?.includes('network') ||
      error.message?.includes('connection') ||
      error.name === 'NetworkError' ||
      !error.status // No HTTP status usually indicates network issue
    );
  }

  private isAuthenticationError(error: any): boolean {
    return (
      error.status === 401 ||
      error.status === 403 ||
      error.code === 'AUTH_ERROR' ||
      error.message?.includes('authentication') ||
      error.message?.includes('unauthorized') ||
      error.message?.includes('forbidden')
    );
  }

  private isProviderError(error: any): boolean {
    return (
      error.provider ||
      error.code?.startsWith('MONO_') ||
      error.message?.includes('provider') ||
      error.message?.includes('bank') ||
      (error.status >= 502 && error.status <= 504)
    );
  }

  private isValidationError(error: any): boolean {
    return (
      error.status === 400 ||
      error.code === 'VALIDATION_ERROR' ||
      error.message?.includes('validation') ||
      error.message?.includes('invalid') ||
      error.details // Validation errors often have details
    );
  }

  private isServerError(error: any): boolean {
    return (
      error.status >= 500 ||
      error.code === 'SERVER_ERROR' ||
      error.message?.includes('server') ||
      error.message?.includes('internal')
    );
  }

  // Recovery state management
  private getRecoveryState(operationId: string): RecoveryState {
    if (!this.recoveryStates.has(operationId)) {
      const newState: RecoveryState = {
        attemptCount: 0,
        lastAttemptAt: new Date().toISOString(),
        nextRetryAt: new Date().toISOString(),
        isRecovering: false,
        errors: [],
        recoveryStrategy: 'retry'
      };
      this.recoveryStates.set(operationId, newState);
    }
    return this.recoveryStates.get(operationId)!;
  }

  private setRecoveryState(operationId: string, state: RecoveryState): void {
    this.recoveryStates.set(operationId, state);
  }

  private clearRecoveryState(operationId: string): void {
    this.recoveryStates.delete(operationId);
  }

  private calculateRetryDelay(attemptCount: number, config: RetryConfig): number {
    let delay = config.baseDelay * Math.pow(config.backoffMultiplier, attemptCount - 1);
    delay = Math.min(delay, config.maxDelay);
    
    if (config.jitter) {
      // Add ±25% jitter to prevent thundering herd
      const jitterRange = delay * 0.25;
      delay += (Math.random() - 0.5) * 2 * jitterRange;
    }
    
    return Math.max(delay, config.baseDelay);
  }

  private logError(error: BankingError, context?: Record<string, any>): void {
    // In a real implementation, this would send to analytics/monitoring service
    console.error('Banking Error Log:', {
      error,
      context,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    });
  }
}

// Export singleton instance
export const bankingErrorRecovery = new BankingErrorRecoveryService();

// Export hook for React components
export const useBankingErrorRecovery = () => {
  return {
    handleError: bankingErrorRecovery.handleBankingError.bind(bankingErrorRecovery),
    attemptRecovery: bankingErrorRecovery.attemptRecovery.bind(bankingErrorRecovery),
    getSuggestions: bankingErrorRecovery.getRecoverySuggestions.bind(bankingErrorRecovery),
    shouldAutoRetry: bankingErrorRecovery.shouldAutoRetry.bind(bankingErrorRecovery),
    createUserMessage: bankingErrorRecovery.createUserFriendlyMessage.bind(bankingErrorRecovery)
  };
};

export default bankingErrorRecovery;
