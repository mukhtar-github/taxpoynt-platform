/**
 * Enhanced Access Point Provider (APP) Interface
 * ===============================================
 * 
 * Professional APP dashboard enhanced with our unified design system.
 * Maintains compatibility with existing Ant Design while integrating our design system.
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

export interface EnhancedAPPInterfaceProps {
  userName?: string;
  userEmail?: string;
  className?: string;
}

export const EnhancedAPPInterface: React.FC<EnhancedAPPInterfaceProps> = ({
  userName = 'Access Point Provider',
  userEmail = 'user@company.com',
  className = ''
}) => {
  const router = useRouter();
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);

  // Real-time APP metrics (would come from API)
  const metrics = {
    transmission: { 
      total: 12456, 
      successful: 12411, 
      failed: 45, 
      rate: 98.7,
      queue: 23
    },
    firs: { 
      status: 'Connected', 
      lastSync: '2 minutes ago', 
      uptime: 99.9,
      submissions: 8432
    },
    security: { 
      score: 96, 
      threats: 0, 
      lastAudit: '1 hour ago',
      certificates: 'Valid'
    },
    compliance: { 
      status: 'Compliant', 
      reports: 145, 
      nextDeadline: '2 days',
      coverage: 100
    }
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
      background: 'linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%)'
    }
  );

  return (
    <DashboardLayout
      role="app"
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
                Access Point Provider Dashboard
              </h1>
              <p 
                className="text-xl text-slate-600"
                style={TYPOGRAPHY_STYLES.optimizedText}
              >
                Manage FIRS transmission, security audits, and compliance reporting
              </p>
            </div>
            
            <div className="flex space-x-4">
              <TaxPoyntButton
                variant="outline"
                onClick={() => router.push('/dashboard/app/transmission/new')}
                className="border-2 border-green-300 text-green-700 hover:bg-green-50"
              >
                <span className="mr-2">📤</span>
                New Transmission
              </TaxPoyntButton>
              <TaxPoyntButton
                variant="primary"
                onClick={() => router.push('/dashboard/app/firs/setup')}
                className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
              >
                <span className="mr-2">🏛️</span>
                FIRS Setup
              </TaxPoyntButton>
            </div>
          </div>

          {/* Quick Stats Bar */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[
              { label: 'Transmission Rate', value: `${metrics.transmission.rate}%`, color: 'green' },
              { label: 'FIRS Status', value: metrics.firs.status, color: 'emerald' },
              { label: 'Security Score', value: `${metrics.security.score}%`, color: 'blue' },
              { label: 'Queue Status', value: `${metrics.transmission.queue} pending`, color: 'orange' }
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
          
          {/* Transmission Monitor */}
          <DashboardCard
            title="Transmission Monitor"
            description="Monitor invoice transmission to FIRS in real-time"
            icon="📤"
            badge={`${metrics.transmission.rate}% Success`}
            badgeColor="green"
            variant="success"
            onClick={() => handleCardClick('transmission', '/dashboard/app/transmission')}
            className="hover:scale-102 transition-transform"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-green-600">Total Transmissions</span>
                <span className="font-bold text-green-700">{metrics.transmission.total.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-green-600">Successful</span>
                <span className="font-bold text-green-700">{metrics.transmission.successful.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-green-600">Failed</span>
                <span className="font-bold text-red-600">{metrics.transmission.failed}</span>
              </div>
              
              <div className="pt-3 border-t border-green-100">
                <div className="flex items-center space-x-2">
                  <div className="w-full bg-green-100 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${metrics.transmission.rate}%` }}
                    ></div>
                  </div>
                  <span className="text-xs text-green-600 font-medium">
                    {metrics.transmission.rate}%
                  </span>
                </div>
              </div>
            </div>
          </DashboardCard>

          {/* FIRS Dashboard */}
          <DashboardCard
            title="FIRS Integration"
            description="Manage FIRS API connections and submissions"
            icon="🏛️"
            badge="Connected"
            badgeColor="green"
            variant="highlight"
            onClick={() => handleCardClick('firs', '/dashboard/app/firs')}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-blue-600">Connection Status</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-green-600 font-medium text-sm">{metrics.firs.status}</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-blue-600">Last Sync</span>
                <span className="font-bold text-blue-700">{metrics.firs.lastSync}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-blue-600">Submissions</span>
                <span className="font-bold text-blue-700">{metrics.firs.submissions.toLocaleString()}</span>
              </div>
              
              <div className="pt-3 border-t border-blue-100">
                <div className="text-center">
                  <div className="text-2xl font-black text-green-600 mb-1">
                    {metrics.firs.uptime}%
                  </div>
                  <div className="text-xs text-blue-700">Uptime (30 days)</div>
                </div>
              </div>
            </div>
          </DashboardCard>

          {/* Security Audit */}
          <DashboardCard
            title="Security Center"
            description="Review security compliance and threat monitoring"
            icon="🛡️"
            badge={`${metrics.security.score}% Score`}
            badgeColor="blue"
            onClick={() => handleCardClick('security', '/dashboard/app/security')}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Security Score</span>
                <span className="font-bold text-blue-600">{metrics.security.score}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Threats Detected</span>
                <span className="font-bold text-green-600">{metrics.security.threats}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Certificates</span>
                <span className="font-bold text-green-600">{metrics.security.certificates}</span>
              </div>
              
              <div className="pt-3 border-t border-gray-100">
                <TaxPoyntButton
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    router.push('/dashboard/app/security/scan');
                  }}
                  className="w-full border-blue-300 text-blue-700 hover:bg-blue-50"
                >
                  Run Security Scan
                </TaxPoyntButton>
              </div>
            </div>
          </DashboardCard>

          {/* Compliance Reports */}
          <DashboardCard
            title="Compliance Reports"
            description="Generate and manage compliance documentation"
            icon="📋"
            badge={`${metrics.compliance.reports} Reports`}
            badgeColor="purple"
            onClick={() => handleCardClick('compliance', '/dashboard/app/compliance')}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Compliance Status</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-green-600 font-medium text-sm">{metrics.compliance.status}</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Total Reports</span>
                <span className="font-bold text-purple-600">{metrics.compliance.reports}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Next Deadline</span>
                <span className="font-bold text-orange-600">{metrics.compliance.nextDeadline}</span>
              </div>
              
              <div className="pt-3 border-t border-gray-100">
                <div className="text-center">
                  <div className="text-2xl font-black text-green-600 mb-1">
                    {metrics.compliance.coverage}%
                  </div>
                  <div className="text-xs text-purple-700">Coverage</div>
                </div>
              </div>
            </div>
          </DashboardCard>

          {/* Data Validation */}
          <DashboardCard
            title="Data Validation"
            description="Validate invoices before transmission"
            icon="✅"
            badge="All Valid"
            badgeColor="green"
            onClick={() => handleCardClick('validation', '/dashboard/app/validation')}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Validation Rate</span>
                <span className="font-bold text-green-600">99.8%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Schema Errors</span>
                <span className="font-bold text-green-600">0</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Format Issues</span>
                <span className="font-bold text-green-600">0</span>
              </div>
              
              <div className="pt-3 border-t border-gray-100">
                <TaxPoyntButton
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    router.push('/dashboard/app/validation/new');
                  }}
                  className="w-full border-green-300 text-green-700 hover:bg-green-50"
                >
                  Validate New Batch
                </TaxPoyntButton>
              </div>
            </div>
          </DashboardCard>

          {/* Status Tracking */}
          <DashboardCard
            title="Status Tracking"
            description="Track submission status and responses"
            icon="📊"
            badge="Real-time"
            badgeColor="blue"
            onClick={() => handleCardClick('tracking', '/dashboard/app/tracking')}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Processing</span>
                <span className="font-bold text-blue-600">23</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Completed</span>
                <span className="font-bold text-green-600">12,433</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Pending</span>
                <span className="font-bold text-orange-600">0</span>
              </div>
              
              <div className="pt-3 border-t border-gray-100">
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div>
                    <div className="text-lg font-bold text-blue-600">23</div>
                    <div className="text-xs text-slate-500">Active</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-green-600">12.4K</div>
                    <div className="text-xs text-slate-500">Done</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-orange-600">0</div>
                    <div className="text-xs text-slate-500">Queue</div>
                  </div>
                </div>
              </div>
            </div>
          </DashboardCard>
        </div>

        {/* Recent Transmissions */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 
              className="text-2xl font-bold text-slate-800"
              style={TYPOGRAPHY_STYLES.optimizedText}
            >
              Recent Transmissions
            </h2>
            <TaxPoyntButton
              variant="outline"
              size="sm"
              onClick={() => router.push('/dashboard/app/transmission/history')}
              className="border-slate-300 text-slate-700 hover:bg-slate-50"
            >
              View All Transmissions
            </TaxPoyntButton>
          </div>
          
          <div className="space-y-4">
            {[
              { time: '1 minute ago', batch: 'BATCH-2024-001', count: 125, status: 'success', response: 'Accepted' },
              { time: '5 minutes ago', batch: 'BATCH-2024-002', count: 89, status: 'success', response: 'Accepted' },
              { time: '12 minutes ago', batch: 'BATCH-2024-003', count: 156, status: 'processing', response: 'Processing' },
              { time: '25 minutes ago', batch: 'BATCH-2024-004', count: 203, status: 'success', response: 'Accepted' }
            ].map((transmission, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="flex items-center space-x-4">
                  <div className={`w-3 h-3 rounded-full ${
                    transmission.status === 'success' ? 'bg-green-500' : 
                    transmission.status === 'processing' ? 'bg-blue-500' : 'bg-orange-500'
                  }`}></div>
                  <div>
                    <div className="font-medium text-slate-800">{transmission.batch}</div>
                    <div className="text-sm text-slate-600">{transmission.count} invoices</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`font-medium ${
                    transmission.status === 'success' ? 'text-green-600' : 
                    transmission.status === 'processing' ? 'text-blue-600' : 'text-orange-600'
                  }`}>
                    {transmission.response}
                  </div>
                  <div className="text-sm text-slate-500">{transmission.time}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              title: 'New Transmission',
              description: 'Submit invoices to FIRS',
              icon: '📤',
              action: () => router.push('/dashboard/app/transmission/new'),
              color: 'green'
            },
            {
              title: 'Security Audit',
              description: 'Run security assessment',
              icon: '🛡️',
              action: () => router.push('/dashboard/app/security'),
              color: 'blue'
            },
            {
              title: 'Generate Report',
              description: 'Create compliance report',
              icon: '📋',
              action: () => router.push('/dashboard/app/reports/new'),
              color: 'purple'
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
