/**
 * Integration Error Recovery Service
 * =================================
 * 
 * Comprehensive error recovery and retry mechanisms for all integration failures.
 * Extends the banking error recovery to cover ERP, CRM, POS, and other integrations.
 * 
 * Features:
 * - Universal error classification for all integration types
 * - Smart retry logic with exponential backoff
 * - Integration-specific recovery strategies
 * - User-friendly error messages and suggestions
 * - Cross-integration error correlation
 * - Recovery analytics and reporting
 */

export interface IntegrationError {
  code: string;
  message: string;
  integrationType: 'banking' | 'erp' | 'crm' | 'pos' | 'ecommerce' | 'accounting' | 'generic';
  provider?: string; // e.g., 'mono', 'odoo', 'salesforce', 'square'
  type: 'network' | 'authentication' | 'configuration' | 'validation' | 'server' | 'permission' | 'timeout' | 'unknown';
  severity: 'low' | 'medium' | 'high' | 'critical';
  retryable: boolean;
  userMessage: string;
  technicalMessage: string;
  suggestedActions: string[];
  recoveryStrategy: 'auto_retry' | 'user_retry' | 'reconfigure' | 'manual_intervention' | 'contact_support';
  metadata?: Record<string, any>;
  timestamp: string;
  correlationId?: string; // For tracking related errors
}

export interface RetryConfig {
  maxAttempts: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
  jitter: boolean;
  timeoutMs?: number;
}

export interface RecoveryState {
  integrationId: string;
  integrationType: string;
  attemptCount: number;
  lastAttemptAt: string;
  nextRetryAt: string;
  isRecovering: boolean;
  errors: IntegrationError[];
  recoveryStrategy: string;
  userNotified: boolean;
}

export interface RecoveryResult {
  success: boolean;
  error?: IntegrationError;
  shouldRetry: boolean;
  nextAction: 'retry' | 'reconfigure' | 'skip' | 'contact_support';
  userMessage: string;
  technicalDetails?: string;
  retryAfter?: number; // milliseconds
  recoveryOptions: RecoveryOption[];
}

export interface RecoveryOption {
  id: string;
  title: string;
  description: string;
  action: 'retry' | 'reconfigure' | 'skip' | 'help';
  primary: boolean;
  estimatedTime?: string;
  difficulty: 'easy' | 'medium' | 'advanced';
}

class IntegrationErrorRecoveryService {
  private defaultRetryConfigs: Record<string, RetryConfig> = {
    banking: {
      maxAttempts: 3,
      baseDelay: 2000,
      maxDelay: 30000,
      backoffMultiplier: 2,
      jitter: true,
      timeoutMs: 60000
    },
    erp: {
      maxAttempts: 4,
      baseDelay: 3000,
      maxDelay: 45000,
      backoffMultiplier: 1.8,
      jitter: true,
      timeoutMs: 90000
    },
    crm: {
      maxAttempts: 3,
      baseDelay: 1500,
      maxDelay: 20000,
      backoffMultiplier: 2,
      jitter: true,
      timeoutMs: 45000
    },
    pos: {
      maxAttempts: 2,
      baseDelay: 1000,
      maxDelay: 10000,
      backoffMultiplier: 2,
      jitter: false,
      timeoutMs: 30000
    },
    generic: {
      maxAttempts: 3,
      baseDelay: 2000,
      maxDelay: 30000,
      backoffMultiplier: 2,
      jitter: true,
      timeoutMs: 60000
    }
  };

  private recoveryStates: Map<string, RecoveryState> = new Map();

  /**
   * Classify and handle an integration error
   */
  handleIntegrationError(
    error: any, 
    integrationType: string, 
    provider?: string,
    context?: Record<string, any>
  ): IntegrationError {
    const integrationError = this.classifyError(error, integrationType, provider, context);
    
    console.error('🚨 Integration error classified:', integrationError);
    
    // Store error for analytics
    this.logError(integrationError, context);
    
    return integrationError;
  }

