/**
 * APP Compliance Reports
 * ======================
 * 
 * Compliance reporting, audit trails, and regulatory documentation for APP providers.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardLayout } from '../../../../shared_components/layouts/DashboardLayout';
import { TaxPoyntButton, TaxPoyntInput } from '../../../../design_system';
import { APIResponse } from '../../../../si_interface/types';
import apiClient from '../../../../shared_components/api/client';

interface ComplianceReport {
  id: string;
  title: string;
  type: 'audit' | 'compliance' | 'security' | 'financial';
  status: 'draft' | 'pending' | 'approved' | 'submitted';
  created: string;
  deadline: string;
  completionPercentage: number;
}

interface ComplianceMetrics {
  totalReports: number;
  pendingReports: number;
  overdue: number;
  complianceScore: number;
  lastAudit: string;
  nextDeadline: string;
  reports: ComplianceReport[];
}

export default function ComplianceReportsPage() {
  const router = useRouter();
  const [metrics, setMetrics] = useState<ComplianceMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedReportType, setSelectedReportType] = useState('audit');
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    loadComplianceMetrics();
  }, []);

  const loadComplianceMetrics = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<APIResponse<ComplianceMetrics>>('/api/v1/app/compliance/metrics');
      if (response.success && response.data) {
        setMetrics(response.data);
        setIsDemo(false);
      } else {
        throw new Error('API response unsuccessful');
      }
    } catch (error) {
      console.error('Failed to load compliance metrics, using demo data:', error);
      // Fallback to demo data
      setIsDemo(true);
      setMetrics({
        totalReports: 145,
        pendingReports: 3,
        overdue: 0,
        complianceScore: 98,
        lastAudit: '2 weeks ago',
        nextDeadline: '5 days',
        reports: [
          {
            id: 'RPT-2024-001',
            title: 'Q1 2024 FIRS Compliance Report',
            type: 'compliance',
            status: 'approved',
            created: '2024-01-15',
            deadline: '2024-01-30',
            completionPercentage: 100
          },
          {
            id: 'RPT-2024-002',
            title: 'Security Audit Report - January',
            type: 'security',
            status: 'pending',
            created: '2024-01-20',
            deadline: '2024-01-25',
            completionPercentage: 85
          },
          {
            id: 'RPT-2024-003',
            title: 'Financial Reconciliation Report',
            type: 'financial',
            status: 'draft',
            created: '2024-01-22',
            deadline: '2024-01-28',
            completionPercentage: 60
          },
          {
            id: 'RPT-2024-004',
            title: 'Data Protection Compliance',
            type: 'audit',
            status: 'submitted',
            created: '2024-01-18',
            deadline: '2024-01-24',
            completionPercentage: 100
          }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  const generateNewReport = async () => {
    try {
      setGenerating(true);
      const response = await apiClient.post<APIResponse>('/api/v1/app/compliance/generate-report', {
        type: selectedReportType,
        includeMetrics: true,
        format: 'pdf'
      });
      
      if (response.success) {
        // Reload metrics after generating report
        await loadComplianceMetrics();
      }
    } catch (error) {
      console.error('Failed to generate report:', error);
    } finally {
      setGenerating(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800';
      case 'submitted': return 'bg-blue-100 text-blue-800';
      case 'pending': return 'bg-orange-100 text-orange-800';
      case 'draft': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'audit': return '🔍';
      case 'compliance': return '📋';
      case 'security': return '🛡️';
      case 'financial': return '💰';
      default: return '📄';
    }
  };

  if (loading) {
    return (
      <DashboardLayout role="app" activeTab="compliance">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading compliance reports...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout role="app" activeTab="compliance">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Compliance Reports</h1>
            <p className="text-gray-600">
              Generate and manage regulatory compliance documentation
              {isDemo && (
                <span className="ml-2 px-2 py-1 text-xs bg-orange-100 text-orange-800 rounded-full">
                  Demo Data
                </span>
              )}
            </p>
          </div>
          <div className="flex space-x-4">
            <TaxPoyntButton
              variant="outline"
              onClick={() => router.back()}
            >
              ← Back to Dashboard
            </TaxPoyntButton>
          </div>
        </div>

        {/* Compliance Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="text-3xl font-bold text-purple-600">{metrics?.totalReports}</div>
              <div className="ml-4">
                <div className="text-sm font-medium text-gray-600">Total Reports</div>
                <div className="text-xs text-gray-500">All Time</div>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="text-3xl font-bold text-orange-600">{metrics?.pendingReports}</div>
              <div className="ml-4">
                <div className="text-sm font-medium text-gray-600">Pending</div>
                <div className="text-xs text-gray-500">In Progress</div>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="text-3xl font-bold text-green-600">{metrics?.overdue}</div>
              <div className="ml-4">
                <div className="text-sm font-medium text-gray-600">Overdue</div>
                <div className="text-xs text-gray-500">Past Deadline</div>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="text-3xl font-bold text-blue-600">{metrics?.complianceScore}%</div>
              <div className="ml-4">
                <div className="text-sm font-medium text-gray-600">Compliance Score</div>
                <div className="text-xs text-gray-500">Excellent</div>
              </div>
            </div>
          </div>
        </div>

        {/* Generate New Report */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Generate New Report</h2>
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Report Type
              </label>
              <select
                value={selectedReportType}
                onChange={(e) => setSelectedReportType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="audit">Security Audit Report</option>
                <option value="compliance">FIRS Compliance Report</option>
                <option value="security">Security Assessment</option>
                <option value="financial">Financial Reconciliation</option>
              </select>
            </div>
            <div className="mt-6">
              <TaxPoyntButton
                variant="primary"
                onClick={generateNewReport}
                disabled={generating}
                className="bg-purple-600 hover:bg-purple-700"
              >
                {generating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Generating...
                  </>
                ) : (
                  <>
                    📋 Generate Report
                  </>
                )}
              </TaxPoyntButton>
            </div>
          </div>
        </div>

        {/* Recent Reports */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Reports</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Report
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Progress
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Deadline
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {metrics?.reports.map((report) => (
                  <tr key={report.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">{getTypeIcon(report.type)}</span>
                        <div>
                          <div className="text-sm font-medium text-gray-900">{report.title}</div>
                          <div className="text-sm text-gray-500">{report.id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="capitalize text-sm text-gray-900">{report.type}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(report.status)}`}>
                        {report.status.charAt(0).toUpperCase() + report.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${report.completionPercentage}%` }}
                        ></div>
                      </div>
                      <span className="text-xs text-gray-500 mt-1">{report.completionPercentage}%</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {report.deadline}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button className="text-purple-600 hover:text-purple-900">View</button>
                        <button className="text-blue-600 hover:text-blue-900">Edit</button>
                        <button className="text-green-600 hover:text-green-900">Download</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Compliance Timeline */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Upcoming Deadlines</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-orange-50 rounded-lg border border-orange-200">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-orange-500 rounded-full mr-4"></div>
                <div>
                  <div className="font-medium text-gray-900">Q1 Financial Reconciliation</div>
                  <div className="text-sm text-gray-600">Due in {metrics?.nextDeadline}</div>
                </div>
              </div>
              <TaxPoyntButton variant="outline" size="sm">
                View Details
              </TaxPoyntButton>
            </div>
            <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-blue-500 rounded-full mr-4"></div>
                <div>
                  <div className="font-medium text-gray-900">Security Audit Review</div>
                  <div className="text-sm text-gray-600">Due in 8 days</div>
                </div>
              </div>
              <TaxPoyntButton variant="outline" size="sm">
                View Details
              </TaxPoyntButton>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
