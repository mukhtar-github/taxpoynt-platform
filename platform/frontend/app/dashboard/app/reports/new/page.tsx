/**
 * APP New Report Generator
 * ========================
 * 
 * Generate custom compliance and transmission reports.
 */

'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardLayout } from '../../../../../shared_components/layouts/DashboardLayout';
import { TaxPoyntButton, TaxPoyntInput } from '../../../../../design_system';
import { APIResponse } from '../../../../../si_interface/types';
import apiClient from '../../../../../shared_components/api/client';

interface ReportConfig {
  type: 'transmission' | 'compliance' | 'security' | 'financial';
  format: 'pdf' | 'excel' | 'csv';
  dateRange: {
    start: string;
    end: string;
  };
  includeMetrics: boolean;
  includeCharts: boolean;
  includeDetails: boolean;
  filters: {
    status?: string[];
    amount?: { min: number; max: number };
    invoiceTypes?: string[];
  };
}

interface ReportTypeOption {
  value: ReportConfig['type'];
  label: string;
  description: string;
  icon: string;
}

export default function NewReportPage() {
  const router = useRouter();
  const [config, setConfig] = useState<ReportConfig>({
    type: 'transmission',
    format: 'pdf',
    dateRange: {
      start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end: new Date().toISOString().split('T')[0]
    },
    includeMetrics: true,
    includeCharts: true,
    includeDetails: false,
    filters: {}
  });
  const [generating, setGenerating] = useState(false);

  const generateReport = async () => {
    try {
      setGenerating(true);
      const response = await apiClient.post<APIResponse<{ reportId: string; downloadUrl: string }>>('/app/reports/generate', config);
      
      if (response.success && response.data) {
        // Download the report
        if (response.data.downloadUrl) {
          window.open(response.data.downloadUrl, '_blank');
        }
        router.push('/dashboard/app/compliance');
      } else {
        // Demo: Generate a sample report
        const demoUrl = `data:text/plain;charset=utf-8,DEMO REPORT%0A%0AReport Type: ${config.type}%0AGenerated: ${new Date().toISOString()}%0A%0AThis is a demo report. In production, this would contain real data.`;
        window.open(demoUrl, '_blank');
      }
    } catch (error) {
      console.error('Report generation failed, using demo:', error);
      // Demo: Generate a sample report
      const demoUrl = `data:text/plain;charset=utf-8,DEMO REPORT%0A%0AReport Type: ${config.type}%0AGenerated: ${new Date().toISOString()}%0A%0AThis is a demo report. In production, this would contain real data.`;
      window.open(demoUrl, '_blank');
    } finally {
      setGenerating(false);
    }
  };

  const updateConfig = (updates: Partial<ReportConfig>) => {
    setConfig(prev => ({ ...prev, ...updates }));
  };

  const updateDateRange = (field: 'start' | 'end', value: string) => {
    setConfig(prev => ({
      ...prev,
      dateRange: { ...prev.dateRange, [field]: value }
    }));
  };

  const reportTypes: ReportTypeOption[] = [
    {
      value: 'transmission',
      label: 'Transmission Report',
      description: 'Detailed analysis of FIRS transmissions and responses',
      icon: '📤'
    },
    {
      value: 'compliance',
      label: 'Compliance Report',
      description: 'Regulatory compliance status and audit trail',
      icon: '📋'
    },
    {
      value: 'security',
      label: 'Security Report',
      description: 'Security assessments and threat analysis',
      icon: '🛡️'
    },
    {
      value: 'financial',
      label: 'Financial Report',
      description: 'Financial metrics and transaction summaries',
      icon: '💰'
    }
  ];

  return (
    <DashboardLayout role="app" activeTab="reports">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Generate New Report</h1>
            <p className="text-gray-600">Create custom compliance and transmission reports</p>
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

        {/* Report Type Selection */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Report Type</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {reportTypes.map((type) => (
              <div
                key={type.value}
                className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  config.type === type.value
                    ? 'border-purple-500 bg-purple-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => updateConfig({ type: type.value })}
              >
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{type.icon}</span>
                  <div>
                    <h3 className="font-medium text-gray-900">{type.label}</h3>
                    <p className="text-sm text-gray-600">{type.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Date Range */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Date Range</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Start Date
              </label>
              <input
                type="date"
                value={config.dateRange.start}
                onChange={(e) => updateDateRange('start', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                End Date
              </label>
              <input
                type="date"
                value={config.dateRange.end}
                onChange={(e) => updateDateRange('end', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>
          <div className="mt-4 flex space-x-2">
            {[
              { label: 'Last 7 Days', days: 7 },
              { label: 'Last 30 Days', days: 30 },
              { label: 'Last 90 Days', days: 90 },
              { label: 'This Year', days: 365 }
            ].map((preset) => (
              <TaxPoyntButton
                key={preset.label}
                variant="outline"
                size="sm"
                onClick={() => {
                  const end = new Date().toISOString().split('T')[0];
                  const start = new Date(Date.now() - preset.days * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
                  updateConfig({ dateRange: { start, end } });
                }}
              >
                {preset.label}
              </TaxPoyntButton>
            ))}
          </div>
        </div>

        {/* Report Options */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Report Options</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Output Format
              </label>
              <select
                value={config.format}
                onChange={(e) => updateConfig({ format: e.target.value as ReportConfig['format'] })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="pdf">PDF Document</option>
                <option value="excel">Excel Spreadsheet</option>
                <option value="csv">CSV Data File</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Content Options
              </label>
              <div className="space-y-2">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="includeMetrics"
                    checked={config.includeMetrics}
                    onChange={(e) => updateConfig({ includeMetrics: e.target.checked })}
                    className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                  />
                  <label htmlFor="includeMetrics" className="ml-2 text-sm text-gray-700">
                    Include Summary Metrics
                  </label>
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="includeCharts"
                    checked={config.includeCharts}
                    onChange={(e) => updateConfig({ includeCharts: e.target.checked })}
                    className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                  />
                  <label htmlFor="includeCharts" className="ml-2 text-sm text-gray-700">
                    Include Charts and Graphs
                  </label>
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="includeDetails"
                    checked={config.includeDetails}
                    onChange={(e) => updateConfig({ includeDetails: e.target.checked })}
                    className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                  />
                  <label htmlFor="includeDetails" className="ml-2 text-sm text-gray-700">
                    Include Detailed Transaction Data
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        {config.type === 'transmission' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Transmission Filters</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Status Filter
                </label>
                <div className="space-y-2">
                  {['completed', 'processing', 'failed', 'rejected'].map((status) => (
                    <div key={status} className="flex items-center">
                      <input
                        type="checkbox"
                        id={`status-${status}`}
                        className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                      />
                      <label htmlFor={`status-${status}`} className="ml-2 text-sm text-gray-700 capitalize">
                        {status}
                      </label>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Amount Range (NGN)
                </label>
                <div className="space-y-2">
                  <TaxPoyntInput
                    placeholder="Minimum Amount"
                    type="number"
                  />
                  <TaxPoyntInput
                    placeholder="Maximum Amount"
                    type="number"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Preview */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Report Preview</h2>
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="space-y-2 text-sm text-gray-700">
              <div><strong>Type:</strong> {reportTypes.find(t => t.value === config.type)?.label}</div>
              <div><strong>Date Range:</strong> {config.dateRange.start} to {config.dateRange.end}</div>
              <div><strong>Format:</strong> {config.format.toUpperCase()}</div>
              <div><strong>Options:</strong> 
                {config.includeMetrics && ' Metrics'}
                {config.includeCharts && ' Charts'}
                {config.includeDetails && ' Details'}
              </div>
            </div>
          </div>
        </div>

        {/* Generate Button */}
        <div className="flex justify-end space-x-4">
          <TaxPoyntButton
            variant="outline"
            onClick={() => router.push('/dashboard/app/compliance')}
          >
            Cancel
          </TaxPoyntButton>
          <TaxPoyntButton
            variant="primary"
            onClick={generateReport}
            disabled={generating}
            className="bg-purple-600 hover:bg-purple-700"
          >
            {generating ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Generating Report...
              </>
            ) : (
              <>
                📋 Generate Report
              </>
            )}
          </TaxPoyntButton>
        </div>
      </div>
    </DashboardLayout>
  );
}
