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

const isPlainObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const mergeDeep = <T,>(target: T, source: Partial<T>): T => {
  if (source === undefined || source === null) {
    return target;
  }

  if (Array.isArray(source)) {
    return source.slice() as unknown as T;
  }

  if (isPlainObject(source)) {
    const base: Record<string, unknown> = isPlainObject(target)
      ? { ...(target as Record<string, unknown>) }
      : {};

    for (const [key, value] of Object.entries(source)) {
      const existing = isPlainObject(target)
        ? (target as Record<string, unknown>)[key]
        : undefined;
      base[key] = mergeDeep(existing as unknown, value as unknown);
    }

    return base as T;
  }

  return source as unknown as T;
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

const formatNumber = (value?: number): string => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '0';
  }
  return value.toLocaleString();
};

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
    lastUpdated: undefined,
    processing: {
      rate: 0,
      success: 0,
      queue: 0,
      apiLatency: 0,
      uptime: 0,
    },
    cashFlow: undefined,
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
          setMetrics((prev) => mergeDeep(prev, response.data));
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

  const validationSummary = metrics.validation?.summary ?? { totals: { total: 0, passed: 0, failed: 0 } };
  const validationTotals = validationSummary.totals ?? { total: 0, passed: 0, failed: 0 };
  const validationPassRate = validationTotals.total
    ? Math.round(((validationTotals.passed ?? 0) / validationTotals.total) * 100)
    : 0;
  const validationRecent = metrics.validation?.recentBatches ?? [];

  const quickStats = [
    {
      label: 'Active systems',
      value:
        metrics.integrations.overall.totalSystems > 0
          ? `${metrics.integrations.overall.activeSystems}/${metrics.integrations.overall.totalSystems}`
          : formatNumber(metrics.integrations.overall.activeSystems),
      helper:
        metrics.integrations.overall.totalSystems > 0
          ? `${toPercentDisplay(metrics.integrations.overall.overallHealthScore) ?? '--'} health`
          : 'No systems connected yet',
      textClass: 'text-indigo-600',
      borderClass: 'border-indigo-100',
    },
    {
      label: 'Auto-reconciled today',
      value: formatNumber(metrics.reconciliation.autoReconciled),
      helper: toPercentDisplay(metrics.reconciliation.successRate) ?? 'Start reconciliation to track progress',
      textClass: 'text-emerald-600',
      borderClass: 'border-emerald-100',
    },
    {
      label: 'FIRS invoices ready',
      value: formatNumber(metrics.compliance.invoicesGenerated),
      helper: `${formatNumber(metrics.compliance.pendingSubmissions)} pending submissions`,
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
      label: 'VAT transactions',
      value: formatNumber(metrics.compliance.vatTransactions),
    },
    {
      label: 'Pending submissions',
      value: formatNumber(metrics.compliance.pendingSubmissions),
    },
    {
      label: 'Validation pass rate',
      value: `${validationPassRate}%`,
    },
  ];

  const lastSubmission = metrics.compliance.lastSubmission
    ? formatDateTime(metrics.compliance.lastSubmission)
    : 'Not submitted yet';

  const hasCashFlow = Boolean(
    metrics.cashFlow &&
      typeof metrics.cashFlow === 'object' &&
      (typeof metrics.cashFlow.netFlow === 'number' ||
        (metrics.cashFlow.categories && Object.keys(metrics.cashFlow.categories).length > 0))
  );

  const cashFlowTopCategories = Object.entries(
    (metrics.cashFlow?.categories as Record<string, number> | undefined) ?? {}
  )
    .sort(([, a], [, b]) => Number(b ?? 0) - Number(a ?? 0))
    .slice(0, 2);

  const financialHighlights = [
    {
      label: 'Net cash flow',
      value: toMillionsDisplay(metrics.cashFlow?.netFlow, 1) ?? '--',
      helper: metrics.cashFlow ? 'This month' : 'Connect banking to begin tracking',
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
    const normalized = (Array.isArray(validationRecent) ? validationRecent : [])
      .slice(0, 3)
      .map((item) => {
        if (!item || typeof item !== 'object') {
          return null;
        }
        const record = item as Record<string, unknown>;
        const title =
          typeof record.title === 'string'
            ? record.title
            : typeof record.status === 'string'
            ? `Batch ${record.status}`
            : 'Validation batch';
        const description =
          typeof record.description === 'string'
            ? record.description
            : typeof record.notes === 'string'
            ? record.notes
            : 'Validation batch status update';
        const timestamp =
          typeof record.updated_at === 'string'
            ? record.updated_at
            : typeof record.created_at === 'string'
            ? record.created_at
            : undefined;
        const invoiceCount =
          typeof record.total_invoices === 'number'
            ? record.total_invoices
            : typeof record.totalInvoices === 'number'
            ? record.totalInvoices
            : undefined;

        return {
          title,
          description,
          meta: timestamp ? formatDateTime(timestamp) : 'Awaiting schedule',
          amount: typeof invoiceCount === 'number' ? `${invoiceCount.toLocaleString()} invoices` : undefined,
        };
      })
      .filter(
        (
          entry,
        ): entry is { title: string; description: string; meta: string; amount?: string } => Boolean(entry && entry.title)
      );

    if (normalized.length > 0) {
      return normalized;
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
  }, [validationRecent]);

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
          </div>
          <div className="flex flex-wrap gap-3">
            <TaxPoyntButton
              variant="outline"
              onClick={() => router.push('/dashboard/si/integrations/new')}
              className="border-2 border-indigo-300 text-indigo-700 hover:bg-indigo-50"
            >
              <span className="mr-2">➕</span>
              Add Integration
            </TaxPoyntButton>
            <TaxPoyntButton
              variant="primary"
              onClick={() => router.push('/dashboard/si/setup')}
              className="bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700"
            >
              <span className="mr-2">⚙️</span>
              System Setup
            </TaxPoyntButton>
          </div>
        </div>

        {/* Quick stats */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          {quickStats.map((stat) => (
            <div
              key={stat.label}
              className={`rounded-2xl border ${stat.borderClass} bg-white p-4 shadow-sm`}
            >
              <p className="text-sm text-slate-500">{stat.label}</p>
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
    </DashboardLayout>
  );
};
