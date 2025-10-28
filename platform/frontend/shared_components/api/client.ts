/**
 * TaxPoynt API Client - Production HTTP Layer
 * ==========================================
 * Centralized Axios configuration with interceptors, error handling,
 * and authentication management for production reliability.
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { secureTokenStorage } from '../utils/secureTokenStorage';
import { secureLogger } from '../utils/secureLogger';
import { secureConfig } from '../utils/secureConfig';

// Extend Axios config to include metadata
interface ExtendedAxiosRequestConfig extends InternalAxiosRequestConfig {
  metadata?: { startTime: Date };
}

// Type for API error response data
interface APIErrorResponseData {
  detail?: string;
  message?: string;
  code?: string;
  [key: string]: any;
}

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://web-production-ea5ad.up.railway.app/api/v1';
const API_TIMEOUT = 30000; // 30 seconds for production reliability

// Token storage keys
const TOKEN_KEY = 'taxpoynt_token';
const USER_KEY = 'taxpoynt_user';

/**
 * Enhanced Error Response Interface
 */
export interface APIError {
  message: string;
  status: number;
  code?: string;
  details?: any;
  timestamp: string;
}

/**
 * Authentication Response Interface
 */
export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in?: number;
  user: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    role: string;
    service_package?: string;
    organization?: any;
  };
}

/**
 * Registration Request Interface
 */
export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
  service_package: string;  // si, app, hybrid (instead of role)
  business_name: string;    // Required by backend
  business_type?: string;   // Now optional - collected during onboarding
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

export interface RegisterPendingResponse {
  status: 'pending';
  next: string;
  user: AuthResponse['user'];
  onboarding_token?: string;
}

export interface VerifyEmailRequest {
  email: string;
  code: string;
  service_package?: string;
  onboarding_token?: string;
  terms_accepted: boolean;
  privacy_accepted: boolean;
  metadata?: Record<string, any>;
}

/**
 * Production-Grade API Client Class
 */
