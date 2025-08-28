/**
 * Registration Validation Utilities
 * =================================
 * Centralized validation logic for user registration forms
 * Ensures consistent validation across all registration components
 */

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  fieldErrors: Record<string, string>;
}

/**
 * Comprehensive registration data validation
 */
export function validateRegistrationData(data: any): ValidationResult {
  const errors: ValidationError[] = [];
  const fieldErrors: Record<string, string> = {};

  // Email validation
  if (!data.email?.trim()) {
    errors.push({ field: 'email', message: 'Email address is required', code: 'REQUIRED' });
    fieldErrors.email = 'Email address is required';
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
    errors.push({ field: 'email', message: 'Please enter a valid email address', code: 'INVALID_FORMAT' });
    fieldErrors.email = 'Please enter a valid email address';
  }

  // Password validation
  if (!data.password) {
    errors.push({ field: 'password', message: 'Password is required', code: 'REQUIRED' });
    fieldErrors.password = 'Password is required';
  } else if (data.password.length < 8) {
    errors.push({ field: 'password', message: 'Password must be at least 8 characters long', code: 'TOO_SHORT' });
    fieldErrors.password = 'Password must be at least 8 characters long';
  } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(data.password)) {
    errors.push({ 
      field: 'password', 
      message: 'Password must contain at least one uppercase letter, one lowercase letter, and one number', 
      code: 'WEAK_PASSWORD' 
    });
    fieldErrors.password = 'Password must contain uppercase, lowercase, and number';
  }

  // Name validation
  if (!data.first_name?.trim()) {
    errors.push({ field: 'first_name', message: 'First name is required', code: 'REQUIRED' });
    fieldErrors.first_name = 'First name is required';
  } else if (data.first_name.trim().length < 2) {
    errors.push({ field: 'first_name', message: 'First name must be at least 2 characters', code: 'TOO_SHORT' });
    fieldErrors.first_name = 'First name must be at least 2 characters';
  }

  if (!data.last_name?.trim()) {
    errors.push({ field: 'last_name', message: 'Last name is required', code: 'REQUIRED' });
    fieldErrors.last_name = 'Last name is required';
  } else if (data.last_name.trim().length < 2) {
    errors.push({ field: 'last_name', message: 'Last name must be at least 2 characters', code: 'TOO_SHORT' });
    fieldErrors.last_name = 'Last name must be at least 2 characters';
  }

  // Phone validation (optional but if provided, must be valid)
  if (data.phone && !/^\+?[1-9]\d{1,14}$/.test(data.phone.replace(/\s/g, ''))) {
    errors.push({ field: 'phone', message: 'Please enter a valid phone number', code: 'INVALID_FORMAT' });
    fieldErrors.phone = 'Please enter a valid phone number';
  }

  // Business information validation
  if (!data.business_name?.trim()) {
    errors.push({ field: 'business_name', message: 'Business name is required', code: 'REQUIRED' });
    fieldErrors.business_name = 'Business name is required';
  } else if (data.business_name.trim().length < 2) {
    errors.push({ field: 'business_name', message: 'Business name must be at least 2 characters', code: 'TOO_SHORT' });
    fieldErrors.business_name = 'Business name must be at least 2 characters';
  }

  if (!data.business_type?.trim()) {
    errors.push({ field: 'business_type', message: 'Business type is required', code: 'REQUIRED' });
    fieldErrors.business_type = 'Business type is required';
  }

  // Service package validation
  const validPackages = ['si', 'app', 'hybrid'];
  if (!data.service_package) {
    errors.push({ field: 'service_package', message: 'Service package is required', code: 'REQUIRED' });
    fieldErrors.service_package = 'Service package is required';
  } else if (!validPackages.includes(data.service_package)) {
    errors.push({ 
      field: 'service_package', 
      message: `Service package must be one of: ${validPackages.join(', ')}`, 
      code: 'INVALID_VALUE' 
    });
    fieldErrors.service_package = 'Please select a valid service package';
  }

  // Critical consent validation
  if (!data.terms_accepted) {
    errors.push({ 
      field: 'terms_accepted', 
      message: 'You must accept the terms and conditions to continue', 
      code: 'CONSENT_REQUIRED' 
    });
    fieldErrors.terms_accepted = 'You must accept the terms and conditions';
  }

  if (!data.privacy_accepted) {
    errors.push({ 
      field: 'privacy_accepted', 
      message: 'You must accept the privacy policy to continue', 
      code: 'CONSENT_REQUIRED' 
    });
    fieldErrors.privacy_accepted = 'You must accept the privacy policy';
  }

  // Optional field validation (if provided)
  if (data.tin && !/^\d{8}-\d{4}$/.test(data.tin)) {
    errors.push({ field: 'tin', message: 'TIN must be in format 12345678-0001', code: 'INVALID_FORMAT' });
    fieldErrors.tin = 'TIN must be in format 12345678-0001';
  }

  if (data.rc_number && data.rc_number.length < 6) {
    errors.push({ field: 'rc_number', message: 'RC number must be at least 6 characters', code: 'TOO_SHORT' });
    fieldErrors.rc_number = 'RC number must be at least 6 characters';
  }

  return {
    isValid: errors.length === 0,
    errors,
    fieldErrors
  };
}

