/**
 * Enhanced Hybrid Interface with Real API Integration
 * ==================================================
 * 
 * Professional Hybrid dashboard that combines SI and APP capabilities
 * with real API calls and demo fallback pattern.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardLayout } from '../shared_components/layouts/DashboardLayout';
import { DashboardCard } from '../shared_components/dashboard/DashboardCard';
import { TaxPoyntButton } from '../design_system';
import { 
  TYPOGRAPHY_STYLES, 
  combineStyles
} from '../design_system/style-utilities';
import apiClient from '../shared_components/api/client';
import { APIResponse } from '../si_interface/types';

export interface EnhancedHybridInterfaceProps {
  userName?: string;
  userEmail?: string;
  className?: string;
}

interface HybridUnifiedAPIData {
  totalIntegrations?: number;
  totalTransmissions?: number;
  successRate?: number;
  complianceScore?: number;
  activeWorkflows?: number;
  siMetrics?: {
    integrations?: { active?: number; pending?: number };
    processing?: { rate?: number; queue?: number };
    analytics?: { revenue?: number; growth?: number };
  };
  appMetrics?: {
    transmission?: { rate?: number; queue?: number };
    firs?: { status?: string; uptime?: number };
    security?: { score?: number; threats?: number };
  };
  validation?: ValidationOverview;
}

interface SIDashboardMetricsSummary {
  integrations?: {
    overall?: {
      totalSystems?: number;
      activeSystems?: number;
      overallHealthScore?: number;
    };
  };
  transactions?: {
    successRate?: number;
  };
}

interface AppDashboardMetricsData {
  transmission?: { rate?: number; queue?: number };
  firs?: { status?: string; uptime?: number };
  security?: { score?: number; threats?: number };
}

interface ValidationOverview {
  summary?: {
    totalBatches?: number;
    statusCounts?: Record<string, number>;
    totals?: { total?: number; passed?: number; failed?: number };
    lastRunAt?: string;
  };
  recentBatches: Array<{
    batchId?: string;
    status?: string;
    createdAt?: string;
    totals?: { total?: number; passed?: number; failed?: number };
  }>;
  slaHours?: number;
}

interface HybridMetrics {
  unified: {
    totalIntegrations: number;
    totalTransmissions: number;
    successRate: number;
    complianceScore: number;
    activeWorkflows: number;
  };
  si: {
    integrations: { active: number; pending: number };
    processing: { rate: number; queue: number };
    analytics: { revenue: number; growth: number };
  };
  app: {
    transmission: { rate: number; queue: number };
    firs: { status: string; uptime: number };
    security: { score: number; threats: number };
  };
  validation: ValidationOverview;
}

const toPercentDisplay = (value?: number, digits: number = 1): string | null => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return null;
  }
  return `${value.toFixed(digits)}%`;
};

const toMillionsDisplay = (value?: number, digits: number = 1): string | null => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return null;
  }
  return `₦${(value / 1_000_000).toFixed(digits)}M`;
};

const buildEmptyHybridMetrics = (): HybridMetrics => ({
  unified: {
    totalIntegrations: 0,
    totalTransmissions: 0,
    successRate: 0,
    complianceScore: 0,
    activeWorkflows: 0,
  },
  si: {
    integrations: { active: 0, pending: 0 },
    processing: { rate: 0, queue: 0 },
    analytics: { revenue: 0, growth: 0 },
  },
  financial: {
    banking: { connected: 0, providers: [], totalAccounts: 0 },
    payments: { connected: 0, providers: [], monthlyVolume: 0 },
  },
  app: {
    transmission: { rate: 0, queue: 0 },
    firs: { status: 'Not connected', uptime: 0 },
    security: { score: 0, threats: 0 },
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
});

export const EnhancedHybridInterfaceWithAPI: React.FC<EnhancedHybridInterfaceProps> = ({
  userName = 'Hybrid User',
  userEmail = 'user@company.com',
  className = ''
}) => {
  const router = useRouter();
  const [activeRole, setActiveRole] = useState<'si' | 'app' | 'unified'>('unified');
  const [isLoading, setIsLoading] = useState(true);
  const [hasLiveData, setHasLiveData] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Combined metrics from both SI and APP perspectives  
  const [metrics, setMetrics] = useState<HybridMetrics>(() => buildEmptyHybridMetrics());

  useEffect(() => {
    loadHybridDashboardData();
  }, [loadHybridDashboardData]);

  const formatDateTime = (value?: string) => {
    if (!value) return 'N/A';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return new Intl.DateTimeFormat('en-NG', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(parsed);
  };

  const validationSummary = metrics.validation.summary;
  const validationTotals = validationSummary?.totals ?? { total: 0, passed: 0, failed: 0 };
  const validationPassRate = validationTotals.total
    ? Math.round(((validationTotals.passed ?? 0) / validationTotals.total) * 100)
    : 0;
  const validationPassDisplay = validationTotals.total ? `${validationPassRate}%` : '--';
  const validationRecent = metrics.validation.recentBatches ?? [];
  const validationStatusEntries = Object.entries(validationSummary?.statusCounts ?? {});

  const loadHybridDashboardData = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);

    try {
      const [hybridResult, siResult, appResult] = await Promise.allSettled([
        apiClient.get<APIResponse<HybridUnifiedAPIData>>('/hybrid/dashboard/unified-metrics'),
        apiClient.get<APIResponse<SIDashboardMetricsSummary>>('/si/dashboard/metrics'),
        apiClient.get<APIResponse<AppDashboardMetricsData>>('/app/dashboard/metrics'),
      ]);

      const errorMessages: string[] = [];

      const hybridSuccess =
        hybridResult.status === 'fulfilled' && hybridResult.value?.success;
      const hybridData = hybridSuccess ? hybridResult.value.data ?? null : null;
      if (hybridResult.status === 'rejected') {
        errorMessages.push('Unified metrics request failed.');
      } else if (!hybridSuccess) {
        errorMessages.push(hybridResult.value?.message || 'Unified metrics unavailable.');
      }

      const siSuccess = siResult.status === 'fulfilled' && siResult.value?.success;
      const siData = siSuccess ? siResult.value.data ?? null : null;
      if (siResult.status === 'rejected') {
        errorMessages.push('SI metrics request failed.');
      } else if (!siSuccess) {
        errorMessages.push(siResult.value?.message || 'SI metrics unavailable.');
      }

      const appSuccess =
        appResult.status === 'fulfilled' && appResult.value?.success;
      const appData = appSuccess ? appResult.value.data ?? null : null;
      if (appResult.status === 'rejected') {
        errorMessages.push('APP metrics request failed.');
      } else if (!appSuccess) {
        errorMessages.push(appResult.value?.message || 'APP metrics unavailable.');
      }

      const siTotal = siData?.integrations?.overall?.totalSystems;
      const siActive = siData?.integrations?.overall?.activeSystems;
      const derivedSiPending =
        siTotal !== undefined && siActive !== undefined
          ? Math.max(siTotal - siActive, 0)
          : undefined;

      setMetrics((prev) => ({
        unified: {
          totalIntegrations:
            hybridData?.totalIntegrations ?? prev.unified.totalIntegrations,
          totalTransmissions:
            hybridData?.totalTransmissions ?? prev.unified.totalTransmissions,
          successRate: hybridData?.successRate ?? prev.unified.successRate,
          complianceScore:
            hybridData?.complianceScore ?? prev.unified.complianceScore,
          activeWorkflows:
            hybridData?.activeWorkflows ?? prev.unified.activeWorkflows,
        },
        si: {
          integrations: {
            active:
              siActive ??
              hybridData?.siMetrics?.integrations?.active ??
              prev.si.integrations.active,
            pending:
              derivedSiPending ??
              hybridData?.siMetrics?.integrations?.pending ??
              prev.si.integrations.pending,
          },
          processing: {
            rate:
              hybridData?.siMetrics?.processing?.rate ??
              prev.si.processing.rate,
            queue:
              hybridData?.siMetrics?.processing?.queue ??
              prev.si.processing.queue,
          },
          analytics: {
            revenue:
              hybridData?.siMetrics?.analytics?.revenue ??
              prev.si.analytics.revenue,
            growth:
              hybridData?.siMetrics?.analytics?.growth ??
              prev.si.analytics.growth,
          },
        },
        app: {
          transmission:
            appData?.transmission ??
            hybridData?.appMetrics?.transmission ??
            prev.app.transmission,
          firs:
            appData?.firs ??
            hybridData?.appMetrics?.firs ??
            prev.app.firs,
          security:
            appData?.security ??
            hybridData?.appMetrics?.security ??
            prev.app.security,
        },
        validation: {
          summary:
            hybridData?.validation?.summary ??
            prev.validation.summary,
          recentBatches:
            hybridData?.validation?.recentBatches ??
            prev.validation.recentBatches,
          slaHours:
            hybridData?.validation?.slaHours ??
            prev.validation.slaHours,
        },
      }));

      const live = Boolean(hybridSuccess || siSuccess || appSuccess);
      setHasLiveData(live);

      if (errorMessages.length > 0) {
        const combined = errorMessages.join(' ');
        setLoadError(
          live
            ? `Some dashboard data failed to load: ${combined}`
            : `Unable to load dashboard data: ${combined}`
        );
      }
    } catch (error) {
      console.error('Failed to load Hybrid dashboard data:', error);
      setHasLiveData(false);
      setLoadError('Failed to load Hybrid dashboard data. Please retry.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleCardClick = (cardId: string, route?: string) => {
    if (route) {
      router.push(route);
    }
  };

  const handleRoleSwitch = (role: 'si' | 'app' | 'unified') => {
    setActiveRole(role);
    if (role === 'si') {
      router.push('/dashboard/si');
    } else if (role === 'app') {
      router.push('/dashboard/app');
    }
  };

  const sectionStyle = combineStyles(
    TYPOGRAPHY_STYLES.optimizedText,
    {
      background: 'linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%)'
    }
  );

  const roleOptions: Array<{
    id: 'unified' | 'si' | 'app';
    label: string;
    icon: string;
    color: string;
  }> = [
    { id: 'unified', label: 'Unified View', icon: '🔄', color: 'purple' },
    { id: 'si', label: 'System Integrator', icon: '🔗', color: 'indigo' },
    { id: 'app', label: 'Access Point Provider', icon: '🏛️', color: 'green' }
  ];

  if (isLoading) {
    return (
      <DashboardLayout
        role="hybrid"
        userName={userName}
        userEmail={userEmail}
        activeTab="dashboard"
        className={className}
      >
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading unified dashboard...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout
      role="hybrid"
      userName={userName}
      userEmail={userEmail}
      activeTab="dashboard"
      className={className}
    >
      <div style={sectionStyle} className="min-h-full">
        {loadError && (
          <div className="mb-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {loadError}
          </div>
        )}
        
        {/* Header Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 
                className="text-4xl font-black text-slate-800 mb-2"
                style={TYPOGRAPHY_STYLES.optimizedText}
              >
                Hybrid Dashboard
              </h1>
              <p 
                className="text-xl text-slate-600"
                style={TYPOGRAPHY_STYLES.optimizedText}
              >
                Unified view of System Integration and Access Point Provider capabilities
                {(!hasLiveData || loadError) && (
                  <span className="ml-2 rounded-full bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-700">
                    {loadError ? 'Data load error' : 'Awaiting live data'}
                  </span>
                )}
              </p>
            </div>
            
            <div className="flex space-x-4">
              <TaxPoyntButton
                variant="outline"
                onClick={() => router.push('/dashboard/hybrid/workflows')}
                className="border-2 border-purple-300 text-purple-700 hover:bg-purple-50"
              >
                <span className="mr-2">🔄</span>
                Manage Workflows
              </TaxPoyntButton>
              <TaxPoyntButton
                variant="primary"
                onClick={() => router.push('/dashboard/hybrid/analytics')}
                className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
              >
                <span className="mr-2">📊</span>
                Advanced Analytics
              </TaxPoyntButton>
            </div>
          </div>

          {/* Role Switching Tabs */}
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-slate-800">Role View</h2>
              <div className="flex items-center space-x-2 text-sm text-slate-600">
                <span>Switch between perspectives:</span>
              </div>
            </div>
            
            <div className="flex space-x-2">
              {roleOptions.map((role) => (
                <button
                  key={role.id}
                  onClick={() => handleRoleSwitch(role.id)}
                  className={`flex items-center px-6 py-3 rounded-xl transition-all duration-200 ${
                    activeRole === role.id
                      ? `bg-${role.color}-500 text-white shadow-lg`
                      : `bg-gray-100 text-slate-600 hover:bg-${role.color}-50 hover:text-${role.color}-700`
                  }`}
                >
                  <span className="mr-2">{role.icon}</span>
                  {role.label}
                </button>
              ))}
            </div>
        </div>

        {/* Unified Stats Bar */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          {[
            {
              label: 'Total Integrations',
              value:
                metrics.unified.totalIntegrations > 0
                  ? metrics.unified.totalIntegrations.toLocaleString()
                  : hasLiveData
                  ? '0'
                  : '--',
              color: 'indigo',
              helper: hasLiveData ? 'Connected systems' : 'Connect SI sources',
            },
            {
              label: 'Total Transmissions',
              value:
                metrics.unified.totalTransmissions > 0
                  ? metrics.unified.totalTransmissions.toLocaleString()
                  : hasLiveData
                  ? '0'
                  : '--',
              color: 'green',
              helper: hasLiveData ? 'Batches routed' : 'Submit via APP to populate',
            },
            {
              label: 'Overall Success Rate',
              value: toPercentDisplay(metrics.unified.successRate) ?? '--',
              color: 'emerald',
              helper: hasLiveData ? 'Unified average' : 'Awaiting data',
            },
            {
              label: 'Compliance Score',
              value: toPercentDisplay(metrics.unified.complianceScore) ?? '--',
              color: 'blue',
              helper: metrics.app.firs.status,
            },
            {
              label: 'Active Workflows',
              value:
                metrics.unified.activeWorkflows > 0
                  ? metrics.unified.activeWorkflows.toString()
                  : hasLiveData
                  ? '0'
                  : '--',
              color: 'purple',
              helper: hasLiveData ? 'Orchestrated automations' : 'Enable workflow engine',
            },
          ].map((stat, index) => (
            <div 
              key={index}
              className={`bg-white p-4 rounded-xl shadow-lg border border-${stat.color}-100`}
            >
              <div className={`text-2xl font-black text-${stat.color}-600 mb-1`}>
                {stat.value}
              </div>
              <div className="text-sm text-slate-600 font-medium">
                {stat.label}
              </div>
              {'helper' in stat && stat.helper && (
                <div className="text-xs text-slate-500 mt-1">{stat.helper}</div>
              )}
            </div>
          ))}
        </div>
        </div>

        {/* Main Dashboard Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          
          {/* Cross-Role Analytics */}
          <DashboardCard
            title="Cross-Role Analytics"
            description="Combined insights from SI and APP operations"
            icon="📊"
            badge={hasLiveData ? 'Real-time' : 'Awaiting data'}
            badgeColor="purple"
            variant="highlight"
            onClick={() => handleCardClick('analytics', '/dashboard/hybrid/analytics')}
            className="hover:scale-102 transition-transform"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-purple-600">SI Revenue (MTD)</span>
                <span className="font-bold text-purple-700">{toMillionsDisplay(metrics.si.analytics.revenue) ?? '--'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-purple-600">APP Success Rate</span>
                <span className="font-bold text-purple-700">{toPercentDisplay(metrics.app.transmission.rate) ?? '--'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-purple-600">Growth Rate</span>
                <span className="font-bold text-green-600">
                  {metrics.si.analytics.growth ? `+${metrics.si.analytics.growth}% MoM` : 'Connect analytics'}
                </span>
              </div>
              
              <div className="pt-3 border-t border-purple-100">
                <div className="text-center">
                  <div className="text-2xl font-black text-purple-600 mb-1">
                    {toPercentDisplay(metrics.unified.complianceScore) ?? '--'}
                  </div>
                  <div className="text-xs text-purple-700">Overall Performance</div>
                </div>
              </div>
            </div>
          </DashboardCard>

          {/* Workflow Orchestration */}
          <DashboardCard
            title="Workflow Orchestration"
            description="Manage end-to-end business processes"
            icon="🔄"
            badge={
              metrics.unified.activeWorkflows > 0
                ? `${metrics.unified.activeWorkflows} Active`
                : hasLiveData
                ? '0 Active'
                : 'No workflows'
            }
            badgeColor="blue"
            onClick={() => handleCardClick('workflows', '/dashboard/hybrid/workflows')}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Active Workflows</span>
                <span className="font-bold text-blue-600">{metrics.unified.activeWorkflows}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Completed Today</span>
                <span className="font-bold text-green-600">
                  {validationTotals.passed ?? 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Pending Actions</span>
                <span className="font-bold text-orange-600">
                  {metrics.app.transmission.queue ?? 0}
                </span>
              </div>
              
              <div className="pt-3 border-t border-gray-100">
                <TaxPoyntButton
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    router.push('/dashboard/hybrid/workflows/designer');
                  }}
                  className="w-full border-blue-300 text-blue-700 hover:bg-blue-50"
                >
                  Workflow Designer
                </TaxPoyntButton>
              </div>
            </div>
          </DashboardCard>

          {/* Compliance Overview */}
          <DashboardCard
            title="Compliance Overview"
            description="Unified compliance monitoring across all systems"
            icon="✅"
            badge={hasLiveData ? 'Tracking' : 'Awaiting data'}
            badgeColor="green"
            variant="success"
            onClick={() => handleCardClick('compliance', '/dashboard/hybrid/compliance')}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-green-600">SI Compliance</span>
                <span className="text-sm font-medium text-slate-700">
                  {hasLiveData ? 'Monitored' : 'Connect integrations'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-green-600">APP Compliance</span>
                <span className="text-sm font-medium text-slate-700">
                  {metrics.app.firs.status}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-green-600">FIRS Integration</span>
                <span className="text-sm font-medium text-slate-700">
                  {metrics.app.firs.uptime ? `${metrics.app.firs.uptime}% uptime` : 'Not connected'}
                </span>
              </div>
              
              <div className="pt-3 border-t border-green-100">
                <div className="text-center">
                  <div className="text-2xl font-black text-green-600 mb-1">
                    {toPercentDisplay(metrics.unified.complianceScore) ?? '--'}
                  </div>
                  <div className="text-xs text-green-700">Compliance Score</div>
                </div>
              </div>
            </div>
          </DashboardCard>

          {/* System Integration Hub */}
          <DashboardCard
            title="Integration Hub"
            description="Monitor all business system connections"
            icon="🔗"
            badge={`${metrics.unified.totalIntegrations} Systems`}
            badgeColor="indigo"
            onClick={() => handleCardClick('integrations', '/dashboard/si/integrations')}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Active Integrations</span>
                <span className="font-bold text-indigo-600">{metrics.si.integrations.active}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Pending Setup</span>
                <span className="font-bold text-orange-600">{metrics.si.integrations.pending}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Processing Rate</span>
                <span className="font-bold text-blue-600">{metrics.si.processing.rate}/hr</span>
              </div>
              
              <div className="pt-3 border-t border-gray-100">
                <TaxPoyntButton
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRoleSwitch('si');
                  }}
                  className="w-full border-indigo-300 text-indigo-700 hover:bg-indigo-50"
                >
                  Switch to SI View
                </TaxPoyntButton>
              </div>
            </div>
          </DashboardCard>

          {/* FIRS Transmission */}
          <DashboardCard
            title="FIRS Transmission"
            description="Monitor invoice transmissions to FIRS"
            icon="🏛️"
            badge={toPercentDisplay(metrics.app.transmission.rate) ?? '--'}
            badgeColor="green"
            onClick={() => handleCardClick('transmission', '/dashboard/app/transmission')}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Success Rate</span>
                <span className="font-bold text-green-600">{toPercentDisplay(metrics.app.transmission.rate) ?? '--'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Queue Status</span>
                <span className="font-bold text-orange-600">{metrics.app.transmission.queue ?? 0} pending</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">FIRS Uptime</span>
                <span className="font-bold text-green-600">{metrics.app.firs.uptime ? `${metrics.app.firs.uptime}%` : '--'}</span>
              </div>
              
              <div className="pt-3 border-t border-gray-100">
                <TaxPoyntButton
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRoleSwitch('app');
                  }}
                  className="w-full border-green-300 text-green-700 hover:bg-green-50"
                >
                  Switch to APP View
                </TaxPoyntButton>
              </div>
            </div>
          </DashboardCard>

          {/* Security & Monitoring */}
          <DashboardCard
            title="Security & Monitoring"
            description="Unified security monitoring across all systems"
            icon="🛡️"
            badge={toPercentDisplay(metrics.app.security.score) ?? '--'}
            badgeColor="blue"
            onClick={() => handleCardClick('security', '/dashboard/hybrid/security')}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Security Score</span>
                <span className="font-bold text-blue-600">{toPercentDisplay(metrics.app.security.score) ?? '--'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Threats Detected</span>
                <span className="font-bold text-green-600">{metrics.app.security.threats}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">System Status</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-green-600 font-medium text-sm">Secure</span>
                </div>
              </div>
              
              <div className="pt-3 border-t border-gray-100">
                <TaxPoyntButton
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    router.push('/dashboard/hybrid/security/scan');
                  }}
                  className="w-full border-blue-300 text-blue-700 hover:bg-blue-50"
                >
                  Run Full Security Scan
                </TaxPoyntButton>
              </div>
            </div>
          </DashboardCard>
        </div>

        {/* Cross-Role Activity Timeline */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 
              className="text-2xl font-bold text-slate-800"
              style={TYPOGRAPHY_STYLES.optimizedText}
            >
              Unified Activity Timeline
            </h2>
            <TaxPoyntButton
              variant="outline"
              size="sm"
              onClick={() => router.push('/dashboard/hybrid/activity')}
              className="border-slate-300 text-slate-700 hover:bg-slate-50"
            >
              View Full Timeline
            </TaxPoyntButton>
          </div>
          
          <div className="space-y-4">
            {hasLiveData && validationRecent.length > 0 ? (
              validationRecent.slice(0, 4).map((batch, index) => {
                const totals = batch.totals ?? {};
                return (
                  <div key={`${batch.batchId ?? 'batch'}-${index}`} className="flex items-center justify-between rounded-lg bg-gray-50 p-4 hover:bg-gray-100 transition-colors">
                    <div>
                      <div className="font-medium text-slate-800">{batch.batchId ?? 'Validation Batch'}</div>
                      <div className="text-sm text-slate-600">
                        {formatDateTime(batch.createdAt)} · {totals.total ?? 0} invoices
                      </div>
                    </div>
                    <div className="text-right text-xs text-slate-500">
                      <div>{batch.status ?? 'pending'}</div>
                      <div>✔ {totals.passed ?? 0} · ✖ {totals.failed ?? 0}</div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="rounded-lg bg-gray-50 p-4 text-sm text-slate-600">
                Activity will appear here after your first integrations and validations run.
              </div>
            )}
          </div>
        </div>

        {/* Validation Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <DashboardCard
            title="Validation Performance"
            description="Recent validation batches across SI and APP flows"
            icon="🧪"
            badge={`${validationTotals.total ?? 0} invoices`}
            badgeColor="purple"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-purple-600">Pass Rate</span>
                <span className="text-2xl font-black text-purple-600">{validationPassDisplay}</span>
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
                      return (
                        <div key={status}>
                          <div className="flex items-center justify-between text-xs text-slate-500">
                            <span className="capitalize text-slate-600">{status}</span>
                            <span className="font-medium text-slate-800">{count ?? 0}</span>
                          </div>
                          <div className="mt-1 h-2 w-full rounded-full bg-purple-100">
                            <div
                              className="h-2 rounded-full bg-purple-500"
                              style={{ width: `${Math.min(share, 100)}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="rounded-lg bg-purple-50 p-3 text-xs text-purple-700">
                    Run your first validation to populate performance trends.
                  </div>
                )}
              </div>
              <div className="pt-3 border-t border-purple-100 text-sm text-slate-600">
                <div className="flex items-center justify-between">
                  <span>Last Run</span>
                  <span className="font-medium text-slate-800">{formatDateTime(validationSummary?.lastRunAt)}</span>
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span>SLA Threshold</span>
                  <span className="font-medium text-slate-800">{metrics.validation.slaHours ?? '--'} hours</span>
                </div>
              </div>
            </div>
          </DashboardCard>

          <DashboardCard
            title="Recent Validation Batches"
            description="Shared visibility across roles"
            icon="📋"
          >
            <div className="space-y-3">
              {validationRecent.length > 0 ? (
                validationRecent.slice(0, 4).map((batch, index) => {
                  const totals = batch.totals ?? {};
                  return (
                    <div key={`${batch.batchId ?? 'batch'}-${index}`} className="bg-gray-50 rounded-lg p-3">
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
                <div className="text-sm text-slate-500">No validation runs recorded yet.</div>
              )}
            </div>
          </DashboardCard>
        </div>

        {/* Quick Actions for Hybrid Users */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[
            {
              title: 'Design Workflow',
              description: 'Create end-to-end process',
              icon: '🔄',
              action: () => router.push('/dashboard/hybrid/workflows/designer'),
              color: 'purple'
            },
            {
              title: 'Cross-Role Analytics',
              description: 'View unified insights',
              icon: '📊',
              action: () => router.push('/dashboard/hybrid/analytics'),
              color: 'blue'
            },
            {
              title: 'System Health',
              description: 'Monitor all systems',
              icon: '🏥',
              action: () => router.push('/dashboard/hybrid/health'),
              color: 'green'
            },
            {
              title: 'Compliance Center',
              description: 'Unified compliance view',
              icon: '✅',
              action: () => router.push('/dashboard/hybrid/compliance'),
              color: 'emerald'
            }
          ].map((quickAction, index) => (
            <div
              key={index}
              className={`bg-white border border-${quickAction.color}-200 rounded-xl p-6 cursor-pointer hover:shadow-lg hover:scale-105 transition-all duration-200`}
              onClick={quickAction.action}
            >
              <div className="text-center">
                <div className="text-4xl mb-3">{quickAction.icon}</div>
                <h3 className={`text-lg font-bold text-${quickAction.color}-800 mb-2`}>
                  {quickAction.title}
                </h3>
                <p className="text-sm text-slate-600">
                  {quickAction.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
};
