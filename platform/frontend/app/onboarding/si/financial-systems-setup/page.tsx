'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { authService, type User } from '../../../../shared_components/services/auth';
import { OnboardingStateManager } from '../../../../shared_components/services/onboardingApi';
import { TaxPoyntButton } from '../../../../design_system';
import { AutosaveStatusChip, type AutosaveStatus } from '../../../../shared_components/onboarding';
import apiClient from '../../../../shared_components/api/client';

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
  const [user, setUser] = useState<User | null>(null);
  const [selectedIntegration, setSelectedIntegration] = useState<string>('');
  const [showMonoWidget, setShowMonoWidget] = useState(false);
  const [monoWidgetUrl, setMonoWidgetUrl] = useState<string>('');
  const [connectedIntegrations, setConnectedIntegrations] = useState<string[]>([]);
  const [autosaveStatus, setAutosaveStatus] = useState<AutosaveStatus>('idle');
  const [autosaveMessage, setAutosaveMessage] = useState<string | null>(null);
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const [isContinuing, setIsContinuing] = useState(false);

  const persistProgress = useCallback(
    async (step: string, markComplete: boolean = false): Promise<boolean> => {
      if (!user) {
        return false;
      }

      setAutosaveStatus('saving');
      setAutosaveMessage(null);

      try {
        await OnboardingStateManager.updateStep(user.id, step, markComplete);
        setAutosaveStatus('saved');
        setLastSavedAt(new Date());
        return true;
      } catch (error) {
        console.error('Failed to persist onboarding progress:', error);
        setAutosaveStatus('error');
        setAutosaveMessage('Unable to save progress');
        return false;
      }
    },
    [user]
  );

  const markIntegrationConnected = useCallback(
    (integrationId: string) => {
      setConnectedIntegrations((prev) => (prev.includes(integrationId) ? prev : [...prev, integrationId]));
      void persistProgress('financial_systems_setup');
    },
    [persistProgress]
  );

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

  const handleBack = () => {
    router.push('/onboarding/si/integration-choice');
  };

  const handleContinue = async () => {
    if (connectedIntegrations.length === 0) {
      setAutosaveStatus('error');
      setAutosaveMessage('Connect at least one financial integration before continuing');
      return;
    }

    if (!user) {
      router.push('/onboarding/si/reconciliation-setup');
      return;
    }

    setIsContinuing(true);

    try {
      const saved = await persistProgress('financial_systems_complete', true);
      if (saved) {
        router.push('/onboarding/si/reconciliation-setup');
      }
    } finally {
      setIsContinuing(false);
    }
  };

  const initiateMonomBankingSetup = async () => {
    try {
      // Call the backend to generate Mono widget URL
      let monoUrl: string | undefined;
      try {
        const data = await apiClient.post<{
          data?: { mono_url?: string };
        }>('/si/banking/open-banking/mono/link', {
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
        });

        if (data.data?.mono_url) {
          setMonoWidgetUrl(data.data.mono_url);
          setShowMonoWidget(true);
          monoUrl = data.data.mono_url;
        } else {
          console.warn('Mono API response missing widget URL, using demo flow');
          handleMonoDemoFlow();
          return;
        }
      } catch (apiError) {
        console.warn('Mono API not available, using demo flow', apiError);
        handleMonoDemoFlow();
        return;
      }

      if (!monoUrl) {
        throw new Error('No Mono URL received from backend');
      }

      // Open Mono widget in popup or new tab
      const monoWindow = window.open(
        monoUrl,
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
      handleFinancialSetupComplete('paystack_processor');
    }, 2000);
  };

  const initiateFlutterwaveSetup = async () => {
    // Demo implementation for Flutterwave
    alert('🌍 Demo: Flutterwave Integration\n\nThis would:\n• Configure Flutterwave API keys\n• Set up multi-currency support\n• Configure payment webhooks\n• Enable bulk payment features\n\nProceeding to reconciliation setup...');
    
    setTimeout(() => {
      handleFinancialSetupComplete('flutterwave_processor');
    }, 2000);
  };

  const initiateReconciliationSetup = async () => {
    console.log('⚖️ Flagging reconciliation setup for later');
    setSelectedIntegration('reconciliation_engine');
    markIntegrationConnected('reconciliation_engine');
  };

  const handleBankingSetupComplete = () => {
    setSelectedIntegration('mono_banking');
    if (user) {
      OnboardingStateManager.updateStep(user.id, 'banking_connected', true);
    }
    markIntegrationConnected('mono_banking');
    setIsLoading(false);
  };

  const handleFinancialSetupComplete = (integrationId: string) => {
    setSelectedIntegration(integrationId);
    if (user) {
      OnboardingStateManager.updateStep(user.id, 'payment_processors_connected', true);
    }
    markIntegrationConnected(integrationId);
    setIsLoading(false);
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
        <div className="mb-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-600">
                Phase 2 · Financial systems
              </p>
              <h1 className="mt-2 text-3xl font-bold text-slate-900">
                💰 Connect your banking and payments stack
              </h1>
              <p className="mt-2 text-base text-slate-600 max-w-3xl">
                Securely link Nigerian banking platforms and payment processors so TaxPoynt can reconcile transactions
                and trigger invoice automation without manual uploads.
              </p>
              <p className="mt-3 text-sm font-medium text-slate-500">
                Next milestone · Enable reconciliation rules once financial feeds are active
              </p>
            </div>
            <AutosaveStatusChip
              status={autosaveStatus}
              lastSavedAt={lastSavedAt ?? undefined}
              message={autosaveMessage}
              className="self-start"
            />
          </div>
          <div className="mt-4 rounded-lg border border-emerald-100 bg-emerald-50 p-4 text-sm text-emerald-800">
            <span className="mr-2">🔐</span>
            <span>Connections happen through secure provider portals. We autosave your progress after each successful link.</span>
          </div>
        </div>

        {/* Integration Cards */}
        <div className="grid grid-cols-1 gap-6 mb-8 md:grid-cols-2">
          {financialIntegrations.map((integration) => {
            const isConnected = connectedIntegrations.includes(integration.id);
            const isProcessing = isLoading && selectedIntegration === integration.id;
            const isAvailable = integration.status === 'available';
            const isDisabled = !isAvailable || isProcessing;

            return (
              <button
                type="button"
                key={integration.id}
                onClick={() => !isDisabled && handleIntegrationClick(integration)}
                disabled={isDisabled}
                className={`relative flex h-full flex-col rounded-2xl border-2 p-6 text-left transition-all duration-200 ${
                  isConnected
                    ? 'border-emerald-500 bg-emerald-50 shadow-lg'
                    : isProcessing
                    ? 'border-emerald-400 bg-emerald-50 opacity-75'
                    : isAvailable
                    ? 'border-slate-200 bg-white hover:border-emerald-300 hover:bg-emerald-50'
                    : 'border-slate-200 bg-white opacity-60'
                } disabled:cursor-not-allowed disabled:pointer-events-none ${integration.isPopular ? 'ring-2 ring-emerald-200' : ''}`}
              >
                {integration.isPopular && (
                  <span className="absolute -top-3 -right-3 inline-flex items-center rounded-full bg-emerald-500 px-3 py-1 text-xs font-semibold text-white">
                    Most popular
                  </span>
                )}
                {isConnected && (
                  <span className="absolute right-4 top-4 inline-flex items-center rounded-full bg-emerald-600 px-3 py-1 text-xs font-semibold text-white">
                    Connected
                  </span>
                )}
                {isProcessing && (
                  <span className="absolute right-4 top-4 inline-flex items-center gap-2 rounded-full bg-emerald-500 px-3 py-1 text-xs font-semibold text-white">
                    <span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Connecting…
                  </span>
                )}

                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <span className="text-4xl">{integration.icon}</span>
                    <div>
                      <h3 className="text-xl font-bold text-slate-900">{integration.name}</h3>
                      <p className="text-sm text-slate-600">by {integration.provider}</p>
                    </div>
                  </div>
                  <span className={`px-3 py-1 text-xs font-semibold capitalize rounded-full ${getStatusColor(integration.status)}`}>
                    {isAvailable ? 'Available' : integration.status.replace('_', ' ')}
                  </span>
                </div>

                <p className="mt-3 text-sm text-slate-600">{integration.description}</p>

                <ul className="mt-4 space-y-2 text-sm text-slate-600">
                  {integration.features.slice(0, 3).map((feature) => (
                    <li key={feature} className="flex items-center gap-2">
                      <span className="text-emerald-500">✓</span>
                      <span>{feature}</span>
                    </li>
                  ))}
                  {integration.features.length > 3 && (
                    <li className="text-xs text-slate-500">+{integration.features.length - 3} more benefits</li>
                  )}
                </ul>

                <div className="mt-4 flex items-center justify-between text-sm text-slate-600">
                  <span>⏱ {integration.estimatedTime}</span>
                  {isAvailable ? (
                    <span className="font-medium text-emerald-600">
                      {isConnected ? 'Connected' : 'Start setup →'}
                    </span>
                  ) : (
                    <span className="text-slate-500">Coming soon</span>
                  )}
                </div>

                {integration.id === 'mono_banking' && (
                  <div className="mt-4 rounded-xl border border-blue-200 bg-blue-50 p-3 text-sm text-blue-700">
                    🔐 Secure Open Banking flow with bank-level authentication
                  </div>
                )}
              </button>
            );
          })}
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

        <div className="mt-10 flex items-center justify-between border-t border-slate-200 pt-6">
          <TaxPoyntButton
            variant="outline"
            onClick={handleBack}
            className="border-slate-300 text-slate-700 hover:bg-slate-50"
          >
            Back
          </TaxPoyntButton>
          <TaxPoyntButton
            variant="primary"
            onClick={handleContinue}
            disabled={isContinuing || connectedIntegrations.length === 0}
            className="bg-gradient-to-r from-emerald-600 to-blue-600 hover:from-emerald-700 hover:to-blue-700"
          >
            {isContinuing ? 'Continuing…' : 'Continue'}
          </TaxPoyntButton>
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
