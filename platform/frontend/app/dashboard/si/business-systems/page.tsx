'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService, type User } from '../../../../shared_components/services/auth';
import { DashboardLayout } from '../../../../shared_components/layouts/DashboardLayout';
import { TaxPoyntButton } from '../../../../design_system';
import apiClient from '../../../../shared_components/api/client';

type V1Response<T> = {
  success: boolean;
  action: string;
  data: T;
  meta?: Record<string, any> | null;
};

interface ErpConnectionRecord {
  connection_id: string;
  organization_id: string;
  erp_system: string;
  connection_name?: string;
  environment: string;
  connection_config?: {
    auth_method?: string;
    url?: string;
    database?: string;
    username?: string;
    auto_sync?: boolean;
    polling_interval?: number;
    [key: string]: any;
  };
  metadata?: Record<string, any>;
  status?: string;
  status_reason?: string;
  owner_user_id?: string | null;
  is_active?: boolean;
  last_status_at?: string | null;
  created_at?: string;
  updated_at?: string;
}

interface ListErpConnectionsResponse {
  connections: ErpConnectionRecord[];
  total_count: number;
}

const statusStyles: Record<string, string> = {
  active: 'text-green-600 bg-green-50 border border-green-200',
  configured: 'text-indigo-600 bg-indigo-50 border border-indigo-200',
  syncing: 'text-blue-600 bg-blue-50 border border-blue-200',
  failed: 'text-red-600 bg-red-50 border border-red-200',
  paused: 'text-yellow-600 bg-yellow-50 border border-yellow-200',
};

