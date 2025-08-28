/**
 * TaxPoynt API Client - Production HTTP Layer
 * ==========================================
 * Centralized Axios configuration with interceptors, error handling,
 * and authentication management for production reliability.
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';

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
    return localStorage.getItem(TOKEN_KEY);
  }

  /**
   * Store authentication data
   */
  private storeAuth(authData: AuthResponse): void {
    if (typeof window === 'undefined') return;
    
    localStorage.setItem(TOKEN_KEY, authData.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(authData.user));
  }

  /**
   * Clear authentication data
   */
  private clearAuth(): void {
    if (typeof window === 'undefined') return;
    
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  /**
   * Get stored user data
   */
  public getStoredUser(): any | null {
    if (typeof window === 'undefined') return null;
    
    const userStr = localStorage.getItem(USER_KEY);
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
  public async register(userData: RegisterRequest): Promise<AuthResponse> {
    try {
      console.log('🚀 TaxPoynt API: Attempting registration to:', `${API_BASE_URL}/auth/register`);
      console.log('📝 Registration data:', { 
        email: userData.email,
        first_name: userData.first_name,
        last_name: userData.last_name,
        business_name: userData.business_name,
        business_type: userData.business_type,
        service_package: userData.service_package,
        password: '***hidden***'
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
      
      console.log('🔄 Sending registration request...');
      const response = await this.client.post<AuthResponse>('/auth/register', userData);
      
      console.log('✅ Registration successful:', response.data.user.email);
      console.log('👤 User created with service_package:', response.data.user.service_package);
      
      // Store authentication data
      this.storeAuth(response.data);
      
      return response.data;
          } catch (error) {
        console.error('❌ Registration failed:', error);

        // Enhanced error handling for registration
        if (axios.isAxiosError(error)) {
          const status = error.response?.status;
          const data = error.response?.data;

          console.log('🔍 Detailed error info:', {
            status,
            data,
            headers: error.response?.headers,
            config: {
              url: error.config?.url,
              method: error.config?.method,
              data: error.config?.data ? JSON.parse(error.config.data) : null
            }
          });

          // Log the raw response data to see what's actually being returned
          console.log('📄 Raw error response data:', JSON.stringify(data, null, 2));
        
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
      this.storeAuth(response.data);
      
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
      console.warn('Logout server call failed:', error);
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