/**
 * Validate specific step of multi-step registration
 */
export function validateRegistrationStep(step: number, data: any): ValidationResult {
  const errors: ValidationError[] = [];
  const fieldErrors: Record<string, string> = {};

  switch (step) {
    case 0: // Account step
      // Basic account validation
      if (!data.email?.trim()) {
        errors.push({ field: 'email', message: 'Email is required', code: 'REQUIRED' });
        fieldErrors.email = 'Email is required';
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
        errors.push({ field: 'email', message: 'Please enter a valid email', code: 'INVALID_FORMAT' });
        fieldErrors.email = 'Please enter a valid email';
      }

      if (!data.password) {
        errors.push({ field: 'password', message: 'Password is required', code: 'REQUIRED' });
        fieldErrors.password = 'Password is required';
      } else if (data.password.length < 8) {
        errors.push({ field: 'password', message: 'Password must be at least 8 characters', code: 'TOO_SHORT' });
        fieldErrors.password = 'Password must be at least 8 characters';
      }

      if (data.password && data.confirmPassword && data.password !== data.confirmPassword) {
        errors.push({ field: 'confirmPassword', message: 'Passwords do not match', code: 'MISMATCH' });
        fieldErrors.confirmPassword = 'Passwords do not match';
      }

      if (!data.first_name?.trim()) {
        errors.push({ field: 'first_name', message: 'First name is required', code: 'REQUIRED' });
        fieldErrors.first_name = 'First name is required';
      }

      if (!data.last_name?.trim()) {
        errors.push({ field: 'last_name', message: 'Last name is required', code: 'REQUIRED' });
        fieldErrors.last_name = 'Last name is required';
      }
      break;

    case 1: // Business step
      if (!data.business_name?.trim()) {
        errors.push({ field: 'business_name', message: 'Business name is required', code: 'REQUIRED' });
        fieldErrors.business_name = 'Business name is required';
      }

      if (!data.business_type?.trim()) {
        errors.push({ field: 'business_type', message: 'Business type is required', code: 'REQUIRED' });
        fieldErrors.business_type = 'Business type is required';
      }
      break;

    case 2: // Consent step
      if (!data.terms_accepted) {
        errors.push({ field: 'terms_accepted', message: 'Terms must be accepted', code: 'CONSENT_REQUIRED' });
        fieldErrors.terms_accepted = 'Terms must be accepted';
      }

      if (!data.privacy_accepted) {
        errors.push({ field: 'privacy_accepted', message: 'Privacy policy must be accepted', code: 'CONSENT_REQUIRED' });
        fieldErrors.privacy_accepted = 'Privacy policy must be accepted';
      }
      break;
  }

  return {
    isValid: errors.length === 0,
    errors,
    fieldErrors
  };
}

/**
 * Get user-friendly error message for API errors
 */
export function getRegistrationErrorMessage(error: any): string {
  if (!error) return 'Registration failed';

  // If it's already a formatted error message, return it
  if (typeof error === 'string') return error;

  // If it's an Error object with a message
  if (error.message) return error.message;

  // If it's an API error with response data
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail;
    
    // Map common backend errors to user-friendly messages
    if (detail.includes('Terms and conditions must be accepted')) {
      return 'Please accept the terms and conditions to continue';
    }
    if (detail.includes('Privacy policy must be accepted')) {
      return 'Please accept the privacy policy to continue';
    }
    if (detail.includes('Email address is already registered')) {
      return 'This email address is already registered. Please use a different email or try logging in.';
    }
    if (detail.includes('Invalid service package')) {
      return 'Please select a valid service package';
    }
    
    return detail;
  }

  // If it's a network error
  if (error.code === 'NETWORK_ERROR' || error.message?.includes('Network Error')) {
    return 'Network connection failed. Please check your internet connection and try again.';
  }

  // Default fallback
  return 'Registration failed. Please check your information and try again.';
}

/**
 * Password strength checker
 */
export function getPasswordStrength(password: string): {
  score: number;
  feedback: string;
  color: string;
} {
  if (!password) return { score: 0, feedback: 'Enter a password', color: 'gray' };

  let score = 0;
  const feedback = [];

  if (password.length >= 8) score++;
  else feedback.push('at least 8 characters');

  if (/[A-Z]/.test(password)) score++;
  else feedback.push('an uppercase letter');

  if (/[a-z]/.test(password)) score++;
  else feedback.push('a lowercase letter');

  if (/[0-9]/.test(password)) score++;
  else feedback.push('a number');

  if (/[^A-Za-z0-9]/.test(password)) score++;
  else feedback.push('a special character');

  const colors = ['red', 'red', 'orange', 'yellow', 'green', 'green'];
  const labels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong', 'Very Strong'];

  return {
    score,
    feedback: feedback.length > 0 ? `Add ${feedback.join(', ')}` : labels[score],
    color: colors[score]
  };
}

