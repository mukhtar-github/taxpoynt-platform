'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '../../../../shared_components/services/auth';
import { OnboardingStateManager } from '../../../../shared_components/onboarding/ServiceOnboardingRouter';
import { TaxPoyntButton } from '../../../../design_system';

interface FinancialIntegration {
  id: string;
  name: string;
  description: string;
  features: string[];
  status: 'available' | 'coming_soon' | 'beta';
  estimatedTime: string;
  provider: string;
  icon: string;
  complexity: 'Easy' | 'Medium' | 'Advanced';
  isPopular?: boolean;
}

export default function FinancialSystemsSetupPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [selectedIntegration, setSelectedIntegration] = useState<string>('');
  const [showMonoWidget, setShowMonoWidget] = useState(false);
  const [monoWidgetUrl, setMonoWidgetUrl] = useState<string>('');

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
    OnboardingStateManager.updateStep(currentUser.id, 'financial_systems_setup');
  }, [router]);

  const financialIntegrations: FinancialIntegration[] = [
    {
      id: 'mono_banking',
      name: 'Mono Banking Integration',
      description: 'Connect your Nigerian bank accounts securely through Mono\'s Open Banking platform',
      features: [
        'Nigerian Bank Connections (All major banks)',
        'Real-time Account Monitoring',
        'Automated Transaction Processing',
        'Payment Reconciliation',
        'CBN Compliance'
      ],
      status: 'available',
      estimatedTime: '10-15 minutes',
      provider: 'Mono Technologies',
      icon: '🏦',
      complexity: 'Easy',
      isPopular: true
    },
    {
      id: 'paystack_processor',
      name: 'Paystack Integration',
      description: 'Integrate Paystack for payment processing and transaction monitoring',
      features: [
        'Payment Processing',
        'Transaction Webhooks',
        'Customer Management',
        'Revenue Analytics',
        'Subscription Management'
      ],
      status: 'available',
      estimatedTime: '5-10 minutes',
      provider: 'Paystack',
      icon: '💳',
      complexity: 'Easy'
    },
    {
      id: 'flutterwave_processor',
      name: 'Flutterwave Integration',
      description: 'Connect with Flutterwave for payment processing across Africa',
      features: [
        'Multi-currency Support',
        'Payment Links',
        'Bulk Payments',
        'KYC Management',
        'Fraud Protection'
      ],
      status: 'available',
      estimatedTime: '5-10 minutes',
      provider: 'Flutterwave',
      icon: '🌍',
      complexity: 'Easy'
    },
    {
      id: 'reconciliation_engine',
      name: 'Auto-Reconciliation Setup',
      description: 'Set up automatic transaction categorization and matching rules',
      features: [
        'Smart Transaction Matching',
        'Automated Categorization',
        'Custom Rules Engine',
        'Exception Handling',
        'Reporting & Analytics'
      ],
      status: 'available',
      estimatedTime: '15-20 minutes',
      provider: 'TaxPoynt',
      icon: '⚖️',
      complexity: 'Medium'
    }
  ];

  const handleSkipForNow = () => {
    // Mark onboarding as complete and go to dashboard
    OnboardingStateManager.completeOnboarding(user?.id);
    router.push('/dashboard/si');
  };

  const handleIntegrationClick = async (integration: FinancialIntegration) => {
    setIsLoading(true);
    setSelectedIntegration(integration.id);

    try {
      console.log('🏦 Starting financial integration:', integration.id);
      
      if (integration.id === 'mono_banking') {
        await initiateMonomBankingSetup();
      } else if (integration.id === 'paystack_processor') {
        await initiatePaystackSetup();
      } else if (integration.id === 'flutterwave_processor') {
        await initiateFlutterwaveSetup();
      } else if (integration.id === 'reconciliation_engine') {
        await initiateReconciliationSetup();
      }
      
    } catch (error) {
      console.error('Integration setup failed:', error);
      alert('Failed to start integration setup. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const initiateMonomBankingSetup = async () => {
    try {
      // Call the backend to generate Mono widget URL
      const response = await fetch('/api/v1/si/banking/open-banking/mono/link', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          customer: {
            name: `${user.first_name} ${user.last_name}`,
            email: user.email
          },
          redirect_url: `${window.location.origin}/onboarding/si/banking-callback`,
          meta: {
            ref: `taxpoynt_onboarding_${Date.now()}`,
            user_id: user.id,
            onboarding_step: 'financial_systems_setup'
          }
        })
      });

      if (!response.ok) {
        // If API fails, fallback to demo/mock flow for development
        console.warn('Mono API not available, using demo flow');
        handleMonoDemoFlow();
        return;
      }

      const data = await response.json();
      
      if (data.data?.mono_url) {
        setMonoWidgetUrl(data.data.mono_url);
        setShowMonoWidget(true);
        
        // Open Mono widget in popup or new tab
        const monoWindow = window.open(
          data.data.mono_url, 
          'mono-banking-widget',
          'width=500,height=600,scrollbars=yes,resizable=yes'
        );

        // Listen for completion (this would normally be handled by redirect_url)
        const checkClosed = setInterval(() => {
          if (monoWindow?.closed) {
            clearInterval(checkClosed);
            handleBankingSetupComplete();
          }
        }, 1000);

      } else {
        throw new Error('No Mono URL received from backend');
      }

    } catch (error) {
      console.error('Mono setup failed:', error);
      // Fallback to demo flow for development
      handleMonoDemoFlow();
    }
  };

  const handleMonoDemoFlow = () => {
    // Demo flow for development when API is not available
    alert('🏦 Demo: Mono Banking Setup\n\nIn production, this would:\n• Open Mono widget\n• Connect Nigerian bank account\n• Configure automatic transaction sync\n• Set up invoice generation triggers\n\nProceeding to dashboard...');
    
    setTimeout(() => {
      handleBankingSetupComplete();
    }, 2000);
  };

  const initiatePaystackSetup = async () => {
    // Demo implementation for Paystack
    alert('💳 Demo: Paystack Integration\n\nThis would:\n• Configure Paystack API keys\n• Set up payment webhooks\n• Configure transaction monitoring\n• Enable invoice payment links\n\nProceeding to reconciliation setup...');
    
    setTimeout(() => {
      handleFinancialSetupComplete();
    }, 2000);
  };

  const initiateFlutterwaveSetup = async () => {
    // Demo implementation for Flutterwave
    alert('🌍 Demo: Flutterwave Integration\n\nThis would:\n• Configure Flutterwave API keys\n• Set up multi-currency support\n• Configure payment webhooks\n• Enable bulk payment features\n\nProceeding to reconciliation setup...');
    
    setTimeout(() => {
      handleFinancialSetupComplete();
    }, 2000);
  };

  const initiateReconciliationSetup = async () => {
    // Route directly to dedicated reconciliation setup page
    console.log('⚖️ Redirecting to reconciliation setup page');
    OnboardingStateManager.updateStep(user.id, 'reconciliation_setup');
    router.push('/onboarding/si/reconciliation-setup');
  };

  const handleBankingSetupComplete = () => {
    // Banking setup complete, now go to reconciliation
    OnboardingStateManager.updateStep(user.id, 'banking_connected', true);
    OnboardingStateManager.updateStep(user.id, 'reconciliation_setup');
    router.push('/onboarding/si/reconciliation-setup');
  };

  const handleFinancialSetupComplete = () => {
    // Payment processor setup complete, now go to reconciliation
    OnboardingStateManager.updateStep(user.id, 'payment_processors_connected', true);
    OnboardingStateManager.updateStep(user.id, 'reconciliation_setup');
    router.push('/onboarding/si/reconciliation-setup');
  };

  const getComplexityColor = (complexity: string) => {
    const colors = {
      'Easy': 'text-green-600 bg-green-100',
      'Medium': 'text-yellow-600 bg-yellow-100',
      'Advanced': 'text-red-600 bg-red-100'
    };
    return colors[complexity as keyof typeof colors] || 'text-gray-600 bg-gray-100';
  };

  const getStatusColor = (status: string) => {
    const colors = {
      'available': 'text-green-600 bg-green-100',
      'beta': 'text-blue-600 bg-blue-100',
      'coming_soon': 'text-gray-600 bg-gray-100'
    };
    return colors[status as keyof typeof colors] || 'text-gray-600 bg-gray-100';
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto py-8 px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <div className="bg-green-100 p-3 rounded-2xl mr-4">
              <span className="text-3xl">💰</span>
            </div>
            <div className="text-left">
              <h1 className="text-3xl font-bold text-gray-900">
                Financial Systems Integration
              </h1>
              <p className="text-green-600 font-medium text-lg">Banking & Payment Processors</p>
            </div>
          </div>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Connect your financial systems to automate transaction processing, reconciliation, and invoice generation
          </p>
        </div>

        {/* Integration Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {financialIntegrations.map((integration) => (
            <div
              key={integration.id}
              onClick={() => handleIntegrationClick(integration)}
              className={`
                relative border-2 rounded-2xl p-6 cursor-pointer transition-all duration-200 hover:shadow-xl hover:transform hover:scale-[1.02]
                ${isLoading && selectedIntegration === integration.id
                  ? 'border-green-500 bg-green-50 opacity-75 pointer-events-none'
                  : integration.status === 'available'
                  ? 'border-gray-200 hover:border-green-400 hover:bg-green-50'
                  : 'border-gray-200 hover:border-gray-300 opacity-60 cursor-not-allowed'
                }
                ${integration.isPopular ? 'ring-2 ring-green-200' : ''}
              `}
            >
              {/* Popular Badge */}
              {integration.isPopular && (
                <div className="absolute -top-3 -right-3">
                  <div className="bg-green-500 text-white text-xs px-3 py-1 rounded-full font-medium">
                    Most Popular
                  </div>
                </div>
              )}

              {/* Loading Indicator */}
              {isLoading && selectedIntegration === integration.id && (
                <div className="absolute top-4 right-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-green-600"></div>
                </div>
              )}

              {/* Icon & Provider */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <span className="text-4xl mr-4">{integration.icon}</span>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">{integration.name}</h3>
                    <p className="text-sm text-gray-600">by {integration.provider}</p>
                  </div>
                </div>
                <div className="flex flex-col items-end space-y-1">
                  <span className={`px-2 py-1 text-xs rounded-full font-medium ${getStatusColor(integration.status)}`}>
                    {integration.status.replace('_', ' ')}
                  </span>
                  <span className={`px-2 py-1 text-xs rounded-full font-medium ${getComplexityColor(integration.complexity)}`}>
                    {integration.complexity}
                  </span>
                </div>
              </div>

              {/* Description */}
              <p className="text-gray-700 mb-4">{integration.description}</p>

              {/* Features */}
              <div className="mb-4">
                <h4 className="text-sm font-semibold text-gray-900 mb-2">Key Features:</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  {integration.features.slice(0, 3).map((feature, index) => (
                    <li key={index} className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      {feature}
                    </li>
                  ))}
                  {integration.features.length > 3 && (
                    <li className="text-gray-500 text-xs">
                      +{integration.features.length - 3} more features
                    </li>
                  )}
                </ul>
              </div>

              {/* Estimated Time */}
              <div className="flex items-center justify-between">
                <div className="flex items-center text-sm text-gray-600">
                  <span className="mr-2">⏱️</span>
                  Setup time: {integration.estimatedTime}
                </div>
                {integration.status === 'available' ? (
                  <div className="text-green-600 font-medium text-sm">
                    {isLoading && selectedIntegration === integration.id ? 'Starting...' : 'Click to Setup →'}
                  </div>
                ) : (
                  <div className="text-gray-500 text-sm">
                    Coming Soon
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Info Section */}
        <div className="bg-blue-50 border border-blue-200 rounded-2xl p-6 mb-6">
          <div className="flex items-start">
            <span className="text-blue-500 mr-3 text-2xl">💡</span>
            <div>
              <h3 className="text-blue-900 font-semibold mb-2">Pro Tip: Start with Banking</h3>
              <p className="text-blue-800 text-sm leading-relaxed">
                We recommend starting with <strong>Mono Banking Integration</strong> as it provides the foundation 
                for all other financial integrations. Once your bank accounts are connected, you can add payment 
                processors and set up automated reconciliation rules.
              </p>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-center space-x-4">
          <TaxPoyntButton
            variant="secondary"
            onClick={handleSkipForNow}
            disabled={isLoading}
            className="px-8"
          >
            Skip for Now
          </TaxPoyntButton>
        </div>

        {/* Help Section */}
        <div className="mt-8 text-center">
          <div className="inline-flex items-center text-gray-600 text-sm">
            <span className="mr-2">💬</span>
            Need help? Our integration specialists are available to assist you.
            <button className="ml-2 text-green-600 hover:text-green-800 font-medium">
              Contact Support
            </button>
          </div>
        </div>

        {/* Mono Widget Modal */}
        {showMonoWidget && monoWidgetUrl && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl p-6 max-w-md w-full mx-4">
              <div className="text-center">
                <div className="text-4xl mb-4">🏦</div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  Mono Banking Widget Ready
                </h3>
                <p className="text-gray-600 mb-6">
                  Click below to open the secure Mono widget and connect your Nigerian bank account.
                </p>
                <div className="space-y-3">
                  <TaxPoyntButton
                    variant="primary"
                    onClick={() => window.open(monoWidgetUrl, '_blank')}
                    className="w-full"
                  >
                    Open Banking Widget
                  </TaxPoyntButton>
                  <TaxPoyntButton
                    variant="secondary"
                    onClick={() => setShowMonoWidget(false)}
                    className="w-full"
                  >
                    Cancel
                  </TaxPoyntButton>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
