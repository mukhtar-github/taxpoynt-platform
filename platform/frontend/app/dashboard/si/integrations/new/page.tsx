'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService, type User } from '../../../../../shared_components/services/auth';
import { DashboardLayout } from '../../../../../shared_components/layouts/DashboardLayout';
import { TaxPoyntButton, TaxPoyntInput } from '../../../../../design_system';
import apiClient from '../../../../../shared_components/api/client';

type AuthMode = 'api_key' | 'password';
type Environment = 'sandbox' | 'production';

interface ConnectionFormState {
  connectionName: string;
  environment: Environment;
  baseUrl: string;
  database: string;
  username: string;
  password: string;
  apiKey: string;
  authMode: AuthMode;
  notes: string;
  autoSync: boolean;
  pollingInterval: number;
}

interface AsyncStatus {
  state: 'idle' | 'saving' | 'testing' | 'success' | 'error';
  message?: string;
}

const DEFAULT_FORM: ConnectionFormState = {
  connectionName: 'Odoo ERP Connection',
  environment: 'sandbox',
  baseUrl: '',
  database: '',
  username: '',
  password: '',
  apiKey: '',
  authMode: 'api_key',
  notes: '',
  autoSync: true,
  pollingInterval: 15,
};

export default function NewIntegrationPage(): JSX.Element | null {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [form, setForm] = useState<ConnectionFormState>(DEFAULT_FORM);
  const [status, setStatus] = useState<AsyncStatus>({ state: 'idle' });
  const [connectionId, setConnectionId] = useState<string | null>(null);

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

  const organizationId = useMemo(() => user?.organization?.id ?? null, [user]);

  const handleFieldChange = (field: keyof ConnectionFormState) => (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const value = event.target.type === 'checkbox'
      ? (event.target as HTMLInputElement).checked
      : event.target.value;

    setForm((prev) => ({
      ...prev,
      [field]: field === 'pollingInterval' ? Number(value) || 5 : value,
    }));
  };

  const buildConnectionPayload = () => {
    const credentials = form.authMode === 'api_key'
      ? { api_key: form.apiKey?.trim() }
      : { password: form.password };

    return {
      erp_system: 'odoo',
      organization_id: organizationId,
      connection_name: form.connectionName,
      environment: form.environment,
      connection_config: {
        type: 'odoo',
        auth_method: form.authMode,
        url: form.baseUrl.trim(),
        database: form.database.trim(),
        username: form.username.trim(),
        ...credentials,
        environment: form.environment,
        auto_sync: form.autoSync,
        polling_interval: form.pollingInterval,
      },
      metadata: {
        notes: form.notes,
      },
    };
  };

  const handleCreateConnection = async () => {
    if (!organizationId) {
      setStatus({ state: 'error', message: 'We could not detect your organization. Please sign in again.' });
      return;
    }

    if (!form.baseUrl || !form.database || !form.username) {
      setStatus({ state: 'error', message: 'Base URL, database, and username are required.' });
      return;
    }

    if (form.authMode === 'api_key' && !form.apiKey) {
      setStatus({ state: 'error', message: 'Provide an API key to authenticate with Odoo.' });
      return;
    }

    if (form.authMode === 'password' && !form.password) {
      setStatus({ state: 'error', message: 'Provide your Odoo password to authenticate.' });
      return;
    }

    try {
      setStatus({ state: 'saving', message: 'Creating connection…' });
      const payload = buildConnectionPayload();

      const response = await apiClient.post('/si/business/erp/connections', payload);
      const connectionData = response?.data?.data ?? {};
      const newConnectionId = connectionData.connection_id || connectionData.id || connectionData?.connection?.id || null;

      setConnectionId(newConnectionId);
      setStatus({ state: 'success', message: 'Connection saved. You can now test the link or start syncing.' });
    } catch (error: unknown) {
      const message = error instanceof Error
        ? error.message
        : 'Unable to create the connection. Please verify your details and try again.';
      setStatus({ state: 'error', message });
    }
  };

  const handleTestConnection = async () => {
    if (!connectionId) {
      setStatus({ state: 'error', message: 'Save the connection before running a test.' });
      return;
    }

    try {
      setStatus({ state: 'testing', message: 'Running test from the gateway…' });
      const response = await apiClient.post<{
        success?: boolean;
        data?: { message?: string; details?: string; [key: string]: any };
        detail?: string;
      }>(`/si/business/erp/connections/${connectionId}/test`, {});

      const success = response?.success ?? true;
      if (success) {
        const payload = response?.data ?? {};
        const message =
          typeof payload.message === 'string'
            ? payload.message
            : typeof payload.details === 'string'
            ? payload.details
            : 'Connection test completed successfully. Monitor integration health for results.';
        setStatus({ state: 'success', message });
      } else {
        const detail = response?.detail || response?.data?.error || 'Connection test failed.';
        setStatus({ state: 'error', message: detail });
      }
    } catch (error: unknown) {
      const message = error instanceof Error
        ? error.message
        : 'Connection test failed. Confirm your credentials and network access.';
      setStatus({ state: 'error', message });
    }
  };

  const handleOpenDocs = () => {
    window.open('https://docs.taxpoynt.com/integrations/erp/odoo', '_blank', 'noopener');
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
      activeTab="integrations"
    >
      <div className="space-y-10">
        <header className="rounded-3xl border border-indigo-100 bg-white/70 p-6 shadow-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-indigo-800">Connect Odoo via RPC</h1>
              <p className="mt-1 text-sm text-slate-600">
                Provide your Odoo credentials to register a reusable connection. This enables invoice extraction,
                POS sync, and compliance checks directly from the SI dashboard.
              </p>
            </div>
            <div className="flex gap-3">
              <TaxPoyntButton variant="outline" onClick={handleOpenDocs}>
                View Integration Guide
              </TaxPoyntButton>
              <TaxPoyntButton
                variant="outline"
                onClick={() => router.push('/dashboard/si/setup')}
              >
                Back to Setup
              </TaxPoyntButton>
            </div>
          </div>
        </header>

        <section className="grid gap-8 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            <div className="rounded-2xl border border-indigo-100 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-indigo-900">Connection Details</h2>
              <p className="text-sm text-slate-600">Fill in your Odoo server credentials. API keys are preferred for production access.</p>

              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <div>
                  <label className="text-sm font-medium text-slate-700">Connection name</label>
                  <TaxPoyntInput value={form.connectionName} onChange={handleFieldChange('connectionName')} placeholder="e.g. Odoo Sandbox" />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700">Environment</label>
                  <select
                    className="mt-1 w-full rounded-lg border border-indigo-100 px-3 py-2 text-sm focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                    value={form.environment}
                    onChange={(event) => setForm((prev) => ({ ...prev, environment: event.target.value as Environment }))}
                  >
                    <option value="sandbox">Sandbox</option>
                    <option value="production">Production</option>
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="text-sm font-medium text-slate-700">Odoo URL</label>
                  <TaxPoyntInput value={form.baseUrl} onChange={handleFieldChange('baseUrl')} placeholder="https://your-odoo-instance.com" />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700">Database</label>
                  <TaxPoyntInput value={form.database} onChange={handleFieldChange('database')} placeholder="odoo_db" />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700">Username / Email</label>
                  <TaxPoyntInput value={form.username} onChange={handleFieldChange('username')} placeholder="integration@company.com" />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700">Authentication method</label>
                  <select
                    className="mt-1 w-full rounded-lg border border-indigo-100 px-3 py-2 text-sm focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                    value={form.authMode}
                    onChange={(event) => setForm((prev) => ({ ...prev, authMode: event.target.value as AuthMode }))}
                  >
                    <option value="api_key">API key</option>
                    <option value="password">Password</option>
                  </select>
                </div>
                {form.authMode === 'api_key' ? (
                  <div className="md:col-span-2">
                    <label className="text-sm font-medium text-slate-700">Odoo API key</label>
                    <TaxPoyntInput value={form.apiKey} onChange={handleFieldChange('apiKey')} placeholder="Paste your API key" type="password" />
                  </div>
                ) : (
                  <div className="md:col-span-2">
                    <label className="text-sm font-medium text-slate-700">Odoo password</label>
                    <TaxPoyntInput value={form.password} onChange={handleFieldChange('password')} placeholder="********" type="password" />
                  </div>
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-indigo-100 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-indigo-900">Automation preferences</h2>
              <p className="text-sm text-slate-600">Configure how often TaxPoynt polls your Odoo workspace for changes.</p>

              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={form.autoSync}
                    onChange={(event) => setForm((prev) => ({ ...prev, autoSync: event.target.checked }))}
                    className="h-4 w-4 rounded border-indigo-200 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="text-sm text-slate-700">Enable automatic invoice sync</span>
                </label>
                <div>
                  <label className="text-sm font-medium text-slate-700">Polling interval (minutes)</label>
                  <TaxPoyntInput
                    type="number"
                    min={5}
                    value={form.pollingInterval}
                    onChange={handleFieldChange('pollingInterval')}
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="text-sm font-medium text-slate-700">Notes</label>
                  <textarea
                    className="mt-1 w-full rounded-lg border border-indigo-100 px-3 py-2 text-sm focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                    rows={4}
                    value={form.notes}
                    onChange={handleFieldChange('notes')}
                    placeholder="Describe which modules should sync or provide credentials rotation details"
                  />
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                {status.state !== 'idle' && (
                  <p className={`text-sm ${status.state === 'error' ? 'text-red-600' : 'text-indigo-600'}`}>{status.message}</p>
                )}
              </div>
              <div className="flex gap-3">
                <TaxPoyntButton variant="outline" onClick={handleTestConnection} disabled={status.state === 'saving' || !connectionId}>
                  {status.state === 'testing' ? 'Testing…' : 'Test connection'}
                </TaxPoyntButton>
                <TaxPoyntButton onClick={handleCreateConnection} disabled={status.state === 'saving'}>
                  {status.state === 'saving' ? 'Saving…' : connectionId ? 'Update connection' : 'Create connection'}
                </TaxPoyntButton>
              </div>
            </div>
          </div>

          <aside className="space-y-6">
            <div className="rounded-2xl border border-indigo-100 bg-indigo-50/60 p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-indigo-900 uppercase tracking-wide">Before you connect</h3>
              <ul className="mt-3 space-y-2 text-sm text-indigo-800">
                <li>• Ensure XML-RPC is accessible from TaxPoynt’s IP range.</li>
                <li>• Generate a dedicated integration user with limited permissions.</li>
                <li>• API keys are preferred; passwords should only be used for testing.</li>
                <li>• Sandbox connections sync to our validation workspace only.</li>
              </ul>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-900">Next steps after connecting</h3>
              <ol className="mt-3 space-y-2 text-sm text-slate-600">
                <li>1. Return to the SI dashboard to monitor sync status.</li>
                <li>2. Configure field mapping for FIRS invoice formats.</li>
                <li>3. Run a sandbox submission before switching to production.</li>
              </ol>
              <TaxPoyntButton
                variant="outline"
                className="mt-4 w-full"
                onClick={() => router.push('/dashboard/si/business-systems')}
              >
                View business systems hub
              </TaxPoyntButton>
            </div>
          </aside>
        </section>
      </div>
    </DashboardLayout>
  );
}
