'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService, type User } from '../../../../shared_components/services/auth';
import { DashboardLayout } from '../../../../shared_components/layouts/DashboardLayout';
import { TaxPoyntButton } from '../../../../design_system';
import { onboardingApi } from '../../../../shared_components/services/onboardingApi';

interface WizardProgress {
  current_step: string;
  completed_steps: string[];
  is_complete: boolean;
  has_started: boolean;
}

export default function SISSetupPage(): JSX.Element | null {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [progress, setProgress] = useState<WizardProgress | null>(null);
  const [progressStatus, setProgressStatus] = useState<'idle' | 'loading' | 'error'>('idle');

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
    setIsLoading(false);
  }, [router]);

  useEffect(() => {
    const fetchProgress = async () => {
      setProgressStatus('loading');
      try {
        const response = await onboardingApi.getOnboardingState();
        if (response) {
          setProgress({
            current_step: response.current_step,
            completed_steps: response.completed_steps,
            is_complete: response.is_complete,
            has_started: response.has_started,
          });
        }
        setProgressStatus('idle');
      } catch (error) {
        console.error('Unable to load onboarding progress', error);
        setProgressStatus('error');
      }
    };

    fetchProgress();
  }, []);

  const navigateTo = (path: string) => () => router.push(path);

  const renderProgressBadge = () => {
    if (progressStatus === 'loading') {
      return <span className="text-xs font-medium text-slate-500">Loading onboarding status…</span>;
    }

    if (!progress) {
      return <span className="text-xs font-medium text-red-500">Onboarding state unavailable</span>;
    }

    if (progress.is_complete) {
      return <span className="rounded-full bg-emerald-100 px-2 py-1 text-xs font-semibold text-emerald-700">Complete</span>;
    }

    const completedCount = progress.completed_steps.length;
    return (
      <span className="rounded-full bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-700">
        {completedCount} steps complete · next: {progress.current_step || 'service-selection'}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <DashboardLayout
      role="si"
      userName={`${user.first_name} ${user.last_name}`}
      userEmail={user.email}
      activeTab="dashboard"
    >
      <div className="space-y-10">
        <header className="rounded-3xl border border-indigo-100 bg-white/70 p-6 shadow-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-indigo-800">System Integrator Setup</h1>
              <p className="mt-1 text-sm text-slate-600">
                Finish onboarding steps, connect Odoo, and enable automated FIRS submissions from a single workspace.
              </p>
            </div>
            {renderProgressBadge()}
          </div>
        </header>

        <section className="grid gap-6 lg:grid-cols-3">
          <div className="rounded-2xl border border-indigo-100 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-indigo-900">1 · Review onboarding wizard</h2>
              <span className="text-sm font-semibold text-indigo-500">Guided</span>
            </div>
            <p className="mt-3 text-sm text-slate-600">
              Update your organization profile, compliance information, and service preferences. The wizard keeps your
              workspace aligned with FIRS requirements.
            </p>
            <div className="mt-4 space-x-3">
              <TaxPoyntButton variant="outline" onClick={navigateTo('/onboarding/si/integration-setup')}>
                Continue wizard
              </TaxPoyntButton>
              <TaxPoyntButton variant="outline" onClick={navigateTo('/onboarding/si/complete-integration-setup')}>
                Resume mapping
              </TaxPoyntButton>
            </div>
          </div>

          <div className="rounded-2xl border border-indigo-100 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-indigo-900">2 · Connect business systems</h2>
              <span className="text-sm font-semibold text-indigo-500">Integrations</span>
            </div>
            <p className="mt-3 text-sm text-slate-600">
              Register your Odoo workspace or any supported ERP/CRM/POS system. Once connected, TaxPoynt can pull data
              for invoice validation and reconciliation.
            </p>
            <div className="mt-4 space-x-3">
              <TaxPoyntButton onClick={navigateTo('/dashboard/si/integrations/new')}>
                Connect Odoo RPC
              </TaxPoyntButton>
              <TaxPoyntButton variant="outline" onClick={navigateTo('/dashboard/si/business-systems')}>
                Manage systems
              </TaxPoyntButton>
            </div>
          </div>

          <div className="rounded-2xl border border-indigo-100 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-indigo-900">3 · Validate FIRS pipeline</h2>
              <span className="text-sm font-semibold text-indigo-500">Compliance</span>
            </div>
            <p className="mt-3 text-sm text-slate-600">
              Test invoice extraction from your ERP, review field mapping, and run a sandbox submission before going
              live with production transmissions.
            </p>
            <div className="mt-4 space-x-3">
              <TaxPoyntButton variant="outline" onClick={navigateTo('/dashboard/si/firs-invoicing')}>
                Generate sandbox batch
              </TaxPoyntButton>
              <TaxPoyntButton variant="outline" onClick={navigateTo('/dashboard/si/financial')}>
                Connect banking data
              </TaxPoyntButton>
            </div>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-base font-semibold text-slate-900">Helpful resources</h3>
            <ul className="mt-3 space-y-2 text-sm text-slate-600">
              <li>
                <a className="text-indigo-600 hover:underline" href="https://docs.taxpoynt.com/integrations/erp/odoo" target="_blank" rel="noopener noreferrer">
                  Odoo RPC integration checklist
                </a>
              </li>
              <li>
                <a className="text-indigo-600 hover:underline" href="https://docs.taxpoynt.com/firs/sandbox" target="_blank" rel="noopener noreferrer">
                  FIRS sandbox submission guide
                </a>
              </li>
              <li>
                <a className="text-indigo-600 hover:underline" href="https://docs.taxpoynt.com/security/ip-allowlist" target="_blank" rel="noopener noreferrer">
                  TaxPoynt IP allowlist for on-premise instances
                </a>
              </li>
            </ul>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-base font-semibold text-slate-900">Need assistance?</h3>
            <p className="mt-3 text-sm text-slate-600">
              Our integration success team can help you deploy connectors, migrate invoice templates, and configure
              reconciliation rules.
            </p>
            <div className="mt-4 space-x-3">
              <TaxPoyntButton variant="outline" onClick={() => router.push('/support')}>Open support</TaxPoyntButton>
              <TaxPoyntButton variant="outline" onClick={() => router.push('/dashboard/si/sdk-hub')}>
                Explore SDK hub
              </TaxPoyntButton>
            </div>
          </div>
        </section>
      </div>
    </DashboardLayout>
  );
}
