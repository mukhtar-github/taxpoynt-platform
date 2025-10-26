'use client';

/**
 * Enhanced System Integrator (SI) Interface
 * ==========================================
 * 
 * Professional SI dashboard enhanced with our unified design system.
 * Maintains all existing functionality while providing modern UI/UX.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardLayout } from '../shared_components/layouts/DashboardLayout';
import { DashboardCard } from '../shared_components/dashboard/DashboardCard';
import { TaxPoyntButton } from '../design_system';
import { 
  TYPOGRAPHY_STYLES, 
  combineStyles,
} from '../design_system/style-utilities';
import apiClient from '../shared_components/api/client';
import { APIResponse } from './types';
import ChecklistSidebar, { ChecklistPayload } from './components/checklistSidebar';
import { onboardingChecklistApi } from '../shared_components/services/onboardingChecklistApi';

const isPlainObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const mergeDeep = (target: any, source: any): any => {
  if (source === undefined || source === null) {
    return target;
  }

  if (Array.isArray(source)) {
    return source.slice();
  }

  if (isPlainObject(source)) {
    const base: Record<string, unknown> = isPlainObject(target)
      ? { ...(target as Record<string, unknown>) }
      : {};

    for (const [key, value] of Object.entries(source)) {
      const existing = isPlainObject(target)
        ? (target as Record<string, unknown>)[key]
        : undefined;
      base[key] = mergeDeep(existing, value);
    }

    return base;
  }

  return source;
};

const toMillionsDisplay = (value?: number, digits: number = 1): string | null => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return null;
  }
  return `₦${(value / 1_000_000).toFixed(digits)}M`;
};

const toPercentDisplay = (value?: number, digits: number = 1): string | null => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return null;
  }
  return `${value.toFixed(digits)}%`;
};

function formatNumber(value?: number): string {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '0';
  }
  return value.toLocaleString();
}

export interface EnhancedSIInterfaceProps {
  userName?: string;
  userEmail?: string;
  className?: string;
}

export const EnhancedSIInterface: React.FC<EnhancedSIInterfaceProps> = ({
  userName = 'System Integrator',
  userEmail = 'user@company.com',
  className = ''
}) => {
  const router = useRouter();
  const [hasLiveData, setHasLiveData] = useState(false);
  const [checklist, setChecklist] = useState<ChecklistPayload | null>(null);
  const [checklistStatus, setChecklistStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [checklistError, setChecklistError] = useState<string | null>(null);
  const [selectedGuidancePhase, setSelectedGuidancePhase] = useState<string | null>(null);

  const buildEmptyMetrics = useCallback(() => ({
    integrations: {
      erp: {
        total: 0,
        active: 0,
        totalCustomers: 0,
        totalInvoices: 0,
        systems: [],
        connectedSystems: [],
      },
      crm: {
        total: 0,
        active: 0,
        totalContacts: 0,
        pipelineValue: 0,
        systems: [],
        connectedSystems: [],
      },
      pos: {
        total: 0,
        active: 0,
        dailySales: 0,
        totalItems: 0,
        systems: [],
        connectedSystems: [],
      },
      ecommerce: {
        total: 0,
        active: 0,
        totalOrders: 0,
        totalCustomers: 0,
        systems: [],
        connectedSystems: [],
      },
      overall: {
        totalSystems: 0,
        activeSystems: 0,
        overallHealthScore: 0,
        totalDataPoints: 0,
        syncEfficiency: 0,
        errorRate: 0,
      },
    },
    financial: {
      banking: { connected: 0, totalAccounts: 0, providers: [] },
      payments: { connected: 0, monthlyVolume: 0, providers: [] },
    },
    reconciliation: {
      autoReconciled: 0,
      manualReview: 0,
      successRate: 0,
      categorized: 0,
      exceptions: 0,
      confidenceScores: { high: 0, medium: 0, low: 0 },
    },
    transactions: {
      totalInvoices: 0,
      autoSubmitted: 0,
      manualReview: 0,
      queue: 0,
      successRate: 0,
    },
    compliance: {
      firsStatus: 'Not connected',
      invoicesGenerated: 0,
      complianceScore: 0,
      vatTransactions: 0,
      pendingSubmissions: 0,
      lastSubmission: undefined,
    },
    validation: {
      summary: {
        totalBatches: 0,
        statusCounts: {},
        totals: { total: 0, passed: 0, failed: 0 },
        lastRunAt: undefined,
      },
      recentBatches: [],
      slaHours: 4,
    },
    validationLogs: [],
    connectionHealth: {
      summary: {
        total: 0,
        active: 0,
        failing: 0,
        needsAttention: 0,
      },
      systems: [],
    },
    irnStatus: {
      totalGenerated: 0,
      pending: 0,
      total: 0,
      lastGeneratedAt: undefined,
      recent: [],
    },
    lastUpdated: undefined,
    processing: {
      rate: 0,
      success: 0,
      queue: 0,
      apiLatency: 0,
      uptime: 0,
    },
    cashFlow: {
      netFlow: 0,
      categories: {},
    },
  }), []);

  type DashboardMetrics = ReturnType<typeof buildEmptyMetrics>;
  const [metrics, setMetrics] = useState<DashboardMetrics>(() => buildEmptyMetrics());

  // Load dashboard data from backend APIs
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        const response = await apiClient.get<APIResponse<Partial<DashboardMetrics>>>(
          '/si/dashboard/metrics'
        );

        if (response?.success && response.data) {
          setMetrics((prev) => mergeDeep(prev, response.data ?? {}));
          setHasLiveData(true);
        } else {
          setHasLiveData(false);
          setMetrics(buildEmptyMetrics());
        }
      } catch (error) {
        console.error('Failed to load SI dashboard data:', error);
        setHasLiveData(false);
        setMetrics(buildEmptyMetrics());
      }
    };

    loadDashboardData();
  }, [buildEmptyMetrics]);

  useEffect(() => {
    let cancelled = false;
    const fetchChecklist = async () => {
      try {
        setChecklistStatus('loading');
        const data = await onboardingChecklistApi.fetchChecklist();
        if (cancelled) {
          return;
        }
        setChecklist(data);
        setChecklistStatus('ready');
        setChecklistError(null);
      } catch (error) {
        if (cancelled) {
          return;
        }
        console.error('Failed to fetch onboarding checklist:', error);
        setChecklist(null);
        setChecklistStatus('error');
        setChecklistError('Unable to load onboarding checklist. Showing latest known progress.');
      }
    };

    fetchChecklist();
    return () => {
      cancelled = true;
    };
  }, []);

  const sectionStyle = combineStyles(
    TYPOGRAPHY_STYLES.optimizedText,
    {
      background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)'
    }
  );

  const formatDateTime = (value?: string) => {
    if (!value) return 'N/A';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return new Intl.DateTimeFormat('en-NG', {
      dateStyle: 'medium',
      timeStyle: 'short'
    }).format(parsed);
  };

  const connectionSummary =
    metrics.connectionHealth?.summary ?? {
      total: 0,
      active: 0,
      failing: 0,
      needsAttention: 0,
    };
  const connectionSystems = Array.isArray(metrics.connectionHealth?.systems)
    ? (metrics.connectionHealth?.systems as Array<Record<string, any>>)
    : [];

  const irnStatus =
    metrics.irnStatus ?? {
      totalGenerated: 0,
      pending: 0,
      total: 0,
      lastGeneratedAt: undefined,
      recent: [],
    };
  const irnRecent = Array.isArray(irnStatus.recent)
    ? (irnStatus.recent as Array<Record<string, any>>)
    : [];

  const validationSummary = metrics.validation?.summary ?? { totals: { total: 0, passed: 0, failed: 0 } };
  const validationTotals = validationSummary.totals ?? { total: 0, passed: 0, failed: 0 };
  const validationPassRate = validationTotals.total
    ? Math.round(((validationTotals.passed ?? 0) / validationTotals.total) * 100)
    : 0;
  const validationRecent = Array.isArray(metrics.validation?.recentBatches)
    ? (metrics.validation?.recentBatches as Array<Record<string, any>>)
    : [];
  const validationLogs = Array.isArray(metrics.validationLogs)
    ? (metrics.validationLogs as Array<Record<string, any>>)
    : [];
  const combinedValidationActivity: Array<Record<string, any>> =
    validationLogs.length > 0 ? validationLogs : validationRecent;

  type QuickStat = {
    label: string;
    value: string;
    helper: string;
    textClass: string;
    borderClass: string;
    actionLabel?: string;
    actionIcon?: string;
    onAction?: () => void;
  };

  const quickStats: QuickStat[] = [
    {
      label: 'Active systems',
      value:
        connectionSummary.total > 0
          ? `${connectionSummary.active}/${connectionSummary.total}`
          : formatNumber(connectionSummary.active),
      helper:
        connectionSummary.total > 0
          ? connectionSummary.needsAttention > 0
            ? `${formatNumber(connectionSummary.needsAttention)} flagged`
            : 'All systems clear'
          : 'Connect a system to start tracking health',
      textClass: 'text-indigo-600',
      borderClass: 'border-indigo-100',
      actionLabel: 'Add integration',
      actionIcon: '➕',
      onAction: () => router.push('/dashboard/si/integrations/new'),
    },
    {
      label: 'Auto-reconciled today',
      value: formatNumber(metrics.reconciliation.autoReconciled),
      helper: toPercentDisplay(metrics.reconciliation.successRate) ?? 'Start reconciliation to track progress',
      textClass: 'text-emerald-600',
      borderClass: 'border-emerald-100',
    },
    {
      label: 'IRNs generated',
      value: formatNumber(irnStatus.totalGenerated),
      helper:
        irnStatus.pending > 0
          ? `${formatNumber(irnStatus.pending)} pending`
          : irnStatus.lastGeneratedAt
          ? `Last: ${formatDateTime(irnStatus.lastGeneratedAt)}`
          : 'Awaiting first IRN',
      textClass: 'text-blue-600',
      borderClass: 'border-blue-100',
    },
    {
      label: 'Compliance score',
      value: toPercentDisplay(metrics.compliance.complianceScore) ?? '0%',
      helper: metrics.compliance.firsStatus ?? 'Not connected',
      textClass: 'text-purple-600',
      borderClass: 'border-purple-100',
    },
  ];

  const priorityActions = [
    {
      id: 'systems',
      icon: '🔌',
      title:
        metrics.integrations.overall.activeSystems > 0
          ? 'Keep integrations healthy'
          : 'Connect your first system',
      description:
        metrics.integrations.overall.activeSystems > 0
          ? 'Review sync status and add new data sources.'
          : 'Add an ERP, CRM, or POS integration to unlock automations.',
      actionLabel:
        metrics.integrations.overall.activeSystems > 0 ? 'Manage integrations' : 'Add integration',
      onAction: () => router.push('/dashboard/si/integrations/new'),
    },
    {
      id: 'invoices',
      icon: '📄',
      title: 'Send invoices to FIRS',
      description: 'Generate APP-ready batches from reconciled data in minutes.',
      actionLabel:
        metrics.compliance.invoicesGenerated > 0 ? 'Open invoice hub' : 'Generate invoice',
      onAction: () => router.push('/dashboard/si/firs-invoicing'),
    },
    {
      id: 'exceptions',
      icon: '🛠️',
      title:
        metrics.reconciliation.exceptions > 0
          ? 'Resolve reconciliation exceptions'
          : 'Monitor exceptions',
      description:
        metrics.reconciliation.exceptions > 0
          ? `${formatNumber(metrics.reconciliation.exceptions)} items need review.`
          : 'We will notify you when manual review is required.',
      actionLabel:
        metrics.reconciliation.exceptions > 0 ? 'Review now' : 'View history',
      onAction: () => router.push('/dashboard/si/reconciliation/exceptions'),
    },
  ];

  const integrationCategories = [
    {
      label: 'ERP systems',
      active: metrics.integrations.erp.active,
      total: metrics.integrations.erp.total,
      helper: `${formatNumber(metrics.integrations.erp.totalCustomers)} customers`,
    },
    {
      label: 'CRM systems',
      active: metrics.integrations.crm.active,
      total: metrics.integrations.crm.total,
      helper: `${formatNumber(metrics.integrations.crm.totalContacts)} contacts`,
    },
    {
      label: 'POS systems',
      active: metrics.integrations.pos.active,
      total: metrics.integrations.pos.total,
      helper: `${formatNumber(metrics.integrations.pos.totalItems)} items tracked`,
    },
    {
      label: 'E-commerce',
      active: metrics.integrations.ecommerce.active,
      total: metrics.integrations.ecommerce.total,
      helper: `${formatNumber(metrics.integrations.ecommerce.totalOrders)} orders`,
    },
  ];

  const complianceSnapshot = [
    {
      label: 'IRNs pending',
      value: formatNumber(irnStatus.pending),
    },
    {
      label: 'Validation pass rate',
      value: `${validationPassRate}%`,
    },
    {
      label: 'Pending submissions',
      value: formatNumber(metrics.compliance.pendingSubmissions),
    },
  ];

  const lastSubmission = irnStatus.lastGeneratedAt
    ? formatDateTime(irnStatus.lastGeneratedAt)
    : metrics.compliance.lastSubmission
    ? formatDateTime(metrics.compliance.lastSubmission)
    : 'Not submitted yet';

  const checklistData = checklistStatus === 'ready' ? checklist : null;
  const onboardingComplete = (checklistData?.summary?.remaining_phases.length ?? 0) === 0;

  const handleResumeOnboarding = useCallback(() => {
    router.push('/onboarding/si/integration-setup');
  }, [router]);

  const handleViewGuidance = useCallback((phaseId: string) => {
    setSelectedGuidancePhase(phaseId);
  }, []);

  const guidancePhase = useMemo(() => {
    if (!selectedGuidancePhase || !checklistData) {
      return null;
    }
    return checklistData.phases.find(phase => phase.id === selectedGuidancePhase) ?? null;
  }, [checklistData, selectedGuidancePhase]);

  useEffect(() => {
    if (!checklistData || selectedGuidancePhase) {
      return;
    }
    const nextPhase = checklistData.phases.find(phase => phase.status !== 'complete');
    if (nextPhase) {
      setSelectedGuidancePhase(nextPhase.id);
    }
  }, [checklistData, selectedGuidancePhase]);

  const checklistBannerMessage = useMemo(() => {
    if (checklistStatus === 'loading') {
      return 'Syncing onboarding checklist…';
    }
    if (checklistStatus === 'error' && checklistError) {
      return checklistError;
    }
    return null;
  }, [checklistError, checklistStatus]);

  const latestValidationLogs = combinedValidationActivity
    .filter((item): item is Record<string, any> => Boolean(item && typeof item === 'object'))
    .slice(0, 3)
    .map((item, index) => {
      const batchId =
        typeof item.batchId === 'string'
          ? item.batchId
          : typeof item.batch_id === 'string'
          ? item.batch_id
          : typeof item.id === 'string'
          ? item.id
          : undefined;
      const status = typeof item.status === 'string' ? item.status : 'unknown';
      const created =
        typeof item.createdAt === 'string'
          ? item.createdAt
          : typeof item.created_at === 'string'
          ? item.created_at
          : undefined;
      const totalsRecord = isPlainObject(item.totals) ? (item.totals as Record<string, unknown>) : {};
      const totalInvoices =
        typeof item.total === 'number'
          ? item.total
          : typeof totalsRecord.total === 'number'
          ? totalsRecord.total
          : typeof item.totalInvoices === 'number'
          ? item.totalInvoices
          : typeof item.invoiceCount === 'number'
          ? item.invoiceCount
          : undefined;

      return {
        id: batchId ?? `validation-${index}`,
        status,
        createdAt: created,
        totalInvoices,
      };
    });

  const cashFlowSummary = metrics.cashFlow as { netFlow?: number; categories?: Record<string, number> };
  const hasCashFlow = Boolean(
    cashFlowSummary &&
      typeof cashFlowSummary.netFlow === 'number' &&
      cashFlowSummary.categories &&
      Object.keys(cashFlowSummary.categories).length > 0
  );

  const cashFlowTopCategories = Object.entries(cashFlowSummary?.categories ?? {})
    .sort(([, a], [, b]) => Number(b ?? 0) - Number(a ?? 0))
    .slice(0, 2);

  const financialHighlights = [
    {
      label: 'Net cash flow',
      value: toMillionsDisplay(cashFlowSummary?.netFlow, 1) ?? '--',
      helper: hasCashFlow ? 'This month' : 'Connect banking to begin tracking',
    },
    {
      label: 'Connected accounts',
      value: formatNumber(metrics.financial.banking.totalAccounts),
      helper: `${formatNumber(metrics.financial.banking.connected)} banking providers`,
    },
    {
      label: 'Payment volume',
      value: toMillionsDisplay(metrics.financial.payments.monthlyVolume, 1) ?? '₦0.0M',
      helper: 'Monthly volume',
    },
  ];

  const activityFeed = useMemo(() => {
    const events: Array<{ title: string; description: string; meta: string; amount?: string }> = [];

    const irnEvents = irnRecent
      .slice(0, 3)
      .map((item) => {
        const irn = typeof item.irn === 'string' ? item.irn : undefined;
        const status = typeof item.status === 'string' ? item.status : 'unknown';
        const created =
          typeof item.createdAt === 'string'
            ? item.createdAt
            : typeof item.created_at === 'string'
            ? item.created_at
            : undefined;
        const qrReady = Boolean(item.qrReady ?? item.qr_ready);
        const qrSigned = Boolean(item.qrSigned ?? item.qr_signed);
        const firsStamped = Boolean(item.firsStamp ?? item.firs_stamp);
        let amount: string | undefined;
        if (firsStamped) {
          amount = 'Stamped';
        } else if (qrSigned) {
          amount = 'QR signed';
        } else if (qrReady) {
          amount = 'QR ready';
        }

        return {
          title: irn ? `IRN ${irn}` : 'IRN submission',
          description: `Status: ${status}`,
          meta: created ? formatDateTime(created) : 'Awaiting acknowledgement',
          amount,
        };
      })
      .filter((entry) => Boolean(entry.title));

    events.push(...irnEvents);

    const validationEvents = combinedValidationActivity
      .slice(0, 3)
      .map((item) => {
        const status = typeof item.status === 'string' ? item.status : 'validation';
        const batchId =
          typeof item.batchId === 'string'
            ? item.batchId
            : typeof item.batch_id === 'string'
            ? item.batch_id
            : undefined;
        const title = batchId ? `Batch ${batchId}` : `Batch ${status}`;
        const created =
          typeof item.updated_at === 'string'
            ? item.updated_at
            : typeof item.createdAt === 'string'
            ? item.createdAt
            : typeof item.created_at === 'string'
            ? item.created_at
            : undefined;
        const totalsRecord = isPlainObject(item.totals) ? (item.totals as Record<string, unknown>) : {};
        const invoiceCount =
          typeof item.total === 'number'
            ? item.total
            : typeof totalsRecord.total === 'number'
            ? totalsRecord.total
            : typeof item.totalInvoices === 'number'
            ? item.totalInvoices
            : undefined;
        const description =
          typeof item.description === 'string'
            ? item.description
            : typeof item.notes === 'string'
            ? item.notes
            : `Validation ${status}`;

        return {
          title,
          description,
          meta: created ? formatDateTime(created) : 'Awaiting schedule',
          amount: typeof invoiceCount === 'number' ? `${invoiceCount.toLocaleString()} invoices` : undefined,
        };
      })
      .filter((entry) => Boolean(entry.title));

    events.push(...validationEvents);

    if (events.length > 0) {
      return events.slice(0, 5);
    }

    return [
      {
        title: 'Connect your first system',
        description: 'Integrate an ERP or CRM to start streaming activity into your workspace.',
        meta: 'Setup',
      },
      {
        title: 'Generate an invoice batch',
        description: 'Use reconciled data to create APP-ready invoices for FIRS submission.',
        meta: 'Compliance',
      },
      {
        title: 'Invite teammates',
        description: 'Give finance and ops teammates access to monitor integrations together.',
        meta: 'Collaboration',
      },
    ];
  }, [combinedValidationActivity, irnRecent]);

  const quickToolCards = [
    {
      title: 'SDK Hub',
      description: 'Download SDKs and access sandbox credentials.',
      actionLabel: 'Open SDK Hub',
      onAction: () => router.push('/dashboard/si/sdk'),
    },
    {
      title: 'Connect banking',
      description: 'Securely link financial accounts for cash-flow automation.',
      actionLabel: metrics.financial.banking.connected > 0 ? 'Manage banking' : 'Connect now',
      onAction: () => router.push('/dashboard/si/financial/connect'),
    },
    {
      title: 'Export audit trail',
      description: 'Download detailed activity logs for compliance reviews.',
      actionLabel: 'Export report',
      onAction: () => router.push('/dashboard/si/audit-trails/export'),
    },
  ];

  return (
    <DashboardLayout
      role="si"
      userName={userName}
      userEmail={userEmail}
      activeTab="dashboard"
      className={className}
    >
      <div style={sectionStyle} className="min-h-full space-y-8">
        {/* Header */}
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h1
              className="text-4xl font-black text-slate-800"
              style={TYPOGRAPHY_STYLES.optimizedText}
            >
              System Integrator Dashboard
            </h1>
            <p
              className="mt-2 text-lg text-slate-600"
              style={TYPOGRAPHY_STYLES.optimizedText}
            >
              Monitor integrations, cash flow, and compliance in one workspace.
              {!hasLiveData && (
                <span className="ml-2 inline-flex items-center rounded-full bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-700">
                  Awaiting live data
                </span>
              )}
            </p>
            {onboardingComplete && (
              <div className="mt-3 inline-flex items-center gap-2 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
                <span>🎉</span>
                <span>Onboarding complete! Continue managing integrations from the actions below.</span>
              </div>
            )}
          </div>
          <div className="flex flex-wrap gap-3">
            <TaxPoyntButton
              variant="primary"
              onClick={() =>
                checklistData?.summary?.remaining_phases.length
                  ? router.push('/onboarding/si/integration-setup')
                  : router.push('/dashboard/si/firs-invoicing')
              }
              className="bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700"
            >
              <span className="mr-2">{checklistData?.summary?.remaining_phases.length ? '🚀' : '📄'}</span>
              {checklistData?.summary?.remaining_phases.length
                ? 'View onboarding guidance'
                : 'Generate first invoice'}
            </TaxPoyntButton>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[320px_1fr] lg:items-start">
          <div className="space-y-4">
            <ChecklistSidebar
              checklist={checklistData}
              onResume={handleResumeOnboarding}
              onViewGuidance={handleViewGuidance}
            />
            {checklistBannerMessage && (
              <p
                className={`text-xs ${checklistStatus === 'error' ? 'text-red-600' : 'text-slate-600'}`}
              >
                {checklistBannerMessage}
              </p>
            )}
            {guidancePhase && (
              <div
                data-testid="checklist-guidance-panel"
                className="rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm text-blue-900"
              >
                <div className="mb-2 flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">Guidance</p>
                    <h4 className="text-sm font-semibold text-blue-900">{guidancePhase.title}</h4>
                    <p className="text-xs text-blue-800">{guidancePhase.description}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSelectedGuidancePhase(null)}
                    className="text-xs font-medium text-blue-700 hover:text-blue-600"
                  >
                    Close
                  </button>
                </div>
                <ul className="space-y-2">
                  {guidancePhase.steps.map(step => (
                    <li key={step.id} className="rounded border border-blue-100 bg-white px-3 py-2 text-xs">
                      <span className="font-semibold text-blue-900">{step.title}</span>
                      {step.success_criteria && (
                        <p className="text-[11px] text-blue-700">Success: {step.success_criteria}</p>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="space-y-8">
            {/* Quick stats */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              {quickStats.map((stat) => (
            <div
              key={stat.label}
              className={`rounded-2xl border ${stat.borderClass} bg-white p-4 shadow-sm`}
            >
              <p className="flex items-center justify-between text-sm text-slate-500">
                <span>{stat.label}</span>
                {stat.onAction && (
                  <button
                    type="button"
                    onClick={stat.onAction}
                    className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-indigo-200 text-indigo-600 hover:bg-indigo-50"
                    aria-label={stat.actionLabel ?? 'Open action'}
                  >
                    {stat.actionIcon ?? '→'}
                  </button>
                )}
              </p>
              <p className={`mt-2 text-2xl font-semibold ${stat.textClass}`}>{stat.value}</p>
              <p className="mt-1 text-xs text-slate-500">{stat.helper}</p>
            </div>
          ))}
        </div>

            {/* Primary focus */}
            <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
          <DashboardCard
            title="Today's focus"
            description="Prioritise the tasks that keep automations healthy."
            icon="🎯"
          >
            <div className="space-y-4">
              {priorityActions.map((item) => (
                <div
                  key={item.id}
                  className="rounded-xl border border-slate-200 bg-slate-50/80 p-4"
                >
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div>
                      <p className="text-sm font-semibold text-slate-800">
                        {item.icon} {item.title}
                      </p>
                      <p className="mt-1 text-sm text-slate-600">{item.description}</p>
                    </div>
                    <TaxPoyntButton variant="outline" size="sm" onClick={item.onAction}>
                      {item.actionLabel}
                    </TaxPoyntButton>
                  </div>
                </div>
              ))}
            </div>
          </DashboardCard>

          <DashboardCard
            title="Integration health"
            description="Snapshot of connected business systems."
            icon="🧩"
            badge={`${metrics.integrations.overall.activeSystems}/${metrics.integrations.overall.totalSystems || 0} active`}
            badgeColor="indigo"
          >
            <div className="space-y-3">
              <div className="rounded-lg border border-indigo-100 bg-indigo-50 px-3 py-2 text-xs text-indigo-700">
                Active {formatNumber(connectionSummary.active)} of {formatNumber(connectionSummary.total)} systems ·{' '}
                {formatNumber(connectionSummary.failing)} failing · {formatNumber(connectionSummary.needsAttention)} flagged
              </div>
              {integrationCategories.map((category) => (
                <div
                  key={category.label}
                  className="flex items-center justify-between rounded-lg border border-slate-100 bg-white px-3 py-2"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-700">{category.label}</p>
                    <p className="text-xs text-slate-500">{category.helper}</p>
                  </div>
                  <span className="text-sm font-semibold text-slate-900">
                    {category.active}/{category.total}
                  </span>
                </div>
              ))}
              {connectionSystems.length > 0 ? (
                <div className="rounded-lg border border-slate-100 bg-white px-3 py-2">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Recent updates</p>
                  <ul className="mt-2 space-y-2">
                    {connectionSystems.slice(0, 3).map((system, index) => {
                      const record = system as Record<string, any>;
                      const systemId =
                        typeof record.id === 'string'
                          ? record.id
                          : typeof record.name === 'string'
                          ? `${record.name}-${index}`
                          : `system-${index}`;
                      const name = typeof record.name === 'string' ? record.name : 'Integration';
                      const status = typeof record.status === 'string' ? record.status : 'unknown';
                      const lastSyncValue =
                        typeof record.lastSync === 'string'
                          ? record.lastSync
                          : typeof record.last_sync === 'string'
                          ? record.last_sync
                          : undefined;
                      const needsAttention = Boolean(record.needsAttention ?? record.needs_attention);
                      const error = typeof record.error === 'string' ? record.error : undefined;

                      return (
                        <li key={systemId} className="flex flex-col rounded-md border border-slate-100 px-3 py-2">
                          <div className="flex items-center justify-between text-sm font-semibold text-slate-800">
                            <span>{name}</span>
                            <span className="text-xs uppercase tracking-wide text-slate-500">{status}</span>
                          </div>
                          <div className="mt-1 text-xs text-slate-500">
                            Last sync: {lastSyncValue ? formatDateTime(lastSyncValue) : 'No sync recorded'}
                          </div>
                          {needsAttention && (
                            <div className="mt-1 text-xs font-semibold text-amber-600">
                              ⚠️ {error ? error : 'Needs attention'}
                            </div>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                </div>
              ) : (
                <div className="rounded-lg border border-dashed border-slate-200 bg-white px-3 py-2 text-xs text-slate-500">
                  Run a connection test to populate recent integration updates.
                </div>
              )}
              <TaxPoyntButton
                variant="outline"
                size="sm"
                className="w-full border-indigo-200 text-indigo-700 hover:bg-indigo-50"
                onClick={() => router.push('/dashboard/si/business-systems')}
              >
                Manage systems
              </TaxPoyntButton>
            </div>
          </DashboardCard>

          <DashboardCard
            title="Compliance readiness"
            description="Ensure you are ready to submit to FIRS."
            icon="✅"
            badge={`${validationPassRate}% pass`}
            badgeColor="emerald"
          >
            <div className="space-y-3">
              {complianceSnapshot.map((item) => (
                <div
                  key={item.label}
                  className="flex items-center justify-between text-sm text-slate-700"
                >
                  <span>{item.label}</span>
                  <span className="font-semibold text-slate-900">{item.value}</span>
                </div>
              ))}
              {latestValidationLogs.length > 0 ? (
                <div className="rounded-lg border border-emerald-100 bg-white px-3 py-2">
                  <p className="text-xs font-semibold uppercase tracking-wide text-emerald-600">Validation logs</p>
                  <ul className="mt-2 space-y-2 text-xs text-emerald-700">
                    {latestValidationLogs.map((log) => (
                      <li key={log.id} className="flex flex-col rounded-md border border-emerald-50 px-2 py-1">
                        <span className="font-semibold text-emerald-700">{log.status}</span>
                        <span className="text-emerald-500">
                          {log.createdAt ? formatDateTime(log.createdAt) : 'Awaiting schedule'}
                        </span>
                        {typeof log.totalInvoices === 'number' && (
                          <span className="text-emerald-500">
                            {log.totalInvoices.toLocaleString()} invoices
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <div className="rounded-lg border border-dashed border-emerald-100 bg-white px-3 py-2 text-xs text-emerald-600">
                  Validation logs will surface here once batches are processed.
                </div>
              )}
              <div className="rounded-lg border border-emerald-100 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
                Last submission: {lastSubmission}
              </div>
              <TaxPoyntButton
                variant="outline"
                size="sm"
                className="w-full border-emerald-200 text-emerald-700 hover:bg-emerald-50"
                onClick={() => router.push('/dashboard/si/compliance')}
              >
                View compliance centre
              </TaxPoyntButton>
            </div>
          </DashboardCard>
        </div>

        {/* Secondary insights */}
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <DashboardCard
            title="Financial snapshot"
            description="Monitor cash flow and payment performance."
            icon="💰"
            badge={
              metrics.financial.banking.connected > 0
                ? `${metrics.financial.banking.connected} providers`
                : undefined
            }
            badgeColor="blue"
          >
            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                {financialHighlights.map((item) => (
                  <div
                    key={item.label}
                    className="rounded-lg border border-blue-100 bg-blue-50/70 p-3"
                  >
                    <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">
                      {item.label}
                    </p>
                    <p className="mt-1 text-lg font-semibold text-blue-900">{item.value}</p>
                    <p className="text-xs text-blue-600">{item.helper}</p>
                  </div>
                ))}
              </div>

              {hasCashFlow ? (
                <div className="rounded-lg border border-blue-100 bg-white p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">
                    Top cash sources
                  </p>
                  <ul className="mt-2 space-y-2">
                    {cashFlowTopCategories.map(([category, amount]) => (
                      <li
                        key={category}
                        className="flex items-center justify-between text-sm text-slate-700"
                      >
                        <span>{category}</span>
                        <span className="font-medium text-slate-900">
                          ₦{Number(amount ?? 0).toLocaleString()}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <div className="rounded-lg border border-dashed border-blue-200 bg-white/70 p-3 text-sm text-blue-700">
                  Connect a banking provider to unlock live cash flow analytics.
                </div>
              )}

              <TaxPoyntButton
                variant="outline"
                size="sm"
                className="border-blue-200 text-blue-700 hover:bg-blue-50"
                onClick={() => router.push('/dashboard/si/financial/connect')}
              >
                Manage financial connections
              </TaxPoyntButton>
            </div>
          </DashboardCard>

          <DashboardCard
            title="Recent activity"
            description="Latest automation events and validation updates."
            icon="🗂️"
          >
            <div className="space-y-3">
              {activityFeed.map((event, index) => (
                <div
                  key={`${event.title}-${index}`}
                  className="rounded-lg border border-slate-100 bg-white px-3 py-2 shadow-sm"
                >
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold text-slate-800">{event.title}</p>
                    {event.amount && (
                      <span className="text-xs font-medium text-slate-500">{event.amount}</span>
                    )}
                  </div>
                  <p className="mt-1 text-sm text-slate-600">{event.description}</p>
                  <p className="mt-1 text-xs uppercase tracking-wide text-slate-400">{event.meta}</p>
                </div>
              ))}
            </div>
          </DashboardCard>
        </div>

        {/* Tools & resources */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {quickToolCards.map((tool) => (
                <div
                  key={tool.title}
                  className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
                >
              <h3 className="text-sm font-semibold text-slate-800">{tool.title}</h3>
              <p className="mt-2 text-sm text-slate-600">{tool.description}</p>
              <TaxPoyntButton
                variant="outline"
                size="sm"
                className="mt-4 border-slate-200 text-indigo-700 hover:bg-indigo-50"
                onClick={tool.onAction}
              >
                {tool.actionLabel}
              </TaxPoyntButton>
            </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};
