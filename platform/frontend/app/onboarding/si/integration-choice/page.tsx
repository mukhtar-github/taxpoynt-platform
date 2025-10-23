'use client';

/**
 * SI Integration Choice Page
 * ==========================
 * Enhanced integration choice page with better UX and clearer explanations
 * Part of the improved onboarding flow for System Integration users
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService, type User } from '../../../../shared_components/services/auth';
import { OnboardingStateManager } from '../../../../shared_components/services/onboardingApi';
import { SkipWithTimeButton } from '../../../../shared_components/onboarding';

interface IntegrationChoice {
  id: string;
  name: string;
  description: string;
  detailedDescription: string;
  features: string[];
  estimatedTime: string;
  complexity: 'Easy' | 'Medium' | 'Advanced';
  icon: string;
  nextStep: string;
}

export default function SIIntegrationChoicePage() {
  const router = useRouter();
  const [selectedIntegration, setSelectedIntegration] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [user, setUser] = useState<User | null>(null);

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
    OnboardingStateManager.updateStep(currentUser.id, 'integration_choice');
  }, [router]);

  const integrationChoices: IntegrationChoice[] = [
    {
      id: 'business_systems',
      name: 'Business Systems Integration',
      description: 'Connect your ERP, CRM, POS, and other business systems',
      detailedDescription: 'Integrate with popular business systems like SAP, Oracle, Microsoft Dynamics, Salesforce, QuickBooks, and more. Perfect for businesses wanting to automate invoice generation from existing business data.',
      features: [
        'ERP System Connections (SAP, Oracle, Dynamics)',
        'CRM Integration (Salesforce, HubSpot)',
        'POS System Integration',
        'Automated Data Mapping',
        'Real-time Invoice Generation',
        'Custom API Connections'
      ],
      estimatedTime: '30-60 minutes',
      complexity: 'Medium',
      icon: '🏢',
      nextStep: '/onboarding/si/business-systems-setup'
    },
    {
      id: 'financial_systems',
      name: 'Financial Systems Integration',
      description: 'Connect to banking and financial systems for automated processing',
      detailedDescription: 'Connect to Nigerian banks and financial platforms using Open Banking APIs. Automatically generate invoices from banking transactions and maintain real-time financial data synchronization.',
      features: [
        'Nigerian Bank Connections (via Mono)',
        'Automated Transaction Processing',
        'Real-time Account Monitoring',
        'Payment Reconciliation',
        'Financial Data Analytics',
        'CBN Compliance Monitoring'
      ],
      estimatedTime: '15-30 minutes',
      complexity: 'Easy',
      icon: '🏦',
      nextStep: '/onboarding/si/financial-systems-setup'
    },
    {
      id: 'both_systems',
      name: 'Complete Integration',
      description: 'Set up both business and financial system integrations',
      detailedDescription: 'The comprehensive solution that connects both your business systems and financial systems for complete automation. Ideal for businesses wanting full invoice automation from multiple data sources.',
      features: [
        'All Business System Features',
        'All Financial System Features',
        'Cross-system Data Correlation',
        'Advanced Analytics & Reporting',
        'Complete Automation Workflow',
        'Priority Support'
      ],
      estimatedTime: '60-90 minutes',
      complexity: 'Advanced',
      icon: '🚀',
      nextStep: '/onboarding/si/complete-integration-setup'
    }
  ];

  const handleIntegrationSelect = async (integrationId: string) => {
    const choice = integrationChoices.find(c => c.id === integrationId);
    if (!choice) return;
    if (!user) return;

    setIsLoading(true);
    setSelectedIntegration(integrationId);
    
    try {
      console.log('📊 SI user selected integration:', integrationId);
      
      // Save integration choice to user profile/onboarding state
      OnboardingStateManager.updateStep(user.id, integrationId, true);
      
      // Route immediately to appropriate setup flow
      router.push(choice.nextStep);
      
    } catch (error) {
      console.error('Integration selection failed:', error);
      setIsLoading(false);
    }
  };

  const handleSkipForNow = () => {
    // Mark onboarding as complete and go to dashboard
    OnboardingStateManager.completeOnboarding(user?.id);
    router.push('/dashboard/si');
  };

  const getComplexityColor = (complexity: string) => {
    const colors = {
      'Easy': 'text-green-600 bg-green-100',
      'Medium': 'text-yellow-600 bg-yellow-100',
      'Advanced': 'text-red-600 bg-red-100'
    };
    return colors[complexity as keyof typeof colors] || 'text-gray-600 bg-gray-100';
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
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Choose Your Integration Path 🛤️
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Select how you&apos;d like to connect your systems to TaxPoynt. 
            You can always add more integrations later.
          </p>
          
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 mt-6 max-w-2xl mx-auto">
            <div className="flex items-center justify-center text-indigo-800 text-sm">
              <span className="mr-2">👋</span>
              <span>Welcome, {user.first_name}! Let&apos;s set up your <strong>System Integration</strong> workspace.</span>
            </div>
          </div>
        </div>

        {/* Integration Options */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
          {integrationChoices.map((choice) => (
            <div
              key={choice.id}
              onClick={() => handleIntegrationSelect(choice.id)}
              className={`relative border-2 rounded-2xl p-6 cursor-pointer transition-all duration-200 hover:border-indigo-400 hover:shadow-xl hover:transform hover:scale-105 ${
                isLoading && selectedIntegration === choice.id
                  ? 'border-indigo-500 bg-indigo-50 opacity-75 pointer-events-none'
                  : 'border-gray-200 hover:bg-gray-50'
              }`}
            >
              {/* Loading Indicator */}
              {isLoading && selectedIntegration === choice.id && (
                <div className="absolute -top-3 -right-3">
                  <div className="bg-indigo-500 text-white rounded-full w-8 h-8 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  </div>
                </div>
              )}

              <div className="text-center mb-4">
                <div className="text-5xl mb-3">{choice.icon}</div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">{choice.name}</h3>
                <p className="text-gray-600 text-sm">{choice.description}</p>
              </div>

              {/* Complexity Badge */}
              <div className="flex justify-center mb-4">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getComplexityColor(choice.complexity)}`}>
                  {choice.complexity} Setup
                </span>
              </div>

              {/* Features */}
              <div className="space-y-2 mb-4">
                {choice.features.slice(0, 3).map((feature, index) => (
                  <div key={index} className="flex items-center text-sm text-gray-600">
                    <span className="text-indigo-500 mr-2">✓</span>
                    {feature}
                  </div>
                ))}
                {choice.features.length > 3 && (
                  <div className="text-xs text-gray-500 text-center">
                    +{choice.features.length - 3} more features
                  </div>
                )}
              </div>

              {/* Time Estimate */}
              <div className="text-center">
                <div className="text-xs text-gray-500">
                  ⏱️ Estimated setup time: {choice.estimatedTime}
                </div>
              </div>

              {/* Click to continue indicator */}
              <div className="mt-4 text-center">
                <div className="inline-flex items-center text-sm text-indigo-600 font-medium">
                  <span>Click to start setup</span>
                  <span className="ml-1">→</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Action Buttons */}
        <div className="flex justify-center">
          <SkipWithTimeButton
            onClick={handleSkipForNow}
            disabled={isLoading}
            text="Skip Setup for Now"
            estimatedTime="15-20 minutes"
            analyticsEvent="si_integration_choice_skipped"
          />
        </div>
        
        {/* Instruction Text */}
        <div className="text-center mt-6">
          <p className="text-gray-600 text-sm">
            💡 <strong>Tip:</strong> Click on any integration card above to start the setup process immediately
          </p>
        </div>

        {/* Help Section */}
        <div className="mt-12 bg-white rounded-xl border border-gray-200 p-6 max-w-4xl mx-auto">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">
            Need Help Deciding? 🤔
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
            <div className="text-center">
              <div className="text-2xl mb-2">🏢</div>
              <h4 className="font-medium text-gray-900 mb-1">Choose Business Systems If:</h4>
              <ul className="text-gray-600 space-y-1">
                <li>• You use ERP/CRM systems</li>
                <li>• You want automated invoicing</li>
                <li>• You have structured business data</li>
              </ul>
            </div>
            <div className="text-center">
              <div className="text-2xl mb-2">🏦</div>
              <h4 className="font-medium text-gray-900 mb-1">Choose Financial Systems If:</h4>
              <ul className="text-gray-600 space-y-1">
                <li>• You want banking integration</li>
                <li>• You need transaction-based invoices</li>
                <li>• You prefer simple setup</li>
              </ul>
            </div>
            <div className="text-center">
              <div className="text-2xl mb-2">🚀</div>
              <h4 className="font-medium text-gray-900 mb-1">Choose Complete Integration If:</h4>
              <ul className="text-gray-600 space-y-1">
                <li>• You want maximum automation</li>
                <li>• You use multiple systems</li>
                <li>• You want comprehensive setup</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
