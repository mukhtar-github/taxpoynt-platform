/**
 * Enhanced Sign Up Form Component
 * ===============================
 * Modern sign-up form using our refined design system
 */

import React, { useState } from 'react';
import Link from 'next/link';
import { TaxPoyntButton, TaxPoyntInput } from '../../design_system';
import { TYPOGRAPHY_STYLES, ACCESSIBILITY_PATTERNS } from '../../design_system/style-utilities';

export interface SignUpFormProps {
  onSignUp: (userData: {
    email: string;
    password: string;
    confirmPassword: string;
    companyName: string;
    fullName: string;
    role: string;
    acceptTerms: boolean;
  }) => Promise<void>;
  isLoading?: boolean;
  error?: string;
}

export const EnhancedSignUpForm: React.FC<SignUpFormProps> = ({ 
  onSignUp, 
  isLoading = false, 
  error 
}) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    companyName: '',
    fullName: '',
    role: 'system_integrator',
    acceptTerms: false,
    subscribeNewsletter: true
  });

  const [fieldErrors, setFieldErrors] = useState<{[key: string]: string}>({});
  const [passwordStrength, setPasswordStrength] = useState<'weak' | 'medium' | 'strong'>('weak');

  const validateForm = () => {
    const errors: {[key: string]: string} = {};
    
    // Email validation
    if (!formData.email) {
      errors.email = 'Email address is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }
    
    // Password validation
    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    }
    
    // Confirm password validation
    if (!formData.confirmPassword) {
      errors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }
    
    // Company name validation
    if (!formData.companyName.trim()) {
      errors.companyName = 'Company name is required';
    }
    
    // Full name validation
    if (!formData.fullName.trim()) {
      errors.fullName = 'Full name is required';
    }
    
    // Terms acceptance validation
    if (!formData.acceptTerms) {
      errors.acceptTerms = 'You must accept the terms and conditions';
    }
    
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const calculatePasswordStrength = (password: string) => {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    
    if (strength <= 2) return 'weak';
    if (strength <= 4) return 'medium';
    return 'strong';
  };

  const handlePasswordChange = (password: string) => {
    setFormData({ ...formData, password });
    setPasswordStrength(calculatePasswordStrength(password));
    if (fieldErrors.password) {
      setFieldErrors({ ...fieldErrors, password: '' });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      await onSignUp(formData);
    } catch (err) {
      // Error handling is done by parent component
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      
      {/* Global Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-2xl">
          <div className="flex items-center">
            <span className="text-red-600 mr-3 text-xl">⚠️</span>
            <div>
              <div className="font-bold text-red-800 text-sm">Registration Failed</div>
              <div className="text-red-700 text-sm">{error}</div>
            </div>
          </div>
        </div>
      )}

      {/* Account Type Selection */}
      <div>
        <label 
          className="block text-sm font-bold text-slate-800 mb-3"
          style={TYPOGRAPHY_STYLES.optimizedText}
        >
          Choose Your Account Type
        </label>
        <div className="grid grid-cols-1 gap-3">
          {[
            { 
              value: 'system_integrator', 
              label: 'System Integrator (SI)', 
              description: 'Connect multiple business systems',
              icon: '🔗',
              popular: true
            },
            { 
              value: 'access_point_provider', 
              label: 'Access Point Provider (APP)', 
              description: 'Direct FIRS communication',
              icon: '🏛️',
              popular: false
            },
            { 
              value: 'hybrid_user', 
              label: 'Hybrid Solution', 
              description: 'Best of both worlds',
              icon: '⚡',
              popular: false
            }
          ].map((roleOption) => (
            <label
              key={roleOption.value}
              className={`relative flex items-center p-4 border-2 rounded-xl cursor-pointer transition-all ${
                formData.role === roleOption.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              <input
                type="radio"
                name="role"
                value={roleOption.value}
                checked={formData.role === roleOption.value}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                className="sr-only"
              />
              <div className="flex items-center w-full">
                <span className="text-2xl mr-3">{roleOption.icon}</span>
                <div className="flex-1">
                  <div className="flex items-center">
                    <span className="font-bold text-slate-800">{roleOption.label}</span>
                    {roleOption.popular && (
                      <span className="ml-2 px-2 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-full">
                        Most Popular
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-slate-600">{roleOption.description}</div>
                </div>
                <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                  formData.role === roleOption.value
                    ? 'border-blue-500 bg-blue-500'
                    : 'border-gray-300'
                }`}>
                  {formData.role === roleOption.value && (
                    <div className="w-2 h-2 bg-white rounded-full"></div>
                  )}
                </div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Company Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label 
            htmlFor="signup-company" 
            className="block text-sm font-bold text-slate-800 mb-2"
            style={TYPOGRAPHY_STYLES.optimizedText}
          >
            Company Name
          </label>
          <TaxPoyntInput
            id="signup-company"
            type="text"
            value={formData.companyName}
            onChange={(e) => {
              setFormData({ ...formData, companyName: e.target.value });
              if (fieldErrors.companyName) {
                setFieldErrors({ ...fieldErrors, companyName: '' });
              }
            }}
            placeholder="Your Company Ltd"
            disabled={isLoading}
            variant={fieldErrors.companyName ? 'error' : 'default'}
            className="w-full"
            required
          />
          {fieldErrors.companyName && (
            <div className="mt-2 text-sm text-red-600 flex items-center">
              <span className="mr-1">❌</span>
              {fieldErrors.companyName}
            </div>
          )}
        </div>

        <div>
          <label 
            htmlFor="signup-name" 
            className="block text-sm font-bold text-slate-800 mb-2"
            style={TYPOGRAPHY_STYLES.optimizedText}
          >
            Full Name
          </label>
          <TaxPoyntInput
            id="signup-name"
            type="text"
            value={formData.fullName}
            onChange={(e) => {
              setFormData({ ...formData, fullName: e.target.value });
              if (fieldErrors.fullName) {
                setFieldErrors({ ...fieldErrors, fullName: '' });
              }
            }}
            placeholder="John Doe"
            disabled={isLoading}
            variant={fieldErrors.fullName ? 'error' : 'default'}
            className="w-full"
            required
          />
          {fieldErrors.fullName && (
            <div className="mt-2 text-sm text-red-600 flex items-center">
              <span className="mr-1">❌</span>
              {fieldErrors.fullName}
            </div>
          )}
        </div>
      </div>

      {/* Email Field */}
      <div>
        <label 
          htmlFor="signup-email" 
          className="block text-sm font-bold text-slate-800 mb-2"
          style={TYPOGRAPHY_STYLES.optimizedText}
        >
          Work Email Address
        </label>
        <TaxPoyntInput
          id="signup-email"
          type="email"
          value={formData.email}
          onChange={(e) => {
            setFormData({ ...formData, email: e.target.value });
            if (fieldErrors.email) {
              setFieldErrors({ ...fieldErrors, email: '' });
            }
          }}
          placeholder="john@yourcompany.com"
          disabled={isLoading}
          variant={fieldErrors.email ? 'error' : 'default'}
          className="w-full"
          required
        />
        {fieldErrors.email && (
          <div className="mt-2 text-sm text-red-600 flex items-center">
            <span className="mr-1">❌</span>
            {fieldErrors.email}
          </div>
        )}
      </div>

      {/* Password Fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label 
            htmlFor="signup-password" 
            className="block text-sm font-bold text-slate-800 mb-2"
            style={TYPOGRAPHY_STYLES.optimizedText}
          >
            Password
          </label>
          <TaxPoyntInput
            id="signup-password"
            type="password"
            value={formData.password}
            onChange={(e) => handlePasswordChange(e.target.value)}
            placeholder="Choose a strong password"
            disabled={isLoading}
            variant={fieldErrors.password ? 'error' : 'default'}
            className="w-full"
            required
          />
          
          {/* Password Strength Indicator */}
          {formData.password && (
            <div className="mt-2">
              <div className="flex items-center space-x-2">
                <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className={`h-full transition-all duration-300 ${
                      passwordStrength === 'weak' ? 'w-1/3 bg-red-500' :
                      passwordStrength === 'medium' ? 'w-2/3 bg-yellow-500' :
                      'w-full bg-green-500'
                    }`}
                  ></div>
                </div>
                <span className={`text-xs font-medium ${
                  passwordStrength === 'weak' ? 'text-red-600' :
                  passwordStrength === 'medium' ? 'text-yellow-600' :
                  'text-green-600'
                }`}>
                  {passwordStrength === 'weak' ? 'Weak' :
                   passwordStrength === 'medium' ? 'Medium' : 'Strong'}
                </span>
              </div>
            </div>
          )}
          
          {fieldErrors.password && (
            <div className="mt-2 text-sm text-red-600 flex items-center">
              <span className="mr-1">❌</span>
              {fieldErrors.password}
            </div>
          )}
        </div>

        <div>
          <label 
            htmlFor="signup-confirm-password" 
            className="block text-sm font-bold text-slate-800 mb-2"
            style={TYPOGRAPHY_STYLES.optimizedText}
          >
            Confirm Password
          </label>
          <TaxPoyntInput
            id="signup-confirm-password"
            type="password"
            value={formData.confirmPassword}
            onChange={(e) => {
              setFormData({ ...formData, confirmPassword: e.target.value });
              if (fieldErrors.confirmPassword) {
                setFieldErrors({ ...fieldErrors, confirmPassword: '' });
              }
            }}
            placeholder="Confirm your password"
            disabled={isLoading}
            variant={fieldErrors.confirmPassword ? 'error' : 'default'}
            className="w-full"
            required
          />
          {fieldErrors.confirmPassword && (
            <div className="mt-2 text-sm text-red-600 flex items-center">
              <span className="mr-1">❌</span>
              {fieldErrors.confirmPassword}
            </div>
          )}
        </div>
      </div>

      {/* Terms and Newsletter */}
      <div className="space-y-4">
        <label className="flex items-start group cursor-pointer">
          <input
            type="checkbox"
            checked={formData.acceptTerms}
            onChange={(e) => {
              setFormData({ ...formData, acceptTerms: e.target.checked });
              if (fieldErrors.acceptTerms) {
                setFieldErrors({ ...fieldErrors, acceptTerms: '' });
              }
            }}
            className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500 transition-all mt-1"
            disabled={isLoading}
            required
          />
          <span 
            className="ml-3 text-sm text-slate-600 group-hover:text-slate-800 transition-colors leading-relaxed"
            style={TYPOGRAPHY_STYLES.optimizedText}
          >
            I agree to the{' '}
            <Link href="/terms" className="text-blue-600 hover:text-blue-800 underline">
              Terms of Service
            </Link>{' '}
            and{' '}
            <Link href="/privacy" className="text-blue-600 hover:text-blue-800 underline">
              Privacy Policy
            </Link>
          </span>
        </label>
        
        {fieldErrors.acceptTerms && (
          <div className="text-sm text-red-600 flex items-center">
            <span className="mr-1">❌</span>
            {fieldErrors.acceptTerms}
          </div>
        )}

        <label className="flex items-start group cursor-pointer">
          <input
            type="checkbox"
            checked={formData.subscribeNewsletter}
            onChange={(e) => setFormData({ ...formData, subscribeNewsletter: e.target.checked })}
            className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500 transition-all mt-1"
            disabled={isLoading}
          />
          <span 
            className="ml-3 text-sm text-slate-600 group-hover:text-slate-800 transition-colors leading-relaxed"
            style={TYPOGRAPHY_STYLES.optimizedText}
          >
            Send me product updates and tax compliance tips (optional)
          </span>
        </label>
      </div>

      {/* Create Account Button */}
      <TaxPoyntButton
        type="submit"
        variant="primary"
        size="lg"
        disabled={isLoading}
        className="w-full"
        style={{
          background: isLoading 
            ? 'linear-gradient(135deg, #94a3b8 0%, #64748b 100%)' 
            : 'linear-gradient(135deg, #059669 0%, #047857 100%)',
          boxShadow: isLoading 
            ? 'none' 
            : '0 10px 25px -5px rgba(5, 150, 105, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
        }}
      >
        {isLoading ? (
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
            Creating account...
          </div>
        ) : (
          <div className="flex items-center justify-center">
            <span className="mr-2">🎉</span>
            Create Free Account
          </div>
        )}
      </TaxPoyntButton>

      {/* Sign In Link */}
      <div className="text-center pt-4 border-t border-gray-200">
        <p 
          className="text-slate-600"
          style={TYPOGRAPHY_STYLES.optimizedText}
        >
          Already have an account?{' '}
          <Link 
            href="/auth/signin"
            className="text-blue-600 hover:text-blue-800 font-bold hover:underline transition-colors"
            style={ACCESSIBILITY_PATTERNS.focusRing}
          >
            Sign in
          </Link>
        </p>
        <p className="text-xs text-slate-500 mt-2">
          14-day free trial • No credit card required • Cancel anytime
        </p>
      </div>
    </form>
  );
};