  /**
   * Classify an error into a structured integration error
   */
  private classifyError(
    error: any, 
    integrationType: string, 
    provider?: string,
    context?: Record<string, any>
  ): IntegrationError {
    const timestamp = new Date().toISOString();
    const correlationId = this.generateCorrelationId();

    // Default error structure
    let integrationError: IntegrationError = {
      code: 'UNKNOWN_ERROR',
      message: error?.message || 'An unknown error occurred',
      integrationType: integrationType as any,
      provider,
      type: 'unknown',
      severity: 'medium',
      retryable: false,
      userMessage: 'Something went wrong with your integration setup',
      technicalMessage: error?.message || 'Unknown error',
      suggestedActions: ['Try again later', 'Contact support if the problem persists'],
      recoveryStrategy: 'user_retry',
      timestamp,
      correlationId,
      metadata: { context, originalError: error }
    };

    // Network/Connection errors
    if (error?.code === 'NETWORK_ERROR' || error?.message?.includes('network') || error?.name === 'NetworkError') {
      integrationError = {
        ...integrationError,
        code: 'NETWORK_ERROR',
        type: 'network',
        severity: 'high',
        retryable: true,
        userMessage: 'Network connection issue detected',
        technicalMessage: 'Failed to connect to integration service',
        suggestedActions: [
          'Check your internet connection',
          'Try again in a few moments',
          'Verify firewall settings if on corporate network'
        ],
        recoveryStrategy: 'auto_retry'
      };
    }

    // Authentication errors
    else if (error?.status === 401 || error?.code === 'UNAUTHORIZED' || error?.message?.includes('auth')) {
      integrationError = {
        ...integrationError,
        code: 'AUTHENTICATION_ERROR',
        type: 'authentication',
        severity: 'high',
        retryable: false,
        userMessage: 'Authentication failed',
        technicalMessage: 'Invalid or expired credentials',
        suggestedActions: [
          'Verify your login credentials',
          'Check if your account is still active',
          'Re-authorize the integration'
        ],
        recoveryStrategy: 'reconfigure'
      };
    }

    // Configuration errors
    else if (error?.status === 400 || error?.code === 'BAD_REQUEST' || error?.message?.includes('config')) {
      integrationError = {
        ...integrationError,
        code: 'CONFIGURATION_ERROR',
        type: 'configuration',
        severity: 'medium',
        retryable: false,
        userMessage: 'Configuration issue detected',
        technicalMessage: 'Invalid configuration parameters',
        suggestedActions: [
          'Review your integration settings',
          'Verify all required fields are filled',
          'Check data format requirements'
        ],
        recoveryStrategy: 'reconfigure'
      };
    }

    // Server errors
    else if (error?.status >= 500 || error?.code === 'SERVER_ERROR') {
      integrationError = {
        ...integrationError,
        code: 'SERVER_ERROR',
        type: 'server',
        severity: 'high',
        retryable: true,
        userMessage: 'Service temporarily unavailable',
        technicalMessage: 'Remote server error',
        suggestedActions: [
          'The service is experiencing issues',
          'Try again in a few minutes',
          'Check service status page if available'
        ],
        recoveryStrategy: 'auto_retry'
      };
    }

    // Timeout errors
    else if (error?.code === 'TIMEOUT' || error?.name === 'TimeoutError') {
      integrationError = {
        ...integrationError,
        code: 'TIMEOUT_ERROR',
        type: 'timeout',
        severity: 'medium',
        retryable: true,
        userMessage: 'Request timed out',
        technicalMessage: 'Operation took too long to complete',
        suggestedActions: [
          'The operation is taking longer than expected',
          'Try again with a stable connection',
          'Consider breaking large operations into smaller parts'
        ],
        recoveryStrategy: 'user_retry'
      };
    }

    // Permission errors
    else if (error?.status === 403 || error?.code === 'FORBIDDEN') {
      integrationError = {
        ...integrationError,
        code: 'PERMISSION_ERROR',
        type: 'permission',
        severity: 'high',
        retryable: false,
        userMessage: 'Permission denied',
        technicalMessage: 'Insufficient permissions for this operation',
        suggestedActions: [
          'Contact your administrator for proper permissions',
          'Verify your account has the required access level',
          'Check if additional approvals are needed'
        ],
        recoveryStrategy: 'manual_intervention'
      };
    }

    // Add integration-specific error handling
    integrationError = this.enhanceWithIntegrationSpecificDetails(integrationError, integrationType, provider);

    return integrationError;
  }

