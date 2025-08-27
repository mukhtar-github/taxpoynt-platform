/**
 * Enhanced System Integrator (SI) Interface
 * ==========================================
 * 
 * Professional SI dashboard enhanced with our unified design system.
 * Maintains all existing functionality while providing modern UI/UX.
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
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);

  // Real-time metrics (would come from API)
  const metrics = {
    integrations: { total: 15, active: 12, pending: 3 },
    processing: { rate: 1234, success: 99.8, queue: 45 },
    compliance: { status: 'Active', score: 98, issues: 0 },
    financial: { connected: 3, active: 2, ready: 1 },
    analytics: { revenue: 45200000, transactions: 12456, growth: 23 },
    tools: { running: 4, ready: 2, maintenance: 1 }
  };

  const handleCardClick = (cardId: string, route?: string) => {
    setSelectedMetric(cardId);
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

          {/* Quick Stats Bar */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[
              { label: 'Active Integrations', value: metrics.integrations.active, total: metrics.integrations.total, color: 'indigo' },
              { label: 'Processing Rate', value: `${metrics.processing.rate}/hr`, color: 'blue' },
              { label: 'Success Rate', value: `${metrics.processing.success}%`, color: 'green' },
              { label: 'Queue Status', value: `${metrics.processing.queue} pending`, color: 'orange' }
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
          
          {/* Integration Hub */}
          <DashboardCard
            title="Integration Hub"
            description="Connect and configure business systems for automated e-invoicing"
            icon="🔗"
            badge={`${metrics.integrations.active}/${metrics.integrations.total}`}
            badgeColor="green"
            variant="highlight"
            onClick={() => handleCardClick('integrations', '/dashboard/si/integrations')}
            className="hover:scale-102 transition-transform"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-blue-600">ERP Systems</span>
                <span className="font-bold text-green-600">15 Connected</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-blue-600">CRM Systems</span>
                <span className="font-bold text-green-600">8 Connected</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-blue-600">POS Systems</span>
                <span className="font-bold text-green-600">12 Connected</span>
              </div>
              
              <div className="pt-3 border-t border-blue-100">
                <div className="flex items-center space-x-2">
                  <div className="w-full bg-blue-100 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-blue-500 to-indigo-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${(metrics.integrations.active / metrics.integrations.total) * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-xs text-blue-600 font-medium">
                    {Math.round((metrics.integrations.active / metrics.integrations.total) * 100)}%
                  </span>
                </div>
              </div>
            </div>
          </DashboardCard>

          {/* Processing Center */}
          <DashboardCard
            title="Processing Center"
            description="Monitor document processing and validation workflows"
            icon="⚙️"
            badge={`${metrics.processing.queue} queued`}
            badgeColor="orange"
            onClick={() => handleCardClick('processing', '/dashboard/si/processing')}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Processing Rate</span>
                <span className="font-bold text-green-600">{metrics.processing.rate} invoices/hour</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Success Rate</span>
                <span className="font-bold text-green-600">{metrics.processing.success}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Queue Status</span>
                <span className="font-bold text-orange-600">{metrics.processing.queue} pending</span>
              </div>
              
              <div className="pt-3 border-t border-gray-100">
                <TaxPoyntButton
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    router.push('/dashboard/si/processing/queue');
                  }}
                  className="w-full border-blue-300 text-blue-700 hover:bg-blue-50"
                >
                  View Queue Details
                </TaxPoyntButton>
              </div>
            </div>
          </DashboardCard>

          {/* Compliance Monitor */}
          <DashboardCard
            title="Compliance Monitor"
            description="Nigerian regulatory compliance monitoring and reporting"
            icon="✅"
            badge="All Systems Go"
            badgeColor="green"
            variant="success"
            onClick={() => handleCardClick('compliance', '/dashboard/si/compliance')}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-green-600">FIRS Compliance</span>
                <span className="font-bold text-green-700">Active</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-green-600">VAT Compliance</span>
                <span className="font-bold text-green-700">Current</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-green-600">CBN Standards</span>
                <span className="font-bold text-green-700">Verified</span>
              </div>
              
              <div className="pt-3 border-t border-green-100">
                <div className="text-center">
                  <div className="text-2xl font-black text-green-600 mb-1">
                    {metrics.compliance.score}%
                  </div>
                  <div className="text-xs text-green-700">Compliance Score</div>
                </div>
              </div>
            </div>
          </DashboardCard>

          {/* Financial Systems */}
          <DashboardCard
            title="Financial Systems"
            description="Banking integration and payment processing"
            icon="💰"
            badge="3 Connected"
            badgeColor="blue"
            onClick={() => handleCardClick('financial', '/dashboard/si/financial')}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Mono Banking</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-green-600 font-medium text-sm">Connected</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Paystack</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-green-600 font-medium text-sm">Active</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Moniepoint</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                  <span className="text-blue-600 font-medium text-sm">Ready</span>
                </div>
              </div>
              
              <div className="pt-3 border-t border-gray-100">
                <TaxPoyntButton
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    router.push('/dashboard/si/financial/connect');
                  }}
                  className="w-full border-blue-300 text-blue-700 hover:bg-blue-50"
                >
                  Add Banking Provider
                </TaxPoyntButton>
              </div>
            </div>
          </DashboardCard>

          {/* Analytics */}
          <DashboardCard
            title="Analytics & Insights"
            description="Business insights and performance metrics"
            icon="📊"
            badge="+23% Growth"
            badgeColor="green"
            onClick={() => handleCardClick('analytics', '/dashboard/si/analytics')}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Revenue (MTD)</span>
                <span className="font-bold text-green-600">₦{(metrics.analytics.revenue / 1000000).toFixed(1)}M</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Transactions</span>
                <span className="font-bold text-blue-600">{metrics.analytics.transactions.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Growth Rate</span>
                <span className="font-bold text-green-600">+{metrics.analytics.growth}% MoM</span>
              </div>
              
              <div className="pt-3 border-t border-gray-100">
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div>
                    <div className="text-lg font-bold text-indigo-600">45.2M</div>
                    <div className="text-xs text-slate-500">Revenue</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-blue-600">12.4K</div>
                    <div className="text-xs text-slate-500">Invoices</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-green-600">23%</div>
                    <div className="text-xs text-slate-500">Growth</div>
                  </div>
                </div>
              </div>
            </div>
          </DashboardCard>

          {/* System Tools */}
          <DashboardCard
            title="System Tools"
            description="Advanced tools and system utilities"
            icon="🛠️"
            badge="All Systems Operational"
            badgeColor="green"
            onClick={() => handleCardClick('tools', '/dashboard/si/tools')}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Schema Validator</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-green-600 font-medium text-sm">Running</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Data Extractor</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                  <span className="text-blue-600 font-medium text-sm">Ready</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Certificates</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-green-600 font-medium text-sm">Valid</span>
                </div>
              </div>
              
              <div className="pt-3 border-t border-gray-100">
                <TaxPoyntButton
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    router.push('/dashboard/si/tools/diagnostics');
                  }}
                  className="w-full border-indigo-300 text-indigo-700 hover:bg-indigo-50"
                >
                  Run Diagnostics
                </TaxPoyntButton>
              </div>
            </div>
          </DashboardCard>
        </div>

        {/* Recent Activity Section */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 
              className="text-2xl font-bold text-slate-800"
              style={TYPOGRAPHY_STYLES.optimizedText}
            >
              Recent Activity
            </h2>
            <TaxPoyntButton
              variant="outline"
              size="sm"
              onClick={() => router.push('/dashboard/si/activity')}
              className="border-slate-300 text-slate-700 hover:bg-slate-50"
            >
              View All Activity
            </TaxPoyntButton>
          </div>
          
          <div className="space-y-4">
            {[
              { time: '2 minutes ago', action: 'New ERP integration', system: 'SAP ERP', status: 'success' },
              { time: '15 minutes ago', action: 'Invoice batch processed', count: '245 invoices', status: 'success' },
              { time: '1 hour ago', action: 'Compliance check completed', result: 'All systems compliant', status: 'success' },
              { time: '3 hours ago', action: 'Banking sync completed', system: 'Mono Banking', status: 'success' }
            ].map((activity, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="flex items-center space-x-3">
                  <div className={`w-2 h-2 rounded-full ${
                    activity.status === 'success' ? 'bg-green-500' : 'bg-orange-500'
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

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              title: 'Add New Integration',
              description: 'Connect a new business system',
              icon: '🔗',
              action: () => router.push('/dashboard/si/integrations/new'),
              color: 'indigo'
            },
            {
              title: 'View Reports',
              description: 'Generate compliance reports',
              icon: '📋',
              action: () => router.push('/dashboard/si/reports'),
              color: 'blue'
            },
            {
              title: 'System Health',
              description: 'Check system status',
              icon: '🏥',
              action: () => router.push('/dashboard/si/health'),
              color: 'green'
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
