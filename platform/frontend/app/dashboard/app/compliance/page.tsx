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
import { TaxPoyntButton } from '../../../../design_system';
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
  slaHours?: number;
  reports: ComplianceReport[];
}

export default function ComplianceReportsPage() {
  const router = useRouter();
  const [metrics, setMetrics] = useState<ComplianceMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedReportType, setSelectedReportType] = useState('audit');
  const [isDemo, setIsDemo] = useState(false);
  const [slaInput, setSlaInput] = useState('');
  const [savingSla, setSavingSla] = useState(false);
  const [slaMessage, setSlaMessage] = useState<string | null>(null);
  const [slaMetadata, setSlaMetadata] = useState<{ updatedAt?: string; updatedBy?: string } | null>(null);

  const formatTimestamp = (value?: string) => {
    if (!value) return 'N/A';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return new Intl.DateTimeFormat('en-NG', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(parsed);
  };

  const formatDueIn = (deadline?: string) => {
    if (!deadline) return 'No pending deadlines';
    const parsed = new Date(deadline);
    if (Number.isNaN(parsed.getTime())) return deadline;
    const diffMs = parsed.getTime() - Date.now();
    const diffHours = diffMs / (1000 * 60 * 60);
    if (diffHours <= 0) return 'Overdue';
    if (diffHours < 1) return `${Math.round(diffHours * 60)} minutes`;
    if (diffHours < 24) return `${Math.round(diffHours)} hours`;
    return `${Math.round(diffHours / 24)} days`;
  };

  const loadComplianceMetrics = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<APIResponse<ComplianceMetrics>>('/app/compliance/metrics');
      if (response.success && response.data) {
        setMetrics(response.data);
        setIsDemo(false);
        if (response.data.slaHours !== undefined) {
          setSlaInput(String(response.data.slaHours));
        }
      } else {
        throw new Error('API response unsuccessful');
      }
    } catch (error) {
      console.error('Failed to load compliance metrics, using demo data:', error);
      setIsDemo(true);
      const now = Date.now();
      const hours = (h: number) => new Date(now + h * 60 * 60 * 1000).toISOString();
      setMetrics({
        totalReports: 145,
        pendingReports: 3,
        overdue: 0,
        complianceScore: 98,
        lastAudit: hours(-24 * 14),
        nextDeadline: hours(24 * 5),
        slaHours: 4,
        reports: [
          {
            id: 'RPT-2024-001',
            title: 'Q1 2024 FIRS Compliance Report',
            type: 'compliance',
            status: 'approved',
            created: hours(-24 * 10),
            deadline: hours(-24 * 5),
            completionPercentage: 100
          },
          {
            id: 'RPT-2024-002',
            title: 'Security Audit Report - January',
            type: 'security',
            status: 'pending',
            created: hours(-24 * 6),
            deadline: hours(24 * 1),
            completionPercentage: 85
          },
          {
            id: 'RPT-2024-003',
            title: 'Financial Reconciliation Report',
            type: 'financial',
            status: 'draft',
            created: hours(-24 * 3),
            deadline: hours(24 * 2),
            completionPercentage: 60
          },
          {
            id: 'RPT-2024-004',
            title: 'Data Protection Compliance',
            type: 'audit',
            status: 'submitted',
            created: hours(-24 * 5),
            deadline: hours(-24 * 1),
            completionPercentage: 100
          }
        ]
      });
      setSlaInput('4');
      setSlaMetadata(null);
    } finally {
      setLoading(false);
    }
  };

  const loadComplianceSla = async () => {
    try {
      const response = await apiClient.get<APIResponse<{ slaHours?: number; updatedAt?: string; updatedBy?: string }>>(
        '/app/setup/compliance-sla'
      );
      if (response.success && response.data) {
        if (response.data.slaHours !== undefined) {
          setSlaInput(String(response.data.slaHours));
        }
        setSlaMetadata({
          updatedAt: response.data.updatedAt,
          updatedBy: response.data.updatedBy,
        });
      }
    } catch (error) {
      console.error('Failed to load compliance SLA configuration:', error);
    }
  };

  useEffect(() => {
    loadComplianceMetrics();
    loadComplianceSla();
  }, []);

  const handleSlaSave = async () => {
    const parsed = Number(slaInput);
    if (!Number.isFinite(parsed) || parsed < 1 || parsed > 168) {
      setSlaMessage('Please enter a value between 1 and 168 hours.');
      return;
    }

    setSavingSla(true);
    setSlaMessage(null);

    try {
      const response = await apiClient.patch<APIResponse<{ slaHours: number; updatedAt?: string; updatedBy?: string }>>(
        '/app/setup/compliance-sla',
        { sla_hours: parsed }
      );

      if (response.success && response.data) {
        setSlaMessage('SLA threshold updated.');
        setSlaInput(String(response.data.slaHours));
        setMetrics((prev) => (prev ? { ...prev, slaHours: response.data.slaHours } : prev));
        setSlaMetadata({
          updatedAt: response.data.updatedAt,
          updatedBy: response.data.updatedBy,
        });
      } else {
        throw new Error('API response unsuccessful');
      }
    } catch (error) {
      console.error('Failed to update SLA threshold:', error);
      setSlaMessage('Unable to update SLA threshold. Please try again.');
    } finally {
      setSavingSla(false);
    }
  };

  const generateNewReport = async () => {
    try {
      setGenerating(true);
      const response = await apiClient.post<APIResponse>('/app/compliance/generate-report', {
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
                <div className="text-xs text-gray-500">Past {(metrics?.slaHours ?? 4)}h SLA</div>
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

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-xs uppercase text-gray-500">Last Audit</div>
            <div className="text-sm font-medium text-gray-800">{formatTimestamp(metrics?.lastAudit)}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-xs uppercase text-gray-500">Next Deadline</div>
            <div className="text-sm font-medium text-gray-800">{formatTimestamp(metrics?.nextDeadline)}</div>
            <div className="text-xs text-gray-500">Due in {formatDueIn(metrics?.nextDeadline)}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-xs uppercase text-gray-500">SLA Threshold</div>
            <div className="text-sm font-medium text-gray-800">{metrics?.slaHours ?? 4} hours</div>
            <div className="mt-3 flex items-center space-x-2">
              <input
                type="number"
                min={1}
                max={168}
                value={slaInput}
                onChange={(event) => setSlaInput(event.target.value)}
                className="w-20 px-2 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              <TaxPoyntButton
                variant="outline"
                size="sm"
                onClick={handleSlaSave}
                loading={savingSla}
                disabled={savingSla}
              >
                Save
              </TaxPoyntButton>
            </div>
            {slaMessage && (
              <div className="mt-2 text-xs text-gray-600">{slaMessage}</div>
            )}
            {slaMetadata?.updatedAt && (
              <div className="mt-1 text-xs text-gray-400">
                Updated {formatTimestamp(slaMetadata.updatedAt)}
                {slaMetadata.updatedBy ? ` · ${slaMetadata.updatedBy}` : ''}
              </div>
            )}
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
                      <div>{formatTimestamp(report.deadline)}</div>
                      <div className="text-xs text-gray-500">{formatDueIn(report.deadline)}</div>
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
                  <div className="text-sm text-gray-600">Due in {formatDueIn(metrics?.nextDeadline)}</div>
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