  /**
   * Enhance error with integration-specific details
   */
  private enhanceWithIntegrationSpecificDetails(
    error: IntegrationError, 
    integrationType: string, 
    provider?: string
  ): IntegrationError {
    const enhanced = { ...error };

    switch (integrationType) {
      case 'banking':
        if (provider === 'mono') {
          enhanced.suggestedActions.unshift('Check Mono service status at status.mono.co');
          if (error.type === 'authentication') {
            enhanced.suggestedActions.push('Verify your Mono API keys in settings');
          }
        }
        break;

      case 'erp':
        if (provider === 'odoo') {
          enhanced.suggestedActions.unshift('Verify Odoo server is accessible');
          if (error.type === 'authentication') {
            enhanced.suggestedActions.push('Check Odoo database credentials and user permissions');
          }
        }
        enhanced.suggestedActions.push('Ensure ERP system is online and accessible');
        break;

      case 'crm':
        enhanced.suggestedActions.push('Verify CRM system connectivity');
        if (error.type === 'authentication') {
          enhanced.suggestedActions.push('Refresh API tokens if applicable');
        }
        break;

      case 'pos':
        enhanced.suggestedActions.push('Check POS system network connectivity');
        if (error.type === 'timeout') {
          enhanced.suggestedActions.push('POS systems may need more time for sync operations');
        }
        break;
    }

    return enhanced;
  }

  /**
   * Attempt recovery for an integration operation
   */
  async attemptRecovery(
    integrationId: string,
    integrationType: string,
    operation: () => Promise<any>,
    config?: Partial<RetryConfig>
  ): Promise<RecoveryResult> {
    const retryConfig = { ...this.defaultRetryConfigs[integrationType] || this.defaultRetryConfigs.generic, ...config };
    
    let state = this.getRecoveryState(integrationId);
    if (!state) {
      state = {
        integrationId,
        integrationType,
        attemptCount: 0,
        lastAttemptAt: '',
        nextRetryAt: '',
        isRecovering: false,
        errors: [],
        recoveryStrategy: 'auto_retry',
        userNotified: false
      };
    }

    state.attemptCount++;
    state.lastAttemptAt = new Date().toISOString();
    state.isRecovering = true;

    try {
      console.log(`🔄 Integration recovery attempt ${state.attemptCount}/${retryConfig.maxAttempts} for ${integrationType}:${integrationId}`);
      
      const result = await this.executeWithTimeout(operation, retryConfig.timeoutMs);
      
      // Success - clear recovery state
      this.clearRecoveryState(integrationId);
      
      return {
        success: true,
        shouldRetry: false,
        nextAction: 'retry',
        userMessage: `${integrationType.charAt(0).toUpperCase() + integrationType.slice(1)} integration restored successfully!`,
        recoveryOptions: []
      };
      
    } catch (error) {
      const integrationError = this.handleIntegrationError(error, integrationType, undefined, { integrationId, attempt: state.attemptCount });
      
      state.errors.push(integrationError);
      state.isRecovering = false;
      
      // Generate recovery options
      const recoveryOptions = this.generateRecoveryOptions(integrationError, state);
      
      // Calculate next retry time if retryable
      if (integrationError.retryable && state.attemptCount < retryConfig.maxAttempts) {
        const delay = this.calculateRetryDelay(state.attemptCount, retryConfig);
        state.nextRetryAt = new Date(Date.now() + delay).toISOString();
        state.recoveryStrategy = 'auto_retry';
        
        this.setRecoveryState(integrationId, state);
        
        return {
          success: false,
          error: integrationError,
          shouldRetry: true,
          nextAction: 'retry',
          userMessage: `${integrationError.userMessage} Retrying in ${Math.ceil(delay / 1000)} seconds...`,
          retryAfter: delay,
          recoveryOptions
        };
      } else {
        state.recoveryStrategy = integrationError.recoveryStrategy;
        this.setRecoveryState(integrationId, state);
        
        return {
          success: false,
          error: integrationError,
          shouldRetry: false,
          nextAction: this.mapRecoveryStrategyToAction(integrationError.recoveryStrategy),
          userMessage: integrationError.userMessage,
          recoveryOptions
        };
      }
    }
  }

  /**
   * Map recovery strategy to valid action
   */
  private mapRecoveryStrategyToAction(strategy: string): 'retry' | 'reconfigure' | 'skip' | 'contact_support' {
    switch (strategy) {
      case 'auto_retry':
      case 'user_retry':
        return 'retry';
      case 'reconfigure':
        return 'reconfigure';
      case 'manual_intervention':
      case 'contact_support':
        return 'contact_support';
      default:
        return 'skip';
    }
  }

