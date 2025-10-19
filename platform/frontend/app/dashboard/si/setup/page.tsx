'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService, type User } from '../../../../shared_components/services/auth';
import { DashboardLayout } from '../../../../shared_components/layouts/DashboardLayout';
import { TaxPoyntButton } from '../../../../design_system';
import { onboardingApi } from '../../../../shared_components/services/onboardingApi';
import apiClient from '../../../../shared_components/api/client';

type JsonMap = Record<string, unknown>;

const isRecord = (value: unknown): value is JsonMap =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const toNumber = (value: unknown): number =>
  typeof value === 'number' && Number.isFinite(value) ? value : 0;

const toJsonMap = (value: unknown): JsonMap | null =>
  value && typeof value === 'object' && !Array.isArray(value) ? (value as JsonMap) : null;

const formatDateTime = (value?: string | null): string => {
  if (!value) {
    return 'N/A';
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat('en-NG', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(parsed);
};

interface ConnectionSystem {
  id: string;
  name: string;
  status: string;
  lastSync?: string | null;
  error?: string | null;
  needsAttention?: boolean;
}

interface RuntimeConnections {
  total: number;
  active: number;
  failing: number;
  needsAttention: number;
  items: ConnectionSystem[];
}

interface RuntimeIrnProgress {
  totalGenerated: number;
  pending: number;
  recent: Array<{
    irn?: string | null;
    status?: string;
    createdAt?: string | null;
  }>;
}

interface RuntimeSnapshot {
  loginCount: number;
  connections: RuntimeConnections | null;
  irnProgress: RuntimeIrnProgress | null;
}

const EMPTY_RUNTIME: RuntimeSnapshot = {
  loginCount: 0,
  connections: null,
  irnProgress: null,
};

function parseRuntimeSnapshot(input: unknown): RuntimeSnapshot {
  if (!isRecord(input)) {
    return EMPTY_RUNTIME;
  }

  const loginCount = toNumber(input.login_count ?? input.loginCount);

  let connections: RuntimeConnections | null = null;
  if (isRecord(input.connections)) {
    const itemsRaw = Array.isArray(input.connections.items) ? input.connections.items : [];
    const items = itemsRaw
      .filter((item): item is JsonMap => isRecord(item))
      .map((item, index) => ({
        id:
          typeof item.id === 'string'
            ? item.id
            : typeof item.name === 'string'
            ? `${item.name}-${index}`
            : `connection-${index}`,
        name: typeof item.name === 'string' ? item.name : 'Integration',
        status: typeof item.status === 'string' ? item.status : 'unknown',
        lastSync:
          typeof item.lastSync === 'string'
            ? item.lastSync
            : typeof item.last_sync === 'string'
            ? item.last_sync
            : undefined,
        error: typeof item.error === 'string' ? item.error : undefined,
        needsAttention: Boolean(item.needsAttention ?? item.needs_attention),
      }));
    const needsAttention =
      typeof input.connections.needsAttention === 'number'
        ? input.connections.needsAttention
        : items.filter((item) => item.needsAttention).length;
    connections = {
      total: toNumber(input.connections.total ?? items.length),
      active: toNumber(input.connections.active),
      failing: toNumber(input.connections.failing),
      needsAttention,
      items,
    };
  }

  let irnProgress: RuntimeIrnProgress | null = null;
  const irnRaw = input.irn_progress ?? input.irnProgress;
  if (isRecord(irnRaw)) {
    const recentRaw = Array.isArray(irnRaw.recent) ? irnRaw.recent : [];
    const recent = recentRaw
      .filter((item): item is JsonMap => isRecord(item))
      .map((item) => ({
        irn: typeof item.irn === 'string' ? item.irn : undefined,
        status: typeof item.status === 'string' ? item.status : undefined,
        createdAt:
          typeof item.createdAt === 'string'
            ? item.createdAt
            : typeof item.created_at === 'string'
            ? item.created_at
            : undefined,
      }));
    irnProgress = {
      totalGenerated: toNumber(irnRaw.total_generated ?? irnRaw.totalGenerated),
      pending: toNumber(irnRaw.pending),
      recent,
    };
  }

  return {
    loginCount,
    connections,
    irnProgress,
  };
}

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
  const [runtimeSnapshot, setRuntimeSnapshot] = useState<RuntimeSnapshot>(EMPTY_RUNTIME);
  const [dashboardMetrics, setDashboardMetrics] = useState<JsonMap | null>(null);
  const [metricsStatus, setMetricsStatus] = useState<'idle' | 'loading' | 'error'>('idle');

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

          const runtimeRaw =
            isRecord(response.metadata) && isRecord(response.metadata.runtime)
              ? response.metadata.runtime
              : null;
          setRuntimeSnapshot(runtimeRaw ? parseRuntimeSnapshot(runtimeRaw) : EMPTY_RUNTIME);
        }
        setProgressStatus('idle');
      } catch (error) {
        console.error('Unable to load onboarding progress', error);
        setProgressStatus('error');
      }
    };

    fetchProgress();
  }, []);

  useEffect(() => {
    const fetchMetrics = async () => {
      setMetricsStatus('loading');
      try {
        const result = await apiClient.get<JsonMap | null>('/si/dashboard/metrics');
        if (result && typeof result === 'object') {
          if ('success' in result) {
            const payload = result as JsonMap & { success?: boolean; data?: JsonMap | null };
            setDashboardMetrics(payload.success ? (toJsonMap(payload.data) ?? null) : null);
          } else {
            setDashboardMetrics(result as JsonMap);
          }
        } else {
          setDashboardMetrics(null);
        }
        setMetricsStatus('idle');
      } catch (error) {
        console.error('Unable to load dashboard metrics', error);
        setMetricsStatus('error');
      }
    };

    fetchMetrics();
  }, []);

  const navigateTo = (path: string) => () => router.push(path);

  const wizardStarted = Boolean(progress?.has_started);
  const wizardCompleted =
    Boolean(progress?.is_complete) ||
    Boolean(progress?.completed_steps?.includes('onboarding_complete'));
  const mappingStageIds = [
    'business_systems_setup',
    'financial_systems_setup',
    'reconciliation_setup',
    'complete_integration_setup',
    'integration_testing',
    'launch_ready',
    'launch',
    'onboarding_complete',
  ];
  const integrationStageIds = [
    'complete_integration_setup',
    'reconciliation_setup',
    'onboarding_complete',
  ];
  const hasReachedStage = (stageIds: string[]) =>
    wizardCompleted ||
    (progress?.current_step ? stageIds.includes(progress.current_step) : false) ||
    Boolean(progress?.completed_steps?.some((step) => stageIds.includes(step)));

  const canResumeMapping = wizardStarted && hasReachedStage(mappingStageIds);
  const canManageIntegrations = wizardStarted && hasReachedStage(integrationStageIds);

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

  const connectionSummary =
    (isRecord(dashboardMetrics?.connectionHealth) && isRecord(dashboardMetrics.connectionHealth.summary)
      ? {
          total: toNumber(dashboardMetrics.connectionHealth.summary.total),
          active: toNumber(dashboardMetrics.connectionHealth.summary.active),
          failing: toNumber(dashboardMetrics.connectionHealth.summary.failing),
          needsAttention: toNumber(dashboardMetrics.connectionHealth.summary.needsAttention),
        }
      : runtimeSnapshot.connections
      ? {
          total: runtimeSnapshot.connections.total,
          active: runtimeSnapshot.connections.active,
          failing: runtimeSnapshot.connections.failing,
          needsAttention: runtimeSnapshot.connections.needsAttention,
        }
      : null) || null;

  const connectionSystems: ConnectionSystem[] = (() => {
    if (isRecord(dashboardMetrics?.connectionHealth) && Array.isArray(dashboardMetrics.connectionHealth.systems)) {
      return dashboardMetrics.connectionHealth.systems
        .filter((item): item is JsonMap => isRecord(item))
        .map((item, index) => ({
          id:
            typeof item.id === 'string'
              ? item.id
              : typeof item.name === 'string'
              ? `${item.name}-${index}`
              : `connection-${index}`,
          name: typeof item.name === 'string' ? item.name : 'Integration',
          status: typeof item.status === 'string' ? item.status : 'unknown',
          lastSync:
            typeof item.lastSync === 'string'
              ? item.lastSync
              : typeof item.last_sync === 'string'
              ? item.last_sync
              : undefined,
          error: typeof item.error === 'string' ? item.error : undefined,
          needsAttention: Boolean(item.needsAttention ?? item.needs_attention),
        }));
    }
    return runtimeSnapshot.connections?.items ?? [];
  })();

  const irnStatus = (() => {
    if (isRecord(dashboardMetrics?.irnStatus)) {
      return {
        totalGenerated: toNumber(dashboardMetrics.irnStatus.totalGenerated ?? dashboardMetrics.irnStatus.total_generated),
        pending: toNumber(dashboardMetrics.irnStatus.pending),
        total: toNumber(dashboardMetrics.irnStatus.total),
        lastGeneratedAt:
          typeof dashboardMetrics.irnStatus.lastGeneratedAt === 'string'
            ? dashboardMetrics.irnStatus.lastGeneratedAt
            : typeof dashboardMetrics.irnStatus.last_generated_at === 'string'
            ? dashboardMetrics.irnStatus.last_generated_at
            : undefined,
        recent: Array.isArray(dashboardMetrics.irnStatus.recent) ? dashboardMetrics.irnStatus.recent : [],
      };
    }
    if (runtimeSnapshot.irnProgress) {
      return {
        totalGenerated: runtimeSnapshot.irnProgress.totalGenerated,
        pending: runtimeSnapshot.irnProgress.pending,
        total: runtimeSnapshot.irnProgress.totalGenerated + runtimeSnapshot.irnProgress.pending,
        lastGeneratedAt: runtimeSnapshot.irnProgress.recent[0]?.createdAt,
        recent: runtimeSnapshot.irnProgress.recent,
      };
    }
    return null;
  })();

  const irnRecent = (irnStatus?.recent ?? [])
    .filter((item): item is JsonMap => isRecord(item))
    .map((item, index) => ({
      id:
        typeof item.irn === 'string'
          ? item.irn
          : typeof item.id === 'string'
          ? item.id
          : `irn-${index}`,
      status: typeof item.status === 'string' ? item.status : 'unknown',
      createdAt:
        typeof item.createdAt === 'string'
          ? item.createdAt
          : typeof item.created_at === 'string'
          ? item.created_at
          : undefined,
      qrReady: Boolean(item.qrReady ?? item.qr_ready),
      qrSigned: Boolean(item.qrSigned ?? item.qr_signed),
      firsStamp: Boolean(item.firsStamp ?? item.firs_stamp),
    }));

  const validationLogs = (() => {
    if (Array.isArray(dashboardMetrics?.validationLogs)) {
      return dashboardMetrics.validationLogs;
    }
    if (isRecord(dashboardMetrics?.validation) && Array.isArray(dashboardMetrics.validation.recentBatches)) {
      return dashboardMetrics.validation.recentBatches;
    }
    return [];
  })();

  const validationEntries = validationLogs
    .filter((item): item is JsonMap => isRecord(item))
    .map((item, index) => {
      const batchId =
        typeof item.batchId === 'string'
          ? item.batchId
          : typeof item.batch_id === 'string'
          ? item.batch_id
          : typeof item.id === 'string'
          ? item.id
          : `batch-${index}`;
      const status = typeof item.status === 'string' ? item.status : 'unknown';
      const created =
        typeof item.createdAt === 'string'
          ? item.createdAt
          : typeof item.created_at === 'string'
          ? item.created_at
          : typeof item.updated_at === 'string'
          ? item.updated_at
          : undefined;
      const totals = isRecord(item.totals) ? item.totals : {};
      const totalInvoices =
        typeof item.total === 'number'
          ? item.total
          : typeof totals.total === 'number'
          ? totals.total
          : typeof item.totalInvoices === 'number'
          ? item.totalInvoices
          : undefined;

      return {
        id: batchId,
        status,
        createdAt: created,
        totalInvoices,
      };
    })
    .slice(0, 4);

  const metricsLoading = metricsStatus === 'loading';
  const metricsErrored = metricsStatus === 'error';

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
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Workspace activity</h2>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                {runtimeSnapshot.loginCount.toLocaleString()} sign-ins
              </span>
            </div>
            <p className="mt-3 text-sm text-slate-600">
              Live onboarding insights from your current workspace usage.
            </p>
            <div className="mt-4 grid grid-cols-1 gap-3 text-sm md:grid-cols-2">
              <div className="rounded-lg border border-slate-100 bg-slate-50 px-4 py-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Onboarding status</p>
                <p className="mt-1 text-lg font-semibold text-slate-900">
                  {progress?.is_complete ? 'Complete' : `${progress?.completed_steps.length ?? 0} steps`}
                </p>
                <p className="text-xs text-slate-500">
                  Next: {progress?.current_step ? progress.current_step.replace(/-/g, ' ') : 'service-selection'}
                </p>
              </div>
              <div className="rounded-lg border border-slate-100 bg-slate-50 px-4 py-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">IRN ready</p>
                <p className="mt-1 text-lg font-semibold text-slate-900">
                  {irnStatus ? irnStatus.totalGenerated.toLocaleString() : '0'}
                </p>
                <p className="text-xs text-slate-500">
                  Pending: {irnStatus ? irnStatus.pending.toLocaleString() : '0'}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-indigo-100 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-indigo-900">Connection health</h2>
              {connectionSummary ? (
                <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-600">
                  {connectionSummary.active}/{connectionSummary.total} active
                </span>
              ) : null}
            </div>
            <p className="mt-3 text-sm text-slate-600">
              Monitor integration status and identify systems needing attention.
            </p>
            {metricsLoading ? (
              <p className="mt-4 text-sm text-slate-500">Loading connection metrics…</p>
            ) : connectionSummary ? (
              <>
                <div className="mt-4 grid grid-cols-3 gap-3 text-xs text-indigo-700">
                  <div className="rounded-lg border border-indigo-100 bg-indigo-50 px-3 py-2 text-center">
                    <p className="font-semibold text-indigo-800">{connectionSummary.active.toLocaleString()}</p>
                    <p className="mt-1 uppercase tracking-wide">Active</p>
                  </div>
                  <div className="rounded-lg border border-indigo-100 bg-indigo-50 px-3 py-2 text-center">
                    <p className="font-semibold text-indigo-800">{connectionSummary.failing.toLocaleString()}</p>
                    <p className="mt-1 uppercase tracking-wide">Failing</p>
                  </div>
                  <div className="rounded-lg border border-indigo-100 bg-indigo-50 px-3 py-2 text-center">
                    <p className="font-semibold text-indigo-800">{connectionSummary.needsAttention.toLocaleString()}</p>
                    <p className="mt-1 uppercase tracking-wide">Attention</p>
                  </div>
                </div>
                <ul className="mt-4 space-y-2">
                  {connectionSystems.slice(0, 4).map((system) => (
                    <li
                      key={system.id}
                      className="rounded-lg border border-slate-100 bg-white px-4 py-3 text-sm text-slate-700"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-900">{system.name}</span>
                        <span className="text-xs uppercase tracking-wide text-slate-500">{system.status}</span>
                      </div>
                      <p className="mt-1 text-xs text-slate-500">
                        Last sync: {system.lastSync ? formatDateTime(system.lastSync) : 'Not synced yet'}
                      </p>
                      {system.needsAttention && (
                        <p className="mt-1 text-xs font-semibold text-amber-600">
                          ⚠️ {system.error || 'Requires follow-up'}
                        </p>
                      )}
                    </li>
                  ))}
                  {connectionSystems.length === 0 && (
                    <li className="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-600">
                      Connect an ERP to populate live health metrics.
                    </li>
                  )}
                </ul>
              </>
            ) : metricsErrored ? (
              <p className="mt-4 text-sm text-red-500">Unable to load connection metrics right now.</p>
            ) : (
              <p className="mt-4 text-sm text-slate-500">No connections detected yet.</p>
            )}
          </div>

          <div className="rounded-2xl border border-emerald-100 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-emerald-900">IRN & validation timeline</h2>
              {irnStatus?.lastGeneratedAt && (
                <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-600">
                  Last IRN: {formatDateTime(irnStatus.lastGeneratedAt)}
                </span>
              )}
            </div>
            <p className="mt-3 text-sm text-slate-600">
              Track recent IRN generations alongside validation batches.
            </p>
            {metricsLoading ? (
              <p className="mt-4 text-sm text-slate-500">Loading timeline…</p>
            ) : (
              <>
                <ul className="mt-4 space-y-2 text-sm text-slate-700">
                  {irnRecent.slice(0, 3).map((entry) => (
                    <li
                      key={entry.id}
                      className="rounded-lg border border-emerald-100 bg-emerald-50 px-4 py-3"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-emerald-900">
                          {entry.id.startsWith('irn-') ? 'IRN submission' : `IRN ${entry.id}`}
                        </span>
                        <span className="text-xs uppercase tracking-wide text-emerald-600">{entry.status}</span>
                      </div>
                      <p className="mt-1 text-xs text-emerald-700">
                        {entry.createdAt ? formatDateTime(entry.createdAt) : 'Awaiting acknowledgement'}
                      </p>
                    </li>
                  ))}
                  {irnRecent.length === 0 && (
                    <li className="rounded-lg border border-dashed border-emerald-100 bg-emerald-50 px-4 py-3 text-xs text-emerald-700">
                      Generate your first IRN to populate the timeline.
                    </li>
                  )}
                </ul>
                <div className="mt-4 rounded-lg border border-emerald-100 bg-white px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-emerald-600">Validation logs</p>
                  <ul className="mt-2 space-y-2 text-xs text-emerald-700">
                    {validationEntries.length > 0 ? (
                      validationEntries.map((log) => (
                        <li key={log.id} className="flex items-center justify-between">
                          <span className="font-semibold">{log.status}</span>
                          <span>{log.createdAt ? formatDateTime(log.createdAt) : 'Pending'}</span>
                        </li>
                      ))
                    ) : (
                      <li className="text-emerald-600">
                        Validation logs will appear after your first batch.
                      </li>
                    )}
                  </ul>
                </div>
              </>
            )}
          </div>
        </section>

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
              <TaxPoyntButton
                variant="primary"
                onClick={() => router.push('/onboarding/si/integration-setup')}
              >
                Continue wizard
              </TaxPoyntButton>
              <TaxPoyntButton
                variant="outline"
                onClick={navigateTo('/onboarding/si/complete-integration-setup')}
                disabled={!canResumeMapping}
              >
                Resume mapping
              </TaxPoyntButton>
            </div>
            {!canResumeMapping && (
              <p className="mt-3 text-xs font-medium text-amber-600">
                Complete the onboarding wizard steps before accessing mapping tools.
              </p>
            )}
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
              <TaxPoyntButton
                onClick={navigateTo('/dashboard/si/integrations/new')}
                disabled={!canManageIntegrations}
              >
                Connect Odoo RPC
              </TaxPoyntButton>
              <TaxPoyntButton
                variant="outline"
                onClick={navigateTo('/dashboard/si/business-systems')}
                disabled={!canManageIntegrations}
              >
                Manage systems
              </TaxPoyntButton>
            </div>
            {!canManageIntegrations && (
              <p className="mt-3 text-xs font-medium text-amber-600">
                Finish the onboarding wizard before connecting external systems.
              </p>
            )}
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
