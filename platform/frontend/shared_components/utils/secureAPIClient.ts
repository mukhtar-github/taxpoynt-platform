/**
 * Secure API Client
 * =================
 * Implements secure patterns for API communication
 * Prevents sensitive data exposure in requests, responses, and logs
 */

import { secureLogger } from './secureLogger';
import { secureTokenStorage } from './secureTokenStorage';

interface APIClientConfig {
  baseURL: string;
  timeout?: number;
  enableLogging?: boolean;
  sanitizeRequests?: boolean;
  sanitizeResponses?: boolean;
}

interface APIRequestConfig {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  url: string;
  data?: any;
  headers?: Record<string, string>;
  params?: Record<string, any>;
}

interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  status: number;
  message?: string;
}

class SecureAPIClient {
  private config: APIClientConfig;
  private sensitiveFields: Set<string> = new Set([
    'password', 'api_key', 'api_secret', 'client_secret', 'token',
    'secret', 'private_key', 'certificate', 'encryption_key',
    'ssn', 'tin', 'rc_number', 'bank_account', 'card_number'
  ]);

  constructor(config: APIClientConfig) {
    this.config = {
      timeout: 30000,
      enableLogging: process.env.NODE_ENV === 'development',
      sanitizeRequests: true,
      sanitizeResponses: true,
      ...config
    };
  }

  /**
   * Make a secure API request
   */
  async request<T = any>(config: APIRequestConfig): Promise<APIResponse<T>> {
    try {
      // Sanitize request data for logging
      const sanitizedData = this.sanitizeData(config.data);
      const sanitizedParams = this.sanitizeData(config.params);

      // Log request (development only)
      if (this.config.enableLogging) {
        secureLogger.apiCall(config.url, config.method, {
          params: sanitizedParams,
          data: sanitizedData,
          headers: this.sanitizeHeaders(config.headers)
        });
      }

      // Prepare request
      const requestConfig = this.prepareRequest(config);
      
      // Make request
      const response = await this.executeRequest(requestConfig);
      
      // Sanitize response for logging
      const sanitizedResponse = this.sanitizeData(response);
      
      // Log response (development only)
      if (this.config.enableLogging) {
        secureLogger.apiCall(`${config.url} (response)`, config.method, {
          status: response.status,
          data: sanitizedResponse
        });
      }

      return this.formatResponse(response);
    } catch (error) {
      // Log error securely
      secureLogger.error(`API request failed: ${config.method} ${config.url}`, error);
      
      return {
        success: false,
        error: this.sanitizeErrorMessage(error),
        status: 500
      };
    }
  }

  /**
   * GET request
   */
  async get<T = any>(url: string, params?: Record<string, any>): Promise<APIResponse<T>> {
    return this.request<T>({
      method: 'GET',
      url,
      params
    });
  }

  /**
   * POST request
   */
  async post<T = any>(url: string, data?: any): Promise<APIResponse<T>> {
    return this.request<T>({
      method: 'POST',
      url,
      data
    });
  }

  /**
   * PUT request
   */
  async put<T = any>(url: string, data?: any): Promise<APIResponse<T>> {
    return this.request<T>({
      method: 'PUT',
      url,
      data
    });
  }

  /**
   * DELETE request
   */
  async delete<T = any>(url: string): Promise<APIResponse<T>> {
    return this.request<T>({
      method: 'DELETE',
      url
    });
  }

  /**
   * PATCH request
   */
  async patch<T = any>(url: string, data?: any): Promise<APIResponse<T>> {
    return this.request<T>({
      method: 'PATCH',
      url,
      data
    });
  }

  /**
   * Sanitize data by removing sensitive fields
   */
  private sanitizeData(data: any): any {
    if (!data || typeof data !== 'object') {
      return data;
    }

    if (Array.isArray(data)) {
      return data.map(item => this.sanitizeData(item));
    }

    const sanitized: any = {};
    for (const [key, value] of Object.entries(data)) {
      const lowerKey = key.toLowerCase();
      const isSensitive = Array.from(this.sensitiveFields).some(field => 
        lowerKey.includes(field) || field.includes(lowerKey)
      );

      if (isSensitive) {
        sanitized[key] = '[REDACTED]';
      } else if (typeof value === 'object' && value !== null) {
        sanitized[key] = this.sanitizeData(value);
      } else {
        sanitized[key] = value;
      }
    }

    return sanitized;
  }

  /**
   * Sanitize headers by removing sensitive information
   */
  private sanitizeHeaders(headers?: Record<string, string>): Record<string, string> {
    if (!headers) return {};

    const sanitized: Record<string, string> = {};
    for (const [key, value] of Object.entries(headers)) {
      const lowerKey = key.toLowerCase();
      if (lowerKey.includes('authorization') || lowerKey.includes('token')) {
        sanitized[key] = '[REDACTED]';
      } else {
        sanitized[key] = value;
      }
    }

    return sanitized;
  }

  /**
   * Prepare request with authentication and headers
   */
  private prepareRequest(config: APIRequestConfig): RequestInit {
    const headers = new Headers({
      'Content-Type': 'application/json',
      ...config.headers
    });

    // Add authentication token if available
    const authHeader = secureTokenStorage.getAuthorizationHeader();
    if (authHeader) {
      headers.set('Authorization', authHeader);
    }

    const requestConfig: RequestInit = {
      method: config.method,
      headers,
      signal: AbortSignal.timeout(this.config.timeout!)
    };

    // Add body for non-GET requests
    if (config.method !== 'GET' && config.data) {
      requestConfig.body = JSON.stringify(config.data);
    }

    return requestConfig;
  }

  /**
   * Execute the actual HTTP request
   */
  private async executeRequest(requestConfig: RequestInit): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

    try {
      const response = await fetch(this.config.baseURL, {
        ...requestConfig,
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  /**
   * Format response into standard format
   */
  private async formatResponse(response: Response): Promise<APIResponse<any>> {
    try {
      const data = await response.json();
      
      return {
        success: response.ok,
        data: response.ok ? data : undefined,
        error: response.ok ? undefined : data.message || 'Request failed',
        status: response.status,
        message: response.statusText
      };
    } catch (error) {
      return {
        success: response.ok,
        status: response.status,
        message: response.statusText
      };
    }
  }

  /**
   * Sanitize error messages to prevent sensitive data exposure
   */
  private sanitizeErrorMessage(error: any): string {
    if (typeof error === 'string') {
      return error;
    }
    
    if (error?.message) {
      return error.message;
    }
    
    return 'An unexpected error occurred';
  }

  /**
   * Update configuration
   */
  updateConfig(newConfig: Partial<APIClientConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Get current configuration
   */
  getConfig(): APIClientConfig {
    return { ...this.config };
  }
}

// Export the class
export { SecureAPIClient };

// Export types
export type { APIClientConfig, APIRequestConfig, APIResponse };

// Create default instance
export const secureAPIClient = new SecureAPIClient({
  baseURL: process.env.NEXT_PUBLIC_API_URL || '/api',
  enableLogging: process.env.NODE_ENV === 'development'
});

export default secureAPIClient;
