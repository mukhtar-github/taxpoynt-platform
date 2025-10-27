/**
 * Onboarding Components Index
 * ===========================
 * 
 * Central export for all onboarding-related components and utilities.
 * Provides standardized onboarding experience across all user roles.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

// ========================================
// ONBOARDING COMPONENTS
// ========================================

// Progress and Navigation - Only export what exists
export {
  OnboardingProgressIndicator
} from './OnboardingProgressIndicator';

export {
  AutosaveStatusChip,
  type AutosaveStatus,
  type AutosaveStatusChipProps
} from './AutosaveStatusChip';

export {
  SkipForNowButton,
  QuickSkipButton,
  SkipWithTimeButton,
  MobileSkipButton,
  CriticalSkipButton
} from './SkipForNowButton';

// Routing and State Management
export {
  ServiceOnboardingRouter
} from './ServiceOnboardingRouter';
export {
  UnifiedOnboardingWizard,
  type ServicePackage
} from './UnifiedOnboardingWizard';

export {
  OnboardingResumeManager
} from './OnboardingResumeManager';

export {
  OnboardingResumeMiddleware
} from './OnboardingResumeMiddleware';

export {
  OnboardingStepGuard
} from './OnboardingStepGuard';

// Loading States - Use what exists
export {
  BankingConnectionLoader,
  OnboardingStepLoader
} from '../loading/OnboardingLoadingStates';

// ========================================
// SERVICES AND UTILITIES  
// ========================================

// Error Recovery
export {
  integrationErrorRecovery
} from '../services/integrationErrorRecovery';

// Mobile Optimization
export {
  mobileOptimizer,
  useMobileOptimization
} from '../utils/mobileOnboardingOptimization';

// ========================================
// HOOKS AND UTILITIES
// ========================================

// Progress Management
export {
  useOnboardingProgress
} from '../hooks/useOnboardingProgress';

// User Context
export {
  useUserContext
} from '../hooks/useUserContext';

// ========================================
// ANALYTICS
// ========================================

// Analytics Service  
export {
  onboardingAnalytics
} from '../analytics/OnboardingAnalytics';

// ========================================
// TYPE EXPORTS
// ========================================

// Re-export service types for convenience
export type {
  IntegrationError,
  RetryConfig,
  RecoveryState,
  RecoveryResult,
  RecoveryOption
} from '../services/integrationErrorRecovery';

export type {
  MobileCapabilities,
  MobileOptimizationConfig
} from '../utils/mobileOnboardingOptimization';

// ========================================
// COMPONENT AGGREGATES (Simplified)
// ========================================

// Note: Component aggregates are available through direct imports
// Use the named exports above for actual implementation

// Export a simple default object
export default {
  // Components available through named exports
};
