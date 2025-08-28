/**
 * Authentication Service
 * =====================
 * Production-grade authentication service using Axios API client.
 * Connects frontend components to backend authentication API endpoints.
 */

import apiClient, { APIError } from '../api/client';

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role: string;
  service_package?: string;
  is_email_verified?: boolean;
  organization?: Organization;
  permissions?: string[];
}

export interface Organization {
  id: string;
  name: string;
  business_type: string;
  tin?: string;
  rc_number?: string;
  status: string;
  service_packages: string[];
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
  service_package: string;
  business_name: string;
  business_type?: string;  // Now optional - collected during onboarding
  tin?: string;
  rc_number?: string;
  address?: string;
  state?: string;
  lga?: string;
  terms_accepted: boolean;
  privacy_accepted: boolean;
  marketing_consent?: boolean;
  consents?: Record<string, any>;
}

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in?: number;
  user: User;
}

class AuthService {
  private tokenKey = 'taxpoynt_token';
  private userKey = 'taxpoynt_user';

  constructor() {
    // API client handles base URL and configuration
  }

  async register(userData: RegisterRequest): Promise<AuthResponse> {
    try {
      // Use API client for registration with built-in error handling
      const authData = await apiClient.register({
        email: userData.email,
        password: userData.password,
        first_name: userData.first_name,
        last_name: userData.last_name,
        phone: userData.phone,
        service_package: userData.service_package,
        business_name: userData.business_name,
        business_type: userData.business_type,
        tin: userData.tin,
        rc_number: userData.rc_number,
        address: userData.address,
        state: userData.state,
        lga: userData.lga,
        terms_accepted: userData.terms_accepted,
        privacy_accepted: userData.privacy_accepted,
        marketing_consent: userData.marketing_consent,
        consents: userData.consents
      });

      // Store auth data using API client's method
      return authData;
    } catch (error) {
      // API client already formats errors consistently
      throw error;
    }
  }

  async login(credentials: LoginRequest): Promise<AuthResponse> {
    try {
      // Use API client for login with built-in error handling
      const authData = await apiClient.login(
        credentials.email,
        credentials.password,
        credentials.remember_me
      );

      return authData;
    } catch (error) {
      // API client already formats errors consistently
      throw error;
    }
  }

  async logout(): Promise<void> {
    try {
      // Use API client for logout with built-in error handling
      await apiClient.logout();
    } catch (error) {
      // Continue with logout even if server call fails
      console.warn('Logout server call failed:', error);
    }
  }

  isAuthenticated(): boolean {
    return apiClient.isAuthenticated();
  }

  getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(this.tokenKey);
  }

  getStoredUser(): User | null {
    return apiClient.getStoredUser();
  }

  getUserRole(): string | null {
    return this.getStoredUser()?.role || null;
  }

  getServicePackage(): string | null {
    return this.getStoredUser()?.service_package || null;
  }

  getAuthHeaders(): Record<string, string> {
    const token = this.getToken();
    if (!token) throw new Error('No authentication token available');
    
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  /**
   * Map frontend service package to backend role
   */
  private mapServicePackageToRole(servicePackage: string): string {
    const roleMapping: Record<string, string> = {
      'si': 'system_integrator',
      'app': 'access_point_provider',
      'hybrid': 'hybrid_user'
    };
    return roleMapping[servicePackage] || 'system_integrator';
  }

  /**
   * Handle authentication errors consistently
   */
  handleAuthError(error: any): string {
    console.log('🔍 Auth Error Debug:', error);
    
    if (error && typeof error === 'object' && 'message' in error) {
      const apiError = error as APIError;
      
      console.log(`🚨 API Error - Status: ${apiError.status}, Message: ${apiError.message}`);
      console.log('📋 Error Details:', apiError.details);
      
      // Map specific error codes to user-friendly messages
      switch (apiError.status) {
        case 400:
          // Try to extract specific field errors from details
          if (apiError.details && typeof apiError.details === 'object') {
            if (apiError.details.detail && typeof apiError.details.detail === 'string') {
              return apiError.details.detail;
            }
            if (apiError.details.message && typeof apiError.details.message === 'string') {
              return apiError.details.message;
            }
            // Handle FastAPI validation errors
            if (Array.isArray(apiError.details.detail)) {
              const validationErrors = apiError.details.detail
                .map((err: any) => `${err.loc?.join('.')}: ${err.msg}`)
                .join(', ');
              return `Validation errors: ${validationErrors}`;
            }
          }
          return apiError.message || 'Invalid request. Please check your information.';
        case 401:
          return 'Invalid email or password. Please try again.';
        case 403:
          return 'Access denied. Please contact support.';
        case 409:
          return 'Email address is already registered. Please try signing in instead.';
        case 422:
          // Handle FastAPI validation errors specifically
          if (apiError.details && Array.isArray(apiError.details.detail)) {
            const validationErrors = apiError.details.detail
              .map((err: any) => `${err.loc?.join('.')}: ${err.msg}`)
              .join(', ');
            return `Please check: ${validationErrors}`;
          }
          return 'Please check your input data for errors.';
        case 429:
          return 'Too many requests. Please wait a moment and try again.';
        case 500:
        case 502:
        case 503:
        case 504:
          return 'Server error. Please try again later.';
        default:
          return apiError.message || 'An unexpected error occurred. Please try again.';
      }
    }

    // Handle string errors
    if (typeof error === 'string') {
      return error;
    }

    // Fallback for unknown error types
    console.log('❓ Unknown error type:', typeof error, error);
    return 'An unexpected error occurred. Please try again.';
  }

  /**
   * Get redirect URL based on user role
   */
  getDashboardRedirectUrl(role: string): string {
    const roleRedirects: Record<string, string> = {
      'system_integrator': '/dashboard/si',
      'access_point_provider': '/dashboard/app',
      'hybrid_user': '/dashboard/hybrid',
    };

    return roleRedirects[role] || '/dashboard';
  }

  /**
   * Check service health
   */
  async checkHealth(): Promise<any> {
    try {
      return await apiClient.healthCheck();
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }
}

export const authService = new AuthService();
// Types already exported above