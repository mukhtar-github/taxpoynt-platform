'use client';

/**
 * SI Complete Integration Setup Page
 * ==================================
 * Comprehensive setup for both business and financial system integrations
 * Provides a wizard-like experience for advanced users
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useUserContext } from '../../../../shared_components/hooks/useUserContext';
import { OnboardingStateManager } from '../../../../shared_components/services/onboardingApi';
import { onboardingApi } from '../../../../shared_components/services/onboardingApi';
import { TaxPoyntButton } from '../../../../design_system';
import { AutosaveStatusChip, type AutosaveStatus } from '../../../../shared_components/onboarding';

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
  const { user, isAuthenticated, isSystemIntegrator, isLoading } = useUserContext({ requireAuth: true });
  const [wizardStatus, setWizardStatus] = useState<'checking' | 'ready'>('checking');
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
        console.error('Failed to persist integration setup progress:', error);
        setAutosaveStatus('error');
        setAutosaveMessage('Unable to save progress');
        return false;
      }
    },
    [user]
  );

  useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated) {
      router.push('/auth/signin');
      return;
    }

    if (!isSystemIntegrator()) {
      router.push('/dashboard');
      return;
    }

    const verifyPrerequisites = async () => {
      try {
        setWizardStatus('checking');
        const state = await onboardingApi.getOnboardingState();
        const prerequisitesMet =
          Boolean(state?.has_started) &&
          (
            Boolean(state?.is_complete) ||
            Boolean(
              state?.current_step &&
                [
                  'business_systems_setup',
                  'financial_systems_setup',
                  'complete_integration_setup',
                  'reconciliation_setup',
                  'launch_ready',
                  'launch',
                  'onboarding_complete',
                ].includes(state.current_step)
            ) ||
            Boolean(
              state?.completed_steps?.some((step) =>
                [
                  'business_systems_setup',
                  'financial_systems_setup',
                  'complete_integration_setup',
                  'reconciliation_setup',
                  'launch_ready',
                  'launch',
                  'onboarding_complete',
                ].includes(step)
              )
            )
          );

        if (!prerequisitesMet) {
          router.replace('/onboarding/si/integration-setup');
          return;
        }

        if (user) {
          OnboardingStateManager.updateStep(user.id, 'complete_integration_setup');
        }
        setWizardStatus('ready');
      } catch (error) {
        console.error('Failed to verify onboarding prerequisites:', error);
        router.replace('/onboarding/si/integration-setup');
      }
    };

    verifyPrerequisites();
  }, [isLoading, isAuthenticated, isSystemIntegrator, user, router]);

  const handleStepAction = async (step: SetupStep) => {
    try {
      console.log('🚀 Starting step:', step.id);

      setSetupSteps((prev) =>
        prev.map((s) => (s.id === step.id ? { ...s, status: 'in_progress' } : s))
      );

      const saved = await persistProgress(step.id);
      if (saved) {
        router.push(step.route);
      }
    } catch (error) {
      console.error('Step navigation failed:', error);
    }
  };

  const handleBack = () => {
    router.push('/onboarding/si/integration-choice');
  };

  const handleContinue = async () => {
    const nextStep = setupSteps.find((step) => step.status !== 'completed');

    if (nextStep) {
      setIsContinuing(true);
      try {
        await handleStepAction(nextStep);
      } finally {
        setIsContinuing(false);
      }
      return;
    }

    if (!user) {
      router.push('/onboarding/si/reconciliation-setup');
      return;
    }

    setIsContinuing(true);
    try {
      const saved = await persistProgress('complete_integration_setup', true);
      if (saved) {
        router.push('/onboarding/si/reconciliation-setup');
      }
    } finally {
      setIsContinuing(false);
    }
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

  if (!user || wizardStatus === 'checking') {
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
        <div className="mb-10">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">
                Phase 2 · Hybrid rollout
              </p>
              <h1 className="mt-2 text-3xl font-bold text-slate-900">
                Coordinate your complete integration setup 🚀
              </h1>
              <p className="mt-2 text-base text-slate-600 max-w-3xl">
                Work through the combined business and financial tasks so launch-day automations stay in sync across systems.
              </p>
              <p className="mt-3 text-sm font-medium text-slate-500">
                Next milestone · Finish reconciliation readiness after linking both data sources
              </p>
            </div>
            <AutosaveStatusChip
              status={autosaveStatus}
              lastSavedAt={lastSavedAt ?? undefined}
              message={autosaveMessage}
              className="self-start"
            />
          </div>

          <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            <span className="mr-2">⭐</span>
            <span>Knock out these coordinated steps to unlock cross-system automations and monitoring.</span>
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
                      variant="outline"
                      onClick={() => handleStepAction(step)}
                      disabled={isLoading}
                      className="px-6 border-indigo-200 text-indigo-700 hover:bg-indigo-50"
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
        {/* Help Section */}
        <div className="mt-12 bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">
            What You&apos;ll Accomplish 💪
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
            disabled={isContinuing}
            className="bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700"
          >
            {isContinuing ? 'Continuing…' : 'Continue'}
          </TaxPoyntButton>
        </div>
      </div>
    </div>
  );
}
