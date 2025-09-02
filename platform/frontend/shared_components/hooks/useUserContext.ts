/**
 * User Context Hook
 * =================
 * 
 * Centralized hook for accessing user context, roles, and permissions.
 * Provides consistent user data access across all components and eliminates
 * inconsistencies in user role checking patterns.
 * 
 * Features:
 * - Centralized user data access
 * - Consistent role checking
 * - Type-safe user context
 * - Automatic token refresh
 * - Error handling and fallbacks
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { authService } from '../services/auth';

export interface User {
  id: string;
  email: string;
  role: 'system_integrator' | 'access_point_provider' | 'hybrid_user';
  service_package: 'si' | 'app' | 'hybrid';
  organization_id?: string;
  profile?: {
    first_name?: string;
    last_name?: string;
    company?: string;
    phone?: string;
  };
  permissions?: string[];
  subscription?: {
    plan: string;
    status: string;
    expires_at?: string;
  };
  metadata?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface UserContext {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Role checking functions
  hasRole: (role: string | string[]) => boolean;
  isSystemIntegrator: () => boolean;
  isAccessPointProvider: () => boolean;
  isHybridUser: () => boolean;
  
  // Service package checking
  hasServicePackage: (servicePackage: string | string[]) => boolean;
  
  // Permission checking
  hasPermission: (permission: string | string[]) => boolean;
  
  // Organization context
  organizationId: string | null;
  
  // Utility functions
  getUserDisplayName: () => string;
  getUserInitials: () => string;
  isSubscriptionActive: () => boolean;
  
  // Actions
  refreshUser: () => Promise<void>;
  logout: () => void;
}

export interface UseUserContextOptions {
  autoRefresh?: boolean;
  refreshInterval?: number;
  requireAuth?: boolean;
}

export const useUserContext = (options: UseUserContextOptions = {}): UserContext => {
  const {
    autoRefresh = false,
    refreshInterval = 30000, // 30 seconds
    requireAuth = false
  } = options;

  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load user data from storage/API
  const loadUser = useCallback(async (skipCache: boolean = false) => {
    try {
      setIsLoading(true);
      setError(null);

      // Check if user is authenticated
      const token = authService.getStoredToken();
      if (!token) {
        setUser(null);
        if (requireAuth) {
          setError('Authentication required');
        }
        return;
      }

      // Try to get user from storage first
      let userData: User | null = null;
      if (!skipCache) {
        try {
          userData = authService.getStoredUser() as User;
        } catch (storageError) {
          console.warn('Failed to get user from storage:', storageError);
        }
      }

      // If no cached user or force refresh, fetch from API
      if (!userData || skipCache) {
        try {
          // This would typically make an API call to refresh user data
          // For now, we'll use the stored user data
          userData = authService.getStoredUser() as User;
          
          if (!userData) {
            throw new Error('No user data available');
          }
        } catch (apiError) {
          console.error('Failed to fetch user from API:', apiError);
          setError('Failed to load user data');
          return;
        }
      }

      // Validate user data structure
      if (userData && userData.id && userData.email && userData.role) {
        setUser(userData);
      } else {
        console.error('Invalid user data structure:', userData);
        setError('Invalid user data');
        setUser(null);
      }

    } catch (error) {
      console.error('Error loading user:', error);
      setError(error instanceof Error ? error.message : 'Failed to load user');
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, [requireAuth]);

  // Initial load
  useEffect(() => {
    loadUser();
  }, [loadUser]);

  // Auto refresh user data
  useEffect(() => {
    if (!autoRefresh || !user) return;

    const interval = setInterval(() => {
      loadUser(true);
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, user, loadUser]);

  // Derived state
  const isAuthenticated = useMemo(() => {
    return !!(user && authService.getStoredToken());
  }, [user]);

  const organizationId = useMemo(() => {
    return user?.organization_id || null;
  }, [user]);

  // Role checking functions
  const hasRole = useCallback((role: string | string[]): boolean => {
    if (!user?.role) return false;
    
    const roles = Array.isArray(role) ? role : [role];
    return roles.includes(user.role);
  }, [user]);

  const isSystemIntegrator = useCallback((): boolean => {
    return hasRole('system_integrator');
  }, [hasRole]);

  const isAccessPointProvider = useCallback((): boolean => {
    return hasRole('access_point_provider');
  }, [hasRole]);

  const isHybridUser = useCallback((): boolean => {
    return hasRole('hybrid_user');
  }, [hasRole]);

  // Service package checking
  const hasServicePackage = useCallback((servicePackage: string | string[]): boolean => {
    if (!user?.service_package) return false;
    
    const packages = Array.isArray(servicePackage) ? servicePackage : [servicePackage];
    return packages.includes(user.service_package);
  }, [user]);

  // Permission checking
  const hasPermission = useCallback((permission: string | string[]): boolean => {
    if (!user?.permissions) return false;
    
    const permissions = Array.isArray(permission) ? permission : [permission];
    return permissions.some(p => user.permissions?.includes(p));
  }, [user]);

  // Utility functions
  const getUserDisplayName = useCallback((): string => {
    if (!user) return 'Unknown User';
    
    const { profile } = user;
    if (profile?.first_name && profile?.last_name) {
      return `${profile.first_name} ${profile.last_name}`;
    }
    
    if (profile?.first_name) {
      return profile.first_name;
    }
    
    if (profile?.company) {
      return profile.company;
    }
    
    return user.email.split('@')[0]; // Use email prefix as fallback
  }, [user]);

  const getUserInitials = useCallback((): string => {
    if (!user) return 'U';
    
    const { profile } = user;
    if (profile?.first_name && profile?.last_name) {
      return `${profile.first_name[0]}${profile.last_name[0]}`.toUpperCase();
    }
    
    if (profile?.first_name) {
      return profile.first_name[0].toUpperCase();
    }
    
    if (profile?.company) {
      return profile.company[0].toUpperCase();
    }
    
    return user.email[0].toUpperCase();
  }, [user]);

  const isSubscriptionActive = useCallback((): boolean => {
    if (!user?.subscription) return false;
    
    const { status, expires_at } = user.subscription;
    
    if (status !== 'active') return false;
    
    if (expires_at) {
      const expiryDate = new Date(expires_at);
      return expiryDate > new Date();
    }
    
    return true; // If no expiry date, assume active
  }, [user]);

  // Actions
  const refreshUser = useCallback(async (): Promise<void> => {
    await loadUser(true);
  }, [loadUser]);

  const logout = useCallback((): void => {
    authService.logout();
    setUser(null);
    setError(null);
  }, []);

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    
    // Role checking
    hasRole,
    isSystemIntegrator,
    isAccessPointProvider,
    isHybridUser,
    
    // Service package checking
    hasServicePackage,
    
    // Permission checking
    hasPermission,
    
    // Organization context
    organizationId,
    
    // Utility functions
    getUserDisplayName,
    getUserInitials,
    isSubscriptionActive,
    
    // Actions
    refreshUser,
    logout
  };
};

// Utility functions for common role checks
export const userContextUtils = {
  /**
   * Check if user has any of the specified roles
   */
  hasAnyRole: (user: User | null, roles: string[]): boolean => {
    if (!user?.role) return false;
    return roles.includes(user.role);
  },

  /**
   * Check if user has specific service package
   */
  hasServicePackage: (user: User | null, servicePackage: string | string[]): boolean => {
    if (!user?.service_package) return false;
    const packages = Array.isArray(servicePackage) ? servicePackage : [servicePackage];
    return packages.includes(user.service_package);
  },

  /**
   * Get user display name
   */
  getDisplayName: (user: User | null): string => {
    if (!user) return 'Unknown User';
    
    const { profile } = user;
    if (profile?.first_name && profile?.last_name) {
      return `${profile.first_name} ${profile.last_name}`;
    }
    
    if (profile?.first_name) return profile.first_name;
    if (profile?.company) return profile.company;
    
    return user.email.split('@')[0];
  },

  /**
   * Check if user can access SI features
   */
  canAccessSIFeatures: (user: User | null): boolean => {
    return userContextUtils.hasAnyRole(user, ['system_integrator', 'hybrid_user']);
  },

  /**
   * Check if user can access APP features  
   */
  canAccessAPPFeatures: (user: User | null): boolean => {
    return userContextUtils.hasAnyRole(user, ['access_point_provider', 'hybrid_user']);
  },

  /**
   * Get dashboard URL based on user role
   */
  getDashboardUrl: (user: User | null): string => {
    if (!user?.role) return '/dashboard';
    
    switch (user.role) {
      case 'system_integrator':
        return '/dashboard/si';
      case 'access_point_provider':
        return '/dashboard/app';
      case 'hybrid_user':
        return '/dashboard/hybrid';
      default:
        return '/dashboard';
    }
  }
};

export default useUserContext;
