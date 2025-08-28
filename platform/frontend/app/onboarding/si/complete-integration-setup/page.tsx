/**
 * SI Complete Integration Setup Page
 * ==================================
 * Comprehensive setup for both business and financial system integrations
 * Provides a wizard-like experience for advanced users
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '../../../../shared_components/services/auth';
import { OnboardingStateManager } from '../../../../shared_components/onboarding/ServiceOnboardingRouter';
import { TaxPoyntButton } from '../../../../design_system';

interface SetupStep {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed';
  nextAction: string;
  route: string;
}

export default function CompleteIntegrationSetupPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [setupSteps, setSetupSteps] = useState<SetupStep[]>([
    {
      id: 'business_systems',
      title: 'Business Systems Integration',
      description: 'Connect your ERP, CRM, POS systems for automated data collection',
      status: 'pending',
      nextAction: 'Start Business Setup',
      route: '/onboarding/si/business-systems-setup'
    },
    {
      id: 'financial_systems',
      title: 'Financial Systems Integration',
      description: 'Link your banking and financial platforms via secure APIs',
      status: 'pending',
      nextAction: 'Start Financial Setup',
      route: '/onboarding/si/financial-systems-setup'
    },
    {
      id: 'integration_testing',
      title: 'Test Integrations',
      description: 'Verify all connections are working correctly',
      status: 'pending',
      nextAction: 'Run Tests',
      route: '/onboarding/si/integration-testing'
    },
    {
      id: 'dashboard_setup',
      title: 'Dashboard Configuration',
      description: 'Customize your SI dashboard and reporting preferences',
      status: 'pending',
      nextAction: 'Configure Dashboard',
      route: '/dashboard/si/setup'
    }
  ]);

  useEffect(() => {
    const currentUser = authService.getStoredUser();
    if (!currentUser || !authService.isAuthenticated()) {
      router.push('/auth/signin');
      return;
    }

    if (currentUser.role !== 'system_integrator') {
      router.push('/dashboard');
      return;
    }

    setUser(currentUser);
    
    // Update onboarding state
    OnboardingStateManager.updateStep(currentUser.id, 'complete_integration_setup');
  }, [router]);

  const handleStepAction = async (step: SetupStep) => {
    setIsLoading(true);
    
    try {
      console.log('🚀 Starting step:', step.id);
      
      // Update step status to in_progress
      setSetupSteps(prev => prev.map(s => 
        s.id === step.id ? { ...s, status: 'in_progress' } : s
      ));
      
      // Save progress
      OnboardingStateManager.updateStep(user.id, step.id, true);
      
      // Navigate to step
      router.push(step.route);
      
    } catch (error) {
      console.error('Step navigation failed:', error);
      setIsLoading(false);
    }
  };

  const handleSkipForNow = () => {
    // Mark onboarding as complete and go to dashboard
    OnboardingStateManager.completeOnboarding(user?.id);
    router.push('/dashboard/si');
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return '✅';
      case 'in_progress':
        return '🔄';
      default:
        return '⏳';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'in_progress':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-blue-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Complete Integration Setup 🚀
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Let's set up comprehensive integrations for your business. 
            We'll guide you through each step to ensure everything works perfectly.
          </p>
          
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mt-6 max-w-2xl mx-auto">
            <div className="flex items-center justify-center text-amber-800 text-sm">
              <span className="mr-2">⭐</span>
              <span>Welcome to the <strong>Complete Integration</strong> experience! This comprehensive setup will unlock maximum automation.</span>
            </div>
          </div>
        </div>

        {/* Progress Overview */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Setup Progress</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {setupSteps.map((step, index) => (
              <div key={step.id} className="text-center">
                <div className={`w-12 h-12 rounded-full border-2 flex items-center justify-center mx-auto mb-2 ${getStatusColor(step.status)}`}>
                  <span className="text-lg">{getStatusIcon(step.status)}</span>
                </div>
                <div className="text-xs font-medium text-gray-900">{step.title}</div>
                <div className="text-xs text-gray-500 mt-1">Step {index + 1}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Setup Steps */}
        <div className="space-y-6 mb-12">
          {setupSteps.map((step, index) => (
            <div
              key={step.id}
              className={`bg-white rounded-xl border-2 p-6 transition-all duration-200 ${getStatusColor(step.status)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <span className="text-2xl mr-3">{getStatusIcon(step.status)}</span>
                    <h3 className="text-xl font-bold text-gray-900">
                      Step {index + 1}: {step.title}
                    </h3>
                  </div>
                  <p className="text-gray-600 mb-4">{step.description}</p>
                  
                  {step.status === 'pending' && (
                    <TaxPoyntButton
                      variant="primary"
                      onClick={() => handleStepAction(step)}
                      loading={isLoading}
                      disabled={isLoading}
                      className="px-6"
                    >
                      {step.nextAction}
                    </TaxPoyntButton>
                  )}
                  
                  {step.status === 'in_progress' && (
                    <div className="flex items-center text-blue-600">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                      <span className="text-sm font-medium">In Progress...</span>
                    </div>
                  )}
                  
                  {step.status === 'completed' && (
                    <div className="flex items-center text-green-600">
                      <span className="text-sm font-medium">✅ Completed</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row justify-center gap-4 max-w-lg mx-auto">
          <TaxPoyntButton
            variant="secondary"
            onClick={handleSkipForNow}
            disabled={isLoading}
            className="flex-1"
          >
            Skip to Dashboard
          </TaxPoyntButton>
        </div>

        {/* Help Section */}
        <div className="mt-12 bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">
            What You'll Accomplish 💪
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">🏢 Business Systems</h4>
              <ul className="text-gray-600 space-y-1">
                <li>• Connect ERP, CRM, and POS systems</li>
                <li>• Automate invoice generation</li>
                <li>• Set up data mapping and validation</li>
                <li>• Configure business rules</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">🏦 Financial Systems</h4>
              <ul className="text-gray-600 space-y-1">
                <li>• Link Nigerian bank accounts</li>
                <li>• Set up transaction monitoring</li>
                <li>• Configure payment reconciliation</li>
                <li>• Enable real-time financial data</li>
              </ul>
            </div>
          </div>
          <div className="mt-6 text-center">
            <p className="text-gray-600 text-sm">
              🕒 <strong>Estimated total time:</strong> 60-90 minutes for complete setup
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
