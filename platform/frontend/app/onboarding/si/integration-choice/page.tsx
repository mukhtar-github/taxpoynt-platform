'use client';

/**
 * SI Integration Choice Page
 * ==========================
 * Enhanced integration choice page with better UX and clearer explanations
 * Part of the improved onboarding flow for System Integration users
 */
import React, { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { authService, type User } from '../../../../shared_components/services/auth';
import { OnboardingStateManager } from '../../../../shared_components/services/onboardingApi';
import { AutosaveStatusChip, type AutosaveStatus } from '../../../../shared_components/onboarding';
import { TaxPoyntButton } from '../../../../design_system';

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
  const [user, setUser] = useState<User | null>(null);
  const [autosaveStatus, setAutosaveStatus] = useState<AutosaveStatus>('idle');
  const [autosaveMessage, setAutosaveMessage] = useState<string | null>(null);
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const [isContinuing, setIsContinuing] = useState(false);

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

  useEffect(() => {
    if (!user) {
      return;
    }

    let cancelled = false;

    const loadExistingSelection = async () => {
      try {
        const state = await OnboardingStateManager.getOnboardingState(user.id);
        if (!state || cancelled) {
          return;
        }

        const previouslySelected = integrationChoices.find((choice) =>
          state.completed_steps?.includes(choice.id)
        );

        if (previouslySelected) {
          setSelectedIntegration(previouslySelected.id);
          if (state.updated_at) {
            setLastSavedAt(new Date(state.updated_at));
            setAutosaveStatus('saved');
          }
        }
      } catch (error) {
        console.error('Failed to load saved integration choice:', error);
      }
    };

    void loadExistingSelection();

    return () => {
      cancelled = true;
    };
  }, [user, integrationChoices]);

  const integrationChoices = useMemo<IntegrationChoice[]>(() => [
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
  ], []);

  const handleIntegrationSelect = async (integrationId: string) => {
    const choice = integrationChoices.find((c) => c.id === integrationId);
    if (!choice) {
      return;
    }

    setSelectedIntegration(integrationId);

    if (!user) {
      return;
    }

    setAutosaveStatus('saving');
    setAutosaveMessage(null);

    try {
      await OnboardingStateManager.updateStep(user.id, integrationId, true);
      setAutosaveStatus('saved');
      setLastSavedAt(new Date());
    } catch (error) {
      console.error('Integration selection failed:', error);
      setAutosaveStatus('error');
      setAutosaveMessage('Unable to save integration choice');
    }
  };

  const handleBack = () => {
    router.push('/onboarding/si/integration-setup');
  };

  const handleContinue = async () => {
    if (!selectedIntegration) {
      setAutosaveStatus('error');
      setAutosaveMessage('Select an integration path to continue');
      return;
    }

    const choice = integrationChoices.find((item) => item.id === selectedIntegration);
    if (!choice) {
      return;
    }

    if (!user) {
      router.push(choice.nextStep);
      return;
    }

    setIsContinuing(true);
    setAutosaveStatus('saving');
    setAutosaveMessage(null);

    try {
      await OnboardingStateManager.updateStep(user.id, selectedIntegration, true);
      setAutosaveStatus('saved');
      setLastSavedAt(new Date());
      router.push(choice.nextStep);
    } catch (error) {
      console.error('Failed to continue onboarding:', error);
      setAutosaveStatus('error');
      setAutosaveMessage('Unable to continue. Try again.');
    } finally {
      setIsContinuing(false);
    }
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
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">
                Phase 1 · Service foundation
              </p>
              <h1 className="mt-2 text-3xl font-bold text-slate-900">Choose your integration path</h1>
              <p className="mt-2 max-w-2xl text-base text-slate-600">
                Decide where to start connecting your systems. You can layer in additional integrations once
                your launch checklist is complete.
              </p>
              <p className="mt-3 text-sm font-medium text-slate-500">
                Next milestone · Configure setup tasks for your selected path
              </p>
            </div>
            <AutosaveStatusChip
              status={autosaveStatus}
              lastSavedAt={lastSavedAt ?? undefined}
              message={autosaveMessage}
              className="self-start"
            />
          </div>
          <div className="mt-4 rounded-lg border border-indigo-100 bg-indigo-50 p-4 text-sm text-indigo-800">
            <span className="mr-2">👋</span>
            <span>
              Welcome, {user.first_name}! Select the stack you want to configure first. You can always return to add more
              systems later.
            </span>
          </div>
        </div>

        <div className="mt-10 grid grid-cols-1 gap-6 lg:grid-cols-3">
          {integrationChoices.map((choice) => {
            const isSelected = selectedIntegration === choice.id;
            return (
              <button
                type="button"
                key={choice.id}
                onClick={() => handleIntegrationSelect(choice.id)}
                className={`relative flex h-full flex-col rounded-2xl border-2 p-6 text-left transition ${
                  isSelected
                    ? 'border-indigo-500 bg-indigo-50 shadow-lg'
                    : 'border-slate-200 bg-white hover:border-indigo-300 hover:shadow-md'
                }`}
              >
                {isSelected && (
                  <span className="absolute right-4 top-4 inline-flex items-center rounded-full bg-indigo-600 px-3 py-1 text-xs font-semibold text-white">
                    Selected
                  </span>
                )}
                <div className="text-5xl">{choice.icon}</div>
                <h3 className="mt-4 text-xl font-semibold text-slate-900">{choice.name}</h3>
                <p className="mt-2 text-sm text-slate-600">{choice.description}</p>
                <div className="mt-4 flex items-center gap-3">
                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${getComplexityColor(choice.complexity)}`}>
                    {choice.complexity} setup
                  </span>
                  <span className="text-xs text-slate-500">⏱ {choice.estimatedTime}</span>
                </div>
                <ul className="mt-4 space-y-2 text-sm text-slate-600">
                  {choice.features.slice(0, 3).map((feature) => (
                    <li key={feature} className="flex items-start gap-2">
                      <span className="text-indigo-500">✓</span>
                      <span>{feature}</span>
                    </li>
                  ))}
                  {choice.features.length > 3 && (
                    <li className="text-xs text-slate-500">+{choice.features.length - 3} more benefits</li>
                  )}
                </ul>
                <span className="mt-auto pt-4 text-sm font-medium text-indigo-600">
                  {isSelected ? 'Ready to continue' : 'Select to preview setup'}
                </span>
              </button>
            );
          })}
        </div>

        <div className="mt-10 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Need help deciding?</h2>
          <p className="mt-2 text-sm text-slate-600">
            Your choice determines the tasks we preload into your checklist. You can expand to other integrations once
            your launch metrics are stable.
          </p>
          <div className="mt-6 grid grid-cols-1 gap-6 text-sm text-slate-600 sm:grid-cols-3">
            <div>
              <div className="text-2xl">🏢</div>
              <h3 className="mt-2 font-medium text-slate-900">Pick Business Systems if you:</h3>
              <ul className="mt-2 space-y-1">
                <li>• Depend on ERP/CRM data for invoicing</li>
                <li>• Need automations tied to operations data</li>
                <li>• Want deep system-to-system mapping</li>
              </ul>
            </div>
            <div>
              <div className="text-2xl">🏦</div>
              <h3 className="mt-2 font-medium text-slate-900">Pick Financial Systems if you:</h3>
              <ul className="mt-2 space-y-1">
                <li>• Want banking and payments live quickly</li>
                <li>• Prefer lightweight transaction-driven flows</li>
                <li>• Need compliance-ready financial data</li>
              </ul>
            </div>
            <div>
              <div className="text-2xl">🚀</div>
              <h3 className="mt-2 font-medium text-slate-900">Pick Complete Integration if you:</h3>
              <ul className="mt-2 space-y-1">
                <li>• Manage multiple data sources today</li>
                <li>• Need unified analytics out of the gate</li>
                <li>• Have a team ready for parallel setup</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="mt-12 flex items-center justify-between border-t border-slate-200 pt-6">
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
            disabled={!selectedIntegration || isContinuing}
            className="bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700"
          >
            {isContinuing ? 'Continuing…' : 'Continue'}
          </TaxPoyntButton>
        </div>
      </div>
    </div>
  );
}
