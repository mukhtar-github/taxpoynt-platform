/**
 * URL Configuration
 * =================
 * 
 * Centralized configuration for all URLs used throughout the application.
 * Prevents mismatches and provides a single source of truth for routing.
 * 
 * Features:
 * - Environment-aware URLs
 * - Type-safe URL construction
 * - Centralized redirect configurations
 * - API endpoint configurations
 * - Onboarding flow URLs
 */

export interface UrlConfig {
  base: {
    frontend: string;
    api: string;
    cdn?: string;
  };
  onboarding: {
    si: {
      integrationChoice: string;
      businessSystemsSetup: string;
      financialSystemsSetup: string;
      bankingCallback: string;
      reconciliationSetup: string;
      completeIntegrationSetup: string;
    };
    app: {
      businessVerification: string;
      firsIntegrationSetup: string;
      complianceSettings: string;
    };
    hybrid: {
      serviceSelection: string;
      combinedSetup: string;
    };
  };
  dashboard: {
    si: string;
    app: string;
    hybrid: string;
    generic: string;
  };
  api: {
    v1: {
      auth: {
        login: string;
        register: string;
        refresh: string;
        logout: string;
      };
      si: {
        onboarding: {
          state: string;
          complete: string;
          analytics: string;
          stepComplete: (stepName: string) => string;
          reset: string;
        };
        banking: {
          monoCallback: string;
          genericCallback: string;
          widgetLink: string;
        };
        organizations: string;
        financial: string;
        transactions: string;
      };
      app: {
        onboarding: {
          state: string;
          complete: string;
          analytics: string;
          stepComplete: (stepName: string) => string;
          reset: string;
          businessVerification: string;
          firsIntegration: string;
        };
        taxpayers: string;
        invoices: string;
        compliance: string;
      };
    };
  };
  external: {
    mono: {
      widget: string;
      api: string;
    };
    firs: {
      sandbox: string;
      production: string;
    };
  };
}

/**
 * Get environment-specific configuration
 */
