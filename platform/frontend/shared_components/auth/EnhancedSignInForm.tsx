/**
 * Enhanced Sign In Form Component
 * ===============================
 * Modern sign-in form using our refined design system
 */

import React, { useState } from 'react';
import Link from 'next/link';
import { TaxPoyntButton, TaxPoyntInput } from '../../design_system';
import { TYPOGRAPHY_STYLES, ACCESSIBILITY_PATTERNS } from '../../design_system/style-utilities';

export interface SignInFormProps {
  onSignIn: (credentials: { email: string; password: string }) => Promise<void>;
  isLoading?: boolean;
  error?: string;
}

export const EnhancedSignInForm: React.FC<SignInFormProps> = ({ 
  onSignIn, 
  isLoading = false, 
  error 
}) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });

  const [fieldErrors, setFieldErrors] = useState<{[key: string]: string}>({});

  const validateForm = () => {
    const errors: {[key: string]: string} = {};
    
    if (!formData.email) {
      errors.email = 'Email address is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }
    
    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      errors.password = 'Password must be at least 6 characters';
    }
    
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      await onSignIn({
        email: formData.email,
        password: formData.password
      });
    } catch (err) {
      // Error handling is done by parent component
    }
  };

  const handleQuickDemo = () => {
    setFormData({ 
      email: 'demo@taxpoynt.com', 
      password: 'demo123', 
      rememberMe: false 
    });
    setFieldErrors({});
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      
      {/* Global Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-2xl">
          <div className="flex items-center">
            <span className="text-red-600 mr-3 text-xl">⚠️</span>
            <div>
              <div className="font-bold text-red-800 text-sm">Sign In Failed</div>
              <div className="text-red-700 text-sm">{error}</div>
            </div>
          </div>
        </div>
      )}

      {/* Email Field */}
      <div>
        <label 
          htmlFor="signin-email" 
          className="block text-sm font-bold text-slate-800 mb-2"
          style={TYPOGRAPHY_STYLES.optimizedText}
        >
          Email Address
        </label>
        <TaxPoyntInput
          id="signin-email"
          type="email"
          value={formData.email}
          onChange={(e) => {
            setFormData({ ...formData, email: e.target.value });
            if (fieldErrors.email) {
              setFieldErrors({ ...fieldErrors, email: '' });
            }
          }}
          placeholder="your@company.com"
          disabled={isLoading}
          variant={fieldErrors.email ? 'error' : 'default'}
          className="w-full"
          aria-describedby={fieldErrors.email ? 'email-error' : undefined}
          required
        />
        {fieldErrors.email && (
          <div id="email-error" className="mt-2 text-sm text-red-600 flex items-center">
            <span className="mr-1">❌</span>
            {fieldErrors.email}
          </div>
        )}
      </div>

      {/* Password Field */}
      <div>
        <label 
          htmlFor="signin-password" 
          className="block text-sm font-bold text-slate-800 mb-2"
          style={TYPOGRAPHY_STYLES.optimizedText}
        >
          Password
        </label>
        <TaxPoyntInput
          id="signin-password"
          type="password"
          value={formData.password}
          onChange={(e) => {
            setFormData({ ...formData, password: e.target.value });
            if (fieldErrors.password) {
              setFieldErrors({ ...fieldErrors, password: '' });
            }
          }}
          placeholder="Enter your password"
          disabled={isLoading}
          variant={fieldErrors.password ? 'error' : 'default'}
          className="w-full"
          aria-describedby={fieldErrors.password ? 'password-error' : undefined}
          required
        />
        {fieldErrors.password && (
          <div id="password-error" className="mt-2 text-sm text-red-600 flex items-center">
            <span className="mr-1">❌</span>
            {fieldErrors.password}
          </div>
        )}
      </div>

      {/* Remember Me & Forgot Password */}
      <div className="flex items-center justify-between">
        <label className="flex items-center group cursor-pointer">
          <input
            type="checkbox"
            checked={formData.rememberMe}
            onChange={(e) => setFormData({ ...formData, rememberMe: e.target.checked })}
            className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500 transition-all"
            disabled={isLoading}
            style={ACCESSIBILITY_PATTERNS.focusRing}
          />
          <span 
            className="ml-2 text-sm text-slate-600 group-hover:text-slate-800 transition-colors"
            style={TYPOGRAPHY_STYLES.optimizedText}
          >
            Remember me for 30 days
          </span>
        </label>
        
        <Link
          href="/auth/forgot-password"
          className="text-sm text-blue-600 hover:text-blue-800 hover:underline font-medium transition-colors"
          style={ACCESSIBILITY_PATTERNS.focusRing}
        >
          Forgot password?
        </Link>
      </div>

      {/* Sign In Button */}
      <TaxPoyntButton
        type="submit"
        variant="primary"
        size="lg"
        disabled={isLoading}
        className="w-full"
        style={{
          background: isLoading 
            ? 'linear-gradient(135deg, #94a3b8 0%, #64748b 100%)' 
            : 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
          boxShadow: isLoading 
            ? 'none' 
            : '0 10px 25px -5px rgba(59, 130, 246, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
        }}
        aria-label={isLoading ? 'Signing in...' : 'Sign in to your account'}
      >
        {isLoading ? (
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
            Signing in...
          </div>
        ) : (
          <div className="flex items-center justify-center">
            <span className="mr-2">🚀</span>
            Sign In to Dashboard
          </div>
        )}
      </TaxPoyntButton>

      {/* Divider */}
      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-300"></div>
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-4 bg-white text-slate-500 font-medium">or</span>
        </div>
      </div>

      {/* Quick Demo Access */}
      <div className="space-y-4">
        <TaxPoyntButton
          type="button"
          variant="outline"
          size="lg"
          onClick={handleQuickDemo}
          disabled={isLoading}
          className="w-full border-2 border-green-300 text-green-700 hover:bg-green-50 hover:border-green-400"
        >
          <div className="flex items-center justify-center">
            <span className="mr-2">🎯</span>
            Try Demo Account
          </div>
        </TaxPoyntButton>

        {/* Demo Account Info */}
        <div className="text-center p-3 bg-green-50 rounded-xl border border-green-200">
          <div className="text-sm text-green-800">
            <div className="font-bold mb-1">Quick Demo Access</div>
            <div className="text-xs">
              Explore all features with pre-loaded demo data • No commitment required
            </div>
          </div>
        </div>
      </div>

      {/* Sign Up Link */}
      <div className="text-center pt-4 border-t border-gray-200">
        <p 
          className="text-slate-600"
          style={TYPOGRAPHY_STYLES.optimizedText}
        >
          Don't have an account?{' '}
          <Link 
            href="/auth/signup"
            className="text-blue-600 hover:text-blue-800 font-bold hover:underline transition-colors"
            style={ACCESSIBILITY_PATTERNS.focusRing}
          >
            Create free account
          </Link>
        </p>
        <p className="text-xs text-slate-500 mt-2">
          14-day free trial • No credit card required • Cancel anytime
        </p>
      </div>
    </form>
  );
};