class TaxPoyntAPIClient {
  private client: AxiosInstance;
  private isRefreshing = false;
  private failedQueue: Array<{
    resolve: (token: string) => void;
    reject: (error: any) => void;
  }> = [];

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  /**
   * Setup request and response interceptors
   */
  private setupInterceptors(): void {
    // Request Interceptor - Add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getStoredToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add request timestamp for monitoring
        (config as ExtendedAxiosRequestConfig).metadata = { startTime: new Date() };
        
        return config;
      },
      (error) => {
        console.error('Request interceptor error:', error);
        return Promise.reject(this.formatError(error));
      }
    );

    // Response Interceptor - Handle errors and token refresh
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        // Log response time for monitoring
        const endTime = new Date();
        const startTime = (response.config as ExtendedAxiosRequestConfig).metadata?.startTime;
        if (startTime) {
          const duration = endTime.getTime() - startTime.getTime();
          console.debug(`API Request to ${response.config.url} took ${duration}ms`);
        }

        return response;
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as any;

        // Handle 401 Unauthorized
        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            // Queue the request if token refresh is in progress
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject });
            }).then(token => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              return this.client(originalRequest);
            }).catch(err => {
              return Promise.reject(err);
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            // Try to refresh token or redirect to login
            const token = await this.handleTokenRefresh();
            this.processQueue(null, token);
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            this.processQueue(refreshError, null);
            this.clearAuth();
            
            // Redirect to login in browser environment
            if (typeof window !== 'undefined') {
              window.location.href = '/auth/signin';
            }
            
            return Promise.reject(refreshError);
          } finally {
            this.isRefreshing = false;
          }
        }

        return Promise.reject(this.formatError(error));
      }
    );
  }

  /**
   * Process queued requests after token refresh
   */
  private processQueue(error: any, token: string | null): void {
    this.failedQueue.forEach(({ resolve, reject }) => {
      if (error) {
        reject(error);
      } else {
        resolve(token!);
      }
    });
    
    this.failedQueue = [];
  }

  /**
   * Handle token refresh (placeholder for future implementation)
   */
  private async handleTokenRefresh(): Promise<string> {
    // For now, just clear auth and throw error
    // In future, implement actual token refresh logic
    throw new Error('Token expired - please login again');
  }

  /**
   * Format error responses consistently
   */
  private formatError(error: AxiosError): APIError {
    const timestamp = new Date().toISOString();
    
    if (error.response) {
      // Server responded with error status
      const errorData = error.response.data as APIErrorResponseData;
      
      console.log(`🌐 HTTP Error ${error.response.status}:`, error.response.data);
      
      return {
        message: errorData?.detail || errorData?.message || `HTTP ${error.response.status} error`,
        status: error.response.status,
        code: errorData?.code,
        details: error.response.data,
        timestamp,
      };
    } else if (error.request) {
      // Request made but no response received
      console.log('🔌 Network Error:', error.message);
      return {
        message: 'Network error - please check your connection',
        status: 0,
        code: 'NETWORK_ERROR',
        details: error.message,
        timestamp,
      };
    } else {
      // Something else happened
      console.log('❓ Request Setup Error:', error.message);
      return {
        message: error.message || 'An unexpected error occurred',
        status: 0,
        code: 'UNKNOWN_ERROR',
        details: error,
        timestamp,
      };
    }
  }

  /**
   * Get stored authentication token
   */
  private getStoredToken(): string | null {
    if (typeof window === 'undefined') return null;
    return secureTokenStorage.getToken();
  }

  /**
   * Store authentication data
   */
  private storeAuth(authData: AuthResponse, options: { persist?: boolean } = {}): void {
    if (typeof window === 'undefined') return;

    const shouldPersist = Boolean(options.persist);
    
    // SECURITY: Store token securely using secureTokenStorage
    secureTokenStorage.storeToken(authData.access_token, { 
      encryptTokens: true, 
      autoRefresh: true,
      persistAcrossSessions: shouldPersist,
    });
    
    // Store user data in sessionStorage for privacy
    const serializedUser = JSON.stringify(authData.user);
    sessionStorage.setItem(USER_KEY, serializedUser);
    if (shouldPersist) {
      localStorage.setItem(USER_KEY, serializedUser);
    } else {
      localStorage.removeItem(USER_KEY);
    }
  }

  /**
   * Clear authentication data
   */
  private clearAuth(): void {
    if (typeof window === 'undefined') return;
    
    secureTokenStorage.clearToken();
    sessionStorage.removeItem(USER_KEY);
    localStorage.removeItem(USER_KEY);
  }

  /**
   * Get stored user data
   */
  public getStoredUser(): any | null {
    if (typeof window === 'undefined') return null;
    
    let userStr = sessionStorage.getItem(USER_KEY);
    if (!userStr) {
      userStr = localStorage.getItem(USER_KEY);
      if (userStr) {
        sessionStorage.setItem(USER_KEY, userStr);
      }
    }
    return userStr ? JSON.parse(userStr) : null;
  }

  /**
   * Check if user is authenticated
   */
  public isAuthenticated(): boolean {
    return !!this.getStoredToken();
  }

  /**
   * Register new user
   */
  public async register(userData: RegisterRequest): Promise<AuthResponse | RegisterPendingResponse> {
    try {
      secureLogger.userAction('TaxPoynt API: Attempting registration', { 
        endpoint: `${API_BASE_URL}/auth/register`,
        user_email: userData.email,
        service_package: userData.service_package
      });
      
      // Validate required fields before sending
      if (!userData.email || !userData.password || !userData.first_name || !userData.last_name) {
        throw new Error('Missing required fields: email, password, first_name, last_name');
      }
      
      if (!userData.business_name) {
        throw new Error('Missing required business field: business_name');
      }
      
      // Note: business_type is now optional and collected during onboarding
      
      if (!userData.service_package) {
        console.warn('⚠️ No service_package specified, defaulting to si');
        userData.service_package = 'si';
      }
      
      secureLogger.userAction('Sending registration request');
      const response = await this.client.post<AuthResponse | RegisterPendingResponse | { success: boolean; data: any }>(
        '/auth/register',
        userData
      );

      const payload = (response.data as any)?.success ? (response.data as any).data : response.data;
      const data = payload as AuthResponse | RegisterPendingResponse;

      if ('status' in data && data.status === 'pending') {
        secureLogger.success('Registration pending verification', {
          user_email: data.user.email,
          service_package: data.user.service_package,
          next: data.next,
        });
        return data;
      }

      secureLogger.success('Registration successful', {
        user_email: data.user.email,
        service_package: data.user.service_package,
      });
      
      // Store authentication data when immediate login is allowed
      this.storeAuth(data as AuthResponse, { persist: false });

      return data;
          } catch (error) {
        secureLogger.error('Registration failed', error);

        // Enhanced error handling for registration
        if (axios.isAxiosError(error)) {
          const status = error.response?.status;
          const data = error.response?.data;

          secureLogger.error('Registration error details', {
            status,
            data: secureConfig.sanitizeConfig(data),
            headers: error.response?.headers,
            config: {
              url: error.config?.url,
              method: error.config?.method,
              data: error.config?.data ? secureConfig.sanitizeConfig(JSON.parse(error.config.data)) : null
            }
          });

          // Log the raw response data to see what's actually being returned
          secureLogger.error('Raw error response data', { 
            data: secureConfig.sanitizeConfig(data) 
          });
        
        if (status === 400) {
          // Parse 400 errors to provide specific feedback
          const detail = data?.detail || 'Registration failed due to validation errors';
          
          if (detail.includes('Terms and conditions must be accepted')) {
            throw new Error('Please accept the terms and conditions to continue');
          } else if (detail.includes('Privacy policy must be accepted')) {
            throw new Error('Please accept the privacy policy to continue');
          } else if (detail.includes('Email address is already registered')) {
            throw new Error('This email address is already registered. Please use a different email or try logging in.');
          } else if (detail.includes('Invalid service package')) {
            throw new Error('Please select a valid service package');
          } else {
            throw new Error(`Registration validation failed: ${detail}`);
          }
        }
      }
      
      throw error; // Re-throw formatted error from interceptor
    }
  }

  public async verifyEmail(payload: VerifyEmailRequest): Promise<AuthResponse> {
    try {
      secureLogger.userAction('TaxPoynt API: Verifying email', { email: payload.email });
      const response = await this.client.post<AuthResponse | { success: boolean; data: AuthResponse }>(
        '/auth/verify-email',
        payload
      );
      const data = (response.data as any)?.success ? (response.data as any).data : response.data;
      this.storeAuth(data as AuthResponse, { persist: false });
      secureLogger.success('Email verification successful', { email: payload.email });
      return data as AuthResponse;
    } catch (error) {
      secureLogger.error('Email verification failed', error);
      throw error;
    }
  }

  /**
   * Login user
   */
  public async login(email: string, password: string, rememberMe = false): Promise<AuthResponse> {
    try {
      const response = await this.client.post<AuthResponse>('/auth/login', {
        email,
        password,
        remember_me: rememberMe,
      });
      
      // Store authentication data
      this.storeAuth(response.data, { persist: rememberMe });
      
      return response.data;
    } catch (error) {
      throw error; // Re-throw formatted error from interceptor
    }
  }

  /**
   * Logout user
   */
  public async logout(): Promise<void> {
    try {
      await this.client.post('/auth/logout');
    } catch (error) {
      // Continue with logout even if server call fails
      secureLogger.error('Logout server call failed', error);
    } finally {
      this.clearAuth();
    }
  }

  /**
   * Get current user info
   */
  public async getCurrentUser(): Promise<any> {
    try {
      const response = await this.client.get('/auth/me');
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Health check
   */
  public async healthCheck(): Promise<any> {
    try {
      const response = await this.client.get('/auth/health');
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Generic GET request
   */
  public async get<T>(url: string, config = {}): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  /**
   * Generic POST request
   */
  public async post<T>(url: string, data = {}, config = {}): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  /**
   * Generic PUT request
   */
  public async put<T>(url: string, data = {}, config = {}): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  /**
   * Generic DELETE request
   */
  public async delete<T>(url: string, config = {}): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }
}

// Create singleton instance
const apiClient = new TaxPoyntAPIClient();

export default apiClient;
export { TaxPoyntAPIClient };
