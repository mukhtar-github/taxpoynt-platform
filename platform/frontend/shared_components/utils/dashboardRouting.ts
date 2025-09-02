/**
 * Dashboard Routing Utilities
 * ===========================
 * Centralized logic for dashboard redirects to ensure consistency
 * across all onboarding and authentication flows.
 * 
 * @deprecated This file is being migrated to use urlConfig. 
 * New implementations should use ../config/urlConfig.ts
 */

import { urlConfig, UrlBuilder } from '../config/urlConfig';

export interface User {
  id: string;
  role: string;
  service_package: string;
  organization?: {
    id: string;
    name: string;
  };
}

export interface OnboardingState {
  hasStarted: boolean;
  currentStep: string;
  completedSteps: string[];
  lastActiveDate: string;
}

/**
 * Role-based dashboard routes
 * @deprecated Use urlConfig.dashboard instead
 */
export const DASHBOARD_ROUTES = {
  SYSTEM_INTEGRATOR: urlConfig.dashboard.si,
  ACCESS_POINT_PROVIDER: urlConfig.dashboard.app,
  HYBRID_USER: urlConfig.dashboard.hybrid,
  FALLBACK: urlConfig.dashboard.generic
} as const;

/**
 * Onboarding routes for continuing incomplete flows
 * @deprecated Use urlConfig.onboarding instead
 */
export const ONBOARDING_ROUTES = {
  SI: {
    SERVICE_INTRODUCTION: '/onboarding/si/service-introduction',
    INTEGRATION_CHOICE: urlConfig.onboarding.si.integrationChoice,
    BUSINESS_SYSTEMS_SETUP: urlConfig.onboarding.si.businessSystemsSetup,
    FINANCIAL_SYSTEMS_SETUP: urlConfig.onboarding.si.financialSystemsSetup,
    BANKING_CALLBACK: urlConfig.onboarding.si.bankingCallback,
    RECONCILIATION_SETUP: urlConfig.onboarding.si.reconciliationSetup,
    COMPLETE_INTEGRATION_SETUP: urlConfig.onboarding.si.completeIntegrationSetup
  },
  APP: {
    SERVICE_INTRODUCTION: '/onboarding/app/service-introduction',
    BUSINESS_VERIFICATION: urlConfig.onboarding.app.businessVerification,
    FIRS_INTEGRATION_SETUP: urlConfig.onboarding.app.firsIntegrationSetup,
    COMPLIANCE_SETTINGS: urlConfig.onboarding.app.complianceSettings
  },
  HYBRID: {
    SERVICE_INTRODUCTION: '/onboarding/hybrid/service-introduction',
    SERVICE_SELECTION: urlConfig.onboarding.hybrid.serviceSelection
  }
} as const;

/**
 * Determine the appropriate dashboard URL for a user
 * @deprecated Use UrlBuilder.dashboardUrl() instead
 */
export function getDashboardUrl(user: User): string {
  if (!user || !user.role) {
    return UrlBuilder.dashboardUrl(null);
  }

  const roleMap: Record<string, 'si' | 'app' | 'hybrid'> = {
    'system_integrator': 'si',
    'access_point_provider': 'app', 
    'hybrid_user': 'hybrid'
  };

  const mappedRole = roleMap[user.role] || null;
  return UrlBuilder.dashboardUrl(mappedRole);
}

/**
 * Determine if user should continue onboarding or go to dashboard
 */
export function getPostAuthRedirectUrl(user: User, onboardingState?: OnboardingState): string {
  if (!user) {
    return '/auth/signin';
  }

  // Check if onboarding is complete
  if (onboardingState?.completedSteps.includes('onboarding_complete')) {
    return getDashboardUrl(user);
  }

  // Check if onboarding is in progress
  if (onboardingState?.hasStarted && onboardingState.currentStep) {
    return getOnboardingContinueUrl(user, onboardingState.currentStep);
  }

  // Start onboarding flow for new users
  return getOnboardingStartUrl(user);
}

/**
 * Get URL to continue onboarding from specific step
 */
export function getOnboardingContinueUrl(user: User, currentStep: string): string {
  const role = user.role;

  if (role === 'system_integrator') {
    switch (currentStep) {
      case 'service_introduction':
        return ONBOARDING_ROUTES.SI.SERVICE_INTRODUCTION;
      case 'integration_choice':
        return ONBOARDING_ROUTES.SI.INTEGRATION_CHOICE;
      case 'business_systems_setup':
        return ONBOARDING_ROUTES.SI.BUSINESS_SYSTEMS_SETUP;
      case 'financial_systems_setup':
        return ONBOARDING_ROUTES.SI.FINANCIAL_SYSTEMS_SETUP;
      case 'banking_connected':
      case 'reconciliation_setup':
        return ONBOARDING_ROUTES.SI.RECONCILIATION_SETUP;
      case 'complete_integration_setup':
        return ONBOARDING_ROUTES.SI.COMPLETE_INTEGRATION_SETUP;
      default:
        return ONBOARDING_ROUTES.SI.INTEGRATION_CHOICE;
    }
  }

  if (role === 'access_point_provider') {
    switch (currentStep) {
      case 'service_introduction':
        return ONBOARDING_ROUTES.APP.SERVICE_INTRODUCTION;
      case 'business_verification':
        return ONBOARDING_ROUTES.APP.BUSINESS_VERIFICATION;
      case 'firs_integration_setup':
        return ONBOARDING_ROUTES.APP.FIRS_INTEGRATION_SETUP;
      case 'compliance_settings':
        return ONBOARDING_ROUTES.APP.COMPLIANCE_SETTINGS;
      default:
        return ONBOARDING_ROUTES.APP.SERVICE_INTRODUCTION;
    }
  }

  if (role === 'hybrid_user') {
    switch (currentStep) {
      case 'service_introduction':
        return ONBOARDING_ROUTES.HYBRID.SERVICE_INTRODUCTION;
      case 'service_selection':
        return ONBOARDING_ROUTES.HYBRID.SERVICE_SELECTION;
      default:
        return ONBOARDING_ROUTES.HYBRID.SERVICE_INTRODUCTION;
    }
  }

  // Fallback to dashboard for unknown roles
  return getDashboardUrl(user);
}

/**
 * Get URL to start onboarding for new users
 */
export function getOnboardingStartUrl(user: User): string {
  const role = user.role;

  switch (role) {
    case 'system_integrator':
      return ONBOARDING_ROUTES.SI.INTEGRATION_CHOICE;
    case 'access_point_provider':
      return ONBOARDING_ROUTES.APP.SERVICE_INTRODUCTION;
    case 'hybrid_user':
      return ONBOARDING_ROUTES.HYBRID.SERVICE_INTRODUCTION;
    default:
      return getDashboardUrl(user);
  }
}

/**
 * Get URL to redirect after successful banking connection
 */
export function getPostBankingUrl(user: User): string {
  if (user.role === 'system_integrator') {
    return ONBOARDING_ROUTES.SI.RECONCILIATION_SETUP;
  }
  
  return getDashboardUrl(user);
}

/**
 * Get URL to redirect after completing onboarding
 */
export function getPostOnboardingUrl(user: User): string {
  return getDashboardUrl(user);
}

/**
 * Utility function to handle router redirect with proper error handling
 */
export function redirectToDashboard(router: any, user: User, onboardingState?: OnboardingState): void {
  try {
    const redirectUrl = getPostAuthRedirectUrl(user, onboardingState);
    router.push(redirectUrl);
  } catch (error) {
    console.error('Dashboard redirect failed:', error);
    // Fallback to basic dashboard
    router.push(getDashboardUrl(user));
  }
}
