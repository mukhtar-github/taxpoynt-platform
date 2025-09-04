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
      const user = authService.getStoredUser();
      
      if (!user || !authService.isAuthenticated()) {
        router.push('/auth/signin');
        return;
      }

      // Redirect based on user role
      switch (user.role) {
        case 'system_integrator':
          router.push('/dashboard/si');
          break;
        case 'access_point_provider':
          router.push('/dashboard/app');
          break;
        case 'hybrid_user':
          router.push('/dashboard/hybrid');
          break;
        default:
          // Default to APP dashboard for unknown roles
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