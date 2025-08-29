/**
 * Secure Configuration Utility
 * ===========================
 * Prevents sensitive configuration data from being exposed in the frontend
 * Implements secure patterns for API keys, secrets, and sensitive data
 */

interface SecureConfigOptions {
  encryptSensitiveData?: boolean;
  useEnvironmentVariables?: boolean;
  fallbackToSecureStorage?: boolean;
}

class SecureConfigManager {
  private static instance: SecureConfigManager;
  private sensitiveFields: Set<string> = new Set([
    'api_key', 'api_secret', 'client_secret', 'password', 'token',
    'secret', 'private_key', 'certificate', 'encryption_key'
  ]);

  private constructor() {}

  static getInstance(): SecureConfigManager {
    if (!SecureConfigManager.instance) {
      SecureConfigManager.instance = new SecureConfigManager();
    }
    return SecureConfigManager.instance;
  }

  /**
   * Sanitize configuration object by masking sensitive fields
   */
  sanitizeConfig<T extends Record<string, any>>(config: T): T {
    const sanitized = { ...config };
    
    for (const [key, value] of Object.entries(sanitized)) {
      if (this.isSensitiveField(key) && typeof value === 'string' && value.length > 0) {
        sanitized[key as keyof T] = this.maskValue(value) as T[keyof T];
      }
    }
    
    return sanitized;
  }

  /**
   * Check if a field name contains sensitive information
   */
  private isSensitiveField(fieldName: string): boolean {
    const lowerField = fieldName.toLowerCase();
    return Array.from(this.sensitiveFields).some(sensitive => 
      lowerField.includes(sensitive) || sensitive.includes(lowerField)
    );
  }

  /**
   * Mask sensitive values for logging/display
   */
  private maskValue(value: string): string {
    if (value.length <= 4) {
      return '*'.repeat(value.length);
    }
    return value.substring(0, 2) + '*'.repeat(value.length - 4) + value.substring(value.length - 2);
  }

  /**
   * Get environment variable safely
   */
  getEnvVar(key: string, defaultValue?: string): string | undefined {
    if (typeof window !== 'undefined') {
      // Frontend - never expose environment variables
      return defaultValue;
    }
    
    // Backend only
    return process.env[key] || defaultValue;
  }

  /**
   * Validate configuration object for sensitive data exposure
   */
  validateConfig<T extends Record<string, any>>(config: T): {
    isValid: boolean;
    violations: string[];
    recommendations: string[];
  } {
    const violations: string[] = [];
    const recommendations: string[] = [];

    for (const [key, value] of Object.entries(config)) {
      if (this.isSensitiveField(key)) {
        if (typeof value === 'string' && value.length > 0) {
          violations.push(`Sensitive field '${key}' contains plain text value`);
          recommendations.push(`Use secure storage or encryption for '${key}'`);
        }
      }
    }

    return {
      isValid: violations.length === 0,
      violations,
      recommendations
    };
  }

  /**
   * Create secure configuration object
   */
  createSecureConfig<T extends Record<string, any>>(
    config: T, 
    options: SecureConfigOptions = {}
  ): T {
    const { encryptSensitiveData = false, useEnvironmentVariables = false } = options;
    
    let secureConfig = { ...config };

    // Apply environment variables if available
    if (useEnvironmentVariables && typeof window === 'undefined') {
      for (const [key, value] of Object.entries(secureConfig)) {
        if (this.isSensitiveField(key) && typeof value === 'string') {
          const envValue = process.env[key.toUpperCase()];
          if (envValue) {
            secureConfig[key as keyof T] = envValue as T[keyof T];
          }
        }
      }
    }

    // Encrypt sensitive data if requested
    if (encryptSensitiveData) {
      for (const [key, value] of Object.entries(secureConfig)) {
        if (this.isSensitiveField(key) && typeof value === 'string') {
          secureConfig[key as keyof T] = this.encryptValue(value) as T[keyof T];
        }
      }
    }

    return secureConfig;
  }

  /**
   * Encrypt value (placeholder - implement actual encryption)
   */
  private encryptValue(value: string): string {
    // TODO: Implement actual encryption
    // For now, return masked value
    return this.maskValue(value);
  }

  /**
   * Decrypt value (placeholder - implement actual decryption)
   */
  decryptValue(encryptedValue: string): string {
    // TODO: Implement actual decryption
    // For now, return as-is
    return encryptedValue;
  }
}

// Export singleton instance
export const secureConfig = SecureConfigManager.getInstance();

// Export types
export type { SecureConfigOptions };

// Export utility functions
export const {
  sanitizeConfig,
  validateConfig,
  createSecureConfig,
  getEnvVar
} = secureConfig;

export default secureConfig;
