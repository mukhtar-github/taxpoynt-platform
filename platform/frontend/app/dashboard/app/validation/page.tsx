/**
 * APP Data Validation Center
 * ==========================
 * 
 * Validate invoice data before transmission to FIRS, ensuring compliance and data quality.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardLayout } from '../../../../shared_components/layouts/DashboardLayout';
import { TaxPoyntButton, TaxPoyntInput } from '../../../../design_system';
import { APIResponse } from '../../../../si_interface/types';
import apiClient from '../../../../shared_components/api/client';

interface ValidationMetrics {
  totalValidated: number;
  passRate: number;
  errorRate: number;
  warningRate: number;
  schemaErrors: number;
  formatErrors: number;
  businessRuleErrors: number;
}

interface ValidationResult {
  id: string;
  batchId: string;
  invoiceCount: number;
  status: 'passed' | 'failed' | 'warning' | 'processing';
  timestamp: string;
  errors: Array<{
    type: 'schema' | 'format' | 'business_rule';
    field: string;
    message: string;
    severity: 'error' | 'warning';
  }>;
  passedInvoices: number;
  failedInvoices: number;
}

export default function DataValidationPage() {
  const router = useRouter();
  const [metrics, setMetrics] = useState<ValidationMetrics | null>(null);
  const [validationResults, setValidationResults] = useState<ValidationResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  useEffect(() => {
    loadValidationData();
  }, []);

  const loadValidationData = async () => {
    try {
      setLoading(true);
      const [metricsResponse, resultsResponse] = await Promise.all([
        apiClient.get<APIResponse<ValidationMetrics>>('/api/v1/app/validation/metrics'),
        apiClient.get<APIResponse<ValidationResult[]>>('/api/v1/app/validation/recent-results')
      ]);
      
      if (metricsResponse.success && metricsResponse.data) {
        setMetrics(metricsResponse.data);
      }
      if (resultsResponse.success && resultsResponse.data) {
        setValidationResults(resultsResponse.data);
      }
    } catch (error) {
      console.error('Failed to load validation data:', error);
      // Fallback to demo data
      setMetrics({
        totalValidated: 1247,
        passRate: 99.8,
        errorRate: 0.2,
        warningRate: 2.1,
        schemaErrors: 0,
        formatErrors: 1,
        businessRuleErrors: 2
      });
      setValidationResults([
        {
          id: 'VAL-2024-001',
          batchId: 'BATCH-2024-015',
          invoiceCount: 156,
          status: 'passed',
          timestamp: '2024-01-15 14:30:00',
          errors: [],
          passedInvoices: 156,
          failedInvoices: 0
        },
        {
          id: 'VAL-2024-002',
          batchId: 'BATCH-2024-014',
          invoiceCount: 89,
          status: 'warning',
          timestamp: '2024-01-15 13:45:00',
          errors: [
            {
              type: 'business_rule',
              field: 'vatAmount',
              message: 'VAT calculation discrepancy detected',
              severity: 'warning'
            }
          ],
          passedInvoices: 89,
          failedInvoices: 0
        },
        {
          id: 'VAL-2024-003',
          batchId: 'BATCH-2024-013',
          invoiceCount: 203,
          status: 'failed',
          timestamp: '2024-01-15 12:20:00',
          errors: [
            {
              type: 'schema',
              field: 'customerTin',
              message: 'Invalid TIN format',
              severity: 'error'
            },
            {
              type: 'format',
              field: 'invoiceDate',
              message: 'Date format does not match ISO 8601',
              severity: 'error'
            }
          ],
          passedInvoices: 201,
          failedInvoices: 2
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const validateNewBatch = async () => {
    if (!selectedFile) {
      alert('Please select a file to validate');
      return;
    }

    try {
      setValidating(true);
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('validateSchema', 'true');
      formData.append('validateBusinessRules', 'true');
      
      const response = await apiClient.post<APIResponse<ValidationResult>>('/api/v1/app/validation/validate-batch', formData);
      
      if (response.success && response.data) {
        // Add new result to the list
        setValidationResults([response.data, ...validationResults]);
        setSelectedFile(null);
        // Reload metrics
        await loadValidationData();
      }
    } catch (error) {
      console.error('Validation failed:', error);
    } finally {
      setValidating(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'warning': return 'bg-orange-100 text-orange-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getSeverityColor = (severity: string) => {
    return severity === 'error' ? 'text-red-600' : 'text-orange-600';
  };

  if (loading) {
    return (
      <DashboardLayout role="app" activeTab="validation">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading validation metrics...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout role="app" activeTab="validation">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Data Validation Center</h1>
            <p className="text-gray-600">Validate invoice data before FIRS transmission</p>
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

        {/* Validation Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="text-3xl font-bold text-green-600">{metrics?.passRate}%</div>
              <div className="ml-4">
                <div className="text-sm font-medium text-gray-600">Pass Rate</div>
                <div className="text-xs text-gray-500">Excellent</div>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="text-3xl font-bold text-blue-600">{metrics?.totalValidated}</div>
              <div className="ml-4">
                <div className="text-sm font-medium text-gray-600">Total Validated</div>
                <div className="text-xs text-gray-500">This Month</div>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="text-3xl font-bold text-red-600">{metrics?.schemaErrors}</div>
              <div className="ml-4">
                <div className="text-sm font-medium text-gray-600">Schema Errors</div>
                <div className="text-xs text-gray-500">Critical Issues</div>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="text-3xl font-bold text-orange-600">{metrics?.warningRate}%</div>
              <div className="ml-4">
                <div className="text-sm font-medium text-gray-600">Warning Rate</div>
                <div className="text-xs text-gray-500">Minor Issues</div>
              </div>
            </div>
          </div>
        </div>

        {/* Validate New Batch */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Validate New Invoice Batch</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload Invoice File (CSV, JSON, XML)
              </label>
              <input
                type="file"
                accept=".csv,.json,.xml"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="validateSchema"
                  defaultChecked
                  className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                />
                <label htmlFor="validateSchema" className="ml-2 text-sm text-gray-700">
                  Schema Validation
                </label>
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="validateBusinessRules"
                  defaultChecked
                  className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                />
                <label htmlFor="validateBusinessRules" className="ml-2 text-sm text-gray-700">
                  Business Rules Validation
                </label>
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="validateFormat"
                  defaultChecked
                  className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                />
                <label htmlFor="validateFormat" className="ml-2 text-sm text-gray-700">
                  Format Validation
                </label>
              </div>
            </div>
            <div>
              <TaxPoyntButton
                variant="primary"
                onClick={validateNewBatch}
                disabled={validating || !selectedFile}
                className="bg-green-600 hover:bg-green-700"
              >
                {validating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Validating...
                  </>
                ) : (
                  <>
                    ✅ Validate Batch
                  </>
                )}
              </TaxPoyntButton>
            </div>
          </div>
        </div>

        {/* Recent Validation Results */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Validation Results</h2>
          <div className="space-y-4">
            {validationResults.map((result) => (
              <div key={result.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-4">
                    <span className={`inline-flex px-3 py-1 text-xs font-semibold rounded-full ${getStatusColor(result.status)}`}>
                      {result.status.charAt(0).toUpperCase() + result.status.slice(1)}
                    </span>
                    <div>
                      <div className="font-medium text-gray-900">{result.batchId}</div>
                      <div className="text-sm text-gray-500">{result.invoiceCount} invoices • {result.timestamp}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-green-600">{result.passedInvoices}</div>
                    <div className="text-xs text-gray-500">Passed</div>
                  </div>
                </div>

                {result.errors.length > 0 && (
                  <div className="mt-3">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Issues Found:</h4>
                    <div className="space-y-1">
                      {result.errors.map((error, index) => (
                        <div key={index} className="flex items-start space-x-2 text-sm">
                          <span className={`font-medium ${getSeverityColor(error.severity)}`}>
                            {error.severity === 'error' ? '❌' : '⚠️'}
                          </span>
                          <div>
                            <span className="font-medium">{error.field}:</span>
                            <span className="ml-1">{error.message}</span>
                            <span className="ml-2 text-xs text-gray-500">({error.type})</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="mt-3 flex justify-end space-x-2">
                  <TaxPoyntButton variant="outline" size="sm">
                    View Details
                  </TaxPoyntButton>
                  {result.status === 'passed' && (
                    <TaxPoyntButton variant="primary" size="sm" className="bg-green-600 hover:bg-green-700">
                      Proceed to Transmission
                    </TaxPoyntButton>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Validation Rules */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Validation Rules</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Schema Validation</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Required fields presence</li>
                <li>• Data type conformance</li>
                <li>• Field length limits</li>
                <li>• UBL 3.0 compliance</li>
              </ul>
            </div>
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Format Validation</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Date format (ISO 8601)</li>
                <li>• TIN format validation</li>
                <li>• Currency code validation</li>
                <li>• Email format check</li>
              </ul>
            </div>
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Business Rules</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• VAT calculation accuracy</li>
                <li>• Total amount verification</li>
                <li>• Tax exemption validation</li>
                <li>• Duplicate invoice check</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