function getEnvironmentConfig(): UrlConfig {
  const environment = process.env.NODE_ENV || 'development';
  const frontendHost = process.env.NEXT_PUBLIC_FRONTEND_URL || 
    (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000');
  const apiHost = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  return {
    base: {
      frontend: frontendHost,
      api: apiHost,
      cdn: process.env.NEXT_PUBLIC_CDN_URL
    },
    onboarding: {
      si: {
        integrationChoice: '/onboarding/si/integration-choice',
        businessSystemsSetup: '/onboarding/si/business-systems-setup',
        financialSystemsSetup: '/onboarding/si/financial-systems-setup',
        bankingCallback: '/onboarding/si/banking-callback',
        reconciliationSetup: '/onboarding/si/reconciliation-setup',
        completeIntegrationSetup: '/onboarding/si/complete-integration-setup'
      },
      app: {
        businessVerification: '/onboarding/app/business-verification',
        firsIntegrationSetup: '/onboarding/app/firs-integration-setup',
        complianceSettings: '/onboarding/app/compliance-settings'
      },
      hybrid: {
        serviceSelection: '/onboarding/hybrid/service-selection',
        combinedSetup: '/onboarding/hybrid/combined-setup'
      }
    },
    dashboard: {
      si: '/dashboard/si',
      app: '/dashboard/app',
      hybrid: '/dashboard/hybrid',
      generic: '/dashboard'
    },
    api: {
      v1: {
        auth: {
          login: `${apiHost}/api/v1/auth/login`,
          register: `${apiHost}/api/v1/auth/register`,
          refresh: `${apiHost}/api/v1/auth/refresh`,
          logout: `${apiHost}/api/v1/auth/logout`
        },
        si: {
          onboarding: {
            state: `${apiHost}/api/v1/si/onboarding/state`,
            complete: `${apiHost}/api/v1/si/onboarding/complete`,
            analytics: `${apiHost}/api/v1/si/onboarding/analytics`,
            stepComplete: (stepName: string) => `${apiHost}/api/v1/si/onboarding/state/step/${stepName}/complete`,
            reset: `${apiHost}/api/v1/si/onboarding/state/reset`
          },
          banking: {
            monoCallback: `${apiHost}/api/v1/si/banking/open-banking/mono/callback`,
            genericCallback: `${apiHost}/api/v1/si/banking/open-banking/callback`,
            widgetLink: `${apiHost}/api/v1/si/banking/open-banking/mono/widget-link`
          },
          organizations: `${apiHost}/api/v1/si/organizations`,
          financial: `${apiHost}/api/v1/si/financial`,
          transactions: `${apiHost}/api/v1/si/transactions`
        },
        app: {
          onboarding: {
            state: `${apiHost}/api/v1/app/onboarding/state`,
            complete: `${apiHost}/api/v1/app/onboarding/complete`,
            analytics: `${apiHost}/api/v1/app/onboarding/analytics`,
            stepComplete: (stepName: string) => `${apiHost}/api/v1/app/onboarding/state/step/${stepName}/complete`,
            reset: `${apiHost}/api/v1/app/onboarding/state/reset`,
            businessVerification: `${apiHost}/api/v1/app/onboarding/business-verification`,
            firsIntegration: `${apiHost}/api/v1/app/onboarding/firs-integration`
          },
          taxpayers: `${apiHost}/api/v1/app/taxpayers`,
          invoices: `${apiHost}/api/v1/app/invoices`,
          compliance: `${apiHost}/api/v1/app/compliance`
        }
      }
    },
    external: {
      mono: {
        widget: 'https://widget.mono.co',
        api: environment === 'production' 
          ? 'https://api.mono.co' 
          : 'https://api.sandbox.mono.co'
      },
      firs: {
        sandbox: 'https://sandbox.firs.gov.ng',
        production: 'https://einvoicing.firs.gov.ng'
      }
    }
  };
}

// Export configuration instance
export const urlConfig: UrlConfig = getEnvironmentConfig();

/**
 * URL Builder Utilities
 */
export class UrlBuilder {
  /**
   * Build a complete redirect URL for banking callbacks
   */
  static bankingCallbackUrl(provider: 'mono' | 'generic' = 'mono'): string {
    const baseUrl = urlConfig.base.frontend;
    const path = urlConfig.onboarding.si.bankingCallback;
    return `${baseUrl}${path}`;
  }

  /**
   * Build a complete API URL
   */
  static apiUrl(endpoint: string): string {
    return `${urlConfig.base.api}${endpoint}`;
  }

  /**
   * Build onboarding step URL
   */
  static onboardingStepUrl(role: 'si' | 'app' | 'hybrid', step: string): string {
    const baseUrl = urlConfig.base.frontend;

    const serviceParam = role;
    const params = new URLSearchParams({ service: serviceParam });

    const nextByRole: Record<'si' | 'app' | 'hybrid', string> = {
      si: urlConfig.onboarding.si.integrationChoice,
      app: urlConfig.onboarding.app.businessVerification,
      hybrid: urlConfig.onboarding.hybrid.serviceSelection,
    };

    // When user is still in account setup stages, route through auth flows
    if (step === 'registration') {
      params.set('next', nextByRole[role]);
      return `${baseUrl}/auth/signup?${params.toString()}`;
    }

    if (step === 'email_verification' || step === 'terms_acceptance') {
      params.set('next', nextByRole[role]);
      return `${baseUrl}/auth/verify-email?${params.toString()}`;
    }

    switch (role) {
      case 'si':
        return `${baseUrl}/onboarding/si/${step}`;
      case 'app':
        return `${baseUrl}/onboarding/app/${step}`;
      case 'hybrid':
        return `${baseUrl}/onboarding/hybrid/${step}`;
      default:
        return `${baseUrl}/onboarding/${step}`;
    }
  }

  /**
   * Build dashboard URL for user role
   */
  static dashboardUrl(role: 'si' | 'app' | 'hybrid' | null): string {
    const baseUrl = urlConfig.base.frontend;
    
    switch (role) {
      case 'si':
        return `${baseUrl}${urlConfig.dashboard.si}`;
      case 'app':
        return `${baseUrl}${urlConfig.dashboard.app}`;
      case 'hybrid':
        return `${baseUrl}${urlConfig.dashboard.hybrid}`;
      default:
        return `${baseUrl}${urlConfig.dashboard.generic}`;
    }
  }

  /**
   * Validate URL format
   */
  static validateUrl(url: string): boolean {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Ensure URL has protocol
   */
  static ensureProtocol(url: string, defaultProtocol: string = 'https'): string {
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }
    return `${defaultProtocol}://${url}`;
  }
}

/**
 * Environment Detection Utilities
 */
export class EnvironmentUtils {
  static isDevelopment(): boolean {
    return process.env.NODE_ENV === 'development';
  }

  static isProduction(): boolean {
    return process.env.NODE_ENV === 'production';
  }

  static isTest(): boolean {
    return process.env.NODE_ENV === 'test';
  }

  static getApiEnvironment(): 'development' | 'staging' | 'production' {
    return (process.env.NEXT_PUBLIC_API_ENV as any) || 
           (this.isProduction() ? 'production' : 'development');
  }
}

/**
 * URL Validation and Consistency Checks
 */
export class UrlValidator {
  /**
   * Check if all configured URLs are accessible
   */
  static async validateConfiguration(): Promise<{
    valid: boolean;
    errors: string[];
    warnings: string[];
  }> {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Validate base URLs
    if (!UrlBuilder.validateUrl(urlConfig.base.frontend)) {
      errors.push(`Invalid frontend URL: ${urlConfig.base.frontend}`);
    }

    if (!UrlBuilder.validateUrl(urlConfig.base.api)) {
      errors.push(`Invalid API URL: ${urlConfig.base.api}`);
    }

    // Check for consistent callback URLs
    const bankingCallbackPath = urlConfig.onboarding.si.bankingCallback;
    if (!bankingCallbackPath.startsWith('/onboarding/si/banking-callback')) {
      warnings.push(`Banking callback path may be inconsistent: ${bankingCallbackPath}`);
    }

    // Validate external service URLs
    if (!UrlBuilder.validateUrl(urlConfig.external.mono.api)) {
      errors.push(`Invalid Mono API URL: ${urlConfig.external.mono.api}`);
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Check for URL consistency across components
   */
  static checkConsistency(): {
    consistent: boolean;
    issues: string[];
  } {
    const issues: string[] = [];

    // Check if dashboard URLs follow pattern
    const dashboardUrls = Object.values(urlConfig.dashboard);
    const invalidDashboardUrls = dashboardUrls.filter(url => !url.startsWith('/dashboard'));
    
    if (invalidDashboardUrls.length > 0) {
      issues.push(`Dashboard URLs should start with /dashboard: ${invalidDashboardUrls.join(', ')}`);
    }

    // Check if onboarding URLs follow pattern
    const onboardingUrls = [
      ...Object.values(urlConfig.onboarding.si),
      ...Object.values(urlConfig.onboarding.app),
      ...Object.values(urlConfig.onboarding.hybrid)
    ];
    
    const invalidOnboardingUrls = onboardingUrls.filter(url => !url.startsWith('/onboarding'));
    
    if (invalidOnboardingUrls.length > 0) {
      issues.push(`Onboarding URLs should start with /onboarding: ${invalidOnboardingUrls.join(', ')}`);
    }

    return {
      consistent: issues.length === 0,
      issues
    };
  }
}

// Export default configuration
export default urlConfig;