const formatDateTime = (iso?: string | null): string => {
  if (!iso) return 'Not available';
  try {
    const date = new Date(iso);
    return new Intl.DateTimeFormat('en-NG', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(date);
  } catch {
    return iso;
  }
};

const formatInterval = (minutes?: number): string => {
  if (!minutes || Number.isNaN(minutes)) return 'Not configured';
  if (minutes < 60) return `${minutes} min`;
  const hrs = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins ? `${hrs}h ${mins}m` : `${hrs}h`;
};

const getStatusBadgeClass = (status?: string): string => {
  if (!status) return 'text-slate-600 bg-slate-100 border border-slate-200';
  const key = status.toLowerCase();
  return statusStyles[key] || 'text-slate-600 bg-slate-100 border border-slate-200';
};

const BusinessSystemsManagementPage = (): JSX.Element | null => {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connections, setConnections] = useState<ErpConnectionRecord[]>([]);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionType, setActionType] = useState<'success' | 'error'>('success');
  const [pendingAction, setPendingAction] = useState<{ type: 'test' | 'sync'; connectionId: string } | null>(null);

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
    fetchConnections(currentUser);
  }, [router]);

  const fetchConnections = async (currentUser: User) => {
    const organizationId = currentUser.organization?.id;
    if (!organizationId) {
      setConnections([]);
      setIsLoading(false);
      setError('No organization context found. Add an organization before managing integrations.');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const query = `?organization_id=${encodeURIComponent(organizationId)}`;
      const response = await apiClient.get<V1Response<ListErpConnectionsResponse>>(
        `/si/business/erp/connections${query}`
      );
      setConnections(response.data?.connections ?? []);
    } catch (err: any) {
      console.error('Failed to load ERP connections:', err);
      const message =
        err?.message ||
        err?.response?.data?.detail ||
        'Unable to load ERP connections. Please try again.';
      setError(message);
      setConnections([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestConnection = async (connectionId: string) => {
    setPendingAction({ type: 'test', connectionId });
    setActionMessage(null);
    try {
      const response = await apiClient.post<V1Response<any>>(
        `/si/business/erp/connections/${connectionId}/test`,
        {}
      );
      const message =
        response.data?.data?.message ||
        response.data?.message ||
        'Connection test completed successfully.';
      setActionType('success');
      setActionMessage(message);
    } catch (err: any) {
      console.error('Connection test failed:', err);
      setActionType('error');
      setActionMessage(
        err?.response?.data?.detail ||
          err?.message ||
          'Connection test failed. Please review your credentials.'
      );
    } finally {
      setPendingAction(null);
    }
  };

  const handleSyncConnection = async (connectionId: string) => {
    setPendingAction({ type: 'sync', connectionId });
    setActionMessage(null);
    try {
      const response = await apiClient.post<V1Response<any>>(
        `/si/business/erp/connections/${connectionId}/sync`,
        { force: true }
      );
      const message =
        response.data?.status?.latest_execution?.status ||
        response.data?.message ||
        'Sync has been queued. Check sync status for progress.';
      setActionType('success');
      setActionMessage(typeof message === 'string' ? message : 'Sync request accepted.');
    } catch (err: any) {
      console.error('Failed to queue sync:', err);
      setActionType('error');
      setActionMessage(
        err?.response?.data?.detail ||
          err?.message ||
          'Unable to queue sync. Please retry later.'
      );
    } finally {
      setPendingAction(null);
      await fetchConnections(user!);
    }
  };

  const summary = useMemo(() => {
    if (!connections.length) {
      return {
        total: 0,
        autoSync: 0,
        active: 0,
      };
    }
    const autoSync = connections.filter(
      (conn) =>
        conn.connection_config?.auto_sync ||
        conn.metadata?.auto_sync ||
        conn.connection_config?.enable_auto_sync
    ).length;
    const active = connections.filter((conn) => (conn.status || '').toLowerCase() === 'active').length;
    return {
      total: connections.length,
      autoSync,
      active,
    };
  }, [connections]);

  if (!user) {
    return null;
  }

  return (
    <DashboardLayout
      role="si"
      userName={`${user.first_name} ${user.last_name}`}
      userEmail={user.email}
      activeTab="business-systems"
    >
      <div className="space-y-8">
        <header className="rounded-3xl border border-indigo-100 bg-white/80 p-6 shadow-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-indigo-900">Business Systems Management</h1>
              <p className="mt-1 text-sm text-slate-600">
                Monitor your connected ERP environments, run ad-hoc syncs, and keep auto-sync schedules
                aligned with FIRS invoice generation.
              </p>
            </div>
            <div className="flex gap-3">
              <TaxPoyntButton
                variant="outline"
                className="whitespace-nowrap"
                onClick={() => router.push('/dashboard/si/integrations/new')}
              >
                Manage integrations
              </TaxPoyntButton>
              <TaxPoyntButton
                variant="primary"
                className="whitespace-nowrap"
                onClick={() => router.push('/dashboard/si/firs-invoice-generator')}
              >
                Open FIRS Invoice Generator
              </TaxPoyntButton>
            </div>
          </div>
        </header>

        {actionMessage && (
          <div
            className={`rounded-xl border p-4 text-sm ${
              actionType === 'success'
                ? 'border-green-200 bg-green-50 text-green-700'
                : 'border-red-200 bg-red-50 text-red-700'
            }`}
          >
            {actionMessage}
          </div>
        )}

        <section className="grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs uppercase tracking-wide text-slate-500">Connected ERP systems</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{summary.total}</p>
            <p className="mt-1 text-sm text-slate-600">
              Manage connections to Odoo, SAP, and other ERP platforms from one place.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs uppercase tracking-wide text-slate-500">Auto-sync enabled</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{summary.autoSync}</p>
            <p className="mt-1 text-sm text-slate-600">
              Connections pushing updates automatically to the FIRS pipeline.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs uppercase tracking-wide text-slate-500">Active status</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{summary.active}</p>
            <p className="mt-1 text-sm text-slate-600">
              Connections currently marked active by the integration health monitor.
            </p>
          </div>
        </section>

        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">ERP connections</h2>
              <p className="text-sm text-slate-600">
                View connection status, scheduling details, and run immediate syncs.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <TaxPoyntButton variant="outline" size="sm" onClick={() => user && fetchConnections(user)}>
                Refresh list
              </TaxPoyntButton>
              <TaxPoyntButton
                variant="outline"
                size="sm"
                onClick={() => router.push('/dashboard/si/setup')}
              >
                System Integrator setup guide
              </TaxPoyntButton>
            </div>
          </div>

          {isLoading ? (
            <div className="flex min-h-[200px] items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-indigo-600" />
            </div>
          ) : error ? (
            <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-6 text-red-700">
              {error}
            </div>
          ) : connections.length === 0 ? (
            <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-6 text-slate-600">
              <p className="font-medium text-slate-800">No ERP integrations yet.</p>
              <p className="mt-2 text-sm">
                Create your first connection to start pulling business transactions into the FIRS workflow.
                Use the integrations manager to create your first connection and start feeding transactions into the FIRS workflow.
              </p>
            </div>
          ) : (
            <div className="mt-6 grid gap-4 lg:grid-cols-2">
              {connections.map((connection) => {
                const statusLabel = connection.status?.replace(/_/g, ' ').toLowerCase() ?? 'configured';
                const autoSync =
                  connection.connection_config?.auto_sync ||
                  connection.metadata?.auto_sync ||
                  connection.connection_config?.enable_auto_sync ||
                  false;
                const polling =
                  connection.metadata?.polling_interval_minutes ??
                  connection.connection_config?.polling_interval;

                return (
                  <div
                    key={connection.connection_id}
                    className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-slate-50/60 p-5 transition hover:border-indigo-200 hover:bg-white"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-xs uppercase tracking-wide text-slate-500">
                          {connection.erp_system.toUpperCase()}
                        </p>
                        <h3 className="mt-1 text-lg font-semibold text-slate-900">
                          {connection.connection_name || connection.connection_config?.url || 'ERP Connection'}
                        </h3>
                        <p className="mt-1 text-sm text-slate-600">
                          Environment: {connection.environment}
                        </p>
                        {connection.connection_config?.url && (
                          <p className="mt-1 text-xs text-slate-500 break-all">
                            {connection.connection_config.url}
                          </p>
                        )}
                      </div>
                      <span className={`rounded-full px-3 py-1 text-xs font-medium ${getStatusBadgeClass(connection.status)}`}>
                        {statusLabel}
                      </span>
                    </div>

                    <div className="mt-4 grid gap-3 text-sm text-slate-600 sm:grid-cols-2">
                      <div className="rounded-lg border border-slate-200 bg-white/60 p-3">
                        <p className="text-xs uppercase tracking-wide text-slate-500">Auto-sync</p>
                        <p className="mt-1 font-medium text-slate-800">
                          {autoSync ? 'Enabled' : 'Disabled'}
                        </p>
                        <p className="text-xs text-slate-500">
                          Polling: {formatInterval(polling)}
                        </p>
                      </div>
                      <div className="rounded-lg border border-slate-200 bg-white/60 p-3">
                        <p className="text-xs uppercase tracking-wide text-slate-500">Last update</p>
                        <p className="mt-1 font-medium text-slate-800">
                          {formatDateTime(connection.last_status_at || connection.updated_at)}
                        </p>
                        {connection.status_reason && (
                          <p className="text-xs text-red-500 mt-1">{connection.status_reason}</p>
                        )}
                      </div>
                    </div>

                    <div className="mt-4 flex flex-wrap gap-2">
                      <TaxPoyntButton
                        size="sm"
                        variant="outline"
                        onClick={() => handleTestConnection(connection.connection_id)}
                        disabled={
                          pendingAction?.connectionId === connection.connection_id &&
                          pendingAction.type === 'test'
                        }
                      >
                        {pendingAction?.connectionId === connection.connection_id &&
                        pendingAction.type === 'test'
                          ? 'Testing…'
                          : 'Test connection'}
                      </TaxPoyntButton>
                      <TaxPoyntButton
                        size="sm"
                        variant="outline"
                        onClick={() => handleSyncConnection(connection.connection_id)}
                        disabled={
                          pendingAction?.connectionId === connection.connection_id &&
                          pendingAction.type === 'sync'
                        }
                      >
                        {pendingAction?.connectionId === connection.connection_id &&
                        pendingAction.type === 'sync'
                          ? 'Queueing sync…'
                          : 'Run manual sync'}
                      </TaxPoyntButton>
                      <TaxPoyntButton
                        size="sm"
                        variant="ghost"
                        onClick={() =>
                          router.push(`/dashboard/si/integrations/new?connectionId=${connection.connection_id}`)
                        }
                      >
                        Edit settings
                      </TaxPoyntButton>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </DashboardLayout>
  );
};

export default BusinessSystemsManagementPage;
