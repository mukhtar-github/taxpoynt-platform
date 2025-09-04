'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '../../../shared_components/services/auth';
import { EnhancedAPPInterface } from '../../../app_interface/EnhancedAPPInterface';

export default function APPDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const currentUser = authService.getStoredUser();
    
    if (!currentUser || !authService.isAuthenticated()) {
      router.push('/auth/signin');
      return;
    }

    // Verify user has APP role
    if (currentUser.role !== 'access_point_provider') {
      router.push('/dashboard'); // Redirect to appropriate dashboard
      return;
    }

    setUser(currentUser);
    setIsLoading(false);
  }, [router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <EnhancedAPPInterface 
      userName={`${user.first_name} ${user.last_name}`}
      userEmail={user.email}
    />
  );
}