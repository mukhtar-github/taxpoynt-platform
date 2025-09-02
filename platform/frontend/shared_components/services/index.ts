/**
 * Shared Services
 * ===============
 * Export all shared services for use across the application
 */

export { authService } from './auth';
export type { 
  AuthResponse, 
  RegisterRequest, 
  LoginRequest, 
  User, 
  Organization 
} from './auth';

// Banking Error Recovery (Legacy)
export { 
  bankingErrorRecovery,
  type BankingError,
  type RetryConfig as BankingRetryConfig,
  type RecoveryState as BankingRecoveryState,
  type RecoveryResult as BankingRecoveryResult
} from './bankingErrorRecovery';

// Universal Integration Error Recovery (New)
export { 
  integrationErrorRecovery,
  type IntegrationError,
  type RetryConfig,
  type RecoveryState,
  type RecoveryResult,
  type RecoveryOption
} from './integrationErrorRecovery';

// Onboarding API
export { 
  onboardingApi,
  type OnboardingState
} from './onboardingApi';