/**
 * Shared Utilities
 * ================
 * Export all shared utilities for use across the application
 */

// Dashboard Routing - Only export what exists
export { 
  DASHBOARD_ROUTES,
  ONBOARDING_ROUTES,
  getDashboardUrl,
  getPostAuthRedirectUrl,
  getOnboardingContinueUrl,
  getOnboardingStartUrl,
  getPostBankingUrl,
  getPostOnboardingUrl,
  redirectToDashboard
} from './dashboardRouting';

// Mobile Onboarding Optimization
export { 
  mobileOptimizer,
  useMobileOptimization
} from './mobileOnboardingOptimization';

// Onboarding Session Persistence
export { default as onboardingSessionPersistence } from './onboardingSessionPersistence';

// Types (avoid duplicate exports)
export type { User as DashboardUser } from './dashboardRouting';
export type {
  MobileCapabilities,
  MobileOptimizationConfig
} from './mobileOnboardingOptimization';