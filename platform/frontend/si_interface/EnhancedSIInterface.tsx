/**
 * Enhanced System Integrator (SI) Interface
 * ==========================================
 * 
 * Professional SI dashboard enhanced with our unified design system.
 * Maintains all existing functionality while providing modern UI/UX.
 */

import React, { useState, useEffect, useCallback } from 'react';
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

  const handleCardClick = (_cardId: string, route?: string) => {
    if (route) {
      router.push(route);
    }
  };

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
  const validationStatusEntries = Object.entries(validationSummary.statusCounts ?? {});

  return (
    <DashboardLayout
      role="si"
      userName={userName}
      userEmail={userEmail}
      activeTab="dashboard"
      className={className}
    >
      <div style={sectionStyle} className="min-h-full">
        
        {/* Header Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 
                className="text-4xl font-black text-slate-800 mb-2"
                style={TYPOGRAPHY_STYLES.optimizedText}
              >
                System Integrator Dashboard
              </h1>
              <p 
                className="text-xl text-slate-600"
                style={TYPOGRAPHY_STYLES.optimizedText}
              >
                Manage business system integrations and automated e-invoicing workflows
                {!hasLiveData && (
                  <span className="ml-2 rounded-full bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-700">
                    Awaiting live data
                  </span>
                )}
              </p>
            </div>
            
            <div className="flex space-x-4">
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

          {/* Enhanced Quick Stats Bar - Business & Financial Integration Focus */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
            {[
              {
                label: 'Active Systems',
                value:
                  metrics.integrations.overall.totalSystems > 0
                    ? `${metrics.integrations.overall.activeSystems}/${metrics.integrations.overall.totalSystems}`
                    : `${metrics.integrations.overall.activeSystems}`,
                color: 'indigo',
                subtext: hasLiveData
                  ? `${toPercentDisplay(metrics.integrations.overall.overallHealthScore) ?? '--'} health`
                  : 'Connect your first integration',
              },
              {
                label: 'Auto-Reconciled',
                value: Number(metrics.reconciliation.autoReconciled ?? 0).toLocaleString(),
                color: 'emerald',
                subtext:
                  toPercentDisplay(metrics.reconciliation.successRate) ?? 'Awaiting reconciliation data',
              },
              {
                label: 'Net Cash Flow',
                value: toMillionsDisplay(metrics.cashFlow?.netFlow) ?? '--',
                color: 'green',
                subtext: metrics.cashFlow ? 'This month' : 'Connect banking data',
              },
              {
                label: 'FIRS Invoices',
                value: Number(metrics.compliance.invoicesGenerated ?? 0).toLocaleString(),
                color: 'blue',
                subtext: `${metrics.compliance.pendingSubmissions} pending`,
              },
              {
                label: 'Compliance Score',
                value: toPercentDisplay(metrics.compliance.complianceScore) ?? '--',
                color: 'purple',
                subtext: metrics.compliance.firsStatus ?? 'Status unavailable',
              },
            ].map((stat, index) => (
              <div 
                key={index}
                className={`bg-white p-4 rounded-xl shadow-lg border border-${stat.color}-100 hover:shadow-xl transition-shadow`}
              >
                <div className={`text-2xl font-black text-${stat.color}-600 mb-1`}>
                  {stat.value}
                </div>
                <div className="text-sm text-slate-700 font-medium mb-1">
                  {stat.label}
                </div>
                <div className="text-xs text-slate-500">
                  {stat.subtext}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Main Dashboard Grid - Financial Integration Hub */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          
          {/* Auto-Reconciliation Center - PRIMARY FOCUS */}
          <DashboardCard
            title="Auto-Reconciliation Hub"
            description="Automatic transaction matching and categorization with AI"
            icon="🤖"
            badge={`${metrics.reconciliation.autoReconciled} reconciled`}
            badgeColor="emerald"
            variant="success"
            onClick={() => handleCardClick('reconciliation', '/dashboard/si/reconciliation')}
            className="hover:scale-102 transition-transform border-2 border-emerald-200"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-emerald-600">High Confidence</span>
                <span className="font-bold text-emerald-700">{metrics.reconciliation.confidenceScores.high}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-emerald-600">Medium Confidence</span>
                <span className="font-bold text-amber-600">{metrics.reconciliation.confidenceScores.medium}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-emerald-600">Manual Review</span>
                <span className="font-bold text-red-600">{metrics.reconciliation.manualReview}</span>
              </div>
              
              <div className="pt-3 border-t border-emerald-100">
                <div className="flex items-center space-x-2">
                  <div className="w-full bg-emerald-100 rounded-full h-3">
                    <div 
                      className="bg-gradient-to-r from-emerald-500 to-green-500 h-3 rounded-full transition-all duration-500"
                      style={{ width: `${metrics.reconciliation.successRate}%` }}
                    ></div>
                  </div>
                  <span className="text-xs text-emerald-600 font-bold">
                    {metrics.reconciliation.successRate}%
                  </span>
                </div>
                <div className="text-center mt-2">
                  <span className="text-xs text-emerald-700 font-medium">Success Rate</span>
                </div>
              </div>
            </div>
          </DashboardCard>

          {/* Real-time Cash Flow */}
          <DashboardCard
            title="Real-time Cash Flow"
            description="Categorized cash flow from all connected financial systems"
            icon="💰"
            badge={toMillionsDisplay(metrics.cashFlow?.netFlow) ?? '--'}
            badgeColor="green"
            variant="highlight"
            onClick={() => handleCardClick('cashflow', '/dashboard/si/cashflow')}
            className="hover:scale-102 transition-transform"
          >
            {metrics.cashFlow ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-green-600">Inflow</span>
                  <span className="font-bold text-green-700">{toMillionsDisplay(metrics.cashFlow.inflow)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-red-600">Outflow</span>
                  <span className="font-bold text-red-600">{toMillionsDisplay(metrics.cashFlow.outflow)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-blue-600">Banking Providers</span>
                  <span className="font-bold text-blue-700">{metrics.financial.banking.connected}</span>
                </div>
                
                <div className="pt-3 border-t border-gray-100">
                  <div className="grid grid-cols-2 gap-2 text-center">
                    <div>
                      <div className="text-lg font-bold text-green-600">
                        {toMillionsDisplay(metrics.cashFlow.categories['Sales Revenue'], 0) ?? '--'}
                      </div>
                      <div className="text-xs text-slate-500">Sales</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-blue-600">
                        {toMillionsDisplay(metrics.cashFlow.categories['Service Revenue'], 0) ?? '--'}
                      </div>
                      <div className="text-xs text-slate-500">Services</div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-lg bg-green-50 p-4 text-sm text-green-700">
                Connect a banking provider to unlock cash flow monitoring and SLA tracking.
              </div>
            )}
          </DashboardCard>

          {/* FIRS Invoice Generation Hub */}
          <DashboardCard
            title="FIRS Invoice Hub"
            description="Generate FIRS-compliant invoices from integrated business systems"
            icon="📋"
            badge={`${metrics.compliance.invoicesGenerated} generated`}
            badgeColor="blue"
            variant="highlight"
            onClick={() => handleCardClick('firs-invoicing', '/dashboard/si/firs-invoicing')}
            className="hover:scale-102 transition-transform border-2 border-blue-200"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-blue-600">Invoice Generation</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-green-600 font-medium text-sm">Active</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-blue-600">VAT Transactions</span>
                <span className="font-bold text-blue-700">{Number(metrics.compliance.vatTransactions ?? 0).toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-blue-600">Ready for APP Submission</span>
                <span className="font-bold text-green-600">{metrics.compliance.invoicesGenerated}</span>
              </div>
              
              <div className="pt-3 border-t border-blue-100">
                <TaxPoyntButton
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    router.push('/dashboard/si/firs-invoicing/generate');
                  }}
                  className="w-full border-blue-300 text-blue-700 hover:bg-blue-50"
                >
                  Generate Invoice Batch
                </TaxPoyntButton>
              </div>
            </div>
          </DashboardCard>

          {/* Exception Reports & Manual Review */}
          <DashboardCard
            title="Exception Reports"
            description="Transactions requiring manual review and compliance verification"
            icon="⚠️"
            badge={`${metrics.reconciliation.exceptions} exceptions`}
            badgeColor="orange"
            onClick={() => handleCardClick('exceptions', '/dashboard/si/exceptions')}
            className="hover:scale-102 transition-transform"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-orange-600">Manual Review</span>
                <span className="font-bold text-orange-700">{metrics.reconciliation.manualReview}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-orange-600">Low Confidence</span>
                <span className="font-bold text-red-600">{metrics.reconciliation.confidenceScores.low}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-orange-600">Compliance Issues</span>
                <span className="font-bold text-amber-600">0</span>
              </div>
              
              <div className="pt-3 border-t border-orange-100">
                <TaxPoyntButton
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    router.push('/dashboard/si/exceptions/review');
                  }}
                  className="w-full border-orange-300 text-orange-700 hover:bg-orange-50"
                >
                  Review Exceptions
                </TaxPoyntButton>
              </div>
            </div>
          </DashboardCard>

          {/* Financial Systems Integration */}
          <DashboardCard
            title="Financial Systems"
            description="Banking and payment processor integrations for real-time data"
            icon="🏦"
            badge={`${metrics.financial.banking.connected + metrics.financial.payments.connected} connected`}
            badgeColor="blue"
            variant="highlight"
            onClick={() => handleCardClick('financial', '/dashboard/si/financial')}
            className="hover:scale-102 transition-transform"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-blue-600">Banking (Mono)</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-green-600 font-medium text-sm">{metrics.financial.banking.totalAccounts} accounts</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-blue-600">Payment Processors</span>
                <span className="font-bold text-green-600">{metrics.financial.payments.connected} active</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-blue-600">Monthly Volume</span>
                <span className="font-bold text-blue-700">₦{(metrics.financial.payments.monthlyVolume / 1000000).toFixed(0)}M</span>
              </div>
              
              <div className="pt-3 border-t border-blue-100">
                <TaxPoyntButton
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    router.push('/dashboard/si/financial/connect');
                  }}
                  className="w-full border-blue-300 text-blue-700 hover:bg-blue-50"
                >
                  Add Integration
                </TaxPoyntButton>
              </div>
            </div>
          </DashboardCard>

          {/* Enhanced Business Systems Integration */}
          <DashboardCard
            title="Business Systems Hub"
            description="Comprehensive ERP, CRM, POS & E-commerce integrations with real-time data flow"
            icon="🏢"
            badge={`${metrics.integrations.overall.activeSystems}/${metrics.integrations.overall.totalSystems} active`}
            badgeColor="indigo"
            variant="highlight"
            onClick={() => handleCardClick('business-systems', '/dashboard/si/business-systems')}
            className="hover:scale-102 transition-transform border-2 border-indigo-200"
          >
            <div className="space-y-3">
              {/* System Categories Overview */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-indigo-50 p-3 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-indigo-700">🏢 ERP Systems</span>
                    <span className="text-xs font-bold text-indigo-600">{metrics.integrations.erp.active}/{metrics.integrations.erp.total}</span>
                  </div>
                  <div className="text-xs text-indigo-600 space-y-1">
                    <div>📊 {Number(metrics.integrations.erp.totalCustomers ?? 0).toLocaleString()} customers</div>
                    <div>📋 {Number(metrics.integrations.erp.totalInvoices ?? 0).toLocaleString()} invoices</div>
                  </div>
                </div>
                
                <div className="bg-green-50 p-3 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-green-700">👥 CRM Systems</span>
                    <span className="text-xs font-bold text-green-600">{metrics.integrations.crm.active}/{metrics.integrations.crm.total}</span>
                  </div>
                  <div className="text-xs text-green-600 space-y-1">
                    <div>👤 {Number(metrics.integrations.crm.totalContacts ?? 0).toLocaleString()} contacts</div>
                    <div>💰 ₦{(metrics.integrations.crm.pipelineValue / 1000000).toFixed(0)}M pipeline</div>
                  </div>
                </div>
                
                <div className="bg-purple-50 p-3 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-purple-700">🛒 POS Systems</span>
                    <span className="text-xs font-bold text-purple-600">{metrics.integrations.pos.active}/{metrics.integrations.pos.total}</span>
                  </div>
                  <div className="text-xs text-purple-600 space-y-1">
                    <div>💳 ₦{(metrics.integrations.pos.dailySales / 1000).toFixed(0)}K today</div>
                    <div>📦 {metrics.integrations.pos.totalItems} items</div>
                  </div>
                </div>
                
                <div className="bg-orange-50 p-3 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-orange-700">🌐 E-commerce</span>
                    <span className="text-xs font-bold text-orange-600">{metrics.integrations.ecommerce.active}/{metrics.integrations.ecommerce.total}</span>
                  </div>
                  <div className="text-xs text-orange-600 space-y-1">
                    <div>📦 {metrics.integrations.ecommerce.totalOrders} orders</div>
                    <div>👥 {Number(metrics.integrations.ecommerce.totalCustomers ?? 0).toLocaleString()} customers</div>
                  </div>
                </div>
              </div>

              {/* System Health & Performance */}
              <div className="pt-3 border-t border-indigo-100">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-indigo-700">System Health</span>
                  <span className="text-sm font-bold text-green-600">{metrics.integrations.overall.overallHealthScore}%</span>
                </div>
                
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div>
                    <div className="text-lg font-bold text-indigo-600">{(metrics.integrations.overall.totalDataPoints / 1000).toFixed(0)}K</div>
                    <div className="text-xs text-slate-500">Data Points</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-green-600">{metrics.integrations.overall.syncEfficiency}%</div>
                    <div className="text-xs text-slate-500">Sync Rate</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-blue-600">{metrics.integrations.overall.errorRate}%</div>
                    <div className="text-xs text-slate-500">Error Rate</div>
                  </div>
                </div>
              </div>

              {/* Connected Systems Status */}
              <div className="pt-3 border-t border-gray-100">
                <div className="text-sm font-medium text-slate-700 mb-2">🔗 Active Connections</div>
                <div className="space-y-1">
                  {metrics.integrations.erp.systems.map((system, index) => (
                    <div key={index} className="flex items-center justify-between text-xs">
                      <span className="text-slate-600">{system}</span>
                      <div className="flex items-center">
                        <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                        <span className="text-green-600 font-medium">Active</span>
                      </div>
                    </div>
                  ))}
                  {metrics.integrations.crm.systems.map((system, index) => (
                    <div key={index} className="flex items-center justify-between text-xs">
                      <span className="text-slate-600">{system}</span>
                      <div className="flex items-center">
                        <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                        <span className="text-green-600 font-medium">Active</span>
                      </div>
                    </div>
                  ))}
                  {metrics.integrations.pos.systems.map((system, index) => (
                    <div key={index} className="flex items-center justify-between text-xs">
                      <span className="text-slate-600">{system}</span>
                      <div className="flex items-center">
                        <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                        <span className="text-green-600 font-medium">Active</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-3 border-t border-indigo-100">
                <TaxPoyntButton
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    router.push('/dashboard/si/business-systems/manage');
                  }}
                  className="w-full border-indigo-300 text-indigo-700 hover:bg-indigo-50"
                >
                  Manage Business Systems
                </TaxPoyntButton>
              </div>
            </div>
          </DashboardCard>

          {/* Audit Trails & Compliance */}
          <DashboardCard
            title="Audit Trails"
            description="Complete audit trails for all automated reconciliation actions"
            icon="📋"
            badge="Real-time Tracking"
            badgeColor="purple"
            onClick={() => handleCardClick('audit-trails', '/dashboard/si/audit-trails')}
            className="hover:scale-102 transition-transform"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-purple-600">Actions Logged</span>
                <span className="font-bold text-purple-700">{metrics.reconciliation.autoReconciled + metrics.reconciliation.manualReview}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-purple-600">Compliance Score</span>
                <span className="font-bold text-green-600">{metrics.compliance.complianceScore}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-purple-600">Last Audit</span>
                <span className="font-bold text-blue-600">2 hours ago</span>
              </div>
              
              <div className="pt-3 border-t border-purple-100">
                <TaxPoyntButton
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    router.push('/dashboard/si/audit-trails/export');
                  }}
                  className="w-full border-purple-300 text-purple-700 hover:bg-purple-50"
                >
                  Export Audit Report
                </TaxPoyntButton>
              </div>
            </div>
          </DashboardCard>

          {/* System Performance */}
          <DashboardCard
            title="System Performance"
            description="Monitor API performance and system health metrics"
            icon="⚡"
            badge={`${metrics.processing.uptime}% Uptime`}
            badgeColor="green"
            onClick={() => handleCardClick('performance', '/dashboard/si/performance')}
            className="hover:scale-102 transition-transform"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">API Latency</span>
                <span className="font-bold text-green-600">{metrics.processing.apiLatency}ms</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Processing Rate</span>
                <span className="font-bold text-blue-600">{metrics.processing.rate}/hr</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Queue Status</span>
                <span className="font-bold text-orange-600">{metrics.processing.queue} pending</span>
              </div>
              
              <div className="pt-3 border-t border-gray-100">
                <div className="text-center">
                  <div className="text-2xl font-black text-green-600 mb-1">
                    {metrics.processing.uptime}%
                  </div>
                  <div className="text-xs text-green-700">System Uptime</div>
                </div>
              </div>
            </div>
          </DashboardCard>
        </div>

        {/* SDK Hub Quick Access */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-2xl shadow-lg p-6 mb-8 text-white">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h2 
                className="text-2xl font-bold text-white mb-2"
                style={TYPOGRAPHY_STYLES.optimizedText}
              >
                🚀 SDK Hub - Integration Made Easy
              </h2>
              <p className="text-blue-100 mb-4">
                Download, test, and integrate TaxPoynt SDKs for seamless business system connectivity
              </p>
              <div className="flex items-center space-x-4 text-sm text-blue-200">
                <span>📦 Multiple Languages</span>
                <span>🧪 Interactive Testing</span>
                <span>📚 Comprehensive Docs</span>
                <span>🔗 Ready-to-Use Examples</span>
              </div>
            </div>
            <div className="flex space-x-3">
              <TaxPoyntButton
                variant="outline"
                size="lg"
                onClick={() => router.push('/dashboard/si/sdk-hub')}
                className="border-white text-white hover:bg-white hover:text-blue-700"
              >
                🚀 Access SDK Hub
              </TaxPoyntButton>
              <TaxPoyntButton
                variant="primary"
                size="lg"
                onClick={() => router.push('/dashboard/si/sdk-sandbox')}
                className="bg-white text-blue-700 hover:bg-gray-100"
              >
                🧪 Test SDKs
              </TaxPoyntButton>
            </div>
          </div>
        </div>

        {/* Auto-Reconciled Transactions - Real-time Financial Data Convergence */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8 border-l-4 border-emerald-500">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 
                className="text-2xl font-bold text-slate-800 mb-2"
                style={TYPOGRAPHY_STYLES.optimizedText}
              >
                🤖 Auto-Reconciled Transactions
              </h2>
              <p className="text-slate-600">Real-time transaction matching from business and financial systems</p>
            </div>
            <div className="flex space-x-3">
              <TaxPoyntButton
                variant="outline"
                size="sm"
                onClick={() => router.push('/dashboard/si/reconciliation/exceptions')}
                className="border-orange-300 text-orange-700 hover:bg-orange-50"
              >
                Review Exceptions ({metrics.reconciliation.exceptions})
              </TaxPoyntButton>
              <TaxPoyntButton
                variant="primary"
                size="sm"
                onClick={() => router.push('/dashboard/si/reconciliation')}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                View All Reconciled
              </TaxPoyntButton>
            </div>
          </div>
          
          <div className="space-y-4">
            {[
              { 
                time: '2 minutes ago', 
                action: 'Business system data reconciled', 
                details: 'SAP ERP → Salesforce CRM → Invoice #INV-2024-1456',
                amount: '₦1,250,000',
                confidence: 'High (98.7%)',
                category: 'Sales Revenue',
                status: 'reconciled',
                sources: ['SAP ERP', 'Salesforce CRM', 'Mono Banking']
              },
              { 
                time: '8 minutes ago', 
                action: 'Multi-system transaction matched', 
                details: 'Shopify POS → Square POS → Customer Payment',
                amount: '₦890,500',
                confidence: 'High (97.3%)',
                category: 'Service Revenue',
                status: 'reconciled',
                sources: ['Shopify POS', 'Square POS', 'Paystack']
              },
              { 
                time: '12 minutes ago', 
                action: 'ERP expense auto-categorized', 
                details: 'Odoo ERP → Operating expense tracking',
                amount: '₦156,800',
                confidence: 'Medium (85.2%)',
                category: 'Operating Expenses',
                status: 'reconciled',
                sources: ['Odoo ERP', 'GTBank', 'Accounting System']
              },
              { 
                time: '25 minutes ago', 
                action: 'E-commerce order processed', 
                details: 'Shopify Store → FIRS-compliant invoice generated',
                amount: '₦2,340,000',
                confidence: 'High (99.1%)',
                category: 'Sales Revenue',
                status: 'invoice-generated',
                sources: ['Shopify Store', 'SAP ERP', 'Invoice Generator']
              },
              { 
                time: '35 minutes ago', 
                action: 'CRM pipeline converted', 
                details: 'Salesforce deal → Customer onboarding complete',
                amount: '₦3,450,000',
                confidence: 'High (96.8%)',
                category: 'Service Revenue',
                status: 'reconciled',
                sources: ['Salesforce CRM', 'Odoo ERP', 'Mono Banking']
              }
            ].map((activity, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors border border-gray-200">
                <div className="flex items-center space-x-4">
                  <div className={`w-3 h-3 rounded-full ${
                    activity.status === 'reconciled' ? 'bg-emerald-500' : 
                    activity.status === 'invoice-generated' ? 'bg-blue-500' : 'bg-orange-500'
                  }`}></div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-1">
                      <div className="font-semibold text-slate-800">{activity.action}</div>
                      <span className="px-2 py-1 text-xs font-medium bg-emerald-100 text-emerald-700 rounded-full">
                        {activity.confidence}
                      </span>
                    </div>
                    <div className="text-sm text-slate-600 mb-1">{activity.details}</div>
                    <div className="flex items-center space-x-4 text-xs text-slate-500">
                      <span>📊 {activity.category}</span>
                      <span>🔗 {activity.sources.join(' + ')}</span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-slate-800">{activity.amount}</div>
                  <div className="text-sm text-slate-500">{activity.time}</div>
                </div>
              </div>
            ))}
          </div>
          
          {/* Summary bar */}
          <div className="mt-6 p-4 bg-emerald-50 rounded-lg border border-emerald-200">
            <div className="grid grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-lg font-bold text-emerald-600">{metrics.reconciliation.autoReconciled}</div>
                <div className="text-xs text-emerald-700">Auto-Reconciled Today</div>
              </div>
              <div>
                <div className="text-lg font-bold text-amber-600">{metrics.reconciliation.manualReview}</div>
                <div className="text-xs text-amber-700">Pending Review</div>
              </div>
              <div>
                <div className="text-lg font-bold text-blue-600">{metrics.compliance.invoicesGenerated}</div>
                <div className="text-xs text-blue-700">FIRS Invoices Generated</div>
              </div>
              <div>
                <div className="text-lg font-bold text-green-600">{metrics.reconciliation.successRate}%</div>
                <div className="text-xs text-green-700">Success Rate</div>
              </div>
            </div>
          </div>
        </div>

        {/* Validation Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <DashboardCard
            title="Validation Performance"
            description="Recent validation batches for APP-ready invoices"
            icon="🧪"
            badge={`${validationTotals.total ?? 0} invoices`}
            badgeColor="indigo"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-indigo-600">Pass Rate</span>
                <span className="text-2xl font-black text-indigo-600">{validationPassRate}%</span>
              </div>
              <div className="flex items-center justify-between text-sm text-slate-600">
                <span>Accepted</span>
                <span className="font-medium text-emerald-600">{validationTotals.passed ?? 0}</span>
              </div>
              <div className="flex items-center justify-between text-sm text-slate-600">
                <span>Failed</span>
                <span className="font-medium text-rose-600">{validationTotals.failed ?? 0}</span>
              </div>
              <div className="pt-3">
                {validationStatusEntries.length > 0 ? (
                  <div className="space-y-2">
                    {validationStatusEntries.map(([status, count]) => {
                      const share = validationTotals.total
                        ? Math.round(((count ?? 0) / (validationTotals.total || 1)) * 100)
                        : 0;
                      const barWidth = Math.min(share, 100);
                      return (
                        <div key={status}>
                          <div className="flex items-center justify-between text-xs text-slate-500">
                            <span className="capitalize text-slate-600">{status}</span>
                            <span className="font-medium text-slate-800">{count ?? 0}</span>
                          </div>
                          <div className="mt-1 h-2 w-full rounded-full bg-indigo-100">
                            <div
                              className="h-2 rounded-full bg-indigo-500 transition-all"
                              style={{ width: `${barWidth}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="rounded-lg bg-indigo-50 p-3 text-xs text-indigo-700">
                    Validation history will appear here once batches are processed.
                  </div>
                )}
              </div>
              <div className="pt-3 border-t border-indigo-100 text-sm text-slate-600">
                <div className="flex items-center justify-between">
                  <span>Last Run</span>
                  <span className="font-medium text-slate-800">{formatDateTime(validationSummary.lastRunAt)}</span>
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span>SLA Threshold</span>
                  <span className="font-medium text-slate-800">{metrics.validation?.slaHours ?? 4} hours</span>
                </div>
              </div>
            </div>
          </DashboardCard>

          <DashboardCard
            title="Recent Validation Batches"
            description="Preview of batches routed for APP transmission"
            icon="📋"
          >
            <div className="space-y-3">
              {validationRecent.length > 0 ? (
                validationRecent.slice(0, 5).map((batch, index) => {
                  const totals = batch.totals ?? {};
                  return (
                    <div key={`${batch.batchId ?? 'batch'}-${index}`} className="bg-slate-50 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-slate-800">{batch.batchId ?? 'Unknown Batch'}</span>
                        <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${batch.status === 'failed' ? 'bg-rose-100 text-rose-700' : batch.status === 'completed' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-700'}`}>
                          {batch.status ?? 'pending'}
                        </span>
                      </div>
                      <div className="text-xs text-slate-600">
                        {formatDateTime(batch.createdAt)} · {totals.total ?? 0} invoices (✔ {totals.passed ?? 0} · ✖ {totals.failed ?? 0})
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="text-sm text-slate-500">No validation batches available yet.</div>
              )}
            </div>
          </DashboardCard>
        </div>

        {/* Financial Integration Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[
            {
              title: 'Generate FIRS Invoice',
              description: 'Create compliant invoices from reconciled data',
              icon: '📋',
              action: () => router.push('/dashboard/si/firs-invoice-generator'),
              color: 'blue',
              highlight: true
            },
            {
              title: 'Connect Banking',
              description: 'Add new banking integration',
              icon: '🏦',
              action: () => router.push('/dashboard/si/financial/banking/connect'),
              color: 'emerald'
            },
            {
              title: 'Review Exceptions',
              description: 'Manual review pending transactions',
              icon: '⚠️',
              action: () => router.push('/dashboard/si/reconciliation/exceptions'),
              color: 'orange',
              badge: metrics.reconciliation.exceptions
            },
            {
              title: 'Export Audit Trail',
              description: 'Download compliance reports',
              icon: '📊',
              action: () => router.push('/dashboard/si/audit-trails/export'),
              color: 'purple'
            }
          ].map((quickAction, index) => (
            <div
              key={index}
              className={`bg-white border rounded-xl p-6 cursor-pointer hover:shadow-lg hover:scale-105 transition-all duration-200 relative ${
                quickAction.highlight 
                  ? `border-${quickAction.color}-300 bg-gradient-to-br from-${quickAction.color}-50 to-white border-2` 
                  : `border-${quickAction.color}-200`
              }`}
              onClick={quickAction.action}
            >
              {quickAction.badge && (
                <div className="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center">
                  {quickAction.badge}
                </div>
              )}
              <div className="text-center">
                <div className="text-4xl mb-3">{quickAction.icon}</div>
                <h3 className={`text-lg font-bold text-${quickAction.color}-800 mb-2`}>
                  {quickAction.title}
                </h3>
                <p className="text-sm text-slate-600">
                  {quickAction.description}
                </p>
                {quickAction.highlight && (
                  <div className="mt-3">
                    <span className={`px-3 py-1 text-xs font-medium bg-${quickAction.color}-100 text-${quickAction.color}-700 rounded-full`}>
                      Primary Action
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
};