  /**
   * Generate recovery options for an error
   */
  private generateRecoveryOptions(error: IntegrationError, state: RecoveryState): RecoveryOption[] {
    const options: RecoveryOption[] = [];

    // Retry option
    if (error.retryable && state.attemptCount < (this.defaultRetryConfigs[error.integrationType]?.maxAttempts || 3)) {
      options.push({
        id: 'retry',
        title: 'Try Again',
        description: `Attempt ${error.integrationType} integration again`,
        action: 'retry',
        primary: true,
        estimatedTime: '1-2 minutes',
        difficulty: 'easy'
      });
    }

    // Reconfiguration option
    if (error.type === 'authentication' || error.type === 'configuration') {
      options.push({
        id: 'reconfigure',
        title: 'Update Settings',
        description: 'Review and update integration configuration',
        action: 'reconfigure',
        primary: !error.retryable,
        estimatedTime: '3-5 minutes',
        difficulty: 'medium'
      });
    }

    // Skip option (always available)
    options.push({
      id: 'skip',
      title: 'Skip for Now',
      description: 'Continue setup and configure this integration later',
      action: 'skip',
      primary: false,
      estimatedTime: 'Immediate',
      difficulty: 'easy'
    });

    // Help option for complex errors
    if (error.severity === 'high' || error.severity === 'critical') {
      options.push({
        id: 'help',
        title: 'Get Help',
        description: 'Contact support or view troubleshooting guide',
        action: 'help',
        primary: false,
        estimatedTime: '5-10 minutes',
        difficulty: 'easy'
      });
    }

    return options;
  }

  /**
   * Execute operation with timeout
   */
  private async executeWithTimeout<T>(operation: () => Promise<T>, timeoutMs?: number): Promise<T> {
    if (!timeoutMs) return operation();

    return Promise.race([
      operation(),
      new Promise<never>((_, reject) => 
        setTimeout(() => reject(new Error('TIMEOUT')), timeoutMs)
      )
    ]);
  }

  /**
   * Calculate retry delay with exponential backoff and jitter
   */
  private calculateRetryDelay(attempt: number, config: RetryConfig): number {
    let delay = Math.min(config.baseDelay * Math.pow(config.backoffMultiplier, attempt - 1), config.maxDelay);
    
    if (config.jitter) {
      delay = delay * (0.5 + Math.random() * 0.5);
    }
    
    return Math.floor(delay);
  }

  /**
   * Generate correlation ID for error tracking
   */
  private generateCorrelationId(): string {
    return `int_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }

  /**
   * Log error for analytics
   */
  private logError(error: IntegrationError, context?: Record<string, any>): void {
    // In a real implementation, this would send to analytics service
    console.log('📊 Integration error logged:', {
      error: {
        code: error.code,
        type: error.type,
        integrationType: error.integrationType,
        provider: error.provider,
        severity: error.severity
      },
      context
    });
  }

  // State management methods
  private getRecoveryState(integrationId: string): RecoveryState | null {
    return this.recoveryStates.get(integrationId) || null;
  }

  private setRecoveryState(integrationId: string, state: RecoveryState): void {
    this.recoveryStates.set(integrationId, state);
  }

  private clearRecoveryState(integrationId: string): void {
    this.recoveryStates.delete(integrationId);
  }

  /**
   * Get recovery suggestions for a specific error type
   */
  getRecoverySuggestions(error: IntegrationError): {
    immediate: string[];
    alternative: string[];
    support: string[];
  } {
    const suggestions = {
      immediate: [...error.suggestedActions],
      alternative: [] as string[],
      support: [] as string[]
    };

    // Add alternative suggestions based on error type
    switch (error.type) {
      case 'network':
        suggestions.alternative.push(
          'Try using a different network connection',
          'Check if VPN is interfering with the connection',
          'Verify no proxy settings are blocking the request'
        );
        break;
      case 'authentication':
        suggestions.alternative.push(
          'Generate new API credentials',
          'Check if account needs re-verification',
          'Verify integration permissions in the source system'
        );
        break;
      case 'configuration':
        suggestions.alternative.push(
          'Use default settings and customize later',
          'Check integration documentation for required fields',
          'Verify data formats match expected values'
        );
        break;
    }

    // Add support suggestions
    suggestions.support.push(
      'Contact TaxPoynt support with error details',
      'Check our knowledge base for similar issues',
      'Join our community forum for help from other users'
    );

    if (error.integrationType === 'banking') {
      suggestions.support.push('Contact your bank to verify API access');
    } else if (error.integrationType === 'erp') {
      suggestions.support.push('Contact your ERP administrator for assistance');
    }

    return suggestions;
  }

  /**
   * Get all active recovery states
   */
  getActiveRecoveries(): RecoveryState[] {
    return Array.from(this.recoveryStates.values()).filter(state => state.isRecovering);
  }

  /**
   * Clear all recovery states (useful for cleanup)
   */
  clearAllRecoveries(): void {
    this.recoveryStates.clear();
  }
}

// Export singleton instance
export const integrationErrorRecovery = new IntegrationErrorRecoveryService();
export default integrationErrorRecovery;
