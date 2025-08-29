/**
 * APP Status Tracking Center
 * ==========================
 * 
 * Real-time tracking of invoice transmission status and FIRS responses.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardLayout } from '../../../../shared_components/layouts/DashboardLayout';
import { TaxPoyntButton, TaxPoyntInput } from '../../../../design_system';
import { APIResponse } from '../../../../si_interface/types';
import apiClient from '../../../../shared_components/api/client';

interface TransmissionStatus {
  id: string;
  batchId: string;
  submittedAt: string;
  status: 'submitted' | 'processing' | 'acknowledged' | 'accepted' | 'rejected' | 'failed';
  invoiceCount: number;
  processedCount: number;
  acceptedCount: number;
  rejectedCount: number;
  firsResponse?: {
    acknowledgeId: string;
    responseDate: string;
    message: string;
    details: Array<{
      invoiceId: string;
      status: 'accepted' | 'rejected';
      reason?: string;
    }>;
  };
}

interface TrackingMetrics {
  totalTransmissions: number;
  processing: number;
  completed: number;
  failed: number;
  averageProcessingTime: string;
}

export default function StatusTrackingPage() {
  const router = useRouter();
  const [metrics, setMetrics] = useState<TrackingMetrics | null>(null);
  const [transmissions, setTransmissions] = useState<TransmissionStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    loadTrackingData();
    // Set up polling for real-time updates
    const interval = setInterval(loadTrackingData, 30000); // Every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadTrackingData = async () => {
    try {
      setLoading(true);
      const [metricsResponse, transmissionsResponse] = await Promise.all([
        apiClient.get<APIResponse<TrackingMetrics>>('/api/v1/app/tracking/metrics'),
        apiClient.get<APIResponse<TransmissionStatus[]>>('/api/v1/app/tracking/transmissions')
      ]);
      
      if (metricsResponse.success && metricsResponse.data) {
        setMetrics(metricsResponse.data);
      }
      if (transmissionsResponse.success && transmissionsResponse.data) {
        setTransmissions(transmissionsResponse.data);
      }
    } catch (error) {
      console.error('Failed to load tracking data:', error);
      // Fallback to demo data
      setMetrics({
        totalTransmissions: 456,
        processing: 23,
        completed: 430,
        failed: 3,
        averageProcessingTime: '2.5 minutes'
      });
      setTransmissions([
        {
          id: 'TX-2024-001',
          batchId: 'BATCH-2024-015',
          submittedAt: '2024-01-15 14:30:00',
          status: 'accepted',
          invoiceCount: 156,
          processedCount: 156,
          acceptedCount: 156,
          rejectedCount: 0,
          firsResponse: {
            acknowledgeId: 'ACK-FIRS-2024-001',
            responseDate: '2024-01-15 14:32:15',
            message: 'All invoices processed successfully',
            details: []
          }
        },
        {
          id: 'TX-2024-002',
          batchId: 'BATCH-2024-014',
          submittedAt: '2024-01-15 13:45:00',
          status: 'processing',
          invoiceCount: 89,
          processedCount: 67,
          acceptedCount: 67,
          rejectedCount: 0
        },
        {
          id: 'TX-2024-003',
          batchId: 'BATCH-2024-013',
          submittedAt: '2024-01-15 12:20:00',
          status: 'rejected',
          invoiceCount: 203,
          processedCount: 203,
          acceptedCount: 201,
          rejectedCount: 2,
          firsResponse: {
            acknowledgeId: 'ACK-FIRS-2024-002',
            responseDate: '2024-01-15 12:25:30',
            message: 'Partial rejection - 2 invoices failed validation',
            details: [
              {
                invoiceId: 'INV-001',
                status: 'rejected',
                reason: 'Invalid TIN format'
              },
              {
                invoiceId: 'INV-002',
                status: 'rejected',
                reason: 'VAT calculation error'
              }
            ]
          }
        },
        {
          id: 'TX-2024-004',
          batchId: 'BATCH-2024-012',
          submittedAt: '2024-01-15 11:10:00',
          status: 'failed',
          invoiceCount: 45,
          processedCount: 0,
          acceptedCount: 0,
          rejectedCount: 0
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'accepted': return 'bg-green-100 text-green-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'acknowledged': return 'bg-cyan-100 text-cyan-800';
      case 'submitted': return 'bg-gray-100 text-gray-800';
      case 'rejected': return 'bg-orange-100 text-orange-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'accepted': return '✅';
      case 'processing': return '⏳';
      case 'acknowledged': return '📨';
      case 'submitted': return '📤';
      case 'rejected': return '⚠️';
      case 'failed': return '❌';
      default: return '📄';
    }
  };

  const filteredTransmissions = transmissions.filter(transmission => {
    const matchesSearch = transmission.batchId.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         transmission.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || transmission.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return (
      <DashboardLayout role="app" activeTab="tracking">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading transmission status...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout role="app" activeTab="tracking">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Status Tracking</h1>
            <p className="text-gray-600">Monitor invoice transmission status and FIRS responses</p>
          </div>
          <div className="flex space-x-4">
            <TaxPoyntButton
              variant="outline"
              onClick={() => router.back()}
            >
              ← Back to Dashboard
            </TaxPoyntButton>
            <TaxPoyntButton
              variant="primary"
              onClick={() => loadTrackingData()}
              className="bg-blue-600 hover:bg-blue-700"
            >
              🔄 Refresh Status
            </TaxPoyntButton>
          </div>
        </div>

        {/* Tracking Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="text-3xl font-bold text-blue-600">{metrics?.processing}</div>
              <div className="ml-4">
                <div className="text-sm font-medium text-gray-600">Processing</div>
                <div className="text-xs text-gray-500">Active</div>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="text-3xl font-bold text-green-600">{metrics?.completed}</div>
              <div className="ml-4">
                <div className="text-sm font-medium text-gray-600">Completed</div>
                <div className="text-xs text-gray-500">Success</div>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="text-3xl font-bold text-red-600">{metrics?.failed}</div>
              <div className="ml-4">
                <div className="text-sm font-medium text-gray-600">Failed</div>
                <div className="text-xs text-gray-500">Errors</div>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="text-lg font-bold text-purple-600">{metrics?.averageProcessingTime}</div>
              <div className="ml-4">
                <div className="text-sm font-medium text-gray-600">Avg. Processing</div>
                <div className="text-xs text-gray-500">Time</div>
              </div>
            </div>
          </div>
        </div>

        {/* Search and Filter */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <TaxPoyntInput
                placeholder="Search by batch ID or transmission ID..."
                value={searchTerm}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
              />
            </div>
            <div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Status</option>
                <option value="submitted">Submitted</option>
                <option value="processing">Processing</option>
                <option value="acknowledged">Acknowledged</option>
                <option value="accepted">Accepted</option>
                <option value="rejected">Rejected</option>
                <option value="failed">Failed</option>
              </select>
            </div>
          </div>
        </div>

        {/* Transmission Status List */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Transmission History</h2>
          <div className="space-y-4">
            {filteredTransmissions.map((transmission) => (
              <div key={transmission.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-4">
                    <span className="text-2xl">{getStatusIcon(transmission.status)}</span>
                    <div>
                      <div className="font-medium text-gray-900">{transmission.batchId}</div>
                      <div className="text-sm text-gray-500">
                        Submitted: {transmission.submittedAt} • {transmission.invoiceCount} invoices
                      </div>
                    </div>
                  </div>
                  <span className={`inline-flex px-3 py-1 text-xs font-semibold rounded-full ${getStatusColor(transmission.status)}`}>
                    {transmission.status.charAt(0).toUpperCase() + transmission.status.slice(1)}
                  </span>
                </div>

                {/* Progress Bar */}
                <div className="mb-3">
                  <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                    <span>Progress</span>
                    <span>{transmission.processedCount} / {transmission.invoiceCount} processed</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${(transmission.processedCount / transmission.invoiceCount) * 100}%` }}
                    ></div>
                  </div>
                </div>

                {/* Results Summary */}
                <div className="grid grid-cols-3 gap-4 mb-3">
                  <div className="text-center">
                    <div className="text-lg font-bold text-green-600">{transmission.acceptedCount}</div>
                    <div className="text-xs text-gray-500">Accepted</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-orange-600">{transmission.rejectedCount}</div>
                    <div className="text-xs text-gray-500">Rejected</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-blue-600">
                      {transmission.invoiceCount - transmission.processedCount}
                    </div>
                    <div className="text-xs text-gray-500">Pending</div>
                  </div>
                </div>

                {/* FIRS Response */}
                {transmission.firsResponse && (
                  <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-medium text-gray-700">FIRS Response</h4>
                      <span className="text-xs text-gray-500">{transmission.firsResponse.responseDate}</span>
                    </div>
                    <div className="text-sm text-gray-600 mb-2">
                      <strong>ID:</strong> {transmission.firsResponse.acknowledgeId}
                    </div>
                    <div className="text-sm text-gray-600 mb-2">
                      {transmission.firsResponse.message}
                    </div>
                    {transmission.firsResponse.details.length > 0 && (
                      <div className="mt-2">
                        <div className="text-xs text-gray-500 mb-1">Rejection Details:</div>
                        {transmission.firsResponse.details.map((detail, index) => (
                          <div key={index} className="text-xs text-red-600">
                            • {detail.invoiceId}: {detail.reason}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Actions */}
                <div className="mt-3 flex justify-end space-x-2">
                  <TaxPoyntButton variant="outline" size="sm">
                    View Details
                  </TaxPoyntButton>
                  {transmission.status === 'rejected' && (
                    <TaxPoyntButton variant="primary" size="sm" className="bg-orange-600 hover:bg-orange-700">
                      Resubmit
                    </TaxPoyntButton>
                  )}
                  {transmission.status === 'failed' && (
                    <TaxPoyntButton variant="primary" size="sm" className="bg-red-600 hover:bg-red-700">
                      Retry
                    </TaxPoyntButton>
                  )}
                  <TaxPoyntButton variant="outline" size="sm">
                    Download Report
                  </TaxPoyntButton>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Real-time Updates Info */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="text-blue-600 mr-3">ℹ️</div>
            <div>
              <div className="text-sm font-medium text-blue-800">Real-time Updates</div>
              <div className="text-sm text-blue-600">
                Status updates are refreshed automatically every 30 seconds. FIRS typically responds within 2-5 minutes.
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
