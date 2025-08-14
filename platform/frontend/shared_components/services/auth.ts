/**
 * Authentication Service
 * =====================
 * Connects frontend components to backend authentication API endpoints.
 * Integrates with the TaxPoynt API Gateway at /api/v1/auth/*
 */

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role: string;
  service_package: string;
  is_email_verified: boolean;
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
  business_type: string;
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
  expires_in: number;
  user: User;
}

class AuthService {
  private baseUrl: string;
  private tokenKey = 'taxpoynt_auth_token';
  private userKey = 'taxpoynt_user_data';

  constructor() {
    // Use environment variable or default to backend
    this.baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  }

  async register(userData: RegisterRequest): Promise<AuthResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    const authData: AuthResponse = await response.json();
    this.storeAuthData(authData);
    return authData;
  }

  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const authData: AuthResponse = await response.json();
    this.storeAuthData(authData);
    return authData;
  }

  async logout(): Promise<void> {
    const token = this.getToken();
    if (token) {
      await fetch(`${this.baseUrl}/api/v1/auth/logout`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      }).catch(() => {});
    }
    this.clearAuthData();
  }

  isAuthenticated(): boolean {
    return !!(this.getToken() && this.getStoredUser());
  }

  getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(this.tokenKey);
  }

  getStoredUser(): User | null {
    if (typeof window === 'undefined') return null;
    const userData = localStorage.getItem(this.userKey);
    return userData ? JSON.parse(userData) : null;
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

  private storeAuthData(authData: AuthResponse): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(this.tokenKey, authData.access_token);
    localStorage.setItem(this.userKey, JSON.stringify(authData.user));
  }

  private clearAuthData(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userKey);
  }
}

export const authService = new AuthService();
export type { AuthResponse, RegisterRequest, LoginRequest, User, Organization };