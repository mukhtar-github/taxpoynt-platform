/**
 * Enhanced Hybrid Interface
 * ==========================
 * 
 * Professional Hybrid dashboard that combines SI and APP capabilities
 * using our unified design system and role-switching functionality.
 */

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardLayout } from '../shared_components/layouts/DashboardLayout';
import { DashboardCard } from '../shared_components/dashboard/DashboardCard';
import { TaxPoyntButton } from '../design_system';
import { 
  TYPOGRAPHY_STYLES, 
  combineStyles,
  getSectionBackground
} from '../design_system/style-utilities';

export interface EnhancedHybridInterfaceProps {
  userName?: string;
  userEmail?: string;
  className?: string;
}

export const EnhancedHybridInterface: React.FC<EnhancedHybridInterfaceProps> = ({
  userName = 'Hybrid User',
  userEmail = 'user@company.com',
  className = ''
}) => {
  const router = useRouter();
  const [activeRole, setActiveRole] = useState<'si' | 'app' | 'unified'>('unified');
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);

  // Combined metrics from both SI and APP perspectives
  const metrics = {
    unified: {
      totalIntegrations: 15,
      totalTransmissions: 8432,
      successRate: 98.7,
      complianceScore: 97,
      activeWorkflows: 23
    },
    si: {
      integrations: { active: 12, pending: 3 },
      processing: { rate: 1234, queue: 45 },
      analytics: { revenue: 45200000, growth: 23 }
    },
    app: {
      transmission: { rate: 98.7, queue: 23 },
      firs: { status: 'Connected', uptime: 99.9 },
      security: { score: 96, threats: 0 }
    }
  };

  const handleCardClick = (cardId: string, route?: string) => {
    setSelectedMetric(cardId);
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

  return (
    <DashboardLayout
      role="hybrid"
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
                Hybrid Dashboard
              </h1>
              <p 
                className="text-xl text-slate-600"
                style={TYPOGRAPHY_STYLES.optimizedText}
              >
                Unified view of System Integration and Access Point Provider capabilities
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
              {[
                { id: 'unified', label: 'Unified View', icon: '🔄', color: 'purple' },
                { id: 'si', label: 'System Integrator', icon: '🔗', color: 'indigo' },
                { id: 'app', label: 'Access Point Provider', icon: '🏛️', color: 'green' }
              ].map((role) => (
                <button
                  key={role.id}
                  onClick={() => handleRoleSwitch(role.id as any)}
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
              { label: 'Total Integrations', value: metrics.unified.totalIntegrations, color: 'indigo' },
              { label: 'Total Transmissions', value: metrics.unified.totalTransmissions.toLocaleString(), color: 'green' },
              { label: 'Overall Success Rate', value: `${metrics.unified.successRate}%`, color: 'emerald' },
              { label: 'Compliance Score', value: `${metrics.unified.complianceScore}%`, color: 'blue' },
              { label: 'Active Workflows', value: metrics.unified.activeWorkflows, color: 'purple' }
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
            badge="Real-time"
            badgeColor="purple"
            variant="highlight"
            onClick={() => handleCardClick('analytics', '/dashboard/hybrid/analytics')}
            className="hover:scale-102 transition-transform"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-purple-600">SI Revenue (MTD)</span>
                <span className="font-bold text-purple-700">₦{(metrics.si.analytics.revenue / 1000000).toFixed(1)}M</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-purple-600">APP Success Rate</span>
                <span className="font-bold text-purple-700">{metrics.app.transmission.rate}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-purple-600">Growth Rate</span>
                <span className="font-bold text-green-600">+{metrics.si.analytics.growth}% MoM</span>
              </div>
              
              <div className="pt-3 border-t border-purple-100">
                <div className="text-center">
                  <div className="text-2xl font-black text-purple-600 mb-1">
                    {metrics.unified.complianceScore}%
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
            badge={`${metrics.unified.activeWorkflows} Active`}
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
                <span className="font-bold text-green-600">156</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Pending Actions</span>
                <span className="font-bold text-orange-600">7</span>
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
            badge="All Compliant"
            badgeColor="green"
            variant="success"
            onClick={() => handleCardClick('compliance', '/dashboard/hybrid/compliance')}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-green-600">SI Compliance</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-green-700 font-medium text-sm">Active</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-green-600">APP Compliance</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-green-700 font-medium text-sm">Current</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-green-600">FIRS Integration</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-green-700 font-medium text-sm">Connected</span>
                </div>
              </div>
              
              <div className="pt-3 border-t border-green-100">
                <div className="text-center">
                  <div className="text-2xl font-black text-green-600 mb-1">
                    {metrics.unified.complianceScore}%
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
            badge={`${metrics.app.transmission.rate}% Success`}
            badgeColor="green"
            onClick={() => handleCardClick('transmission', '/dashboard/app/transmission')}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Success Rate</span>
                <span className="font-bold text-green-600">{metrics.app.transmission.rate}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Queue Status</span>
                <span className="font-bold text-orange-600">{metrics.app.transmission.queue} pending</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">FIRS Uptime</span>
                <span className="font-bold text-green-600">{metrics.app.firs.uptime}%</span>
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
            badge={`${metrics.app.security.score}% Score`}
            badgeColor="blue"
            onClick={() => handleCardClick('security', '/dashboard/hybrid/security')}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Security Score</span>
                <span className="font-bold text-blue-600">{metrics.app.security.score}%</span>
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
            {[
              { time: '2 minutes ago', action: 'SI: New ERP integration completed', system: 'SAP ERP', type: 'si', status: 'success' },
              { time: '5 minutes ago', action: 'APP: Invoice batch transmitted to FIRS', count: '245 invoices', type: 'app', status: 'success' },
              { time: '12 minutes ago', action: 'Workflow: End-to-end process completed', result: 'Invoice → FIRS submission', type: 'workflow', status: 'success' },
              { time: '25 minutes ago', action: 'SI: Banking sync with Mono completed', system: 'Mono Banking', type: 'si', status: 'success' }
            ].map((activity, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${
                    activity.type === 'si' ? 'bg-indigo-500' :
                    activity.type === 'app' ? 'bg-green-500' :
                    activity.type === 'workflow' ? 'bg-purple-500' : 'bg-blue-500'
                  }`}></div>
                  <div>
                    <div className="font-medium text-slate-800">{activity.action}</div>
                    <div className="text-sm text-slate-600">
                      {activity.system || activity.count || activity.result}
                    </div>
                  </div>
                </div>
                <div className="text-sm text-slate-500">{activity.time}</div>
              </div>
            ))}
          </div>
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
