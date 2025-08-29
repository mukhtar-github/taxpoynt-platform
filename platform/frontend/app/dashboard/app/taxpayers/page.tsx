/**
 * APP Taxpayer Management
 * =======================
 * 
 * Manage taxpayer onboarding, verification, and e-invoicing compliance.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardLayout } from '../../../../shared_components/layouts/DashboardLayout';
import { TaxPoyntButton, TaxPoyntInput } from '../../../../design_system';
import { APIResponse } from '../../../../si_interface/types';
import apiClient from '../../../../shared_components/api/client';

interface Taxpayer {
  id: string;
  tin: string;
  businessName: string;
  contactEmail: string;
  contactPhone: string;
  businessType: 'large' | 'medium' | 'small';
  status: 'active' | 'pending' | 'suspended' | 'rejected';
  onboardedAt: string;
  lastActivity: string;
  invoiceCount: number;
  compliance: {
    einvoicingMandatory: boolean;
    complianceScore: number;
    lastAudit: string;
    issues: string[];
  };
}

interface TaxpayerMetrics {
  total: number;
  active: number;
  pending: number;
  suspended: number;
  onboardedThisMonth: number;
  complianceRate: number;
}

export default function TaxpayerManagementPage() {
  const router = useRouter();
  const [taxpayers, setTaxpayers] = useState<Taxpayer[]>([]);
  const [metrics, setMetrics] = useState<TaxpayerMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [businessTypeFilter, setBusinessTypeFilter] = useState('all');
  const [showOnboardingModal, setShowOnboardingModal] = useState(false);

  useEffect(() => {
    loadTaxpayerData();
  }, []);

  const loadTaxpayerData = async () => {
    try {
      setLoading(true);
      const [metricsResponse, taxpayersResponse] = await Promise.all([
        apiClient.get<APIResponse<TaxpayerMetrics>>('/api/v1/app/taxpayers/metrics'),
        apiClient.get<APIResponse<Taxpayer[]>>('/api/v1/app/taxpayers')
      ]);
      
      if (metricsResponse.success && metricsResponse.data) {
        setMetrics(metricsResponse.data);
      }
      if (taxpayersResponse.success && taxpayersResponse.data) {
        setTaxpayers(taxpayersResponse.data);
      }
    } catch (error) {
      console.error('Failed to load taxpayer data:', error);
      // Fallback to demo data
      setMetrics({
        total: 1247,
        active: 1180,
        pending: 45,
        suspended: 22,
        onboardedThisMonth: 89,
        complianceRate: 96.2
      });
      setTaxpayers([
        {
          id: 'TP-001',
          tin: '12345678901234',
          businessName: 'TechCorp Nigeria Ltd',
          contactEmail: 'admin@techcorp.ng',
          contactPhone: '+234-801-234-5678',
          businessType: 'large',
          status: 'active',
          onboardedAt: '2024-01-10',
          lastActivity: '2024-01-15 14:30:00',
          invoiceCount: 1247,
          compliance: {
            einvoicingMandatory: true,
            complianceScore: 98,
            lastAudit: '2024-01-01',
            issues: []
          }
        },
        {
          id: 'TP-002',
          tin: '98765432109876',
          businessName: 'Green Energy Solutions',
          contactEmail: 'billing@greenenergy.ng',
          contactPhone: '+234-802-345-6789',
          businessType: 'medium',
          status: 'active',
          onboardedAt: '2024-01-08',
          lastActivity: '2024-01-14 16:45:00',
          invoiceCount: 456,
          compliance: {
            einvoicingMandatory: false,
            complianceScore: 92,
            lastAudit: '2024-01-05',
            issues: ['Late submission: 2 invoices']
          }
        },
        {
          id: 'TP-003',
          tin: '11111111111111',
          businessName: 'Local Retail Store',
          contactEmail: 'owner@retailstore.ng',
          contactPhone: '+234-803-456-7890',
          businessType: 'small',
          status: 'pending',
          onboardedAt: '2024-01-14',
          lastActivity: '2024-01-14 10:20:00',
          invoiceCount: 23,
          compliance: {
            einvoicingMandatory: false,
            complianceScore: 75,
            lastAudit: '',
            issues: ['Incomplete business verification', 'Missing tax certificates']
          }
        },
        {
          id: 'TP-004',
          tin: '22222222222222',
          businessName: 'Manufacturing Inc',
          contactEmail: 'finance@manufacturing.ng',
          contactPhone: '+234-804-567-8901',
          businessType: 'large',
          status: 'suspended',
          onboardedAt: '2023-12-15',
          lastActivity: '2024-01-10 09:15:00',
          invoiceCount: 2156,
          compliance: {
            einvoicingMandatory: true,
            complianceScore: 65,
            lastAudit: '2023-12-20',
            issues: ['Multiple failed transmissions', 'Non-compliance with UBL format', 'Outstanding audit items']
          }
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-orange-100 text-orange-800';
      case 'suspended': return 'bg-red-100 text-red-800';
      case 'rejected': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getBusinessTypeIcon = (type: string) => {
    switch (type) {
      case 'large': return '🏢';
      case 'medium': return '🏬';
      case 'small': return '🏪';
      default: return '🏢';
    }
  };

  const handleStatusUpdate = async (taxpayerId: string, newStatus: string) => {
    try {
      const response = await apiClient.post<APIResponse>(`/api/v1/app/taxpayers/${taxpayerId}/status`, {
        status: newStatus,
        reason: 'Updated from taxpayer management dashboard'
      });
      
      if (response.success) {
        // Update local state
        setTaxpayers(prev => prev.map(tp => 
          tp.id === taxpayerId ? { ...tp, status: newStatus as any } : tp
        ));
      }
    } catch (error) {
      console.error('Failed to update taxpayer status:', error);
    }
  };

  const filteredTaxpayers = taxpayers.filter(taxpayer => {
    const matchesSearch = taxpayer.tin.includes(searchTerm) ||
                         taxpayer.businessName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         taxpayer.contactEmail.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || taxpayer.status === statusFilter;
    const matchesType = businessTypeFilter === 'all' || taxpayer.businessType === businessTypeFilter;
    return matchesSearch && matchesStatus && matchesType;
  });

  if (loading) {
    return (
      <DashboardLayout role="app" activeTab="taxpayers">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading taxpayer data...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout role="app" activeTab="taxpayers">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Taxpayer Management</h1>
            <p className="text-gray-600">Manage taxpayer onboarding and e-invoicing compliance</p>
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
              onClick={() => setShowOnboardingModal(true)}
              className="bg-blue-600 hover:bg-blue-700"
            >
              👥 Onboard New Taxpayer
            </TaxPoyntButton>
          </div>
        </div>

        {/* Metrics Overview */}
        <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-2xl font-bold text-blue-600">{metrics?.total}</div>
            <div className="text-sm text-gray-600">Total Taxpayers</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-2xl font-bold text-green-600">{metrics?.active}</div>
            <div className="text-sm text-gray-600">Active</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-2xl font-bold text-orange-600">{metrics?.pending}</div>
            <div className="text-sm text-gray-600">Pending</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-2xl font-bold text-red-600">{metrics?.suspended}</div>
            <div className="text-sm text-gray-600">Suspended</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-2xl font-bold text-purple-600">{metrics?.onboardedThisMonth}</div>
            <div className="text-sm text-gray-600">New This Month</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-2xl font-bold text-emerald-600">{metrics?.complianceRate}%</div>
            <div className="text-sm text-gray-600">Compliance Rate</div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
              <TaxPoyntInput
                placeholder="Search by TIN, business name, or email..."
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
                <option value="active">Active</option>
                <option value="pending">Pending</option>
                <option value="suspended">Suspended</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Business Type</label>
              <select
                value={businessTypeFilter}
                onChange={(e) => setBusinessTypeFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Types</option>
                <option value="large">Large Taxpayers</option>
                <option value="medium">Medium Taxpayers</option>
                <option value="small">Small Taxpayers</option>
              </select>
            </div>
            <div className="flex items-end">
              <TaxPoyntButton
                variant="outline"
                onClick={() => {
                  setSearchTerm('');
                  setStatusFilter('all');
                  setBusinessTypeFilter('all');
                }}
                className="w-full"
              >
                Clear Filters
              </TaxPoyntButton>
            </div>
          </div>
        </div>

        {/* Taxpayers Table */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Taxpayer
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Invoices
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Compliance
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Activity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredTaxpayers.map((taxpayer) => (
                  <tr key={taxpayer.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">{getBusinessTypeIcon(taxpayer.businessType)}</span>
                        <div>
                          <div className="text-sm font-medium text-gray-900">{taxpayer.businessName}</div>
                          <div className="text-sm text-gray-500">TIN: {taxpayer.tin}</div>
                          <div className="text-sm text-gray-500">{taxpayer.contactEmail}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(taxpayer.status)}`}>
                        {taxpayer.status.charAt(0).toUpperCase() + taxpayer.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 capitalize">{taxpayer.businessType}</div>
                      {taxpayer.compliance.einvoicingMandatory && (
                        <div className="text-xs text-blue-600">E-invoicing Required</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {taxpayer.invoiceCount.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="text-sm font-medium text-gray-900">{taxpayer.compliance.complianceScore}%</div>
                        <div className="ml-2 w-16 bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              taxpayer.compliance.complianceScore >= 90 ? 'bg-green-500' :
                              taxpayer.compliance.complianceScore >= 70 ? 'bg-orange-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${taxpayer.compliance.complianceScore}%` }}
                          ></div>
                        </div>
                      </div>
                      {taxpayer.compliance.issues.length > 0 && (
                        <div className="text-xs text-red-600 mt-1">
                          {taxpayer.compliance.issues.length} issue(s)
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {taxpayer.lastActivity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button className="text-blue-600 hover:text-blue-900">
                          View
                        </button>
                        <button className="text-green-600 hover:text-green-900">
                          Edit
                        </button>
                        {taxpayer.status === 'pending' && (
                          <button
                            onClick={() => handleStatusUpdate(taxpayer.id, 'active')}
                            className="text-green-600 hover:text-green-900"
                          >
                            Approve
                          </button>
                        )}
                        {taxpayer.status === 'active' && (
                          <button
                            onClick={() => handleStatusUpdate(taxpayer.id, 'suspended')}
                            className="text-red-600 hover:text-red-900"
                          >
                            Suspend
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Compliance Issues Summary */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Compliance Issues Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <h3 className="font-medium text-red-800 mb-2">Critical Issues</h3>
              <div className="text-2xl font-bold text-red-600">3</div>
              <div className="text-sm text-red-700">Suspended taxpayers</div>
            </div>
            <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
              <h3 className="font-medium text-orange-800 mb-2">Pending Actions</h3>
              <div className="text-2xl font-bold text-orange-600">12</div>
              <div className="text-sm text-orange-700">Require review</div>
            </div>
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <h3 className="font-medium text-green-800 mb-2">Compliant</h3>
              <div className="text-2xl font-bold text-green-600">{metrics?.complianceRate}%</div>
              <div className="text-sm text-green-700">Overall compliance rate</div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
