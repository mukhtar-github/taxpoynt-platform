/**
 * Secure Token Storage Utility
 * ============================
 * Implements secure patterns for storing and retrieving authentication tokens
 * Prevents token exposure and implements proper security measures
 */

interface TokenStorageOptions {
  encryptTokens?: boolean;
  useHttpOnly?: boolean;
  expirationCheck?: boolean;
  autoRefresh?: boolean;
  persistAcrossSessions?: boolean;
}

interface StoredToken {
  value: string;
  expiresAt: number;
  refreshToken?: string;
  scope?: string[];
  persistAcrossSessions?: boolean;
}

class SecureTokenStorage {
  private static instance: SecureTokenStorage;
  private readonly STORAGE_KEY = 'taxpoynt_secure_tokens';
  private readonly REFRESH_THRESHOLD = 5 * 60 * 1000; // 5 minutes before expiry

  private constructor() {}

  static getInstance(): SecureTokenStorage {
    if (!SecureTokenStorage.instance) {
      SecureTokenStorage.instance = new SecureTokenStorage();
    }
    return SecureTokenStorage.instance;
  }

  /**
   * Store authentication token securely
   */
  storeToken(token: string, options: TokenStorageOptions = {}): void {
    try {
      if (typeof window === 'undefined') {
        throw new Error('Token storage is only available in the browser');
      }

      const persistAcrossSessions = Boolean(options.persistAcrossSessions);
      const tokenData: StoredToken = {
        value: this.encryptToken(token),
        expiresAt: this.calculateExpiration(),
        scope: this.extractTokenScope(token),
        persistAcrossSessions
      };

      // Store in sessionStorage for better security (cleared on tab close)
      sessionStorage.setItem(this.STORAGE_KEY, JSON.stringify(tokenData));

      if (persistAcrossSessions) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(tokenData));
      } else {
        localStorage.removeItem(this.STORAGE_KEY);
      }
      
      // Set up auto-refresh if enabled
      if (options.autoRefresh) {
        this.setupTokenRefresh(tokenData);
      }
    } catch (error) {
      console.error('Failed to store token securely:', error);
      throw new Error('Token storage failed');
    }
  }

  /**
   * Retrieve authentication token
   */
  getToken(): string | null {
    try {
      if (typeof window === 'undefined') {
        return null;
      }

      let stored = sessionStorage.getItem(this.STORAGE_KEY);
      if (!stored) {
        stored = localStorage.getItem(this.STORAGE_KEY);
        if (!stored) {
          return null;
        }
        // Rehydrate sessionStorage for faster subsequent lookups
        sessionStorage.setItem(this.STORAGE_KEY, stored);
      }

      const tokenData: StoredToken = JSON.parse(stored);
      
      // Check if token is expired
      if (this.isTokenExpired(tokenData)) {
        this.clearToken();
        return null;
      }

      // Check if token needs refresh
      if (this.shouldRefreshToken(tokenData)) {
        this.triggerTokenRefresh(tokenData);
      }

      return this.decryptToken(tokenData.value);
    } catch (error) {
      console.error('Failed to retrieve token:', error);
      this.clearToken();
      return null;
    }
  }

  /**
   * Clear stored token
   */
  clearToken(): void {
    try {
      if (typeof window === 'undefined') {
        return;
      }
      sessionStorage.removeItem(this.STORAGE_KEY);
      // Clear any related data
      sessionStorage.removeItem('taxpoynt_auth_token');
      localStorage.removeItem('taxpoynt_auth_token');
      localStorage.removeItem(this.STORAGE_KEY);
    } catch (error) {
      console.error('Failed to clear token:', error);
    }
  }

  /**
   * Check if token is valid
   */
  isTokenValid(): boolean {
    const token = this.getToken();
    return token !== null && token.length > 0;
  }

  /**
   * Get token expiration time
   */
  getTokenExpiration(): Date | null {
    try {
      const stored = sessionStorage.getItem(this.STORAGE_KEY);
      if (!stored) return null;

      const tokenData: StoredToken = JSON.parse(stored);
      return new Date(tokenData.expiresAt);
    } catch (error) {
      return null;
    }
  }

  /**
   * Check if token is expired
   */
  private isTokenExpired(tokenData: StoredToken): boolean {
    return Date.now() > tokenData.expiresAt;
  }

  /**
   * Check if token should be refreshed
   */
  private shouldRefreshToken(tokenData: StoredToken): boolean {
    return Date.now() > (tokenData.expiresAt - this.REFRESH_THRESHOLD);
  }

  /**
   * Calculate token expiration time (default: 1 hour)
   */
  private calculateExpiration(): number {
    return Date.now() + (60 * 60 * 1000); // 1 hour
  }

  /**
   * Extract token scope (placeholder implementation)
   */
  private extractTokenScope(token: string): string[] {
    // TODO: Implement JWT scope extraction
    return ['read', 'write'];
  }

  /**
   * Encrypt token (placeholder implementation)
   */
  private encryptToken(token: string): string {
    // TODO: Implement actual encryption
    // For now, use simple obfuscation
    return btoa(token + '_secured');
  }

  /**
   * Decrypt token (placeholder implementation)
   */
  private decryptToken(encryptedToken: string): string {
    // TODO: Implement actual decryption
    // For now, reverse simple obfuscation
    try {
      const decoded = atob(encryptedToken);
      return decoded.replace('_secured', '');
    } catch (error) {
      return encryptedToken; // Fallback
    }
  }

  /**
   * Set up automatic token refresh
   */
  private setupTokenRefresh(tokenData: StoredToken): void {
    const timeUntilRefresh = tokenData.expiresAt - Date.now() - this.REFRESH_THRESHOLD;
    
    if (timeUntilRefresh > 0) {
      setTimeout(() => {
        this.triggerTokenRefresh(tokenData);
      }, timeUntilRefresh);
    }
  }

  /**
   * Trigger token refresh
   */
  private triggerTokenRefresh(tokenData: StoredToken): void {
    // TODO: Implement actual token refresh logic
    console.log('Token refresh triggered');
  }

  /**
   * Get authorization header for API calls
   */
  getAuthorizationHeader(): string | null {
    const token = this.getToken();
    return token ? `Bearer ${token}` : null;
  }

  /**
   * Validate token format
   */
  validateTokenFormat(token: string): boolean {
    // Basic JWT format validation
    const jwtPattern = /^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]*$/;
    return jwtPattern.test(token);
  }
}

// Export singleton instance
export const secureTokenStorage = SecureTokenStorage.getInstance();

// Export types
export type { TokenStorageOptions, StoredToken };

// Export utility functions
export const {
  storeToken,
  getToken,
  clearToken,
  isTokenValid,
  getTokenExpiration,
  getAuthorizationHeader,
  validateTokenFormat
} = secureTokenStorage;

export default secureTokenStorage;
