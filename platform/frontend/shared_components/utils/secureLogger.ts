/**
 * Secure Logging Utility
 * ======================
 * Prevents sensitive user data from being logged to the console
 * Only logs in development mode and sanitizes sensitive information
 */

interface LogLevel {
  DEBUG: 'debug';
  INFO: 'info';
  WARN: 'warn';
  ERROR: 'error';
}

const LOG_LEVELS: LogLevel = {
  DEBUG: 'debug',
  INFO: 'info',
  WARN: 'warn',
  ERROR: 'error'
};

// Sensitive fields that should never be logged
const SENSITIVE_FIELDS = [
  'password',
  'email',
  'first_name',
  'last_name',
  'business_name',
  'phone',
  'tin',
  'rc_number',
  'address',
  'bank_account',
  'card_number',
  'ssn',
  'passport',
  'drivers_license',
  'date_of_birth',
  'national_id',
  'tax_id',
  'company_registration',
  'business_license',
  'financial_data',
  'personal_data',
  'user_data',
  'registration_data',
  'form_data'
];

// Sanitize data by removing sensitive fields
const sanitizeData = (data: any): any => {
  if (!data || typeof data !== 'object') {
    return data;
  }

  if (Array.isArray(data)) {
    return data.map(item => sanitizeData(item));
  }

  const sanitized: any = {};
  for (const [key, value] of Object.entries(data)) {
    const lowerKey = key.toLowerCase();
    const isSensitive = SENSITIVE_FIELDS.some(field => 
      lowerKey.includes(field) || field.includes(lowerKey)
    );

    if (isSensitive) {
      sanitized[key] = '[REDACTED]';
    } else if (typeof value === 'object' && value !== null) {
      sanitized[key] = sanitizeData(value);
    } else {
      sanitized[key] = value;
    }
  }

  return sanitized;
};

// Secure logging class
class SecureLogger {
  private isDevelopment = process.env.NODE_ENV === 'development';
  private isProduction = process.env.NODE_ENV === 'production';

  /**
   * Log debug information (development only)
   */
  debug(message: string, data?: any): void {
    if (this.isDevelopment) {
      console.log(`🔍 [DEBUG] ${message}`, data ? sanitizeData(data) : '');
    }
  }

  /**
   * Log general information (development only)
   */
  info(message: string, data?: any): void {
    if (this.isDevelopment) {
      console.log(`ℹ️ [INFO] ${message}`, data ? sanitizeData(data) : '');
    }
  }

  /**
   * Log warnings (always logged)
   */
  warn(message: string, data?: any): void {
    console.warn(`⚠️ [WARN] ${message}`, data ? sanitizeData(data) : '');
  }

  /**
   * Log errors (always logged)
   */
  error(message: string, error?: any): void {
    console.error(`❌ [ERROR] ${message}`, error ? sanitizeData(error) : '');
  }

  /**
   * Log success messages (development only)
   */
  success(message: string, data?: any): void {
    if (this.isDevelopment) {
      console.log(`✅ [SUCCESS] ${message}`, data ? sanitizeData(data) : '');
    }
  }

  /**
   * Log form data safely (development only)
   */
  formData(message: string, formData: any): void {
    if (this.isDevelopment) {
      console.log(`📝 [FORM] ${message}`, sanitizeData(formData));
    }
  }

  /**
   * Log user actions safely (development only)
   */
  userAction(action: string, context?: any): void {
    if (this.isDevelopment) {
      console.log(`👤 [USER] ${action}`, context ? sanitizeData(context) : '');
    }
  }

  /**
   * Log system events safely (development only)
   */
  systemEvent(event: string, data?: any): void {
    if (this.isDevelopment) {
      console.log(`⚙️ [SYSTEM] ${event}`, data ? sanitizeData(data) : '');
    }
  }

  /**
   * Log API calls safely (development only)
   */
  apiCall(endpoint: string, method: string, data?: any): void {
    if (this.isDevelopment) {
      console.log(`🌐 [API] ${method.toUpperCase()} ${endpoint}`, data ? sanitizeData(data) : '');
    }
  }

  /**
   * Log navigation events safely (development only)
   */
  navigation(from: string, to: string): void {
    if (this.isDevelopment) {
      console.log(`🧭 [NAV] ${from} → ${to}`);
    }
  }

  /**
   * Log performance metrics (development only)
   */
  performance(metric: string, value: number, unit: string = 'ms'): void {
    if (this.isDevelopment) {
      console.log(`⚡ [PERF] ${metric}: ${value}${unit}`);
    }
  }

  /**
   * Log security events (always logged)
   */
  security(event: string, details?: any): void {
    console.warn(`🔒 [SECURITY] ${event}`, details ? sanitizeData(details) : '');
  }

  /**
   * Log compliance events (always logged)
   */
  compliance(event: string, details?: any): void {
    console.log(`📋 [COMPLIANCE] ${event}`, details ? sanitizeData(details) : '');
  }
}

// Export singleton instance
export const secureLogger = new SecureLogger();

// Export types for use in other components
export type { LogLevel };
export { LOG_LEVELS, sanitizeData };

// Export individual methods for convenience
export const {
  debug,
  info,
  warn,
  error,
  success,
  formData,
  userAction,
  systemEvent,
  apiCall,
  navigation,
  performance,
  security,
  compliance
} = secureLogger;

export default secureLogger;
