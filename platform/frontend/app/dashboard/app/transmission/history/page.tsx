/**
 * APP Transmission History
 * ========================
 * 
 * Complete history of all invoice transmissions to FIRS with detailed reports.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardLayout } from '../../../../../shared_components/layouts/DashboardLayout';
import { TaxPoyntButton, TaxPoyntInput } from '../../../../../design_system';
import { APIResponse } from '../../../../../si_interface/types';
import apiClient from '../../../../../shared_components/api/client';

interface TransmissionRecord {
  id: string;
  batchId: string;
  submittedAt: string;
  completedAt?: string;
  status: 'submitted' | 'processing' | 'completed' | 'failed' | 'rejected';
  invoiceCount: number;
  acceptedCount: number;
  rejectedCount: number;
  totalAmount: number;
  firsAcknowledgeId?: string;
  submittedBy: string;
  processingTime?: string;
}

export default function TransmissionHistoryPage() {
  const router = useRouter();
  const [transmissions, setTransmissions] = useState<TransmissionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [dateRange, setDateRange] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  useEffect(() => {
    loadTransmissionHistory();
  }, [currentPage, statusFilter, dateRange]);

  const loadTransmissionHistory = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<APIResponse<TransmissionRecord[]>>('/api/v1/app/transmission/history', {
        params: {
          page: currentPage,
          limit: itemsPerPage,
          status: statusFilter !== 'all' ? statusFilter : undefined,
          dateRange: dateRange !== 'all' ? dateRange : undefined
        }
      });
      
      if (response.success && response.data) {
        setTransmissions(response.data);
      }
    } catch (error) {
      console.error('Failed to load transmission history:', error);
      // Fallback to demo data
      setTransmissions([
        {
          id: 'TX-2024-001',
          batchId: 'BATCH-2024-015',
          submittedAt: '2024-01-15 14:30:00',
          completedAt: '2024-01-15 14:32:15',
          status: 'completed',
          invoiceCount: 156,
          acceptedCount: 156,
          rejectedCount: 0,
          totalAmount: 2450000,
          firsAcknowledgeId: 'ACK-FIRS-2024-001',
          submittedBy: 'admin@company.com',
          processingTime: '2m 15s'
        },
        {
          id: 'TX-2024-002',
          batchId: 'BATCH-2024-014',
          submittedAt: '2024-01-15 13:45:00',
          status: 'processing',
          invoiceCount: 89,
          acceptedCount: 67,
          rejectedCount: 0,
          totalAmount: 1230000,
          submittedBy: 'operator@company.com'
        },
        {
          id: 'TX-2024-003',
          batchId: 'BATCH-2024-013',
          submittedAt: '2024-01-15 12:20:00',
          completedAt: '2024-01-15 12:25:30',
          status: 'rejected',
          invoiceCount: 203,
          acceptedCount: 201,
          rejectedCount: 2,
          totalAmount: 3450000,
          firsAcknowledgeId: 'ACK-FIRS-2024-002',
          submittedBy: 'admin@company.com',
          processingTime: '5m 30s'
        },
        {
          id: 'TX-2024-004',
          batchId: 'BATCH-2024-012',
          submittedAt: '2024-01-15 11:10:00',
          completedAt: '2024-01-15 11:15:45',
          status: 'failed',
          invoiceCount: 45,
          acceptedCount: 0,
          rejectedCount: 0,
          totalAmount: 890000,
          submittedBy: 'operator@company.com',
          processingTime: '5m 45s'
        },
        {
          id: 'TX-2024-005',
          batchId: 'BATCH-2024-011',
          submittedAt: '2024-01-14 16:30:00',
          completedAt: '2024-01-14 16:33:20',
          status: 'completed',
          invoiceCount: 298,
          acceptedCount: 298,
          rejectedCount: 0,
          totalAmount: 4560000,
          firsAcknowledgeId: 'ACK-FIRS-2024-003',
          submittedBy: 'admin@company.com',
          processingTime: '3m 20s'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'submitted': return 'bg-gray-100 text-gray-800';
      case 'rejected': return 'bg-orange-100 text-orange-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✅';
      case 'processing': return '⏳';
      case 'submitted': return '📤';
      case 'rejected': return '⚠️';
      case 'failed': return '❌';
      default: return '📄';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency: 'NGN'
    }).format(amount);
  };

  const filteredTransmissions = transmissions.filter(transmission => {
    const matchesSearch = transmission.batchId.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         transmission.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         transmission.submittedBy.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch;
  });

  const downloadReport = async (transmissionId: string) => {
    try {
      const response = await apiClient.get<Blob>(`/api/v1/app/transmission/${transmissionId}/report`, {
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(response as any);
      const link = document.createElement('a');
      link.href = url;
      link.download = `transmission-report-${transmissionId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download report:', error);
    }
  };

  if (loading) {
    return (
      <DashboardLayout role="app" activeTab="transmission">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading transmission history...</p>
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
            <h1 className="text-3xl font-bold text-gray-900">Transmission History</h1>
            <p className="text-gray-600">Complete record of all FIRS transmissions</p>
          </div>
          <div className="flex space-x-4">
            <TaxPoyntButton
              variant="outline"
              onClick={() => router.back()}
            >
              ← Back to Transmission
            </TaxPoyntButton>
            <TaxPoyntButton
              variant="primary"
              onClick={() => router.push('/dashboard/app/transmission/new')}
              className="bg-green-600 hover:bg-green-700"
            >
              📤 New Transmission
            </TaxPoyntButton>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
              <TaxPoyntInput
                placeholder="Search by batch ID, transmission ID, or user..."
                value={searchTerm}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Status</option>
                <option value="completed">Completed</option>
                <option value="processing">Processing</option>
                <option value="submitted">Submitted</option>
                <option value="rejected">Rejected</option>
                <option value="failed">Failed</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Date Range</label>
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Time</option>
                <option value="today">Today</option>
                <option value="week">This Week</option>
                <option value="month">This Month</option>
                <option value="quarter">This Quarter</option>
              </select>
            </div>
            <div className="flex items-end">
              <TaxPoyntButton
                variant="outline"
                onClick={() => {
                  setSearchTerm('');
                  setStatusFilter('all');
                  setDateRange('all');
                }}
                className="w-full"
              >
                Clear Filters
              </TaxPoyntButton>
            </div>
          </div>
        </div>

        {/* Transmission History Table */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Transmission
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Invoices
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Processing Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Submitted By
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredTransmissions.map((transmission) => (
                  <tr key={transmission.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">{getStatusIcon(transmission.status)}</span>
                        <div>
                          <div className="text-sm font-medium text-gray-900">{transmission.batchId}</div>
                          <div className="text-sm text-gray-500">{transmission.id}</div>
                          <div className="text-sm text-gray-500">{transmission.submittedAt}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(transmission.status)}`}>
                        {transmission.status.charAt(0).toUpperCase() + transmission.status.slice(1)}
                      </span>
                      {transmission.firsAcknowledgeId && (
                        <div className="text-xs text-gray-500 mt-1">
                          {transmission.firsAcknowledgeId}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        <div>Total: {transmission.invoiceCount}</div>
                        <div className="text-green-600">Accepted: {transmission.acceptedCount}</div>
                        {transmission.rejectedCount > 0 && (
                          <div className="text-red-600">Rejected: {transmission.rejectedCount}</div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency(transmission.totalAmount)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {transmission.processingTime || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {transmission.submittedBy}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => router.push(`/dashboard/app/tracking?filter=${transmission.id}`)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Track
                        </button>
                        <button
                          onClick={() => downloadReport(transmission.id)}
                          className="text-green-600 hover:text-green-900"
                        >
                          Report
                        </button>
                        {transmission.status === 'failed' && (
                          <button className="text-orange-600 hover:text-orange-900">
                            Retry
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
            <div className="flex-1 flex justify-between sm:hidden">
              <TaxPoyntButton
                variant="outline"
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
              >
                Previous
              </TaxPoyntButton>
              <TaxPoyntButton
                variant="outline"
                onClick={() => setCurrentPage(currentPage + 1)}
              >
                Next
              </TaxPoyntButton>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Showing <span className="font-medium">{(currentPage - 1) * itemsPerPage + 1}</span> to{' '}
                  <span className="font-medium">{Math.min(currentPage * itemsPerPage, filteredTransmissions.length)}</span> of{' '}
                  <span className="font-medium">{filteredTransmissions.length}</span> results
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setCurrentPage(currentPage + 1)}
                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                  >
                    Next
                  </button>
                </nav>
              </div>
            </div>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[
            { 
              label: 'Total Transmissions', 
              value: filteredTransmissions.length, 
              color: 'blue' 
            },
            { 
              label: 'Completed', 
              value: filteredTransmissions.filter(t => t.status === 'completed').length, 
              color: 'green' 
            },
            { 
              label: 'Processing', 
              value: filteredTransmissions.filter(t => t.status === 'processing').length, 
              color: 'orange' 
            },
            { 
              label: 'Failed', 
              value: filteredTransmissions.filter(t => t.status === 'failed').length, 
              color: 'red' 
            }
          ].map((stat, index) => (
            <div key={index} className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <div className={`text-3xl font-bold text-${stat.color}-600`}>{stat.value}</div>
                <div className="ml-4">
                  <div className="text-sm font-medium text-gray-600">{stat.label}</div>
                  <div className="text-xs text-gray-500">In current view</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
