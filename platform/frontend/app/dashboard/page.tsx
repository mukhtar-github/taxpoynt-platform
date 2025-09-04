'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '../../shared_components/services/auth';
import { Logo } from '../../design_system/components/Logo';

export default function DashboardRedirect() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const redirectToDashboard = () => {
      console.log('🔍 Dashboard: Starting authentication check');
      
      const user = authService.getStoredUser();
      const isAuth = authService.isAuthenticated();
      const token = authService.getToken();
      
      console.log('🔍 Dashboard: Auth state', {
        hasUser: !!user,
        userRole: user?.role,
        isAuthenticated: isAuth,
        hasToken: !!token,
        tokenLength: token?.length || 0
      });
      
      if (!user || !isAuth) {
        console.log('🚨 Dashboard: Not authenticated, redirecting to signin');
        router.push('/auth/signin');
        return;
      }

      // Redirect based on user role
      console.log(`🎯 Dashboard: Redirecting user with role '${user.role}'`);
      
      switch (user.role) {
        case 'system_integrator':
          console.log('➡️ Dashboard: Redirecting to SI dashboard');
          router.push('/dashboard/si');
          break;
        case 'access_point_provider':
          console.log('➡️ Dashboard: Redirecting to APP dashboard');
          router.push('/dashboard/app');
          break;
        case 'hybrid_user':
          console.log('➡️ Dashboard: Redirecting to Hybrid dashboard');
          router.push('/dashboard/hybrid');
          break;
        default:
          console.log(`⚠️ Dashboard: Unknown role '${user.role}', defaulting to APP dashboard`);
          router.push('/dashboard/app');
      }
    };

    // Small delay to ensure localStorage is available
    const timer = setTimeout(() => {
      redirectToDashboard();
      setIsLoading(false);
    }, 100);

    return () => clearTimeout(timer);
  }, [router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="mb-6">
            <Logo size="xl" variant="full" showTagline={true} />
          </div>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 font-body">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return null;
}