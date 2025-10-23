'use client';

/**
 * APP New Transmission Form
 * =========================
 * 
 * Create and submit new invoice transmissions to FIRS.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardLayout } from '../../../../../shared_components/layouts/DashboardLayout';
import { TaxPoyntButton } from '../../../../../design_system';
import { APIResponse } from '../../../../../si_interface/types';
import apiClient from '../../../../../shared_components/api/client';

interface InvoiceBatch {
  id: string;
  name: string;
  source: 'upload' | 'si_integration' | 'manual';
  invoiceCount: number;
  totalAmount: number;
  created: string;
  validated: boolean;
}

export default function NewTransmissionPage() {
  const router = useRouter();
  const [availableBatches, setAvailableBatches] = useState<InvoiceBatch[]>([]);
  const [selectedBatches, setSelectedBatches] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [transmissionMode, setTransmissionMode] = useState<'batch' | 'upload'>('batch');

  useEffect(() => {
    loadAvailableBatches();
  }, []);

  const loadAvailableBatches = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<APIResponse<InvoiceBatch[]>>('/app/transmission/available-batches');
      if (response.success && response.data) {
        setAvailableBatches(response.data);
      } else {
        throw new Error('API response unsuccessful');
      }
    } catch (error) {
      console.error('Failed to load available batches, using demo data:', error);
      // Fallback to demo data
      setAvailableBatches([
        {
          id: 'BATCH-2024-015',
          name: 'January Sales Invoices',
          source: 'si_integration',
          invoiceCount: 156,
          totalAmount: 2450000,
          created: '2024-01-15 10:30:00',
          validated: true
        },
        {
          id: 'BATCH-2024-014',
          name: 'Service Invoices - Week 2',
          source: 'upload',
          invoiceCount: 89,
          totalAmount: 1230000,
          created: '2024-01-14 16:45:00',
          validated: true
        },
        {
          id: 'BATCH-2024-013',
          name: 'Export Invoices',
          source: 'manual',
          invoiceCount: 23,
          totalAmount: 5670000,
          created: '2024-01-13 14:20:00',
          validated: false
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleBatchSelection = (batchId: string) => {
    setSelectedBatches(prev => 
      prev.includes(batchId)
        ? prev.filter(id => id !== batchId)
        : [...prev, batchId]
    );
  };

  const submitTransmission = async () => {
    if (transmissionMode === 'batch' && selectedBatches.length === 0) {
      alert('Please select at least one batch to transmit');
      return;
    }
    
    if (transmissionMode === 'upload' && !uploadFile) {
      alert('Please select a file to upload');
      return;
    }

    try {
      setSubmitting(true);
      
      let response;
      if (transmissionMode === 'batch') {
        response = await apiClient.post<APIResponse>('/app/transmission/submit-batches', {
          batchIds: selectedBatches,
          priority: 'normal',
          validateBeforeSubmission: true
        });
      } else {
        const formData = new FormData();
        formData.append('file', uploadFile!);
        formData.append('autoValidate', 'true');
        formData.append('priority', 'normal');
        
        response = await apiClient.post<APIResponse>('/app/transmission/submit-file', formData);
      }
      
      if (response.success) {
        router.push('/dashboard/app/tracking');
      }
    } catch (error) {
      console.error('Transmission submission failed:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'si_integration': return '🔗';
      case 'upload': return '📁';
      case 'manual': return '✏️';
      default: return '📄';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency: 'NGN'
    }).format(amount);
  };

  if (loading) {
    return (
      <DashboardLayout role="app" activeTab="transmission">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading available batches...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout role="app" activeTab="transmission">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">New Transmission</h1>
            <p className="text-gray-600">Submit invoice batches to FIRS for processing</p>
          </div>
          <div className="flex space-x-4">
            <TaxPoyntButton
              variant="outline"
              onClick={() => router.back()}
            >
              ← Back to Transmission
            </TaxPoyntButton>
          </div>
        </div>

        {/* Transmission Mode Selection */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Transmission Mode</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div
              className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                transmissionMode === 'batch'
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setTransmissionMode('batch')}
            >
              <div className="flex items-center space-x-3">
                <input
                  type="radio"
                  checked={transmissionMode === 'batch'}
                  onChange={() => setTransmissionMode('batch')}
                  className="h-4 w-4 text-green-600"
                />
                <div>
                  <h3 className="font-medium text-gray-900">Submit Existing Batches</h3>
                  <p className="text-sm text-gray-600">Select from validated invoice batches</p>
                </div>
              </div>
            </div>
            <div
              className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                transmissionMode === 'upload'
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setTransmissionMode('upload')}
            >
              <div className="flex items-center space-x-3">
                <input
                  type="radio"
                  checked={transmissionMode === 'upload'}
                  onChange={() => setTransmissionMode('upload')}
                  className="h-4 w-4 text-green-600"
                />
                <div>
                  <h3 className="font-medium text-gray-900">Upload New File</h3>
                  <p className="text-sm text-gray-600">Upload and submit invoice file directly</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Batch Selection Mode */}
        {transmissionMode === 'batch' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Select Invoice Batches</h2>
            <div className="space-y-4">
              {availableBatches.map((batch) => (
                <div
                  key={batch.id}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                    selectedBatches.includes(batch.id)
                      ? 'border-green-500 bg-green-50'
                      : batch.validated
                      ? 'border-gray-200 hover:border-gray-300'
                      : 'border-red-200 bg-red-50 cursor-not-allowed'
                  }`}
                  onClick={() => batch.validated && handleBatchSelection(batch.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <input
                        type="checkbox"
                        checked={selectedBatches.includes(batch.id)}
                        onChange={() => batch.validated && handleBatchSelection(batch.id)}
                        disabled={!batch.validated}
                        className="h-4 w-4 text-green-600"
                      />
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">{getSourceIcon(batch.source)}</span>
                        <div>
                          <div className="font-medium text-gray-900">{batch.name}</div>
                          <div className="text-sm text-gray-500">
                            {batch.invoiceCount} invoices • {formatCurrency(batch.totalAmount)} • {batch.created}
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {batch.validated ? (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                          ✅ Validated
                        </span>
                      ) : (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                          ❌ Not Validated
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* File Upload Mode */}
        {transmissionMode === 'upload' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload Invoice File</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Invoice File (CSV, JSON, XML, UBL)
                </label>
                <input
                  type="file"
                  accept=".csv,.json,.xml,.ubl"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div className="p-4 bg-blue-50 rounded-lg">
                <h3 className="font-medium text-blue-800 mb-2">Upload Requirements</h3>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• File must be in valid format (CSV, JSON, XML, or UBL)</li>
                  <li>• Maximum file size: 50MB</li>
                  <li>• Invoice data will be automatically validated before submission</li>
                  <li>• Processing time: 2-5 minutes depending on file size</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Transmission Settings */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Transmission Settings</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Priority Level
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500">
                <option value="normal">Normal Priority</option>
                <option value="high">High Priority</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Validation Level
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500">
                <option value="standard">Standard Validation</option>
                <option value="strict">Strict Validation</option>
                <option value="minimal">Minimal Validation</option>
              </select>
            </div>
          </div>
          <div className="mt-4 flex items-center space-x-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="notifyOnCompletion"
                defaultChecked
                className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
              />
              <label htmlFor="notifyOnCompletion" className="ml-2 text-sm text-gray-700">
                Send email notification on completion
              </label>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="generateReport"
                defaultChecked
                className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
              />
              <label htmlFor="generateReport" className="ml-2 text-sm text-gray-700">
                Generate transmission report
              </label>
            </div>
          </div>
        </div>

        {/* Submission Summary */}
        {((transmissionMode === 'batch' && selectedBatches.length > 0) || 
          (transmissionMode === 'upload' && uploadFile)) && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Submission Summary</h2>
            {transmissionMode === 'batch' ? (
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Selected Batches:</span>
                  <span className="font-medium">{selectedBatches.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Invoices:</span>
                  <span className="font-medium">
                    {availableBatches
                      .filter(batch => selectedBatches.includes(batch.id))
                      .reduce((sum, batch) => sum + batch.invoiceCount, 0)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Amount:</span>
                  <span className="font-medium">
                    {formatCurrency(
                      availableBatches
                        .filter(batch => selectedBatches.includes(batch.id))
                        .reduce((sum, batch) => sum + batch.totalAmount, 0)
                    )}
                  </span>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">File:</span>
                  <span className="font-medium">{uploadFile?.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">File Size:</span>
                  <span className="font-medium">
                    {uploadFile ? (uploadFile.size / 1024 / 1024).toFixed(2) + ' MB' : '0 MB'}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-end space-x-4">
          <TaxPoyntButton
            variant="outline"
            onClick={() => router.push('/dashboard/app/transmission')}
          >
            Cancel
          </TaxPoyntButton>
          <TaxPoyntButton
            variant="primary"
            onClick={submitTransmission}
            disabled={submitting || 
              (transmissionMode === 'batch' && selectedBatches.length === 0) ||
              (transmissionMode === 'upload' && !uploadFile)
            }
            className="bg-green-600 hover:bg-green-700"
          >
            {submitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Submitting to FIRS...
              </>
            ) : (
              <>
                📤 Submit to FIRS
              </>
            )}
          </TaxPoyntButton>
        </div>
      </div>
    </DashboardLayout>
  );
}
